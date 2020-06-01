
from multiprocessing import Process
import numpy as np

from face_detection_constants import *
import imutils

from face_detector import FaceNet_vcaffe
from tracking.tracker import Tracker,TrackerCV
from object_manager.manager import ObjectManager
from utils.geometric_functions import resize_image
from utils.socket_commons import send_data, recv_data
from utils.stats_maker import StatsMaker

import copy
import zmq
import time,json
import cv2
import sys






class ObjectsProvider(Process):

    def __init__(self, configuration):

        Process.__init__(self)
        self.stats_maker = StatsMaker()
        self.pub_port = configuration['out']
        self.col_port = configuration['out_col']
        self.rec_port = configuration['in']


        self.tracker = Tracker(**LK_PARAMS) # method for points tracking
        #self.tracker = TrackerCV() # method for points tracking
        
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
       
        self.face_det = FaceNet_vcaffe(**FACENET_PARAMS) # method for face detection.
        object_manager = ObjectManager()
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
        #col_socket.bind(PROT+'*:'+self.col_port)
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

            try:
                self.ratio = FACE_IMAGE_WIDTH/float(current_frame.shape[1])
            except Exception as e:
                print('exception in rec frame ',e)
                continue

            current_frame = imutils.resize(current_frame, width=FACE_IMAGE_WIDTH)

            #computation of tracking features
            if any(self.features.values()) and  (self.tracking_success or self.features_by_detector):
                """
                try:
                    self.tracking_success, new_features = self.tracker.update_features(current_frame,self.features, **{'features_by_detector':self.features_by_detector})   
                except Exception as e:
                    print(str(e),'tracks')
                    self.reset_app()
                """
                #print('tr')
                self.tracking_success, new_features = self.tracker.update_features(current_frame,self.features, **{'features_by_detector':self.features_by_detector})   

                if self.tracking_success:
                    self.features = new_features
                    self.features_by_detector = False
                

            # computation of detector features
            if frame_counter % DETECTION_INTERVAL == 0 or not self.tracking_success:
                #print('det')
                self.features = self.face_det.detect_face(current_frame)
                self.features_by_detector = True



            # creating / updating / removing objects
            object_list = object_manager.manage_object_list(self.features, current_frame.shape[1],current_frame.shape[0],'POINTS')
            """
            try:

                object_list = object_manager.manage_object_list(self.features, current_frame.shape[1],current_frame.shape[0])

            except Exception as e:
                print(str(e),'updating')
                self.reset_app()
            """

        
            
            
            self.tracker.set_last_frame(current_frame)






            res = dict()
            crops = []
            obj_list_serialized = []


            for obj in object_list:
                obj_serialized = obj.serialize()

                obj_rect = obj_serialized['rect']
                obj_points = obj_serialized['points']
                crop = current_frame[obj_rect['top_left_point']['y_coordinate']:obj_rect['bottom_right_point']['y_coordinate'],obj_rect['top_left_point']['x_coordinate']:obj_rect['bottom_right_point']['x_coordinate']]
                
                obj_dict = dict()
                
                rect = dict()
                rect['x_topleft'] = int(obj_rect['top_left_point']['x_coordinate'] / self.ratio)
                rect['y_topleft'] = int(obj_rect['top_left_point']['y_coordinate'] / self.ratio)
                rect['x_bottomright'] = int(obj_rect['bottom_right_point']['x_coordinate'] / self.ratio)
                rect['y_bottomright'] =int(obj_rect['bottom_right_point']['y_coordinate'] / self.ratio)
                
                
                points = []
                for obj_p in obj_points:
                    points.append([obj_p['x_coordinate']/self.ratio, obj_p['y_coordinate'] / self.ratio, obj_p['properties']['tag']])
                    
                obj_dict['pid'] = obj_serialized['pid']
                obj_dict['rect'] = rect
                obj_dict['points'] = points
                obj_list_serialized.append(obj_dict)
                crops.append(np.ascontiguousarray(crop, dtype=np.uint8))

                
            
            res['frame_idx'] = vc_frame_idx
            res['objects'] = obj_list_serialized
            res['fp_time'] = time.time()
            res['vc_time'] = vc_time

            print('det res: ',obj_list_serialized)
            
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


            
            
if __name__ == '__main__':
    

    
    prod = ObjectsProvider({'in':VC_OUT,'out': FP_OUT,'out_col': FP_OUT_TO_COL })
    prod.start() 

            
            
