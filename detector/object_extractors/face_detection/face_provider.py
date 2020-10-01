
from multiprocessing import Process
import numpy as np

from face_detection_constants import *
from test_2 import FaceDetectorExecutor
"""
import imutils
from face_detector import FaceNet_vcaffe
from tracking.tracker import Tracker,TrackerCV
from object_manager.manager import ObjectManager
"""
from utils.socket_commons import send_data, recv_data
from utils.stats_maker import StatsMaker
from utils.features import Object, Rect, Point

import copy
import zmq
import time,json
import cv2
import sys





class FaceProvider(Process):

    def __init__(self, configuration):

        Process.__init__(self)
        self.stats_maker = StatsMaker()
        self.pub_port = configuration['out']
        self.col_port = configuration['out_col']
        self.rec_port = configuration['in']

        """
        self.tracker = Tracker(**LK_PARAMS) # method for points tracking
        #self.tracker = TrackerCV() # method for points tracking
        self.detector = FaceNet_vcaffe(**FACENET_PARAMS) # method for face detection.
        self.object_manager = ObjectManager()
        
        self.tracks = []
        self.tracking_success = False
        self.ratio = 1
        """
    """
    def reset_app(self):
        self.tracks = []
        self.tracking_success = False
    """




    def run(self):


        """
        caffe.set_mode_gpu()
        caffe.set_device(0)
        """
       
        
        
        context = zmq.Context()


        # subscribes to Stream Manager
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
        
        self.executor = FaceDetectorExecutor()
        while True:
            object_list = []

            rec_dict,imgs = recv_data(vc_socket,0,False)

            self.stats_maker.received_frames += 1
            current_frame = imgs[0]
            vc_frame_idx = rec_dict['frame_idx']
            vc_time = rec_dict['vc_time']
            frame_shape = rec_dict['frame_shape']

            if time.time() - vc_time > MAX_ALLOWED_DELAY:
                self.stats_maker.skipped_frames += 1
                print('skipping')
                continue

            #algorithm start
            try:
                executor_dict = dict(rec_dict)
                executor_dict['frame_counter'] = frame_counter
                object_list = self.executor.extract_features(current_frame,executor_dict)

            except Exception as e:
                print('gen ',e)
                raise e

            

            






            res = dict()
            crops = []
            obj_list_serialized = []


            for obj in object_list:
                
                crop = current_frame[obj.rect.top_left_point.y_coordinate:obj.rect.bottom_right_point.y_coordinate, obj.rect.top_left_point.x_coordinate:obj.rect.bottom_right_point.x_coordinate]
                
                obj_dict = self.__rescale_object(obj)
                obj_list_serialized.append(obj_dict)
                crops.append(np.ascontiguousarray(crop, dtype=np.uint8))

                
            
            res['frame_idx'] = vc_frame_idx
            res['objects'] = obj_list_serialized
            res['fp_time'] = time.time()
            res['vc_time'] = vc_time
            res['frame_shape'] = frame_shape

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

    """
    def extract_features(self,current_frame,*args):

        frame_counter = args[0]
        print('frame: ',frame_counter)
        try:
            self.ratio = FACE_IMAGE_WIDTH/float(current_frame.shape[1])
        except Exception as e:
            print('exception in rec frame ',e)
            

        current_frame = imutils.resize(current_frame, width=FACE_IMAGE_WIDTH)

        #computation of tracking features
        if len(self.tracks) > 0:
            

            print('tr')
            self.tracking_success, new_features = self.tracker.update_features(current_frame,self.tracks)   

            if self.tracking_success:
                self.tracks = new_features

        # computation of detector features
        if frame_counter % DETECTION_INTERVAL == 0 or not self.tracking_success:
            print('det')
            det_features = self.detector.detect(current_frame)
            self.object_manager.check_people(det_features)
            self.tracks = self.tracker.create_track_points(det_features['points'])

        people = self.object_manager.track_people(current_frame, self.tracks)
        

        self.tracker.set_last_frame(current_frame)


        object_list = self.__create_objects(people)
        return object_list
    """
                



    def __send_stats(self):
        
        stats = self.stats_maker.create_stats()
        stats_dict = {self.__class__.__name__:stats}
        send_data(self.monitor_stats_sender,None,0,False,**stats_dict)

    def __rescale_object(self,obj):

        obj_dict = dict()
                
        rect = dict()
        rect['x_topleft'] = int(obj.rect.top_left_point.x_coordinate / self.executor.ratio)
        rect['y_topleft'] = int(obj.rect.top_left_point.y_coordinate / self.executor.ratio)
        rect['x_bottomright'] = int(obj.rect.bottom_right_point.x_coordinate / self.executor.ratio)
        rect['y_bottomright'] =int(obj.rect.bottom_right_point.y_coordinate / self.executor.ratio)
        
        
        points = []
        for obj_p in obj.points:
            points.append([int(obj_p.x_coordinate / self.executor.ratio), int(obj_p.y_coordinate / self.executor.ratio), obj_p.properties['tag']])
            
        obj_dict['pid'] = str(obj.pid)
        obj_dict['rect'] = rect
        obj_dict['points'] = points
        obj_dict['class'] = 'face'
        return obj_dict


    """
    def __create_objects(self,people):
        objects = []
        for p in people:
            obj_points = []
            top_left = Point(p.rect['x_topleft'],p.rect['y_topleft'])
            bottom_right = Point(p.rect['x_bottomright'],p.rect['y_bottomright'])
            obj_rect = Rect(top_left,bottom_right)
            for k,v in p.face_points.items():
                point = Point(v[0][0],v[0][1],**{'tag':k})
                obj_points.append(point)
            obj = Object(rect = obj_rect, points = obj_points, pid = p.pid)
            objects.append(obj)
        return objects
    """

            
            
if __name__ == '__main__':
    

    
    prod = FaceProvider({'in':VC_OUT,'out': FP_OUT,'out_col': FP_OUT_TO_COL })
    prod.start()
    

            
            
