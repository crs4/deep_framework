
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

features = face_det.detect_face(nextframe)
rects = features['boxes']
print(rects)




obj_list_det = obj_man.manage_object_list(features, frame.shape[1],frame.shape[0],'POINTS')

for obj in obj_list_det:
	print('ser: ',obj.serialize() )

tracker.set_last_frame(frame)

succ,features = tracker.update_features(nextframe,features,**{'features_by_detector':True})
print('Tracker features: ',features)
new_points_obj = features['points']

obj_list_track = obj_man.manage_object_list(features, nextframe.shape[1],nextframe.shape[0],'POINTS')
print('Obj after track: ',obj_list_track)


for obj in obj_list_det:
	print('after ser: ',obj.serialize() )

for i,obj in enumerate(obj_list_track):
	points = obj.points
	for p in points:
		if p.properties['tag'] == 'right_eye':
			x,y = int(p.x_coordinate) , int(p.y_coordinate)
			cv2.circle(nextframe,(x,y), 3, (50,i*255,0) , -1)



for i,rect in enumerate(rects):
	centroid = rect.centroid
	x,y = int(centroid.x_coordinate) , int(centroid.y_coordinate)
	cv2.circle(nextframe,(x,y), 3, (50,i*255,0) , -1)
	cv2.rectangle(nextframe,(int(rect.top_left_point.x_coordinate),int(rect.top_left_point.y_coordinate)),(int(rect.bottom_right_point.x_coordinate),int(rect.bottom_right_point.y_coordinate)),(50,i*255,0),2)



cv2.imwrite('/tmp/res_p.jpg',nextframe)


