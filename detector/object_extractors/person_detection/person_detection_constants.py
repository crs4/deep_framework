import cv2

import os








MODEL_NAME = 'faster_rcnn_inception_v2_coco_2018_01_28/frozen_inference_graph.pb'
MOBILE_MODEL_NAME = "MobileNetSSD_deploy.caffemodel"
MOBILE_PROTO_NAME = "MobileNetSSD_deploy.prototxt"

CONFIDENCE_THR = 0.95




#TRACKING PARAMS

DETECTION_INTERVAL = 15# number of frames between network detection


BODY_IMAGE_WIDTH = 500


PROT= os.environ['PROT']
MAX_ALLOWED_DELAY	= float(os.environ['MAX_ALLOWED_DELAY'])
VC_OUT	= os.environ['VC_OUT']
COLLECTOR_ADDRESS	= os.environ['COLLECTOR_ADDRESS']
PP_OUT	= os.environ['PP_OUT']
PP_OUT_TO_COL	= os.environ['PP_OUT_TO_COL']
VIDEOSRC_ADDRESS = os.environ['VIDEOSRC_ADDRESS']
MONITOR_ADDRESS = os.environ['MONITOR_ADDRESS']
MONITOR_STATS_IN = os.environ['MONITOR_STATS_IN']
INTERVAL_STATS = float(os.environ['INTERVAL_STATS'])