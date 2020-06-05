import cv2

import os
#FACE PARAMS

LK_PARAMS = dict( winSize  = (15, 15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

FACENET_PARAMS = dict( minsize = 20, # minimum size of face
                       threshold = [ 0.6, 0.7, 0.8], # three steps's threshold
                       factor = 0.709) # scale factor




#TRACKING PARAMS

DETECTION_INTERVAL = 10 # number of frames between keypoints detection
LOST_THR = 5 # number of points min

FACE_DETECTION_THR=0.95
DELTA_RECT=1.2
DELTA_EYE_W=0.3
DELTA_EYE_H=0.22


FACE_IMAGE_WIDTH = 640


PROT= os.environ['PROT']
MAX_ALLOWED_DELAY	= float(os.environ['MAX_ALLOWED_DELAY'])
VC_OUT	= os.environ['VC_OUT']
COLLECTOR_ADDRESS	= os.environ['COLLECTOR_ADDRESS']
FP_OUT	= os.environ['FP_OUT']
FP_OUT_TO_COL	= os.environ['FP_OUT_TO_COL']
VIDEOSRC_ADDRESS = os.environ['VIDEOSRC_ADDRESS']
MONITOR_ADDRESS = os.environ['MONITOR_ADDRESS']
MONITOR_STATS_IN = os.environ['MONITOR_STATS_IN']
INTERVAL_STATS = float(os.environ['INTERVAL_STATS'])