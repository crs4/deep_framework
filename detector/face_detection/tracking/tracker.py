

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
        tags = []
        for obj_points in points:
            for p in obj_points:
                kpoints.append([[p.x_coordinate, p.y_coordinate]])
                tags.append(p.properties['tag'])

        points_to_track = []
        if points is not None:
            for x,y in np.float32(kpoints).reshape(-1, 2):
                points_to_track.append([[x, y]])

        return tags,np.array(points_to_track, np.float32)

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
    def update_features(self, current_frame, features,**settings):

        current_frame = self.__convert_to_grayscale(current_frame) # gray frame required by tracking system
        
        points_obj = features['points']

        num_obj = len(points_obj)

        tags,tracked_points = self.__create_track_points(points_obj)
       
        new_tracks = []
        tracks_split = []

        img0, img1 = self.previous_frame, current_frame
        p0 = np.float32([tr[-1] for tr in tracked_points]).reshape(-1, 1, 2)
        p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **self.params)
        p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **self.params)
        d = abs(p0-p0r).reshape(-1, 2).max(-1)
        
        good = d < 1


        for (x, y), good_flag,tag in zip( p1.reshape(-1, 2), good,tags):

            if not good_flag:
                continue


            #point = Point(x,y)
            point = Point(x,y,**{'tag':tag})
            new_tracks.append(point)

        success = self.check_tracking_success(num_obj, len(new_tracks), LOST_THR)
        if success:
            tracks_split = [new_tracks[i:i+LOST_THR] for i in range(0,len(new_tracks),LOST_THR)]
        else:
            print('no succ')

        new_features = {'boxes': [],'points': tracks_split}
        return success, new_features






















class TrackerCV:

    def __init__(self):
        self.OPENCV_OBJECT_TRACKERS = {
            "csrt": cv2.TrackerCSRT_create,
            "kcf": cv2.TrackerKCF_create,
            "boosting": cv2.TrackerBoosting_create,
            "mil": cv2.TrackerMIL_create,
            "tld": cv2.TrackerTLD_create,
            "medianflow": cv2.TrackerMedianFlow_create,
            "mosse": cv2.TrackerMOSSE_create
        }

    def set_last_frame(self,frame):
        self.previous_frame = frame

    def __format_boxes(self,features,frame_w,frame_h):
        boxes_formatted = []
        if len(features['boxes']) > 0:
            for box in features['boxes']:
                x = box.top_left_point.x_coordinate
                y = box.top_left_point.y_coordinate
                w = box.bottom_right_point.x_coordinate - box.top_left_point.x_coordinate
                h = box.bottom_right_point.y_coordinate - box.top_left_point.y_coordinate
                boxes_formatted.append((x,y,w,h))
            return boxes_formatted
        else:
            if len(features['points']) > 0:
                for object_points in features['points']:
                    box = get_rect_around_points(frame_w,frame_h,object_points,delta_rect=1)
                    x = box.top_left_point.x_coordinate
                    y = box.top_left_point.y_coordinate
                    w = box.bottom_right_point.x_coordinate - box.top_left_point.x_coordinate
                    h = box.bottom_right_point.y_coordinate - box.top_left_point.y_coordinate
                    boxes_formatted.append(rect)
                return boxes_formatted

    def update_features(self, current_frame, features,**settings):
        
        frame_w = current_frame.shape[1]
        frame_h = current_frame.shape[0]
        features_by_detector = settings['features_by_detector']
        boxes = self.__format_boxes(features,frame_w,frame_h)
        res_boxes = []


        if features_by_detector:
            self.trackers = cv2.MultiTracker_create()

            for box in boxes:
                tracker = self.OPENCV_OBJECT_TRACKERS["csrt"]()
                self.trackers.add(tracker, current_frame, box)



        (success, new_boxes) = self.trackers.update(current_frame)
        #print('tr_in: ',new_boxes)

        if success:
            for box in new_boxes:
                x,y,w,h = box
                p_top = Point(x,y)
                p_bot = Point(x+w,y+h)

                box = Rect(p_top,p_bot)
                res_boxes.append(box)

        new_features = {'boxes': res_boxes,'points': []}

        return success, new_features


   

