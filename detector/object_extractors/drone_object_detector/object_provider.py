
import numpy as np
"""
from detection_constants import *

from deep_sort import preprocessing
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from deep_sort.detection import Detection as ddet
from deep_sort.tracker import Tracker
from deep_sort.tools import generate_detections as gdet

from yolo_detector import YoloDetector

from associator import associate
"""
from utils.socket_commons import send_data, recv_data
from utils.stats_maker import StatsMaker
from utils.features import Object, Point, Rect



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

        

        
        
   



    def run(self):


        """
        caffe.set_mode_gpu()
        caffe.set_device(0)
        """
       
        
        
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
        
        MAX_SKIP_TIME = 0.3
        buffer_was_empty = True
        skip_counter = 0
        # read the first frame waiting indefinetely
        last_rec_dict, last_imgs = recv_data(vc_socket,0,False)
        last_vc_time = last_rec_dict['vc_time']
        last_alg_time = 0
        skipping = True
        
        while True:
            object_list = []

            # rec_dict,imgs = recv_data(vc_socket,0,False)

            # self.stats_maker.received_frames += 1
            # current_frame = imgs[0]
            # vc_frame_idx = rec_dict['frame_idx']
            # vc_time = rec_dict['vc_time']

            # if time.time() - vc_time > MAX_ALLOWED_DELAY:
            #     self.stats_maker.skipped_frames += 1
            #     temp = True
            #     count = 0
            #     while temp:
            #         print('flushing')
            #         rec_dict,imgs = recv_data(vc_socket,0,False)
            #         count+=1
            #         vc_time = rec_dict['vc_time']
            #         if time.time() - vc_time < 0.3:
            #             temp = False
            #             print('Buffer frame flushed: ',count)

            #     continue
            
            # ****** Always skipping code ******
            try:
                if skipping:
                    # read a new frame without waiting (raise an error is there is none)
                    new_rec_dict, new_imgs = recv_data(vc_socket,1,False) 
                    buffer_was_empty = False               
                else:
                    # use last read frame 
                    new_rec_dict, new_imgs = last_rec_dict, last_imgs 
                    skipping = True

                new_vc_time = new_rec_dict['vc_time']
                skip_time = new_vc_time - last_vc_time
                current_delay = time.time() - new_vc_time
                forecast_delay = current_delay + last_alg_time
                if current_delay > MAX_ALLOWED_DELAY:
                    print(f'Skipping because delay is already too high. current_delay: {current_delay}, forecast_delay: {forecast_delay}, skip_time: {skip_time}')
                    skipping = True
                # elif forecast_delay > MAX_ALLOWED_DELAY:
                #     print(f'Skipping because delay will be too high. forecast_delay: {forecast_delay}, current_delay: {current_delay}, skip_time: {skip_time}')
                #     skipping = True
                elif skip_time > MAX_SKIP_TIME:
                    print(f'Max skip time reached. skip_time: {skip_time}, current_delay: {current_delay}, forecast_delay: {forecast_delay}')
                    skipping = False
                
                if skipping:
                    # save the read frame
                    last_rec_dict, last_imgs = new_rec_dict, new_imgs 
                    skip_counter += 1 
                    # and try to read a new one  
                    continue 
                else: # if the max skip time was reached
                    print('using last frame')
                    # use the previous frame (which do not goes over the max skip time)
                    rec_dict, imgs = last_rec_dict, last_imgs
                    # save the read frame
                    last_rec_dict, last_imgs = new_rec_dict, new_imgs
            except zmq.ZMQError:
                print('Buffer empty')
                if buffer_was_empty:
                    print('Wating for new frames because buffer was already empty')
                    # read a new frame waiting indefinetely
                    rec_dict,imgs = recv_data(vc_socket,0,False)
                    buffer_was_empty = False
                else:
                    print('using last frame')
                    # use last read frame 
                    rec_dict,imgs = last_rec_dict, last_imgs
                    buffer_was_empty = True
            
            print(f'Frames skipped: {skip_counter}')
            skip_counter = 0
            last_vc_time = rec_dict['vc_time']

            self.stats_maker.received_frames += 1
            current_frame = imgs[0]
            vc_frame_idx = rec_dict['frame_idx']
            vc_time = rec_dict['vc_time']  
            # ****** End always skipping code ******
            frame_shape = rec_dict['frame_shape']  


            #algorithm start
            alg_start = time.time()
            object_list = self.extract_features(current_frame,(frame_counter))
            alg_end = time.time()

            last_alg_time = alg_end - alg_start
            print('Total alg time: ', alg_end - alg_start)
            res = dict()
            crops = []
            obj_list_serialized = []

            for i,obj in enumerate(object_list):
                #print(obj)
                
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
            print('Total provider time: ', time.time() - alg_start, ' for frame ', frame_counter, 'with ', len(object_list), ' objects')
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

    def __rescale_object(self,obj):
        obj_dict = dict()
                
        rect_dict = dict()
        rect_dict['x_topleft'] = int(obj.rect.top_left_point.x_coordinate / self.ratio)
        rect_dict['y_topleft'] = int(obj.rect.top_left_point.y_coordinate / self.ratio)
        rect_dict['x_bottomright'] = int(obj.rect.bottom_right_point.x_coordinate / self.ratio)
        rect_dict['y_bottomright'] =int(obj.rect.bottom_right_point.y_coordinate / self.ratio)
        
        points = []
        for obj_p in obj.points:
            points.append([int(obj_p.x_coordinate / self.ratio), int(obj_p.y_coordinate / self.ratio), obj_p.properties['tag']])
        """
        try:
            print('len',len(points))
            print(str(obj.pid))
            obj_dict['pid'] = str(obj.pid)
            obj_dict['rect'] = rect_dict
            obj_dict['points'] = points
            print(obj_dict)
        except Exception as e:
            raise e
        """
        obj_dict['pid'] = str(obj.pid)
        obj_dict['rect'] = rect_dict
        obj_dict['points'] = points
        obj_dict['class'] = obj.rect.properties['class']

        return obj_dict


            
            
if __name__ == '__main__':
    

    
    prod = ObjectsProvider({'in':VC_OUT,'out': FP_OUT,'out_col': FP_OUT_TO_COL })
    prod.run()

            
            
