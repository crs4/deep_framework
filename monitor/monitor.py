

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

        descriptor_elaborated_acc = 0
        descriptor_skipped_acc = 0
        descriptor_received_acc = 0

        last_descriptor_elaborated = 0
        last_descriptor_skipped = 0
        last_descriptor_received = 0
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
                #print('stream_MAN',stats)
                self.stats[source_id]['stream_manager'] = stats

            elif component_type == 'detector':
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
                                print(stats)
                                self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['fps'] = stats['fps']
                                self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['worker'] = rec_dict['worker']
                            else:
                                worker_id = rec_dict['worker_id']
                                #print(worker_id, stats)
                                if last_worker_id == worker_id:
                                    #print('same')
                                    descriptor_elaborated_acc = descriptor_elaborated_acc + (stats['elaborated_frames']- last_descriptor_elaborated)
                                    descriptor_received_acc = descriptor_received_acc + (stats['received_frames']- last_descriptor_received)
                                    descriptor_skipped_acc = descriptor_skipped_acc + (stats['skipped_frames']- last_descriptor_skipped)
                      
                                else:
                                    #print('diff','--------',self.stats[source_id]['pipelines'][category]['descriptors'][component_name])
                                    descriptor_elaborated_acc = descriptor_elaborated_acc + stats['elaborated_frames']
                                    descriptor_skipped_acc = descriptor_skipped_acc + stats['skipped_frames']
                                    descriptor_received_acc = descriptor_received_acc + stats['received_frames']

                                
                                self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['elaborated_frames'] = descriptor_elaborated_acc
                                self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['skipped_frames'] = descriptor_skipped_acc
                                self.stats[source_id]['pipelines'][category]['descriptors'][component_name]['received_frames'] = descriptor_received_acc
                                
                                last_worker_id = worker_id
                                last_descriptor_elaborated = stats['elaborated_frames']
                                last_descriptor_skipped = stats['received_frames']
                                last_descriptor_received = stats['skipped_frames']


                        else:
                            self.stats[source_id]['pipelines'][category]['descriptors'][component_name] = stats

                    else:
                        #self.stats[source_id]['pipelines'][category]['descriptors'] = {component_name:{'elaborated_frames':stats['elaborated_frames'],'skipped_frames': stats['skipped_frames'],'received_frames':stats['received_frames'] }}
                        self.stats[source_id]['pipelines'][category] = {'descriptors':{component_name:stats}}






            elif component_type == 'collector':
                category = rec_dict['component_name'].split('_')[0]
                if category in self.stats[source_id]['pipelines'].keys():
                    self.stats[source_id]['pipelines'][category]['collector'] = stats


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

