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
DST_THR = 15
DELTA_RECT=1.2
DELTA_EYE_W=0.3
DELTA_EYE_H=0.22


FACE_IMAGE_WIDTH = 640