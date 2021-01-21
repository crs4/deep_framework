
import numpy as np
import dlib
import imutils

from .person_detection_constants import *



from .person_detector import MobileDetector
from .dlib_tracker.centroidtracker import CentroidTracker
from .dlib_tracker.trackableobject import TrackableObject

from utils.socket_commons import send_data, recv_data
from utils.stats_maker import StatsMaker

from utils.geometric_functions import check_point_in_rect
from utils.features import Object, Rect, Point
from utils.abstract_detector import AbstractDetector



class PersonExecutor(AbstractDetector):

    ratio = 1

    def __init__(self):
        self.person_detector = MobileDetector()
        self.trackers = []
        self.ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
        self.trackableObjects = {}

    def __create_objects(self,objs):
        objects = []
        for obj in objs:
            obj_points = []
            top_left = Point(obj['rect']['x_topleft'],obj['rect']['y_topleft'])
            bottom_right = Point(obj['rect']['x_bottomright'],obj['rect']['y_bottomright'])
            obj_rect = Rect(top_left,bottom_right)
            
            obj = Object(rect = obj_rect, points = obj_points, pid = obj['pid'])
            objects.append(obj)
        return objects


    def extract_features(self,current_frame,executor_dict):

        objects_list = []
        frame_counter = executor_dict['frame_counter']



        try:
            self.ratio = BODY_IMAGE_WIDTH/float(current_frame.shape[1])
        except Exception as e:
            print('exception in rec frame ',e)

        rects = []
        current_frame = imutils.resize(current_frame, width=BODY_IMAGE_WIDTH)
        rgb = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
        H, W = current_frame.shape[:2]

        if frame_counter % DETECTION_INTERVAL == 0:


            self.trackers = []
            boxes = self.person_detector.detect_person(current_frame)

            # construct a dlib rectangle object from the bounding
            # box coordinates and then start the dlib correlation
            # tracker
            for box in boxes:
                startX, startY, endX, endY = box
                tracker = dlib.correlation_tracker()
                rect = dlib.rectangle(startX, startY, endX, endY)
                tracker.start_track(rgb, rect)

                # add the tracker to our list of trackers so we can
                # utilize it during skip frames
                self.trackers.append(tracker)
        else:

            for tracker in self.trackers:
                # set the status of our system to be 'tracking' rather
                # than 'waiting' or 'detecting'
                status = "Tracking"

                # update the tracker and grab the updated position
                tracker.update(rgb)
                pos = tracker.get_position()

                # unpack the position object
                startX = int(pos.left())
                startY = int(pos.top())
                endX = int(pos.right())
                endY = int(pos.bottom())

                # add the bounding box coordinates to the rectangles list
                rects.append((startX, startY, endX, endY))


        objects = self.ct.update(rects)

        

        # loop over the tracked objects
        for (objectID, centroid) in objects.items():
            obj_dict = {}
            # check to see if a trackable object exists for the current
            # object ID
            to = self.trackableObjects.get(objectID, None)

            # if there is no existing trackable object, create one
            if to is None:
                to = TrackableObject(objectID, centroid)

            
            # otherwise, there is a trackable object so we can utilize it
            # to determine direction
            else:
                # the difference between the y-coordinate of the *current*
                # centroid and the mean of *previous* centroids will tell
                # us in which direction the object is moving (negative for
                # 'up' and positive for 'down')
                y = [c[1] for c in to.centroids]
                direction = centroid[1] - np.mean(y)
                to.centroids.append(centroid)

                # check to see if the object has been counted or not
                if not to.counted:
                    # if the direction is negative (indicating the object
                    # is moving up) AND the centroid is above the center
                    # line, count the object
                    if direction < 0 and centroid[1] < H // 2:
                        #totalUp += 1
                        to.counted = True

                    # if the direction is positive (indicating the object
                    # is moving down) AND the centroid is below the
                    # center line, count the object
                    elif direction > 0 and centroid[1] > H // 2:
                        #totalDown += 1
                        to.counted = True
            
            # store the trackable object in our dictionary
            self.trackableObjects[objectID] = to

            cx = int(centroid[0]/self.ratio)
            cy = int(centroid[1]/self.ratio)



            for rect in rects: 
                startX, startY, endX, endY = rect
                y_topleft_coord = int(startY/self.ratio)
                y_bottomright_coord = int(endY/self.ratio)
                x_topleft_coord = int(startX/self.ratio)
                x_bottomright_coord = int(endX/self.ratio)
                rect_scaled = dict(y_topleft=y_topleft_coord,y_bottomright=y_bottomright_coord,x_topleft=x_topleft_coord,x_bottomright=x_bottomright_coord)
                if check_point_in_rect((cx,cy),rect_scaled):
                    obj_dict['pid'] = str(objectID)
                    obj_dict['rect'] = rect_scaled

                    objects_list.append(obj_dict)
                    break

        objects_list_final = self.__create_objects(objects_list)
        print(objects_list_final)
        return objects_list_final












