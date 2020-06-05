
from multiprocessing import Process
import numpy as np




from detector import VisdroneDectector
from tracker import Tracker



from object_manager.manager import ObjectManager
import copy
import zmq
import time,json
import cv2
import sys

frame = cv2.imread('/tmp/sauron_image.jpg')
#nextframe = cv2.imread('/tmp/test2.jpg')

det = VisdroneDectector()
obj_man = ObjectManager()
tracker = Tracker()

features = det.detect(frame)
rects = features['boxes']

tracker_outputs = tracker.update(rects, frame)
tracked_boxes = tracker_outputs['boxes']

#outputs = det.predict(frame)
for i in range(4):
	tracker_outputs = tracker.update(rects, frame)
	tracked_boxes = tracker_outputs['boxes']
	for i,rect in enumerate(tracked_boxes):
		print(rect.serialize())
		centroid = rect.centroid
		x,y = int(centroid.x_coordinate) , int(centroid.y_coordinate)
		cv2.circle(frame,(x,y), 3, (50,255,0) , -1)
		cv2.rectangle(frame,(int(rect.top_left_point.x_coordinate),int(rect.top_left_point.y_coordinate)),(int(rect.bottom_right_point.x_coordinate),int(rect.bottom_right_point.y_coordinate)),(50,i*255,0),2)
		cv2.putText(frame, str(rect.properties['pid']), ( int(rect.top_left_point.x_coordinate) , int(rect.top_left_point.y_coordinate)), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1)



cv2.imwrite('/tmp/res_sau.jpg',frame)


"""
for i in range(4):
	tracker_outputs_new = tracker.update_new(outputs_nu['boxes'], frame)

	tracker_outputs = tracker.update(outputs['boxes'], outputs['scores'], frame)
	tracked_boxes = tracker_outputs['boxes']
	tracked_ids = tracker_outputs['ids']
	print(tracked_boxes)
	print(tracked_ids)

	tracked_boxes_new = tracker_outputs_new['boxes']
	tracked_ids_new = tracker_outputs_new['ids']
	print('nu  ',tracked_boxes_new)
	print('nu  ',tracked_ids_new)
"""
"""
for i,rect in enumerate(rects):
	print(rect.serialize())
	centroid = rect.centroid
	x,y = int(centroid.x_coordinate) , int(centroid.y_coordinate)
	cv2.circle(frame,(x,y), 3, (50,255,0) , -1)
	cv2.rectangle(frame,(int(rect.top_left_point.x_coordinate),int(rect.top_left_point.y_coordinate)),(int(rect.bottom_right_point.x_coordinate),int(rect.bottom_right_point.y_coordinate)),(50,i*255,0),2)
	cv2.putText(frame, rect.properties['category'], ( int(rect.top_left_point.x_coordinate) , int(rect.top_left_point.y_coordinate)), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1)



cv2.imwrite('/tmp/res_drone.jpg',frame)
"""

"""
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
"""

