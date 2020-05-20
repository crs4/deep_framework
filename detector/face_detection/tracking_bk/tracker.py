

import numpy as np
import cv2
#from utils.opencv_common import anorm2, draw_str
from time import clock
from face_detection_constants import *
#from constants import *

class Tracker:

    def __init__(self, **params):
        self.params = params

    #This function take points that will be tracked and reshape them in the correct format
    #The parameter 'points' must be in the following format points = [[[x0,y0]],...,[[xn,yn]]]
    def create_track_points(self,points):
        
        points_to_track = []
        if points is not None:
            for x, y in np.float32(points).reshape(-1, 2):
                points_to_track.append([[x, y]])

        return np.array(points_to_track, np.float32)

    
    #This function checks tracked points between frames and add other good points if present and returns them
    #Frames must be in gray scale. 'tracked_points' must be in the current format tracked_points = [[[x0,y0]],...,[[xn,yn]]]
    def manage_track_points(self, prev_frame, current_frame, tracked_points):
            
        new_tracks = []
        img0, img1 = prev_frame, current_frame
        p0 = np.float32([tr[-1] for tr in tracked_points]).reshape(-1, 1, 2)
        p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **self.params)
        p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **self.params)
        d = abs(p0-p0r).reshape(-1, 2).max(-1)
        
        good = d < 1


        for (x, y), good_flag in zip( p1.reshape(-1, 2), good):

            if not good_flag:
                continue


            
            new_tracks.append([[x,y]])

        return np.array(new_tracks, np.float32)

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


   

