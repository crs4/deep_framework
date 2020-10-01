

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



        while True:
            


            #get message from sub collector
            
            rec_dict, __ = recv_data(sub_col_socket,0,False)


            #sends results to main collector
            #col_socket.send_pyobj(rec_dict)

            send_data(col_socket,None,0,False,**rec_dict)


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
    subs = []
    
    ALGS=os.environ['ALGS']
    alg_list=ALGS.split(',')
    

    for alg in alg_list:
        alg_name,broker_port, sub_col_port, col_port = alg.split(':')
        sub = SubCollector({'in':sub_col_port,'out':col_port,'alg':alg_name})
        subs.append(sub)


    # start worker 
    for s in subs:
        s.start()
   




