from config import *

class PipelineManager:

	def __init__(self,matches,sources):
		self.__set_connection_ports()
		self.detectors = matches['detectors']
		self.descriptors = matches['descriptors']
		self.sources = sources
		self.__set_connection_ports()
		

	def __set_connection_ports(self):
		self.ports = dict()

		self.ports['detector_collector_port'] = 4001
		self.ports['detector_broker_port'] = 5001
		self.ports['stream_manager_detector_port'] = 3500  # ?????
		self.ports['broker_descriptor_port'] = 6000
		self.ports['descriptor_subcollector_port'] = 6050
		self.ports['subcollector_collector_port'] = 7000
		self.ports['collector_stream_manager_port'] = 7050
		self.ports['collector_server_port'] = 4050
		self.ports['stream_manager_server_port'] = 4200
		self.ports['server_port'] = APP_PORT
		self.ports['monitor_in_port'] = 5550
		self.ports['monitor_out_port'] = 5551



	def create_deep_structure(self):
		deep_structure = dict()
		deep_structure['pipelines'] = []

		server = ServerComponent(self.ports)

		for source in self.sources:
			pipeline = self.create_pipeline(source,server)
			deep_structure['pipelines'].append(pipeline)

		deep_structure['server'] = server
		deep_structure['monitor'] = MonitorComponent(self.ports)

		return deep_structure


	def create_pipeline(self,source,server):
		source_id = source['source_id']
		source_type = source['source_type']
		pipeline = dict()
		pipeline['chains'] = []

		stream_manager = StreamManagerComponent(self.ports,source)
		server.server_pair_ports.append((source_id,self.ports['stream_manager_server_port']))
		




		for chain_id,det_params in enumerate(self.detectors):
			chain_id+=1

			if det_params['source_id'] != source_id:
				continue

			stream_manager.collector_ports.append(self.ports['collector_stream_manager_port'])
			server.collector_ports.append((det_params['name'],source_id,self.ports['collector_server_port']))

			

			chain = self.create_chain(det_params,chain_id,stream_manager, source_id)
			pipeline['chains'].append(chain)

		pipeline['stream_manager'] = stream_manager
		self.ports['stream_manager_server_port'] += 1

		return pipeline




	def create_chain(self,det_params,chain_id,stream_manager,source_id):
		chain = dict()
		det_name = det_params['name']
		detector = DetectorComponent(det_params,self.ports,source_id)
		collector = CollectorComponent(self.ports,det_name,source_id)
		detector.connected_to['collector'] = collector.component_name
		collector.connected_to['stream_manager'] = stream_manager.component_name
		detector.connected_to['stream_manager'] = stream_manager.component_name

		desc_chains = self.create_broker_descriptor_subcollector_subchain(det_name,detector,collector,source_id)

		chain['descriptors'] = desc_chains
		chain['detector'] = detector
		chain['collector'] = collector

		self.ports['detector_collector_port'] += chain_id
		self.ports['detector_broker_port'] += chain_id
		self.ports['collector_stream_manager_port'] += chain_id
		self.ports['collector_server_port'] += chain_id


		return chain



	def create_broker_descriptor_subcollector_subchain(self,det_name,detector,collector,source_id):
		
		desc_chains = []
		for i,desc_params in enumerate(self.descriptors):
			i+=1
			desc_chain = dict()
			desc_chain['descriptors'] = []


			if desc_params['related_to'] == det_name and desc_params['source_id'] == source_id:
				
				
				desc_name = desc_params['name']
				broker = BrokerComponent(desc_params,self.ports,desc_name,source_id)
				descriptor = DescriptorComponent(desc_params,self.ports,desc_name,source_id)
				subcollector = SubCollectorComponent(self.ports,desc_params,source_id)

				

				broker.connected_to['detector'] = detector.component_name
				subcollector.connected_to['collector'] =  collector.component_name
				descriptor.connected_to['broker'] = broker.component_name
				descriptor.connected_to['subcollector'] = subcollector.component_name
				collector.subcollector_collector_port.append((desc_name,self.ports['subcollector_collector_port']))


				desc_chain['broker'] = broker
				desc_chain['subcollector'] = subcollector
				desc_chain['descriptors'].append(descriptor)
				desc_chains.append(desc_chain)

				self.ports['broker_descriptor_port']+=i
				self.ports['descriptor_subcollector_port']+=i
				self.ports['subcollector_collector_port']+=i

		return desc_chains
			







class DetectorComponent:

	def __init__(self,det_params,ports,source_id):
		self.params = det_params
		self.collector_port = ports['detector_collector_port']
		self.broker_port = ports['detector_broker_port']
		self.stream_manager_port = ports['stream_manager_detector_port']
		self.monitor_in_port = ports['monitor_in_port']
		self.component_type = 'detector'
		self.component_name = det_params['name'] + '_' + self.component_type + '_' + source_id
		self.connected_to = {'monitor':'monitor'}


class DescriptorComponent:

	def __init__(self,desc_params,ports,prefix,source_id):
		self.params = desc_params
		self.broker_port = ports['broker_descriptor_port']
		self.subcollector_port = ports['descriptor_subcollector_port']
		self.monitor_in_port = ports['monitor_in_port']
		self.component_type = 'descriptor'
		self.component_name = prefix +'_'+ self.component_type + '_' + source_id
		self.connected_to = {'monitor':'monitor'}

class BrokerComponent:

	def __init__(self,desc_params,ports,prefix,source_id):
		self.params = desc_params
		self.detector_port = ports['detector_broker_port']
		self.descriptor_port = ports['broker_descriptor_port']
		self.component_type = 'broker'
		self.component_name = prefix +'_'+ self.component_type + '_' + source_id
		self.connected_to = {}

class SubCollectorComponent:

	def __init__(self,ports,desc_params,source_id):
		self.params = desc_params
		self.descriptor_port = ports['descriptor_subcollector_port']
		self.collector_port = ports['subcollector_collector_port']
		self.component_type = 'sub_collector'
		self.component_name = desc_params['name'] +'_'+ self.component_type + '_' + source_id
		self.connected_to = {}

class CollectorComponent:

	def __init__(self,ports,prefix,source_id):
		self.detector_port = ports['detector_collector_port']
		self.subcollector_collector_port = []
		self.stream_manager_port = ports['collector_stream_manager_port']
		self.server_port = ports['collector_server_port']
		self.monitor_in_port = ports['monitor_in_port']
		self.component_type = 'collector'
		self.component_name = prefix +'_'+ self.component_type + '_' + source_id
		self.connected_to = {'monitor':'monitor','server':'server'}


class StreamManagerComponent:

	def __init__(self,ports,source_params):
		self.params = source_params
		self.detector_port = ports['stream_manager_detector_port']
		self.collector_ports = []
		self.server_port = ports['server_port']
		self.server_pair_port = ports['stream_manager_server_port']
		self.component_type = 'stream_manager'
		self.component_name = self.component_type + '_' + source_params['source_id']
		self.connected_to = {'server':'server'}



class MonitorComponent:

	def __init__(self,ports):
		self.monitor_in_port = ports['monitor_in_port']
		self.monitor_out_port = ports['monitor_out_port']
		self.component_type = 'monitor'
		self.component_name = self.component_type
		self.connected_to = {}

class ServerComponent:

	def __init__(self,ports):
		self.server_port = ports['server_port']
		self.monitor_port = ports['monitor_out_port']
		self.server_pair_ports = []
		self.connected_to = {'monitor':'monitor'}
		self.collector_ports = []
		self.component_type = 'server'
		self.component_name = self.component_type











