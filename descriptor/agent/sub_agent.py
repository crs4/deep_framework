
from multiprocessing import Process
from utils.window import SlidingWindow


from utils.stats_maker import StatsMaker

from sub_agent_constants import *

import time
import zmq
import cv2
import sys
import os
import importlib



from utils.socket_commons import send_data, recv_data



class Sub(Process):
    def __init__(self,configuration):
        """
        This class allows to execute a generic descriptor
        """
        
        self.rec_det_port = configuration['in']
        self.send_port = configuration['out']
        self.alg = configuration['alg']
        self.stats_maker = StatsMaker()
        Process.__init__(self)

    def run(self):

        if MODE == 'GPU':
            gpu_id=int(os.environ['GPU_ID'])
            framework=os.environ['FRAMEWORK']
            if framework == 'caffe':
                import caffe
                caffe.set_mode_gpu()
                caffe.set_device(gpu_id)
            if framework == 'tensorflow':
                os.environ['CUDA_VISIBLE_DEVICES'] = os.environ['GPU_ID']

        try:
            # create instance of specific descriptor
            self.alg_name = self.alg['name']
            module = importlib.import_module(self.alg['path'])
            alg_instance = getattr(module, self.alg['class'])
            det = alg_instance()
            print('CREATED ',self.alg_name)
            WIN_SIZE = det.win_size
        except Exception as e:
                print(e,'setup')

        context = zmq.Context()


        # sends stats to monitor
        self.monitor_sender = context.socket(zmq.PUB)
        self.monitor_sender.connect(PROT+MONITOR_ADDRESS+':'+MONITOR_STATS_IN)
        

        # subscribes to sub broker to get people data
        sub_broker_socket = context.socket(zmq.PULL)
        sub_broker_socket.connect(PROT+BROKER_ADDRESS+':'+self.rec_det_port)

       

        # sends results to sub collector
        sub_col_socket = context.socket(zmq.PUSH)
        sub_col_socket.connect(PROT+SUB_COLLECTOR_ADDRESS+':'+self.send_port)

        people_old = []
        windows = dict()
        
        print('END INIT ' + self.alg_name)
        # run timer in order to compute stats
        self.stats_maker.run_fps_timer()
        self.stats_maker.run_stats_timer(INTERVAL_STATS,self.__send_stats)
       
        while True:
            

            sub_res = dict()
            res_dict = dict()
            pids_old = []

            #get message from publisher
            rec_dict,crops =recv_data(sub_broker_socket,0,False)
            self.stats_maker.received_frames +=1

            vc_frame_idx = rec_dict['frame_idx']
            people = rec_dict['objects'] # {'frame_idx': 123, 'data': [(p1,crop1),....,(pn,cropn)]}

            fp_time = rec_dict['fp_time']
            vc_time = rec_dict['vc_time']
            
            #skip old frames
            if (time.time() - fp_time) > MAX_ALLOWED_DELAY or (time.time() - vc_time) > MAX_ALLOWED_DELAY:
                self.stats_maker.skipped_frames+=1
                continue

            
            # tracks people present in previous frames
            if len(people_old) != 0:
                
                pids_new = list(map(lambda x: x['pid'], people)) # id of new people in the scene
                people_old = list(filter(lambda x: x['pid'] in pids_new , people_old)) # list of people in the scene already present in previous frames
                
                pids_old = list(map(lambda x: x['pid'], people_old))
                windows = {k: v for k, v in windows.items() if k in pids_new}

            
            alg_res = []
            try:
                alg_res = det.detect_batch(crops)
            except Exception as e:
                print(e,'desc')


            for p,r in zip(people,alg_res):
                # check if person is already present
                if p['pid'] in pids_old:
                    win = windows[p['pid']]
                
                else:
                    win = SlidingWindow(size=WIN_SIZE)
                    windows[p['pid']] = win
                    people_old.append(p)

                
                win.add_item(r)

                ref = det.refine_classification(win.items)

                res_dict[p['pid']] = ref

           
            
            self.stats_maker.elaborated_frames+=1
          
            sub_res['sub_res_dict'] = res_dict
            sub_res['frame_idx'] = vc_frame_idx
            
            #sends results to collector
            send_data(sub_col_socket,None,0,False,**sub_res)

            #clearing memory
            crops = None
            

        print("subs: interrupt received, stopping")
        # clean up
        sub_col_socket.close()
        sub_broker_socket.close()
        context.term()

    def __send_stats(self):
        
        stats = self.stats_maker.create_stats()
        stats_dict={self.alg_name:stats}
        send_data(self.monitor_sender,None,0,False,**stats_dict)


if __name__ == '__main__':


    import importlib
    import os
    from configparser import ConfigParser



    """
    Load configuration of descriptors installed
    """
    
    installed_algs = []
    subs = []
    cur_dir =  os.path.split(os.path.abspath(__file__))[0]
    

    config_file = [os.path.join(dp, f) for dp, dn, filenames in os.walk(cur_dir) for f in filenames if os.path.splitext(f)[1] == '.ini'][0]
    config = ConfigParser()
    config.read(config_file)
    alg_config = {'path': config.get('CONFIGURATION','PATH'), 'class':config.get('CONFIGURATION','CLASS'),'name':config.get('CONFIGURATION','NAME')}
    
    ALGS=os.environ['ALGS']
    alg_list=ALGS.split(',')
    

    for alg in alg_list:
        
        alg_name,broker_port, sub_col_port, col_port = alg.split(':')
        if alg_name == alg_config['name']:
            sub = Sub({'in':broker_port,'out':sub_col_port,'alg':alg_config})
            subs.append(sub)


    # start worker 
    for s in subs:
        s.start()
    
    






