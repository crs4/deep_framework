
from multiprocessing import Process
import numpy as np
from configparser import ConfigParser

from interface_constants import *


from utils.socket_commons import send_data, recv_data
from utils.stats_maker import StatsMaker
from utils.features import Object, Rect, Point

import copy
import zmq
import time,json
import cv2
import sys
import importlib








class ObjectProvider(Process):

    def __init__(self, configuration):

        Process.__init__(self)
        self.stats_maker = StatsMaker()
        self.pub_port = configuration['out']
        self.col_port = configuration['out_col']
        self.rec_port = configuration['in']
        self.det_config = configuration['det_config']

    def run(self):


        try:
            # create instance of specific descriptor
            self.det_name = self.det_config['category']
            module = importlib.import_module(self.det_config['path'])
            det_instance = getattr(module, self.det_config['class'])
            self.executor = det_instance()
            print('CREATED ',self.det_name)
        except Exception as e:
                print(e,'setup detector')

        
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
            """
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

            """
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
            frame_shape = rec_dict['frame_shape']  






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


    def __send_stats(self):
        
        stats = self.stats_maker.create_stats()
        stats_dict = {self.__class__.__name__:stats}
        send_data(self.monitor_stats_sender,None,0,False,**stats_dict)

    def __rescale_object(self,obj):

        obj_dict = dict()
                
        rect = dict()
        rect['x_topleft'] = int(obj.rect.top_left_point.x_coordinate)
        rect['y_topleft'] = int(obj.rect.top_left_point.y_coordinate)
        rect['x_bottomright'] = int(obj.rect.bottom_right_point.x_coordinate )
        rect['y_bottomright'] =int(obj.rect.bottom_right_point.y_coordinate)
        
        
        points = []
        for obj_p in obj.points:
            points.append([int(obj_p.x_coordinate), int(obj_p.y_coordinate), obj_p.properties['tag']])
            
        obj_dict['pid'] = str(obj.pid)
        obj_dict['rect'] = rect
        obj_dict['points'] = points
        if 'class' in obj.rect.properties.keys():
            obj_class = obj.rect.properties['class']
        else:
            obj_class = self.det_name
        obj_dict['class'] = obj_class
        return obj_dict

            
if __name__ == '__main__':




    """
    Load configuration of descriptors installed
    """
    
    installed_algs = []
    detector_list = []
    cur_dir =  os.path.split(os.path.abspath(__file__))[0]
    

    config_file = [os.path.join(dp, f) for dp, dn, filenames in os.walk(cur_dir) for f in filenames if os.path.splitext(f)[1] == '.ini'][0]
    config = ConfigParser()
    config.read(config_file)
    det_config = {'path': config.get('CONFIGURATION','PATH'), 'class':config.get('CONFIGURATION','CLASS'),'category':config.get('CONFIGURATION','CATEGORY')}
 
    
    prod = ObjectProvider({'in':STREAM_OUT,'out': FP_OUT,'out_col': FP_OUT_TO_COL, 'det_config': det_config})
    prod.start()
    

            
            
