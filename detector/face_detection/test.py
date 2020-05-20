
from multiprocessing import Process
import numpy as np

import imutils

from face_detector import FaceNet_vcaffe
from tracking.tracker import Tracker
import copy
import zmq
import time,json
import cv2
import sys

LK_PARAMS = dict( winSize  = (15, 15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

FACENET_PARAMS = dict( minsize = 20, # minimum size of face
                       threshold = [ 0.6, 0.7, 0.8], # three steps's threshold
                       factor = 0.709) # scale factor

def draw_keypoints(img, keypoints,color):
    
    for i,p in enumerate(keypoints):
        x,y = int(p[0][0]),int(p[0][1])
        cv2.circle(img,(x,y), 3, color, -1)


frame = cv2.imread('test2.jpg')
nextframe = cv2.imread('test2.jpg')

tracker = Tracker(**LK_PARAMS) # method for points tracking
face_det = FaceNet_vcaffe(**FACENET_PARAMS) # method for face detection.

features = face_det.detect_face(frame)


tracker.set_last_frame(frame)
print('Det: ',features)

succ,tracks = tracker.update_features(nextframe,features)
new_points_obj = tracks['points']
for i,obj in enumerate(new_points_obj):
	for p in obj:
		x,y = int(p.x_coordinate) , int(p.y_coordinate)
		cv2.circle(nextframe,(x,y), 3, (50,i*255,0) , -1)


cv2.imwrite('/tmp/res.jpg',nextframe)
print('Tracks: ', tracks)


