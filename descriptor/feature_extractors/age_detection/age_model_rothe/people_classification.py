import cv2
import face_extractor_constants as c
from face_extractor_utils import batch, bbox_opencv_to_dlib
import facenet_tools as facenet
import numpy as np
import os
from scipy import misc
from screeninfo import get_monitors
import skimage.io
import sys

sys.path.insert(0, os.path.join(c.CAFFE_ROOT_PATH, 'python'))
import caffe

sys.path.insert(0, c.ADIENCE_ALIGN_MASTER_PATH)
from adiencealign.affine_alignment.affine_aligner import AffineAligner
from adiencealign.landmarks_detection.landmarks_detector import detect_landmarks
from adiencealign.common.landmarks import read_fidu


class PeopleClassification(object):
    """
    Tool for people classification
    """

    def __init__(self, params=None):
        """
        Initialize tool

        :type params: dictionary
        :param params: parameters (see table)
        ============================  ====================================================  ==============================================
        Key                           Value                                                 Default value
        ============================  ====================================================  ==============================================
        caffe_use_gpu                 if True, caffe will use GPU                           True
        tensorflow_use_gpu            if True, tensorflow (used for face detection)         False
                                      will use GPU
        model_dir_age                 path of directory containing neural network files     /home/idrogeno/caffe-master/models/age_model_rothe
                                      for age estimation
        model_definition_age          name of file containing the structure of the model    age.prototxt
                                      for age estimation
        model_weights_age             name of file containing the trained weights           dex_chalearn_iccv2015.caffemodel
                                      for age estimation
        model_dir_gender              path of directory containing neural network files     /home/idrogeno/caffe-master/models/gender_model_rothe
                                      for gender estimation
        model_definition_gender       name of file containing the structure of the model    age.prototxt
                                      for gender estimation
        model_weights_gender          name of file containing the trained weights           gender.caffemodel
                                      for age estimation
        im_width                      width to which images must be resized                 224
        im_height                     height to which images must be resized                224
        batch_size                    number of images to be processed in a single batch    32
        mean_image_file_path          path of file containing the mean dataset image
        mean_values                   tuple of RGB values to be used to normalize
                                      the images,if not provi+++ded values extracted from file
                                      with mean_image_file_path path will be used
        network_output                key used in dictionary containing network output      prob
        align_faces                   if True, align faces                                  False
        alignment                     type of alignment ('dlib' or 'adience')               'dlib'
        max_nr_pixels                 maximum number of pixels in the image                 400000
                                      (if image is bigger it will be resized)
        ============================  ====================================================  ==============================================
        """

        start = cv2.getTickCount()

        # Set configurable parameters
        self.caffe_use_gpu = c.CAFFE_USE_GPU
        self.tensorflow_use_gpu = c.TENSORFLOW_USE_GPU
        model_dir_age_path = c.CAFFE_MODEL_DIR_AGE_PATH
        model_def_age = c.CAFFE_MODEL_DEF_AGE
        model_weights_age = c.CAFFE_MODEL_WEIGHTS_AGE
        model_dir_gender_path = c.CAFFE_MODEL_DIR_GENDER_PATH
        model_def_gender = c.CAFFE_MODEL_DEF_GENDER
        model_weights_gender = c.CAFFE_MODEL_WEIGHTS_GENDER
        im_width = c.CAFFE_IM_WIDTH
        im_height = c.CAFFE_IM_HEIGHT
        self.batch_size = c.CAFFE_BATCH_SIZE
        mean_image_file_path = c.CAFFE_MEAN_IMAGE_FILE_PATH
        mean_values = None
        self.network_output = c.CAFFE_NETWORK_OUTPUT
        self.label_output = c.CAFFE_LABEL_OUTPUT
        self.align_faces = c.PEOPLE_CLASSIFICATION_ALIGN_FACES
        self.alignment_method = c.PEOPLE_CLASSIFICATION_ALIGNMENT_METHOD
        self.max_nr_pixels = c.MAX_NR_PIXELS

        if params is not None:
            if c.CAFFE_USE_GPU_KEY in params:
                self.caffe_use_gpu = params[c.CAFFE_USE_GPU_KEY]
            if c.TENSORFLOW_USE_GPU_KEY in params:
                self.tensorflow_use_gpu = params[c.TENSORFLOW_USE_GPU_KEY]
            if c.CAFFE_MODEL_DIR_AGE_PATH_KEY in params:
                model_dir_age_path = params[c.CAFFE_MODEL_DIR_AGE_PATH_KEY]
            if c.CAFFE_MODEL_DEF_AGE_KEY in params:
                model_def_age = params[c.CAFFE_MODEL_DEF_AGE_KEY]
            if c.CAFFE_MODEL_WEIGHTS_AGE_KEY in params:
                model_weights_age = params[c.CAFFE_MODEL_WEIGHTS_AGE_KEY]
            if c.CAFFE_MODEL_DIR_GENDER_PATH_KEY in params:
                model_dir_gender_path = params[c.CAFFE_MODEL_DIR_GENDER_PATH_KEY]
            if c.CAFFE_MODEL_DEF_GENDER_KEY in params:
                model_def_gender = params[c.CAFFE_MODEL_DEF_GENDER_KEY]
            if c.CAFFE_MODEL_WEIGHTS_GENDER_KEY in params:
                model_weights_gender = params[c.CAFFE_MODEL_WEIGHTS_GENDER_KEY]
            if c.CAFFE_IM_WIDTH_KEY in params:
                im_width = params[c.CAFFE_IM_WIDTH_KEY]
            if c.CAFFE_IM_HEIGHT_KEY in params:
                im_height = params[c.CAFFE_IM_HEIGHT_KEY]
            if c.CAFFE_BATCH_SIZE_KEY in params:
                self.batch_size = params[c.CAFFE_BATCH_SIZE_KEY]
            if c.CAFFE_MEAN_IMAGE_FILE_PATH_KEY in params:
                mean_image_file_path = params[c.CAFFE_MEAN_IMAGE_FILE_PATH_KEY]
            if c.CAFFE_MEAN_VALUES_KEY in params:
                mean_values = params[c.CAFFE_MEAN_VALUES_KEY]

                # Get values from string
                if type(mean_values) is str:
                    mean_values_str = mean_values[1:-1]  # Do not consider parenthesis
                    mean_values_items = mean_values_str.split(',')
                    mean_values = []
                    for item in mean_values_items:
                        mean_value = int(item)
                        mean_values.append(mean_value)

                mean_values = np.array(mean_values)
            if c.CAFFE_NETWORK_OUTPUT_KEY in params:
                self.network_output = params[c.CAFFE_NETWORK_OUTPUT_KEY]
            if c.CAFFE_LABEL_OUTPUT_KEY in params:
                self.label_output = params[c.CAFFE_LABEL_OUTPUT_KEY]
            if c.PEOPLE_CLASSIFICATION_ALIGN_FACES_KEY in params:
                self.align_faces = params[c.PEOPLE_CLASSIFICATION_ALIGN_FACES_KEY]
            if c.PEOPLE_CLASSIFICATION_ALIGNMENT_METHOD_KEY in params:
                self.alignment_method = params[c.PEOPLE_CLASSIFICATION_ALIGNMENT_METHOD_KEY]
            if c.MAX_NR_PIXELS_KEY in params:
                self.max_nr_pixels = params[c.MAX_NR_PIXELS_KEY]

        if self.caffe_use_gpu:
            caffe.set_mode_gpu()
        else:
            caffe.set_mode_cpu()

        caffe_mode = caffe.TEST

        # Define neural network for age estimation
        model_def_age_file_path = os.path.join(model_dir_age_path, model_def_age)
        model_weights_age_file_path = os.path.join(model_dir_age_path, model_weights_age)
        self.age_net = caffe.Net(model_def_age_file_path, model_weights_age_file_path, caffe_mode)

        # Define neural networ for gender estimation
        model_def_gender_file_path = os.path.join(model_dir_gender_path, model_def_gender)
        model_weights_gender_file_path = os.path.join(model_dir_gender_path, model_weights_gender)
        self.gender_net = caffe.Net(model_def_gender_file_path, model_weights_gender_file_path, caffe_mode)

        if mean_values is None:
            # Load the mean dataset image for subtraction
            mean_values = np.load(mean_image_file_path)
            mean_values_shape = mean_values.shape
            if len(mean_values_shape) == 3:
                mean_values = mean_values.mean(1).mean(1)  # average over pixels to obtain the mean (BGR) pixel values
            elif len(mean_values_shape) == 4:
                mean_values = mean_values.mean(2).mean(2)
                mean_values = mean_values[0]
            else:
                print 'Warning! Mean shape has %d axis instead of 3 or 4' % len(mean_values_shape)
                return

        # Create transformer for the age network
        self.age_transformer = caffe.io.Transformer({'data': self.age_net.blobs['data'].data.shape})

        self.age_transformer.set_transpose('data', (2, 0, 1))     # Move image channels to outermost dimension
        self.age_transformer.set_mean('data', mean_values)        # Subtract the dataset-mean value in each channel
        self.age_transformer.set_raw_scale('data', 255)           # Rescale from [0, 1] to [0, 255]
        self.age_transformer.set_channel_swap('data', (2, 1, 0))  # Swap channels from RGB to BGR

        # Create transformer for the gender network
        self.gender_transformer = caffe.io.Transformer({'data': self.gender_net.blobs['data'].data.shape})

        self.gender_transformer.set_transpose('data', (2, 0, 1))  # Move image channels to outermost dimension
        self.gender_transformer.set_mean('data', mean_values)  # Subtract the dataset-mean value in each channel
        self.gender_transformer.set_raw_scale('data', 255)  # Rescale from [0, 1] to [0, 255]
        self.gender_transformer.set_channel_swap('data', (2, 1, 0))  # Swap channels from RGB to BGR

        # Set the size of the input
        self.age_net.blobs['data'].reshape(self.batch_size,      # Batch size
                                           3,                    # 3-channel (BGR) images
                                           im_width, im_height)  # Image size is im_width x im_height
        self.gender_net.blobs['data'].reshape(self.batch_size,  # Batch size
                                              3,  # 3-channel (BGR) images
                                              im_width, im_height)  # Image size is im_width x im_height

        # Set aligner for 'adience' alignment
        if self.align_faces:
            if self.alignment_method == 'adience':
                fidu_model_file = os.path.join(c.ADIENCE_ALIGN_MASTER_PATH, 'adiencealign/resources/model_ang_0.txt')
                self.adience_aligner = AffineAligner(fidu_model_file=fidu_model_file)
                self.fidu_exec_dir = os.path.join(c.ADIENCE_ALIGN_MASTER_PATH, 'adiencealign/resources')
            elif self.alignment_method == 'dlib':
                self.opface = openface.Openface()
            else:
                print 'Warning! Alignment type not available. Alignment will not be carried out'

        self.fcnet = facenet.FaceNet()

        elapsed_time = (cv2.getTickCount() - start) / cv2.getTickFrequency()
        print '\nTime for initial setup: %02.02f seconds' % elapsed_time

    def save_faces(self, im_paths, only_largest_face=True, bbox_increase_pct=1.0, vert_offset=0.0,
                   square_faces=True, use_gpu=False, show_results=False):
        """
        Save faces detected in images

        :type im_paths: list
        :param im_paths: paths of image files or directories containing the images

        :type only_largest_face: boolean
        :param only_largest_face: if True, use only largest face detected in image

        :type bbox_increase_pct: float
        :param bbox_increase_pct: size of bounding box used for saving faces,
                                  in percentage of size of detection bounding box
        :type vert_offset: float
        :param vert_offset: vertical offset of bounding box used for saving faces,
                            from bottom, in percentage of size of new bounding box

        :type square_faces: boolean
        :param square_faces: if True, transform face detection bounding boxes into squares

        :type use_gpu: boolean
        :param use_gpu: if True, use GPU in face detection

        :type show_results: boolean
        :param show_results: if True, save bounding boxes that will be used when showing results of classification

        :rtype: dictionary
        :returns: results of face detection and alignment
        """

        # Hide GPUs
        if not use_gpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

        # Get paths of image files from directories
        im_file_paths = []
        for im_path in im_paths:
            if os.path.isfile(im_path):
                im_file_paths.append(im_path)
            else:
                for root, sub_dirs, files in os.walk(im_path):
                    for im_name in files:
                        im_path = os.path.join(root, im_name)
                        im_file_paths.append(im_path)

        # Detect faces and save them in temporary files
        im_face_paths = []
        im_bbox_paths = []
        show_im_paths = []
        original_paths = {}
        bboxes = {}
        for im_path in im_paths:

            im_basename, ext = os.path.splitext(im_path)

            # Detect faces in image
            start = cv2.getTickCount()
            faces = []

            while True:
                # Load image
                if self.align_faces and self.alignment_method == 'adience':
                    img = cv2.imread(im_path)
                else:
                    img = misc.imread(im_path)

                if img is not None and len(img.shape) >= 2:

                    # Resize image
                    h = img.shape[0]
                    w = img.shape[1]
                    resize_ratio = 1
                    while h * w > self.max_nr_pixels:
                        h = int(h / 2.0)
                        w = int(w / 2.0)
                        resize_ratio *= 2
                    if resize_ratio != 1:
                        resized_img = cv2.resize(img, (w, h))
                    else:
                        resized_img = img

                    if only_largest_face:
                        face_bbox = self.fcnet.detect_largest_face_in_image(resized_img)
                        if face_bbox is not None:
                            faces = [{'bbox': face_bbox}]
                    else:
                        faces = self.fcnet.detect_faces_in_image(resized_img)

                    break

            # TODO DELETE
            # elapsed_time = (cv2.getTickCount() - start) / cv2.getTickFrequency()
            # print '\nTime for face detection: %02.02f seconds' % elapsed_time

            face_counter = 0
            for face in faces:
                (or_x, or_y, or_width, or_height) = face['bbox']

                # Resize bounding box
                if resize_ratio != 1:
                    or_x = or_x * resize_ratio
                    or_y = or_y * resize_ratio
                    or_width = or_width * resize_ratio
                    or_height = or_height * resize_ratio

                if square_faces:

                    # Enlarge shorter side
                    if or_width < or_height:
                        width = height = or_height
                        width_diff = width - or_width
                        x = int(or_x - width_diff / 2.0)
                        y = or_y
                    elif or_height < or_width:
                        width = height = or_width
                        height_diff = height - or_height
                        x = or_x
                        y = int(or_y - height_diff / 2.0)
                    else:
                        (x, y, width, height) = (or_x, or_y, or_width, or_height)

                        # # Decrease longer side
                        # if or_width < or_height:
                        #     width = height = or_width
                        #     height_diff = or_height - height
                        #     x = or_x
                        #     y = int(or_y + height_diff)
                        # elif or_height < or_width:
                        #     width = height = or_height
                        #     width_diff = or_width - width
                        #     x = int(or_x + width_diff / 2.0)
                        #     y = or_y
                        # else:
                        #     (x, y, width, height) = (or_x, or_y, or_width, or_height)
                else:
                    (x, y, width, height) = (or_x, or_y, or_width, or_height)

                if self.align_faces and self.alignment_method == 'dlib':
                    dlib_bbox = bbox_opencv_to_dlib((x, y, width, height), img.shape)
                    (bbox, face_roi) = self.opface.align_face(img, dlib_bbox)
                else:
                    new_width = int(width * bbox_increase_pct)
                    new_height = int(height * bbox_increase_pct)
                    width_diff = new_width - width
                    height_diff = new_height - height
                    new_x1 = int(x - width_diff / 2.0)
                    new_y1 = int(y - height_diff / 2.0 - new_height * vert_offset)

                    # Crop bounding box to image
                    (im_height, im_width, ch) = img.shape
                    new_x2 = new_x1 + new_width
                    new_y2 = new_y1 + new_height

                    if new_x1 < 0:
                        new_x1 = 0

                    if new_y1 < 0:
                        new_y1 = 0

                    if new_x2 >= im_width:
                        new_x2 = im_width

                    if new_y2 >= im_height:
                        new_y2 = im_height

                    face_roi = img[new_y1:new_y2, new_x1:new_x2]

                # Save image file with face
                im_face_basename = im_basename + '_face_' + str(face_counter)
                im_face_path = im_face_basename + ext
                if self.align_faces and self.alignment_method == 'adience':
                    cv2.imwrite(im_face_path, face_roi)
                else:
                    misc.imsave(im_face_path, face_roi)
                im_face_paths.append(im_face_path)
                original_paths[im_face_path] = im_path
                bboxes[im_face_path] = (or_x, or_y, or_width, or_height)

                if self.align_faces and self.alignment_method == 'adience':
                    detect_landmarks(fname=im_face_path, fidu_exec_dir=fidu_exec_dir)
                    fidu_file = im_face_path.rsplit('.', 1)[0] + '.cfidu'
                    fidu_score, yaw_angle, fidu_points = read_fidu(fidu_file)

                    # Delete file with fiducial points
                    os.remove(fidu_file)

                    if fidu_score is not None and yaw_angle in [-45, -30, -15, 0, 15, 30, 45]:
                        _, base_fname = os.path.split(im_face_path)
                        aligned_face, R = adience_aligner.align(face_roi, fidu_points)
                        cv2.imwrite(im_face_path, aligned_face)

                if show_results:

                    # Convert image to BGR
                    if not self.align_faces or self.alignment_method != 'adience':
                        bgr_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                    # Save temporary image file with bounding box
                    im_bbox_basename = im_basename + '_bbox_' + str(face_counter)
                    im_bbox_path = im_bbox_basename + ext

                    # Draw bounding box on image
                    color = (0, 0, 255)  # Red color
                    pt1 = (or_x, or_y)
                    pt2 = (or_x + or_width, or_y + or_height)
                    cv2.rectangle(bgr_img, pt1, pt2, color, thickness=2)

                    # Save image
                    cv2.imwrite(im_bbox_path, bgr_img)
                    im_bbox_paths.append(im_bbox_path)
                    show_im_paths.append(im_bbox_path)

                face_counter += 1

        # Make GPUs visible again
        if not use_gpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = "1"

        result = {c.IM_FACE_PATHS_KEY: im_face_paths,
                  c.IM_BBOX_PATHS_KEY: im_bbox_paths,
                  c.SHOW_IM_PATHS_KEY: show_im_paths,
                  c.ORIGINAL_PATHS: original_paths,
                  c.BBOXES_KEY: bboxes}
        return result

    def classif_people(self, im_paths, only_largest_face=False, bbox_increase_pct=1.0, vert_offset=0.0,
                       square_faces=True, show_results=False):
        """
        Classify people detected in given images

        :type im_paths: list
        :param im_paths: list of paths of images to be classified

        :type only_largest_face: boolean
        :param only_largest_face: if True, use only largest face detected in image

        :type bbox_increase_pct: float
        :param bbox_increase_pct: size of bounding box used for saving faces,
                                  in percentage of size of detection bounding box

        :type vert_offset: float
        :param vert_offset: vertical offset of bounding box used for saving faces,
                            from bottom, in percentage of size of new bounding box

        :type square_faces: boolean
        :param square_faces: if True, transform face detection bounding boxes into squares

        :type show_results: boolean
        :param show_results: if True, show results of classification

        :rtype: dictionary
        :returns: a dictionary containing, for each image path and for each detected face,
                  the face bounding box and a (labels, tags, probs) tuple,
                  where labels is a list with labels associated to the image,
                  tags is a list with corresponding meaningful tags
                  and probs is a list with corresponding probabilities
        """

        result = {}
        im_face_paths = []
        im_bbox_paths = []
        show_im_paths = []

        try:

            start = cv2.getTickCount()

            # Prepare dictionaries with results
            for im_path in im_paths:
                result[im_path] = {}
            show_result = {}

            faces_result = self.save_faces(im_paths, only_largest_face=only_largest_face,
                                           bbox_increase_pct=bbox_increase_pct, vert_offset=vert_offset,
                                           square_faces=square_faces, show_results=show_results)

            im_face_paths = faces_result[c.IM_FACE_PATHS_KEY]
            im_bbox_paths = faces_result[c.IM_BBOX_PATHS_KEY]
            original_paths = faces_result[c.ORIGINAL_PATHS]
            bboxes = faces_result[c.BBOXES_KEY]

            # Classify faces
            b = 0
            for im_batch in batch(im_face_paths, self.batch_size):

                im_in_batch = 0

                for im_face_path in im_batch:

                    # Load image with face
                    image = caffe.io.load_image(im_face_path)

                    # Perform preprocessing on face
                    transformed_image_age = self.age_transformer.preprocess('data', image)
                    transformed_image_gender = self.age_transformer.preprocess('data', image)

                    # Copy the image data into the memory allocated for the neural network
                    self.age_net.blobs['data'].data[im_in_batch, ...] = transformed_image_age
                    self.gender_net.blobs['data'].data[im_in_batch, ...] = transformed_image_gender

                    im_in_batch += 1

                # Perform classification
                classif_batch_age = self.age_net.forward()
                classif_batch_gender = self.gender_net.forward()

                classifs_age = classif_batch_age[self.network_output]
                classifs_gender = classif_batch_gender[self.network_output]

                for i in range(im_in_batch):

                    # The output probability vector related to age for image i
                    classif_prob_age = classifs_age[i]

                    # Get predictions from softmax output
                    inds = classif_prob_age.argsort()[::-1]

                    probs = []
                    for idx in inds:
                        prob = classif_prob_age[idx]
                        probs.append(float(prob))

                    # Age is given by expected value of years
                    age = int(np.round(np.average(np.array(inds), weights=probs)))

                    # The output probability vector related to gender for image i
                    classif_prob_gender = classifs_gender[i]

                    # Get predictions from softmax output
                    inds = classif_prob_gender.argsort()[::-1]

                    gender_idx = inds[1]
                    if gender_idx == 0:
                        gender = 'Male'
                        prob = classif_prob_gender[1]
                    else:
                        gender = 'Female'
                        prob = classif_prob_gender[0]

                    if show_results:
                        im_bbox_path = im_bbox_paths[b]
                        show_result[im_bbox_path] = {'age': age,
                                                     'gender': (gender, prob)}

                    im_face_path = im_face_paths[b]
                    im_path = original_paths[im_face_path]
                    im_path_basename, ext = os.path.splitext(im_face_path)
                    face_number = int(im_path_basename[(im_path_basename.rfind('_') + 1):])
                    bbox = bboxes[im_face_path]
                    result[im_path][face_number] = {
                        'bbox': bbox,
                        'age': age,
                        'gender': (gender, prob)
                    }

                    b += 1

            # Set results for images with no detected face
            for im_path in im_paths:
                if im_path in result:
                    im_result = result[im_path]
                    if 0 not in im_result:
                        result[im_path] = 'No detected face'
                        show_result[im_path] = 'Nessuna faccia rilevata'
                        show_im_paths.append(im_path)

            elapsed_time = (cv2.getTickCount() - start) / cv2.getTickFrequency()

            if show_results:

                print '\nTime for classification: %02.02f seconds' % elapsed_time

                nr_images = len(im_bbox_paths)
                grid_size = c.CLASS_IMAGES_GRID_ROWS * c.CLASS_IMAGES_GRID_COLUMNS

                for index in range(0, nr_images, grid_size):

                    imgs_to_show_grid = im_bbox_paths[index: min(index + grid_size, nr_images)]

                    self.show_classified_images_in_grid(imgs_to_show_grid, show_result)

        except:
            raise
        finally:
            # Delete temporary files
            for im_path in im_face_paths:
                if os.path.exists(im_path):
                    os.remove(im_path)
            for im_path in im_bbox_paths:
                if os.path.exists(im_path):
                    os.remove(im_path)

        return result

    def show_classified_images_in_grid(self, im_paths, class_result):
        """
        Show classified images in grid

        :type im_paths:list
        :param im_paths: image paths

        :type class_result: dictionary
        :param class_result: classification results
        """

        # Get screen resolution and calculate window resolution and font size
        monitor = get_monitors()[0]
        hor_res = 0.9 * monitor.width
        vert_res = 0.9 * monitor.height
        fontscale = hor_res / c.CLASS_IMAGES_HEIGHT_TO_FONTSCALE_RATIO

        # Create blank image
        blank_im = np.zeros((int(vert_res), int(hor_res), 3), np.uint8)

        # Space for text and images
        space_for_text = vert_res / c.CLASS_IMAGES_HEIGHT_TO_SPACE_FOR_TEXT_RATIO
        im_space_height = float(
            vert_res - c.CLASS_IMAGES_GRID_ROWS *
            (c.CLASS_IMAGES_GRID_SPACING + space_for_text * 2)) / c.CLASS_IMAGES_GRID_ROWS
        im_space_width = float(
            hor_res - c.CLASS_IMAGES_GRID_COLUMNS *
            c.CLASS_IMAGES_GRID_SPACING) / c.CLASS_IMAGES_GRID_COLUMNS

        im_counter = 0
        row_counter = 0
        column_counter = 0
        for im_path in im_paths:
            im = cv2.imread(im_path)

            if im is not None:

                # Resize image retaining shape
                im_height = im.shape[0]
                im_width = im.shape[1]
                f_resize_x = im_space_width / im_width
                f_resize_y = im_space_height / im_height
                f_resize = min(f_resize_x, f_resize_y)
                if cv2.__version__ > 3:
                    new_im = cv2.resize(im, (0, 0), fx=f_resize, fy=f_resize, interpolation=cv2.INTER_NEAREST)
                else:
                    new_im = cv2.resize(im, (0, 0), fx=f_resize, fy=f_resize, interpolation=cv2.cv.CV_INTER_NN)

                new_im_height = new_im.shape[0]
                new_im_width = new_im.shape[1]

                # Copy image to blank image
                im_space_hor_shift = c.CLASS_IMAGES_GRID_SPACING / 2.0 + column_counter * \
                    (im_space_width + c.CLASS_IMAGES_GRID_SPACING)
                im_space_vert_shift = c.CLASS_IMAGES_GRID_SPACING / 2.0 + row_counter * \
                    (im_space_height + c.CLASS_IMAGES_GRID_SPACING + space_for_text * 2)
                im_hor_shift = int(im_space_hor_shift + ((im_space_width - new_im_width) / 2.0))
                im_vert_shift = int(im_space_vert_shift + ((im_space_height - new_im_height) / 2.0))
                blank_im[im_vert_shift:(im_vert_shift + new_im_height), im_hor_shift:(im_hor_shift + new_im_width)] = new_im

                # Put text under image
                im_result = class_result[im_path]
                text_hor_shift = int(im_space_hor_shift + c.CLASS_IMAGES_GRID_SPACING)
                text_vert_shift = int(im_vert_shift + new_im_height + space_for_text)
                position = (text_hor_shift, text_vert_shift)
                if im_result == 'Nessuna faccia rilevata':
                    text = 'NESSUNA FACCIA RILEVATA'
                    cv2.putText(blank_im, text, position, fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=fontscale, color=(255, 255, 255), thickness=1)
                else:
                    # (gender, prob) = im_result['gender']
                    # age = im_result['age']
                    # prob *= 100
                    # text = '%s (%02.2f %%), %s YEARS OLD' % (gender.upper(), prob, age)
                    # cv2.putText(blank_im, text, position, fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    #             fontScale=fontscale, color=(255, 255, 255), thickness=1)

                    (gender, prob) = im_result['gender']
                    age = im_result['age']
                    prob *= 100
                    text = '     %s (%02.2f %%)' % (gender.upper(), prob)
                    cv2.putText(blank_im, text, position, fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=fontscale, color=(255, 255, 255), thickness=1)
                    text_vert_shift += int(space_for_text)
                    position = (text_hor_shift, text_vert_shift)
                    text = '     %s YEARS OLD' % age
                    cv2.putText(blank_im, text, position, fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=fontscale, color=(255, 255, 255), thickness=1)

                column_counter += 1
                if column_counter == c.CLASS_IMAGES_GRID_COLUMNS:
                    row_counter += 1
                    column_counter = 0

            im_counter += 1

        cv2.imshow('Image classification', blank_im)
        cv2.waitKey(0)
