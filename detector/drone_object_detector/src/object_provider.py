
import numpy as np

from detection_constants import *
import imutils
from tracker import DeepSortTracker

from detector import VisdroneDectector
from utils.geometric_functions import resize_image
from utils.socket_commons import send_data, recv_data
from utils.stats_maker import StatsMaker

import copy
import zmq
import time,json
import cv2
import sys





class ObjectsProvider():

    def __init__(self, configuration):

        #Process.__init__(self)
        self.stats_maker = StatsMaker()
        self.pub_port = configuration['out']
        self.col_port = configuration['out_col']
        self.rec_port = configuration['in']


        #self.tracker = Tracker(**LK_PARAMS) # method for points tracking
        #self.tracker = TrackerCV() # method for points tracking
        self.tracker = DeepSortTracker()
        self.features = dict()
        self.tracking_success = False
        self.features_by_detector = False
    
    def reset_app(self):
        self.features = []
        self.tracking_success = False
        self.features_by_detector = False




    def run(self):


        """
        caffe.set_mode_gpu()
        caffe.set_device(0)
        """
       
        
        self.detector = VisdroneDectector() # method for face detection.
        
        context = zmq.Context()


        # subscribes to VideoCapture
        vc_socket = context.socket(zmq.SUB)
        vc_socket.setsockopt_string(zmq.SUBSCRIBE, "",encoding='ascii')
        vc_socket.connect(PROT+VIDEOSRC_ADDRESS+':'+self.rec_port)
        
        # configure output
        publisher = context.socket(zmq.PUB)
        
        #if publisher detects slow subscribers, skips frames
        publisher.sndhwm = 1
        publisher.bind(PROT+'*:'+self.pub_port)

        # PAIR connection to collector
        col_socket = context.socket(zmq.PAIR)
        col_socket.connect(PROT+COLLECTOR_ADDRESS+':'+self.col_port)
        
        # connection to monitor for stats
        self.monitor_stats_sender= context.socket(zmq.PUB)
        self.monitor_stats_sender.connect(PROT+MONITOR_ADDRESS+':'+MONITOR_STATS_IN)

        # manage sending stats to monitor
        self.stats_maker.run_stats_timer(INTERVAL_STATS,self.__send_stats)
        self.stats_maker.run_fps_timer()
        
        
        current_frame = None
        frame_counter = 0
        

        while True:
            object_list = []

            rec_dict,imgs = recv_data(vc_socket,0,False)

            self.stats_maker.received_frames += 1
            current_frame = imgs[0]
            vc_frame_idx = rec_dict['frame_idx']
            vc_time = rec_dict['vc_time']

            if time.time() - vc_time > MAX_ALLOWED_DELAY:
                self.stats_maker.skipped_frames += 1
                continue

            #algorithm start

            try:
                self.ratio = FACE_IMAGE_WIDTH/float(current_frame.shape[1])
            except Exception as e:
                print('exception in rec frame ',e)
                continue

            current_frame = imutils.resize(current_frame, width=FACE_IMAGE_WIDTH)

            # computation of detector features
            if frame_counter % DETECTION_INTERVAL == 0:
                print('det')
                detector_features = self.detector.detect(current_frame)
                features = self.tracker.update_features(current_frame,detector_features)
                rects = features['boxes']
            
            else:
                continue


            res = dict()
            crops = []
            obj_list_serialized = []

            for i,rect in enumerate(rects):
                
                crop = current_frame[rect.top_left_point.y_coordinate:rect.bottom_right_point.y_coordinate,rect.top_left_point.x_coordinate:rect.bottom_right_point.x_coordinate]
                
                obj_dict = self.__rescale_object(rect)
                obj_list_serialized.append(obj_dict)
                crops.append(np.ascontiguousarray(crop, dtype=np.uint8))

                
            res['frame_idx'] = vc_frame_idx
            res['objects'] = obj_list_serialized
            res['fp_time'] = time.time()
            res['vc_time'] = vc_time

            #print('det res: ',obj_list_serialized)
            
            # send images to descriptors only if objects are detected
            if len(crops) > 0:
                send_data(publisher,crops,0,False,**res)

            # send data to collector
            send_data(col_socket,None,0,False,**res)

            frame_counter += 1
            
            #clearing memory
            current_frame= None

            self.stats_maker.elaborated_frames += 1
            self.stats_maker.stat_people = len(object_list)
            
            

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

    def __rescale_object(self,rect):

        obj_dict = dict()
                
        rect_dict = dict()
        rect_dict['x_topleft'] = int(rect.top_left_point.x_coordinate / self.ratio)
        rect_dict['y_topleft'] = int(rect.top_left_point.y_coordinate / self.ratio)
        rect_dict['x_bottomright'] = int(rect.bottom_right_point.x_coordinate / self.ratio)
        rect_dict['y_bottomright'] =int(rect.bottom_right_point.y_coordinate / self.ratio)
        
        
        obj_dict['pid'] = str(rect.properties['pid'])
        obj_dict['rect'] = rect_dict
        return obj_dict


            
            
if __name__ == '__main__':
    

    
    prod = ObjectsProvider({'in':VC_OUT,'out': FP_OUT,'out_col': FP_OUT_TO_COL })
    prod.run()

            
            
