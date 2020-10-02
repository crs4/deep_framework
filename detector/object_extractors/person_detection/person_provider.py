
from multiprocessing import Process
import numpy as np
import dlib

from person_detection_constants import *



from person_detector import MobileDetector
from dlib_tracker.centroidtracker import CentroidTracker
from dlib_tracker.trackableobject import TrackableObject

from utils.socket_commons import send_data, recv_data
from utils.stats_maker import StatsMaker

from utils.geometric_functions import check_point_in_rect



#import caffe
import zmq
import time,json
import cv2
import sys
import imutils





class PersonProvider(Process):

    def __init__(self, configuration):

        Process.__init__(self)
        self.stats_maker = StatsMaker()
        self.pub_port = configuration['out']
        self.pair_port = configuration['out_to_col']
        self.rec_port = configuration['in'] 
        self.people = []      
       

    def run(self):


       
        self.person_detector = MobileDetector()

        context = zmq.Context()


        # subscribes to VideoCapture
        vc_socket = context.socket(zmq.SUB)
        vc_socket.setsockopt_string(zmq.SUBSCRIBE, "",encoding='ascii')
        vc_socket.connect(PROT+VIDEOSRC_ADDRESS+':'+self.rec_port)

        # configure output
        publisher = context.socket(zmq.PUB)
        #if publisher detetcts slow subscribers, skips frames
        publisher.sndhwm = 1
        publisher.bind(PROT+'*:'+self.pub_port)


        # PAIR connection to collector
        
        col_socket = context.socket(zmq.PAIR)
        #col_socket.bind(PROT+'*:'+self.pair_port)
        col_socket.connect(PROT+COLLECTOR_ADDRESS+':'+self.pair_port)

        
        # connection to monitor for stats
        self.monitor_stats_sender= context.socket(zmq.PUB)
        self.monitor_stats_sender.connect(PROT+MONITOR_ADDRESS+':'+MONITOR_STATS_IN)

        # manage sending stats to monitor
        self.stats_maker.run_stats_timer(INTERVAL_STATS,self.__send_stats)
        self.stats_maker.run_fps_timer()
        
        trackers = []
        rects = []
        ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
        trackableObjects = {}
        totalFrames = 0
        while True:
            
            rec_dict,imgs = recv_data(vc_socket,0,False)

            current_frame = imgs[0]
            
            vc_frame_idx = rec_dict['frame_idx']
            vc_time = rec_dict['vc_time']
            
            if time.time() - vc_time > MAX_ALLOWED_DELAY:
                self.stats_maker.skipped_frames += 1
                continue
           


            try:
                self.ratio = BODY_IMAGE_WIDTH/float(self.displayed_frame.shape[1])
            except Exception as e:
                print('exception in rec frame ',e)
                continue

            rects = []
            crops = []
            current_frame = imutils.resize(current_frame, width=BODY_IMAGE_WIDTH)
            rgb = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
            H, W = current_frame.shape[:2]

            if totalFrames % DETECTION_INTERVAL == 0:


                trackers = []
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
                    trackers.append(tracker)
            else:

                for tracker in trackers:
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



            for rect in rects:
                startX, startY, endX, endY = rect
                crop = current_frame[startY:endY,startX:endX]
                crops.append(np.ascontiguousarray(crop, dtype=np.uint8))


            res = dict()
            obj_list = []
            objects = ct.update(rects)

            # loop over the tracked objects
            for (objectID, centroid) in objects.items():
                obj_dict = {}
                # check to see if a trackable object exists for the current
                # object ID
                to = trackableObjects.get(objectID, None)

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
                trackableObjects[objectID] = to

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

                        obj_list.append(obj_dict)
                        break


            totalFrames += 1




            
        
          

            res['frame_idx'] = vc_frame_idx
            res['data'] = obj_list
            res['fp_time'] = time.time()
            res['vc_time'] = vc_time
            
            # send images to descriptors only if people is detected
            if len(crops) > 0:
                send_data(publisher,crops,0,False,**res)


            #sending data to collector
            col_dict = {'people': obj_list ,'frame_idx':vc_frame_idx,'vc_time':vc_time}
            send_data(col_socket,None,0,False,**col_dict)
            

            #clearing memory
            self.displayed_frame= None
            self.stats_maker.elaborated_frames += 1
            self.stats_maker.stat_people = len(self.people)




            
            

        print("fp: interrupt received, stopping")
        # clean up
        vc_socket.close()
        col_socket.close()
        publisher.close()
        context.term()

    def __send_stats(self):
        
        stats = self.stats_maker.create_stats()
        stats_dict = {self.__class__.__name__:stats}
        send_data(self.monitor_stats_sender,None,0,False,**stats_dict)

            
            
if __name__ == '__main__':
    

    prod = PersonProvider({'in':VC_OUT,'out': PP_OUT, 'out_to_col': PP_OUT_TO_COL })
    prod.start() 

            
            
