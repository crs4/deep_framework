

from multiprocessing import Process

from sub_collector_constants import *

import time
import zmq
import sys
import os

from utils.socket_commons import send_data, recv_data
from utils.stats_maker import StatsMaker






class SubCollector(Process):
    def __init__(self,configuration):
        """
        This class allows to aggregate message senf from descriptors
        """
        self.__init_stats()
        self.rec_det_port = configuration['in']
        self.send_port = configuration['out']
        Process.__init__(self)

    def run(self):

        context = zmq.Context()

        # get data from subs
        sub_col_socket = context.socket(zmq.PULL)
        sub_col_socket.bind(PROT+'*'+':'+self.rec_det_port)


        # send data to main collector
        col_socket = context.socket(zmq.PAIR)
        col_socket.connect(PROT+COLLECTOR_ADDRESS+':'+self.send_port)

        # sends stats to monitor
        self.monitor_sender = context.socket(zmq.PUB)
        self.monitor_sender.connect(PROT+MONITOR_ADDRESS+':'+MONITOR_STATS_IN)
        
        self.source_id = COLLECTOR_ADDRESS.split('collector_')[-1]
        self.alg_detector_category = COLLECTOR_ADDRESS.split('_')[0]


        sub_max_size = int(WORKER)
        last_vc_time = 0

        self.stats_maker.run_fps_timer()
        self.stats_maker.run_stats_timer(INTERVAL_STATS,self.__send_stats)
        while True:
            

            rec_dict, __ = recv_data(sub_col_socket,0,False)

            vc_time = rec_dict['vc_time']
            if vc_time > last_vc_time:
                send_data(col_socket,None,0,False,**rec_dict)
                last_vc_time = vc_time
                self.stats_maker.elaborated_frames+=1



        print("subs collector: interrupt received, stopping")
        # clean up
        col_socket.close()
        col_socket.close()
        context.term()

    def __init_stats(self):
        self.stats_maker = StatsMaker()
        self.stats_maker.elaborated_frames = 0

    def __send_stats(self):
        stats = self.stats_maker.create_stats()
        #stats_dict={self.alg_name:stats}
        stats_dict={'component_name':DESC_NAME,'component_type': 'sub_collector', 'source_id':self.source_id, 'detector_category':self.alg_detector_category, 'stats':stats}
        send_data(self.monitor_sender,None,0,False,**stats_dict)
  
if __name__ == '__main__':


    import os

    """
    Load configuration of descriptors installed
    """
    
    

    
    sub = SubCollector({'in':SUB_COL_PORT,'out':COL_PORT})
    sub.start()

  




