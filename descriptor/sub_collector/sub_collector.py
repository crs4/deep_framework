

from multiprocessing import Process

from sub_collector_constants import *

import time
import zmq
import sys
import os

from utils.socket_commons import send_data, recv_data






class SubCollector(Process):
    def __init__(self,configuration):
        """
        This class allows to aggregate message senf from descriptors
        """
        
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

        ordered_buffer = []
        sub_buffer = []
        sub_max_size = int(WORKER)
        while True:
            


            #get message from sub collector
            
            rec_dict, __ = recv_data(sub_col_socket,0,False)
            if len(sub_buffer) < sub_max_size:
                sub_buffer.append(rec_dict)
                continue
            else:
                ordered_buffer = sorted(sub_buffer, key=lambda k: k['vc_time'])
                sub_buffer = []





            #sends results to main collector
            for msg_dict in ordered_buffer:
                #print(msg_dict)
                send_data(col_socket,None,0,False,**msg_dict)

            ordered_buffer = []


        print("subs collector: interrupt received, stopping")
        # clean up
        col_socket.close()
        col_socket.close()
        context.term()
  
if __name__ == '__main__':


    import os

    """
    Load configuration of descriptors installed
    """
    
    

    
    sub = SubCollector({'in':SUB_COL_PORT,'out':COL_PORT})
    sub.start()

  




