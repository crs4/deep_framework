import face_extractor_constants as fec
import cv2
import numpy as np
import os
import sys
import tensorflow as tf
import yaml
sys.path.insert(0, fec.FACENET_SRC_PATH)
sys.path.insert(0, os.path.join(fec.FACENET_SRC_PATH, 'align'))
import facenet
import detect_face

from scipy import misc


class FaceNet(object):
    """
    Tool for face detection and recognition with FaceNet
    """

    def __init__(self, params=None):
        """
        Initialize tool

        :type params: dictionary
        :param params: parameters (see table)
        ============================  ====================================================  ============================
        Key                           Value                                                 Default value
        ============================  ====================================================  ============================
        scale_factor                  scale factor between two scans in face detection      0.709
        detection_threshold_1         detection threshold for first step                    0.5
        detection_threshold_2         detection threshold for second step                   0.6
        detection_threshold_3         detection threshold for third step                    0.89
        min_size                      minimum size of face detection                        20
                                      bounding box (in pixels)
        gpu_memory_fraction           GPU memory fraction to be used                        0.9
        facenet_model_path            path of FaceNet model
        ============================  ====================================================  ============================
        """

        # Set parameters
        self.scale_factor = fec.FACENET_FACE_DETECTION_SCALE_FACTOR
        det_threshold_1 = fec.FACENET_DETECTION_THRESHOLD_1
        det_threshold_2 = fec.FACENET_DETECTION_THRESHOLD_2
        det_threshold_3 = fec.FACENET_DETECTION_THRESHOLD_3
        self.min_size = fec.FACENET_FACE_DETECTION_MIN_SIZE
        gpu_mem_fraction = fec.FACENET_GPU_MEMORY_FRACTION
        self.model_path = fec.FACENET_MODEL_PATH

        if params is not None:
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
            if fec.FACENET_GPU_MEMORY_FRACTION_KEY in params:
                gpu_mem_fraction = params[fec.FACENET_GPU_MEMORY_FRACTION_KEY]
            if fec.FACENET_MODEL_PATH_KEY in params:
                self.model_path = params[fec.FACENET_MODEL_PATH_KEY]

        self.det_thresholds = [det_threshold_1, det_threshold_2, det_threshold_3]

        # Create network and load parameters
        with tf.Graph().as_default():
            gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_mem_fraction)
            sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
            with sess.as_default():
                self.pnet, self.rnet, self.onet = detect_face.create_mtcnn(sess, fec.FACENET_DATA_PATH)

    def detect_faces_in_image(self, img, show_results=False):
        """
        Detect faces in given image

        :type img: numpy.ndarray (3 channel RGB image)
        :param img: image to be analyzed

        :type show_results: boolean
        :param show_results: show (True) or do not show (False)
                             image with detected faces

        :rtype: list
        :returns: detected faces, results for each face are represented by a dictionary (see table)

        ============================  ==================================================================================
        Key                           Value
        ============================  ==================================================================================
        bbox                          face bounding box as a (x, y, width, height) tuple
        points                        facial features
        ============================  ==================================================================================
        """

        faces = []

        # Use facenet face detector
        (bboxes, points) = detect_face.detect_face(
            img, self.min_size, self.pnet, self.rnet, self.onet, self.det_thresholds, self.scale_factor)

        for i, bbox in enumerate(bboxes):

            # Transform bounding box, using integer values
            x = int(round(bbox[0]))
            y = int(round(bbox[1]))
            width = int(round(bbox[2] - bbox[0]))
            height = int(round(bbox[3] - bbox[1]))

            face_dict = {
                fec.FACE_BBOX_KEY: (x, y, width, height),
                fec.FACE_SCORE_KEY: bbox[4]
            }
            faces.append(face_dict)

        if show_results:
            # Show image with bounding boxes of detected faces
            print faces

            # Convert face to BGR
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            color = (0, 0, 255)  # Red color
            i = 0
            for face in faces:
                bbox = face[fec.FACE_BBOX_KEY]
                pt1 = (bbox[0], bbox[1])
                pt2 = (bbox[0] + bbox[2], bbox[1] + bbox[3])
                cv2.rectangle(img, pt1, pt2, color)
                i += 1
            cv2.imshow('image', img)
            cv2.waitKey(0)

        return faces

    def detect_largest_face_in_image(self, img, show_results=False):
        """
        Detect largest face in given image

        :type img: numpy.ndarray (3 channel RGB image)
        :param img: image to be analyzed

        :type show_results: boolean
        :param show_results: show (True) or do not show (False)
                             image with detecte face

        :rtype: tuple
        :returns: face bounding box as a (x, y, width, height) tuple
        """

        face_bbox = None

        # Get size of image
        img_size = np.asarray(img.shape)[0:2]

        # Use facenet face detector
        (bboxes, points) = detect_face.detect_face(
            img, self.min_size, self.pnet, self.rnet, self.onet, self.det_thresholds, self.scale_factor)

        nr_faces = bboxes.shape[0]

        if nr_faces > 0:
            det = bboxes[:, 0:4]

            if nr_faces > 1:
                bbox_size = (det[:, 2] - det[:, 0]) * (det[:, 3] - det[:, 1])
                img_center = img_size / 2
                offsets = np.vstack(
                    [(det[:, 0] + det[:, 2]) / 2 - img_center[1], (det[:, 1] + det[:, 3]) / 2 - img_center[0]])
                offset_dist_squared = np.sum(np.power(offsets, 2.0), 0)

                # Weight more the center
                index = np.argmax(bbox_size - offset_dist_squared * 2.0)

                det = det[index, :]

            face_bbox = np.squeeze(det)

            if face_bbox is not None:

                # Transform bounding box, using integer values
                x = int(round(face_bbox[0]))
                y = int(round(face_bbox[1]))
                width = int(round(face_bbox[2] - face_bbox[0]))
                height = int(round(face_bbox[3] - face_bbox[1]))
                face_bbox = (x, y, width, height)

        if show_results:
            # Show image with bounding boxes of detected faces
            if face_bbox is None:
                print 'No detected faces'
            else:
                print 'Detected face:'
                print face_bbox

                # Convert face to BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                color = (0, 0, 255)  # Red color
                i = 0
                pt1 = (face_bbox[0], face_bbox[1])
                pt2 = (face_bbox[0] + face_bbox[2], face_bbox[1] + face_bbox[3])
                cv2.rectangle(img, pt1, pt2, color)
                i += 1
                cv2.imshow('image', img)
                cv2.waitKey(0)

        return face_bbox

    def align_face(self, img, bbox=None, show_results=False):
        """
        Align given face

        :type img: numpy.ndarray (3 channel RGB image)
        :param img: image to be analyzed

        :type bbox: tuple
        :param bbox: face bounding box as a (x, y, width, height) tuple,
                     if not given largest face found in image is considered

        :type show_results: boolean
        :param show_results: show (True) or do not show (False)
                             image with detected faces

        :rtype: tuple
        :return: a (bounding_box, aligned face) tuple,
                 where bounding box is a (x, y, width, height) tuple
                 and aligned face is a numpy.ndarray (3 channel RGB image)
        """

        aligned_face = None

        # Get size of image
        img_size = np.asarray(img.shape)[0:2]

        if bbox is None:

            # Use facenet face detector
            (bboxes, points) = detect_face.detect_face(
                img, self.min_size, self.pnet, self.rnet, self.onet, self.det_thresholds, self.scale_factor)

            nr_faces = bboxes.shape[0]

            if nr_faces > 0:
                det = bboxes[:, 0:4]

                if nr_faces > 1:
                    bbox_size = (det[:, 2] - det[:, 0]) * (det[:, 3] - det[:, 1])
                    img_center = img_size / 2
                    offsets = np.vstack(
                        [(det[:, 0] + det[:, 2]) / 2 - img_center[1], (det[:, 1] + det[:, 3]) / 2 - img_center[0]])
                    offset_dist_squared = np.sum(np.power(offsets, 2.0), 0)

                    # Weight more the center
                    index = np.argmax(bbox_size - offset_dist_squared * 2.0)

                    det = det[index, :]

                bbox = np.squeeze(det)

        else:

            bbox = (bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3])

        if bbox is not None:

            x1 = int(round(np.maximum(bbox[0] - fec.FACENET_MARGIN / 2, 0)))
            y1 = int(round(np.maximum(bbox[1] - fec.FACENET_MARGIN / 2, 0)))
            x2 = int(round(np.minimum(bbox[2] + fec.FACENET_MARGIN / 2, img_size[1])))
            y2 = int(round(np.minimum(bbox[3] + fec.FACENET_MARGIN / 2, img_size[0])))

            bbox = (x1, y1, x2 - x1, y2 - y1)

            cropped_face = img[bbox[1]:(bbox[1] + bbox[3]), bbox[0]:(bbox[0] + bbox[2]), :]
            aligned_face = misc.imresize(
                cropped_face, (fec.FACENET_ALIGNED_FACE_SIZE, fec.FACENET_ALIGNED_FACE_SIZE), interp='bilinear')

            if show_results:
                if aligned_face is not None:
                    # Show aligned face

                    # Convert face in BGR
                    aligned_face_bgr = cv2.cvtColor(aligned_face, cv2.COLOR_RGB2BGR)

                    cv2.imshow('aligned face', aligned_face_bgr)
                    cv2.waitKey(0)
                else:
                    print 'Alignment failed'

        else:
            if show_results:
                print 'No face detected'

        return bbox, aligned_face


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Face detection and recognition with FaceNet')
    parser.add_argument('--detect_faces', '-d', help='path of image containing faces to be detected')
    parser.add_argument('--align_face', '-a', help='path of image containing face to be aligned')
    parser.add_argument('--show_results', '-s', help='show results', action='store_true')
    parser.add_argument('--params', '-p', help='path of YAML file with algorithm parameters, '
                                               'if not provided default values will be used')

    args = parser.parse_args()

    params = None
    if args.params:
        with open(args.params, 'r') as stream:
            params = yaml.load(stream)

    facenet = FaceNet(params)

    if args.detect_faces:
        img = misc.imread(args.detect_faces)
        facenet.detect_faces_in_image(img, args.show_results)
    elif args.align_face:
        img = misc.imread(args.align_face)
        facenet.align_face(img, show_results=args.show_results)
