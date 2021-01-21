import cv2

import os








MODEL_NAME = 'faster_rcnn_inception_v2_coco_2018_01_28/frozen_inference_graph.pb'
MOBILE_MODEL_NAME = "MobileNetSSD_deploy.caffemodel"
MOBILE_PROTO_NAME = "MobileNetSSD_deploy.prototxt"

CONFIDENCE_THR = 0.95




#TRACKING PARAMS

DETECTION_INTERVAL = 15# number of frames between network detection


BODY_IMAGE_WIDTH = 500