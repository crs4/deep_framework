
from multiprocessing import Process

from utils.stats_maker import StatsMaker

from collector_constants import *
import time

import zmq
import cv2
import json
import os,sys
from utils.socket_commons import recv_data, send_data


class Collector(Process):
    """
    This class aggregates images from FrameProvider and results from descriptors.
    It executes continous no blocking polling from these components.
    """

    
    def __init__(self,subscribers,configuration):
        self.subs = subscribers
        self.out_stream_port = configuration['out_stream_port']
        self.out_server_port = configuration['out_server_port']
        self.fp_port =configuration['fp_in']
        self.stats_maker = StatsMaker()
        Process.__init__(self)

        

    def run(self):
        """
        Run collecting process.
        """
        
        context = zmq.Context()
        poller = zmq.Poller()

        #  registration of algorithms subscribers
        receivers = []
        for s in self.subs:
            rec = context.socket(zmq.PAIR)
            rec.bind(PROT+'*:'+s['send_port'])
            poller.register(rec, zmq.POLLIN)
            receivers.append((s['alg'],rec))

        
        
        # sends final data stream

        sender = context.socket(zmq.PAIR)
        sender.connect(PROT+STREAM_MANAGER_ADDRESS+':'+self.out_stream_port)

        server_sender = context.socket(zmq.PAIR)
        server_sender.connect(PROT+SERVER_ADDRESS+':'+self.out_server_port)

        # sends stats to monitor
        self.monitor_sender = context.socket(zmq.PUB)
        self.monitor_sender.connect(PROT+MONITOR_ADDRESS+':'+MONITOR_STATS_IN)

        self.source_id = STREAM_MANAGER_ADDRESS.split('stream_manager_')[-1]



        #get frame from frame provider
        fp_socket = context.socket(zmq.PAIR)
        fp_socket.bind(PROT+'*:'+self.fp_port)

       
        subs_output = dict()
        subs_image_attributes = dict()
        subs_image_attributes['image_attributes'] = dict()

        objects_res = []
        mess = None
        
        # run timer for stats computation
        self.stats_maker.run_fps_timer()
        self.stats_maker.run_stats_timer(INTERVAL_STATS,self.__send_stats)
        
        while True:
            result = dict()
            objects_res = []

            # receive frame and data from frame provider
            fp_dict,__= recv_data(fp_socket,0,False)
            frame_id = fp_dict['frame_idx']
            fp_objects = fp_dict['objects']
            vc_time = fp_dict['vc_time']

            pids_fp = list(map(lambda x: x['pid'], fp_objects)) # id of new objects in the scene
            for p in pids_fp:
                if p not in subs_output.keys():
                    subs_output[p] = dict()
            
            # blocks until one or more puller receives a message for a waiting time
            socks = dict(poller.poll(0)) 
            for rec_tuple in receivers:
                name, rec = rec_tuple
                if rec in socks and socks[rec] == zmq.POLLIN:
                    mess, __ = recv_data(rec,zmq.DONTWAIT,False)
                    
                    res_dict = mess['obj_res_dict']
                    img_res = mess['img_res']
                    vc_alg_time = mess['vc_time']
                    if img_res:
                        subs_image_attributes['image_attributes'][name] = {'value':img_res,'vc_time':vc_alg_time}
                        #subs_image_attributes['image_attributes'][name] = img_res

                    for pid, res in res_dict.items():

                        try:
                            subs_output[pid][name] = {'value':res,'vc_time':vc_alg_time}
                        except Exception as inst:
                            print(inst, 'ex coll')
                            continue

                        

                    # mess = {'frame_idx':123,'sub_res_dict': res_alg, 'draw': draw_func}

                    # res_alg ={'ueu8300029ks993': ['angry',...'], 'hdfhsdfk883u': ['sad',...'] }

            for obj in fp_objects:

                

                temp_obj_dict = obj

                res_algs = subs_output[obj['pid']]

                if len( res_algs.keys() ) > 0:

                    for alg_name, classification in res_algs.items():

                        temp_obj_dict[alg_name] = classification
                       

                objects_res.append(temp_obj_dict)

            
           

            r = dict()
            r['collector_time'] = time.time()
            r['objects'] = objects_res
            r['frame_attributes'] = subs_image_attributes['image_attributes']
            r['vc_time'] = vc_time
            
            
            send_data(sender,None,0,False,**r)
            send_data(server_sender,None,0,False,**r)


            self.stats_maker.elaborated_frames+=1



            #clearing objects not more in scene
            pids_departed = set(subs_output.keys()).difference(set(pids_fp))
            if len(pids_departed) > 0:
                
                for p_dep in pids_departed:
                    del subs_output[p_dep]
        

            
        print("collector: interrupt received, stopping")
        # clean up
        fp_socket.close()
        sender.close()
        context.term()

    def __send_stats(self):
        
        stats = self.stats_maker.create_stats()
        #stats_dict={COMPONENT_NAME:stats}
        stats_dict={'component_name':COMPONENT_NAME, 'component_type': 'collector', 'source_id':self.source_id, 'stats':stats}

        send_data(self.monitor_sender,None,0,False,**stats_dict)



if __name__ == '__main__':
    
    subs = []
    alg_list=ALGS.split(',')

    if len(alg_list) > 0 and alg_list[0] != '':

        for i, alg in enumerate(alg_list):
            alg_name, col_port = alg.split(':')
            subs.append({'send_port':col_port,'alg':alg_name})


    print(subs)
    collector = Collector(subs, {'fp_in': PROV_OUT_TO_COL,'out_stream_port':OUT_STREAM_PORT,'out_server_port':OUT_SERVER_PORT} )
    collector.start()


