

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
        last_worker_id = None
        while True:
            #get message
            rec_dict, __ = recv_data(self.rec_stats,0,False)

            source_id = rec_dict['source_id']
            source_id = 'source_'+source_id
            component_type = rec_dict['component_type']
            stats = rec_dict['stats']
            if source_id not in self.stats.keys():
                self.stats[source_id] = {'stream_manager': dict(),'pipelines': dict()}

            if component_type == 'stream_manager':
                print(stats)
                self.stats[source_id]['stream_manager'] = stats

            elif component_type == 'detector':
                print('det')
                category = rec_dict['component_name']
                if category in self.stats[source_id]['pipelines'].keys():
                    self.stats[source_id]['pipelines'][category]['detector'] = stats
                else:
                    self.stats[source_id]['pipelines'][category] = {'detector':stats}


            elif component_type == 'descriptor' or component_type == 'sub_collector':
                component_name = rec_dict['component_name']
                category = rec_dict['detector_category']
                if category in self.stats[source_id]['pipelines'].keys():
                    if 'descriptors' in self.stats[source_id]['pipelines'][category].keys():
                        if component_name in self.stats[source_id]['pipelines'][category]['descriptors'].keys():
                            if component_type == 'sub_collector':
                                self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['fps'] = stats['fps']
                            else:
                                worker_id = rec_dict['worker_id']
                                if last_worker_id == worker_id:
                                    self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['elaborated_frames'] = stats['elaborated_frames']
                                    self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['skipped_frames'] = stats['skipped_frames']
                                    self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['received_frames'] = stats['received_frames']

                                else:
                                    self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['elaborated_frames'] = self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['elaborated_frames'] + stats['elaborated_frames']
                                    self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['skipped_frames'] = self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['skipped_frames'] + stats['skipped_frames']
                                    self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['received_frames'] = self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['received_frames'] + stats['received_frames']

                                last_worker_id = worker_id


                        else:
                            self.stats[source_id]['pipelines'][category]['descriptors'] = {component_name:stats}

                    else:
                        self.stats[source_id]['pipelines'][category]['descriptors'] = {component_name:stats}






            elif component_type == 'collector':
                category = rec_dict['component_name'].split('_')[0]
                if category in self.stats[source_id]['pipelines'].keys():
                    self.stats[source_id]['pipelines'][category]['collector'] = stats




            """
            for k,v in rec_dict.items():

                if k in self.algs:
                    algs_stats[k] = v
                    continue
                
                self.stats[k] = v

            self.stats['algorithms'] = algs_stats
            """
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

