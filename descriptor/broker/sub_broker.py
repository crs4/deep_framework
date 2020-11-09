

from multiprocessing import Process

from sub_broker_constants import *

import time
import zmq
import sys
import os

from utils.socket_commons import send_data,recv_data








class SubBroker(Process):
    def __init__(self,configuration):
        """
        This class allows to distribute messages between descriptors
        """
        
        self.rec_det_port = configuration['in']
        self.send_port = configuration['out']
        self.broker_name = configuration['broker_name']
        Process.__init__(self)

    def run(self):

        context = zmq.Context()

        #socket to receive from frame provider
        fp_socket = context.socket(zmq.SUB)
        fp_socket.setsockopt_string(zmq.SUBSCRIBE, "",encoding='ascii')
        fp_socket.connect(PROT+FP_ADDRESS+':'+self.rec_det_port)

        #socket to send to descriptors
        sub_broker_socket = context.socket(zmq.PUSH)
        sub_broker_socket.bind(PROT+'*'+':'+self.send_port)
        sub_broker_data = dict()

        print('START BROKER: ',self.broker_name)

        while True:
            
            #receive data from frame provider. Data type: {'frame_idx': 123, 'data': [(p1,crop1),....,(pn,cropn)]}
            rec_dict,imgs =recv_data(fp_socket,0,False)
            vc_frame_idx = rec_dict['frame_idx']
            people_data = rec_dict['objects'] 
            fp_time = rec_dict['fp_time']
            vc_time = rec_dict['vc_time']
            
            # skip old frames
            if (time.time() - vc_time) > MAX_ALLOWED_DELAY:
                continue
            
            # creation of message for descriptors
            sub_broker_data['objects'] = people_data
            sub_broker_data['frame_idx'] = vc_frame_idx
            sub_broker_data['vc_time'] = vc_time
            sub_broker_data['fp_time'] = fp_time
            sub_broker_data['frame_shape'] = rec_dict['frame_shape']
            
            
            send_data(sub_broker_socket,imgs,0,False,**sub_broker_data)




        print("subs broker: interrupt received, stopping")
        # clean up
        sub_broker_socket.close()
        fp_socket.close()
        context.term()
  
if __name__ == '__main__':


    import os

    """
    Load configuration of descriptors installed
    """
    
    

    sub = SubBroker({'in':FP_OUT,'out':BROKER_PORT,'broker_name':BROKER_NAME})
    sub.start()


    




