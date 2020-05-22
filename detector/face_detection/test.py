
from multiprocessing import Process
import numpy as np

import imutils

from face_detector import FaceNet_vcaffe
from tracking.tracker import Tracker
from object_manager.manager import ObjectManager
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




frame = cv2.imread('/tmp/test2.jpg')
nextframe = cv2.imread('/tmp/test2.jpg')

tracker = Tracker(**LK_PARAMS) # method for points tracking
face_det = FaceNet_vcaffe(**FACENET_PARAMS) # method for face detection.
obj_man = ObjectManager()

features = face_det.detect_face(frame)
print('Det: ',features)

obj_list_det = obj_man.manage_object_list(features, frame.shape[1],frame.shape[0])
print('Obj after det: ',obj_list_det)

tracker.set_last_frame(frame)

succ,features = tracker.update_features(nextframe,features)
print('Tracker features: ',features)
new_points_obj = features['points']

obj_list_track = obj_man.manage_object_list(features, nextframe.shape[1],nextframe.shape[0])
print('Obj after track: ',obj_list_track)

for i,obj in enumerate(new_points_obj):
	for p in obj:
		x,y = int(p.x_coordinate) , int(p.y_coordinate)
		cv2.circle(nextframe,(x,y), 3, (50,i*255,0) , -1)


cv2.imwrite('/tmp/res.jpg',nextframe)


