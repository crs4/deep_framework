import face_extractor_constants as fec
import cv2
from facenet_tools import FaceNet
import numpy as np
import os
import pickle
import shutil
import sys
import tensorflow as tf
import utils
import yaml
sys.path.insert(0, fec.FACENET_SRC_PATH)
import facenet


class FaceRecognition:
    """
    Face recognition with FaceNet

    :type params: dictionary
    :param params: configuration parameters (see table)

    ================================  ====================================================  ============================
        Key                           Value                                                 Default value
    ================================  ====================================================  ============================
    scale_factor                      scale factor between two scans in face detection      0.709
    detection_threshold_1             detection threshold for first step                    0.6
    detection_threshold_2             detection threshold for second step                   0.7
    detection_threshold_3             detection threshold for third step                    0.7
    min_size                          minimum size of face detection                        20
                                      bounding box (in pixels)
    gpu_memory_fraction               GPU memory fraction to be used                        0.9
    facenet_model_path                path of FaceNet model
    face_recognition_dir_path         path of directory with people recognition data
    face_recognition_threshold        threshold for retaining prediction
                                      in face recognition
                                      (faces whose prediction has a
                                      confidence value greater than this
                                      will be considered unknown)
    ================================  ====================================================  ============================
    """

    def __init__(self, params=None):
        """
        Initialize the face models

        :type params: dictionary
        :param params: configuration parameters
        """

        self.params = params

        # Set parameters
        self.scale_factor = fec.FACENET_FACE_DETECTION_SCALE_FACTOR
        det_threshold_1 = fec.FACENET_DETECTION_THRESHOLD_1
        det_threshold_2 = fec.FACENET_DETECTION_THRESHOLD_2
        det_threshold_3 = fec.FACENET_DETECTION_THRESHOLD_3
        self.min_size = fec.FACENET_FACE_DETECTION_MIN_SIZE
        self.model_path = fec.FACENET_MODEL_PATH
        self.data_dir_path = fec.FACE_REC_DATA_DIR_PATH
        self.face_rec_threshold = fec.FACE_REC_THRESHOLD
        if self.params is not None:
            if fec.FACENET_FACE_DETECTION_SCALE_FACTOR_KEY in params:
                self.scale_factor = params[fec.FACENET_FACE_DETECTION_SCALE_FACTOR_KEY]
            if fec.FACENET_DETECTION_THRESHOLD_1_KEY in params:
                det_threshold_1 = params[fec.FACENET_DETECTION_THRESHOLD_1_KEY]
            if fec.FACENET_DETECTION_THRESHOLD_2_KEY in params:
                det_threshold_2 = params[fec.FACENET_DETECTION_THRESHOLD_2_KEY]
            if fec.FACENET_DETECTION_THRESHOLD_3_KEY in params:
                det_threshold_3 = params[fec.FACENET_DETECTION_THRESHOLD_3_KEY]
            if fec.FACENET_FACE_DETECTION_MIN_SIZE_KEY in params:
                self.min_size = params[fec.FACENET_FACE_DETECTION_MIN_SIZE_KEY]
            if fec.FACENET_MODEL_PATH_KEY in params:
                self.model_path = params[fec.FACENET_MODEL_PATH_KEY]
            if fec.FACE_REC_DATA_DIR_PATH_KEY in params:
                self.data_dir_path = params[fec.FACE_REC_DATA_DIR_PATH_KEY]
            if fec.FACE_REC_THRESHOLD_KEY in self.params:
                self.face_rec_threshold = self.params[fec.FACE_REC_THRESHOLD_KEY]

        self.det_thresholds = [det_threshold_1, det_threshold_2, det_threshold_3]

        # Initialize tools for face detection and alignment
        self.tools = FaceNet(params)

        # Create directory with people recognition data if it does not exist
        if not os.path.exists(self.data_dir_path):
            os.makedirs(self.data_dir_path)

        # Load existing face models
        self.models = None
        self.load_models()

    def add_faces(self, labels, tags, im_paths, add_rotations=False):
        """
        Add faces to face models for people recognition

        :type labels: list
        :param labels: identifiers of people in database

        :type tags: list
        :param tags: tags of people whom faces belong to

        :type im_paths: list
        :param im_paths: paths of images containing the faces

        :type add_rotations: boolean
        :param add_rotations: if True, add face rotations up to 45 degrees to dataset

        :rtype: boolean
        :returns: true if faces have been added
        """

        ok = False

        try:

            # Check if face models are loaded
            if not self.models:
                self.models = {}

            # Load file with tag-label associations
            tag_label_associations_file_name = fec.TAG_LABEL_ASSOCIATIONS_FILE + '_facenet.yaml'
            tag_label_associations_file_path = os.path.join(
                self.data_dir_path, tag_label_associations_file_name)

            tag_label_associations = None
            max_existing_label = 0
            if os.path.exists(tag_label_associations_file_path):
                tag_label_associations = utils.load_YAML_file(
                    tag_label_associations_file_path)
                max_existing_label = max(tag_label_associations.keys()) + 1

            im_list = []
            good_labels = []
            good_tags = []
            i = 0
            for im_path in im_paths:

                print('Adding %s to face model' % im_path)

                img = cv2.imread(im_path, cv2.IMREAD_COLOR)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Detect largest face and align it
                (bbox, aligned_face) = self.tools.align_face(img)

                if aligned_face is not None:

                    # Prewhiten face
                    face = facenet.prewhiten(aligned_face)

                    im_list.append(face)

                    label = labels[i] + max_existing_label
                    good_labels.append(label)
                    tag = tags[i]
                    good_tags.append(tag)

                    if add_rotations:
                        (h, w, ch) = face.shape
                        for rot in range(-91, 91, 10):

                            # Compute a rotation matrix with respect to the center of the image
                            center = (w / 2, h / 2)
                            scale = 1
                            rot_mat = cv2.getRotationMatrix2D(center, rot, scale)

                            # Rotate image
                            out_im_size = (w, h)
                            face_rot = cv2.warpAffine(face, rot_mat, out_im_size)

                            # Resize image in order to not contain black regions
                            (w_crop, h_crop) = utils.get_rotated_image_size(w, h, rot)
                            x1_crop = int((w - w_crop) / 2.0)
                            y1_crop = int((h - h_crop) / 2.0)
                            x2_crop = x1_crop + w_crop
                            y2_crop = y1_crop + h_crop
                            face_crop = face_rot[y1_crop:y2_crop, x1_crop:x2_crop]

                            # Resize face_crop to same shape as original face
                            face_crop = cv2.resize(face_crop, dsize=(h, w))

                            im_list.append(face_crop)
                            good_labels.append(label)
                            good_tags.append(tag)

                i += 1

            if len(im_list) > 0:

                # Create representations for faces
                imgs = np.stack(im_list)
                with tf.Graph().as_default():
                    with tf.Session() as sess:

                        # Load model
                        facenet.load_model(self.model_path)

                        # Get input and output tensors
                        images_placeholder = tf.get_default_graph().get_tensor_by_name('input:0')
                        embeddings = tf.get_default_graph().get_tensor_by_name('embeddings:0')
                        phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")

                        # Run forward pass to calculate embeddings
                        feed_dict = {images_placeholder: imgs, phase_train_placeholder: False}
                        reps = sess.run(embeddings, feed_dict=feed_dict)

                # Check if there are existing models
                if 'reps' in self.models and 'labels' in self.models:

                    # Update existing face models
                    existing_reps = self.models['reps']
                    self.models['reps'] = np.concatenate((existing_reps, reps))
                    self.models['labels'].extend(good_labels)
                else:

                    # Create face models
                    self.models['reps'] = reps
                    self.models['labels'] = good_labels

                # Save file with face models
                db_file_name = fec.FACE_MODELS_FILE + '_facenet'
                db_file_path = os.path.join(
                    self.data_dir_path, db_file_name)

                with open(db_file_path, 'wb') as f:
                    pickle.dump(self.models, f)

                if not tag_label_associations:

                    # Create dictionary with tag-label associations
                    tag_label_associations = {}

                # Add new tags with related labels
                i = 0
                for label in good_labels:
                    tag = good_tags[i]
                    tag_label_associations[label] = tag
                    i += 1

                # Save new dictionary in YAML file
                utils.save_YAML_file(
                    tag_label_associations_file_path, tag_label_associations)

        except IOError as e:
            errno, strerror = e.args
            print("I/O error({0}): {1}".format(errno, strerror))
            print('I/O error')

        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise

        return ok

    def change_tag_to_label(self, label, tag):
        """
        Change tag to given label

        :type label: integer
        :param label: label whose tag is to be changed

        :type tag: string
        :param tag: tag to be used for given label
        """

        # Load file with tag-label associations
        tag_label_associations_file_name = fec.TAG_LABEL_ASSOCIATIONS_FILE + '_facenet.yaml'
        tag_label_associations_file_path = os.path.join(
            self.data_dir_path, tag_label_associations_file_name)
        tag_label_associations = utils.load_YAML_file(
            tag_label_associations_file_path)

        if label in tag_label_associations:
            tag_label_associations[label] = tag

        # Save file
        utils.save_YAML_file(
            tag_label_associations_file_path, tag_label_associations)

    def delete_models(self):
        """
        Delete all data for face recognition
        """

        for item in os.listdir(self.data_dir_path):
            item_path = os.path.join(self.data_dir_path, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except IOError as e:
                errno, strerror = e.args
                print("I/O error({0}): {1}".format(errno, strerror))
            except:
                print("Unexpected error:", sys.exc_info()[0])
                raise

    def get_labels(self):
        """
        Get all labels

        :rtype: set
        :returns: a set containing all labels
        """

        labels = []
        tag_label_associations = None

        # Load file with tag-label associations
        tag_label_associations_file_name = fec.TAG_LABEL_ASSOCIATIONS_FILE + '_facenet.yaml'
        tag_label_associations_file_path = os.path.join(
            self.data_dir_path, tag_label_associations_file_name)
        if os.path.exists(tag_label_associations_file_path):
            tag_label_associations = utils.load_YAML_file(
                tag_label_associations_file_path)

        if tag_label_associations:
            labels = tag_label_associations.keys()

        return set(labels)

    def get_labels_for_tag(self, tag):
        """
        Get labels corresponding to given tag

        :type tag: string
        :param tag: tag for which corresponding label is wanted

        :rtype: list
        :returns: list of labels corresponding to given tag
        """

        labels = []

        # Load file with tag-label associations
        tag_label_associations_file_name = fec.TAG_LABEL_ASSOCIATIONS_FILE + '_facenet.yaml'
        tag_label_associations_file_path = os.path.join(
            self.data_dir_path, tag_label_associations_file_name)
        tag_label_associations = utils.load_YAML_file(
            tag_label_associations_file_path)

        if tag_label_associations:
            for dict_label, dict_tag in tag_label_associations.items():
                if dict_tag == tag:
                    labels.append(dict_label)

        return labels

    def get_tag(self, label):
        """
        Get tag corresponding to given label

        :type label: integer
        :param label: label for which corresponding tag is wanted

        :rtype: string
        :returns: tag corresponding to given label
        """

        tag = fec.UNDEFINED_TAG

        # Load file with tag-label associations
        tag_label_associations_file_name = fec.TAG_LABEL_ASSOCIATIONS_FILE + '_facenet.yaml'
        tag_label_associations_file_path = os.path.join(
            self.data_dir_path, tag_label_associations_file_name)
        tag_label_associations = utils.load_YAML_file(
            tag_label_associations_file_path)

        if (tag_label_associations and
                (label in tag_label_associations)):
            tag = tag_label_associations[label]

        return tag

    def get_tags(self):
        """
        Get all tags

        :rtype: set
        :returns: a set containing all tags
        """

        tags = []

        # Load file with tag-label associations
        tag_label_associations_file_name = fec.TAG_LABEL_ASSOCIATIONS_FILE + '_facenet.yaml'
        tag_label_associations_file_path = os.path.join(
            self.data_dir_path, tag_label_associations_file_name)
        tag_label_associations = utils.load_YAML_file(
            tag_label_associations_file_path)

        if tag_label_associations:
            tags = tag_label_associations.values()

        return set(tags)

    def get_people_nr(self):
        """
        Get number of people in face model

        :rtype: integer
        :returns: number of people in face model
        """

        labels = self.get_labels()

        people_nr = len(labels)

        return people_nr

    def load_models(self):
        """
        Load face models

        :rtype: boolean
        :returns: True if models were successfully loaded,
                  False otherwise
        """

        ok = False

        # File where models are saved
        db_file_name = fec.FACE_MODELS_FILE + '_facenet'
        db_file_path = os.path.join(
            self.data_dir_path, db_file_name)

        # Check if file with models exist
        if os.path.exists(db_file_path):
            with open(db_file_path, 'rb') as f:

                # Load models
                self.models = pickle.load(f)
                ok = True
        return ok

    def recognize_face(self, face, align=True, bbox=None):
        """
        Recognize given face using
        the stored face recognition models

        :type face: numpy.ndarray (3 channel RGB image)
        :param face: face to be recognized

        :type align: bool
        :param align: if True, align face

        :type bbox: tuple
        :param bbox: face bounding box as a (x, y, width, height) tuple,
                     if not given largest face found in image is considered

        :rtype: tuple
        :returns: a tuple containing face bounding box (in dlib's format),
                  predicted label and corresponding confidence
        """

        # Set parameters
        cropped_face_size = fec.FACENET_ALIGNED_FACE_SIZE
        face_rec_threshold = fec.FACE_REC_THRESHOLD
        if self.params is not None:
            if fec.FACE_REC_THRESHOLD_KEY in self.params:
                face_rec_threshold = self.params[fec.FACE_REC_THRESHOLD_KEY]

        label = fec.UNDEFINED_LABEL
        conf = sys.maxint

        if align:
            (bbox, face) = self.tools.align_face(face, bbox)
        else:
            # Check size of image and, if necessary, resize it
            width, height = face.shape
            if width != cropped_face_size or height != cropped_face_size:
                face = cv2.resize(face, (cropped_face_size, cropped_face_size))

        if face is not None and self.models is not None:
            # Create representation for face

            # Prewhiten face
            face = facenet.prewhiten(face)

            im_list = [face]
            imgs = np.stack(im_list)

            with tf.Graph().as_default():
                with tf.Session() as sess:

                    # Load model
                    facenet.load_model(self.model_path)

                    # Get input and output tensors
                    images_placeholder = tf.get_default_graph().get_tensor_by_name('input:0')
                    embeddings = tf.get_default_graph().get_tensor_by_name('embeddings:0')
                    phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")

                    # Run forward pass to calculate embedding
                    feed_dict = {images_placeholder: imgs, phase_train_placeholder: False}
                    rep = sess.run(embeddings, feed_dict=feed_dict)

            # Get representations from train model
            train_reps = self.models['reps']
            train_labels = self.models['labels']

            # Iterate through representations
            # in training model
            for t in range(0, len(train_reps)):
                train_rep = train_reps[t, :]

                # Calculate distance between faces
                diff = np.sqrt(np.sum(np.square(np.subtract(rep, train_rep))))

                if ((diff < conf) and
                        (diff < face_rec_threshold)):
                    conf = diff
                    label = train_labels[t]

        return bbox, label, conf

    def recognize_faces(self, faces, align=True, bboxes=None):
        """
        Recognize given faces using
        the stored face recognition models

        :type faces: list of numpy.ndarray (3 channel RGB images)
        :param face: list of faces to be recognized

        :type align: bool
        :param align: if True, align faces

        :type bboxes: list
        :param bboxes: list of face bounding boxes as (x, y, width, height) tuples,
                       if not given largest face found in image is considered

        :rtype: list
        :returns: a list of a tuples containing each the face bounding box as a (x, y, width, height) tuple,
                  predicted label and corresponding confidence
        """

        # Set parameters
        cropped_face_size = fec.FACENET_ALIGNED_FACE_SIZE
        face_rec_threshold = fec.FACE_REC_THRESHOLD
        if self.params is not None:
            if fec.FACE_REC_THRESHOLD_KEY in self.params:
                face_rec_threshold = self.params[fec.FACE_REC_THRESHOLD_KEY]

        im_list = []
        new_bboxes = []
        good_face_counters = []
        result = None

        if self.models is not None:

            result = []

            # Create list of faces
            face_counter = 0
            for face in faces:

                if bboxes:
                    bbox = bboxes[face_counter]
                else:
                    bbox = None

                if align:
                    (bbox, face) = self.tools.align_face(face, bbox)
                else:
                    # Check size of image and, if necessary, resize it
                    width, height = face.shape
                    if width != cropped_face_size or height != cropped_face_size:
                        face = cv2.resize(face, (cropped_face_size, cropped_face_size))

                if face is not None:

                    # Prewhiten face
                    face = facenet.prewhiten(face)

                    im_list.append(face)
                    good_face_counters.append(face_counter)

                new_bboxes.append(bbox)
                face_counter += 1

            imgs = np.stack(im_list)

            # Create representation for faces
            with tf.Graph().as_default():
                with tf.Session() as sess:

                    # Load model
                    facenet.load_model(self.model_path)

                    # Get input and output tensors
                    images_placeholder = tf.get_default_graph().get_tensor_by_name('input:0')
                    embeddings = tf.get_default_graph().get_tensor_by_name('embeddings:0')
                    phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")

                    # Run forward pass to calculate embedding
                    feed_dict = {images_placeholder: imgs, phase_train_placeholder: False}
                    reps = sess.run(embeddings, feed_dict=feed_dict)

            # Get representations from train model
            train_reps = self.models['reps']
            train_labels = self.models['labels']

            # Iterate through representations \
            # of given faces
            face_counter = 0
            for i in range(len(faces)):

                label = fec.UNDEFINED_LABEL
                conf = sys.maxint
                bbox = None

                if face_counter in good_face_counters:

                    rep_index = good_face_counters.index(face_counter)
                    rep = reps[rep_index]
                    bbox = new_bboxes[face_counter]

                    # Iterate through representations
                    # in training model
                    for t in range(0, len(train_reps)):
                        train_rep = train_reps[t, :]

                        # Calculate distance between faces
                        diff = np.sqrt(np.sum(np.square(np.subtract(rep, train_rep))))

                        if ((diff < conf) and
                                (diff < face_rec_threshold)):
                            conf = diff
                            label = train_labels[t]

                result.append((bbox, label, conf))

                face_counter += 1

        return result

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Management of face models with FaceNet')
    parser.add_argument('--add_faces', '-a',  help='add faces contained in given directory to face models')
    parser.add_argument('--tags', '-t', help='list of directory/tag pairs', nargs='+')
    parser.add_argument('--add_rotations', '-r',
                        help='if used, add face rotations up to 45 degrees to dataset', action='store_true')
    parser.add_argument('--show_results', '-s', help='show results', action='store_true')
    parser.add_argument('--params', '-p', help='path of YAML file with algorithm parameters, '
                                               'if not provided default values will be used')

    args = parser.parse_args()

    params = None
    if args.params:
        with open(args.params, 'r') as stream:
            params = yaml.load(stream)

    fm = FaceRecognition(params)
    if args.add_faces:

        # Create dictionary with directory/tag pairs
        dirs_tags = {}
        if args.tags:
            counter = 1
            for item in args.tags:

                if counter % 2 != 0:

                    # Odd item -> directory
                    label = item

                else:

                    # Even item -> tag
                    tag = item
                    dirs_tags[label] = tag

                counter += 1

        labels = []
        tags = []
        im_paths = []
        label = 0
        for person_dir in os.listdir(args.add_faces):
            if person_dir in dirs_tags:
                tag = dirs_tags[person_dir]
            else:
                tag = person_dir

            person_dir_path = os.path.join(args.add_faces, person_dir)
            for im_name in os.listdir(person_dir_path):
                labels.append(label)
                tags.append(tag)
                im_path = os.path.join(person_dir_path, im_name)
                im_paths.append(im_path)
            label += 1

        fm.add_faces(labels, tags, im_paths, args.add_rotations)