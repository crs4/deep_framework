

import numpy as np
import cv2
#from utils.opencv_common import anorm2, draw_str
from time import clock
#from constants import *
from utils.features import Point,Rect
#from face_detection_constants import *
LOST_THR = 5

class Tracker:

    def __init__(self, **params):
        self.params = params



    #This function take points that will be tracked and reshape them in the correct format
    #The parameter 'points' must be in the following format points = [[[x0,y0]],...,[[xn,yn]]]
    def __create_track_points(self,points):
        # formats mtcnn_points in order to be tracked

        kpoints = []

        for obj_points in points:
            for p in obj_points:
                kpoints.append([[p.x_coordinate, p.y_coordinate]])

        points_to_track = []
        if points is not None:
            for x, y in np.float32(kpoints).reshape(-1, 2):
                points_to_track.append([[x, y]])

        return np.array(points_to_track, np.float32)

    def __convert_to_grayscale(self,image):
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray_image


    def set_last_frame(self,image):
        self.previous_frame = self.__convert_to_grayscale(image)


    def check_tracking_success(self, num_objects, num_tracked_points, lost_thr):
        """
        This function check if some track point is lost
        """
        temp = lost_thr * num_objects
        if num_tracked_points < temp or num_objects == 0:
            return False
        return True
   


    
    #This function checks tracked points between frames and add other good points if present and returns them
    #Frames must be in gray scale. 'tracked_points' must be in the current format tracked_points = [[[x0,y0]],...,[[xn,yn]]]
    def update_features(self, current_frame, features):

        current_frame = self.__convert_to_grayscale(current_frame) # gray frame required by tracking system
        
        points_obj = features['points']

        num_obj = len(points_obj)

        tracked_points = self.__create_track_points(points_obj)
        
        new_tracks = []
        tracks_split = []

        img0, img1 = self.previous_frame, current_frame
        p0 = np.float32([tr[-1] for tr in tracked_points]).reshape(-1, 1, 2)
        p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **self.params)
        p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **self.params)
        d = abs(p0-p0r).reshape(-1, 2).max(-1)
        
        good = d < 1


        for (x, y), good_flag in zip( p1.reshape(-1, 2), good):

            if not good_flag:
                continue


            point = Point(x,y)
            new_tracks.append(point)

        success = self.check_tracking_success(num_obj, len(new_tracks), LOST_THR)
        if success:
            tracks_split = [new_tracks[i:i+LOST_THR] for i in range(0,len(new_tracks),LOST_THR)]

        new_features = {'boxes': [],'points': tracks_split}
        return success, new_features






















class TrackerCV:

    def __init__(self):
        self.trackers = cv2.MultiTracker_create()
        self.OPENCV_OBJECT_TRACKERS = {
            "csrt": cv2.TrackerCSRT_create,
            "kcf": cv2.TrackerKCF_create,
            "boosting": cv2.TrackerBoosting_create,
            "mil": cv2.TrackerMIL_create,
            "tld": cv2.TrackerTLD_create,
            "medianflow": cv2.TrackerMedianFlow_create,
            "mosse": cv2.TrackerMOSSE_create
        }
        self.tracker = self.OPENCV_OBJECT_TRACKERS["csrt"]()

    def create_trackable_objects(frame,box):
        # box = (x, y, w, h)
        self.trackers.add(self.tracker, frame, box)

    def update_tracked_objects(frame):
        (success, boxes) = trackers.update(frame)
        return (success, boxes)


   

