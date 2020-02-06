

from multiprocessing import Process

from monitor_constants import *

import time
import zmq

from utils.socket_commons import recv_data, send_data

import os,sys



class Monitor(Process):
    def __init__(self,configuration):
        
        self.rec_stats_port = configuration['in_stats']
        self.send_stats_port = configuration['out_stats']
        
        self.algs = configuration['algs']
        Process.__init__(self)

    def run(self):
        
        self.stats = dict()
        
        context = zmq.Context()
        
        
        # rec stats from components
        self.rec_stats = context.socket(zmq.SUB)
        self.rec_stats.setsockopt_string(zmq.SUBSCRIBE, "",encoding='ascii')
        
        self.rec_stats.bind(PROT+'*:'+self.rec_stats_port)


        # sends stats
        self.stats_send = context.socket(zmq.PUB)
        self.stats_send.bind(PROT+'*:'+self.send_stats_port)

        algs_stats = dict()
        while True:
            #get message
            rec_dict, __ = recv_data(self.rec_stats,0,False)

            for k,v in rec_dict.items():

                if k in self.algs:
                    algs_stats[k] = v
                    continue
                
                self.stats[k] = v

            self.stats['algorithms'] = algs_stats
            #sends results
            send_data(self.stats_send,None,0,False,**self.stats)

        print("monitor: interrupt received, stopping")
        # clean up
        sender.close()
        context.term()
        sys.exit(0)

        
             


if __name__ == '__main__':

   
    ALGS = os.environ['ALGS']
    alg_list=ALGS.split(',')

    subs = []
    for alg in alg_list:

        subs.append(alg)

    
    monitor = Monitor({'in_stats':MONITOR_STATS_IN,'out_stats': MONITOR_STATS_OUT,'algs':subs})


    monitor.start()

