from config import *

class PipelineManager:

	def __init__(self,matches):
		self.__set_connection_ports()
		self.detectors = matches['detectors']
		self.descriptors = matches['descriptors']
		self.__set_connection_ports()
		

	def __set_connection_ports(self):
		self.ports = dict()

		self.ports['detector_collector_port'] = 4001
		self.ports['detector_broker_port'] = 5001
		self.ports['stream_manager_detector_port'] = 3500
		self.ports['broker_descriptor_port'] = 6000
		self.ports['descriptor_subcollector_port'] = 6050
		self.ports['subcollector_collector_port'] = 7000
		self.ports['collector_stream_manager_port'] = 7050
		self.ports['collector_server_port'] = 4050
		self.ports['stream_manager_server_port'] = APP_PORT
		self.ports['stream_capture_server_port'] = APP_PORT
		self.ports['monitor_in_port'] = 5550
		self.ports['monitor_out_port'] = 5551



	def create_pipeline(self):
		pipeline = dict()
		pipeline['chains'] = []
		stream_manager = StreamManagerComponent(self.ports)
		server = ServerComponent(self.ports)

		for chain_id,det_params in enumerate(self.detectors):
			chain_id+=1

			stream_manager.collector_ports.append(self.ports['collector_stream_manager_port'])
			server.collector_ports.append(self.ports['collector_server_port'])

			

			chain = self.create_chain(det_params,chain_id)
			pipeline['chains'].append(chain)

			
		pipeline['server'] = server
		pipeline['stream_manager'] = stream_manager
		pipeline['stream_capture'] = StreamCaptureComponent(self.ports)
		pipeline['monitor'] = MonitorComponent(self.ports)

		return pipeline




	def create_chain(self,det_params,chain_id):
		chain = dict()
		det_name = det_params['name']
		detector = DetectorComponent(det_params,self.ports,det_name)
		collector = CollectorComponent(self.ports,det_name)
		detector.connected_to['collector'] = collector.component_name

		desc_chains = self.create_broker_descriptor_subcollector_subchain(det_name,detector,collector)

		chain['descriptors'] = desc_chains
		chain['detector'] = detector
		chain['collector'] = collector

		self.ports['detector_collector_port'] += chain_id
		self.ports['detector_broker_port'] += chain_id
		self.ports['collector_stream_manager_port'] += chain_id
		self.ports['collector_server_port'] += chain_id


		return chain



	def create_broker_descriptor_subcollector_subchain(self,det_name,detector,collector):
		
		desc_chains = []
		for i,desc_params in enumerate(self.descriptors):
			desc_chain = dict()
			desc_chain['descriptors'] = []


			if desc_params['related_to'] == det_name:
				

				desc_name = desc_params['name']
				broker = BrokerComponent(self.ports,desc_name)
				descriptor = DescriptorComponent(desc_params,self.ports,desc_name)
				subcollector = SubCollectorComponent(self.ports,desc_name)

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

	def __init__(self,det_params,ports,prefix):
		self.params = det_params
		self.collector_port = ports['detector_collector_port']
		self.broker_port = ports['detector_broker_port']
		self.stream_manager_port = ports['stream_manager_detector_port']
		self.monitor_in_port = ports['monitor_in_port']
		self.component_type = 'detector'
		self.component_name = prefix +'_'+ self.component_type
		self.connected_to = {'stream_manager':'stream_manager','monitor':'monitor'}


class DescriptorComponent:

	def __init__(self,desc_params,ports,prefix):
		self.params = desc_params
		self.broker_port = ports['broker_descriptor_port']
		self.subcollector_port = ports['descriptor_subcollector_port']
		self.monitor_in_port = ports['monitor_in_port']
		self.component_type = 'descriptor'
		self.component_name = prefix +'_'+ self.component_type
		self.connected_to = {'monitor':'monitor'}

class BrokerComponent:

	def __init__(self,ports,prefix):
		self.detector_port = ports['detector_broker_port']
		self.descriptor_port = ports['broker_descriptor_port']
		self.component_type = 'broker'
		self.component_name = prefix +'_'+ self.component_type
		self.connected_to = {}

class SubCollectorComponent:

	def __init__(self,ports,prefix):
		self.descriptor_port = ports['descriptor_subcollector_port']
		self.collector_port = ports['subcollector_collector_port']
		self.component_type = 'sub_collector'
		self.component_name = prefix +'_'+ self.component_type
		self.connected_to = {}

class CollectorComponent:

	def __init__(self,ports,prefix):
		self.detector_port = ports['detector_collector_port']
		self.subcollector_collector_port = []



		self.stream_manager_port = ports['collector_stream_manager_port']




		self.server_port = ports['collector_server_port']
		self.monitor_in_port = ports['monitor_in_port']
		self.component_type = 'collector'
		self.component_name = prefix +'_'+ self.component_type
		self.connected_to = {'stream_manager':'stream_manager','monitor':'monitor','server':'server'}


class StreamManagerComponent:

	def __init__(self,ports):
		self.detector_port = ports['stream_manager_detector_port']
		self.collector_ports = []
		self.server_port = ports['stream_manager_server_port']
		self.component_type = 'stream_manager'
		self.component_name = 'stream_manager'
		self.connected_to = {'server':'server'}

class StreamCaptureComponent:

	def __init__(self,ports):
		self.server_port = ports['stream_capture_server_port']
		self.component_type = 'stream_capture'
		self.component_name = 'stream_capture'
		self.connected_to = {'server':'server'}

class MonitorComponent:

	def __init__(self,ports):
		self.monitor_in_port = ports['monitor_in_port']
		self.monitor_out_port = ports['monitor_out_port']
		self.component_name = 'monitor'
		self.component_type = 'monitor'
		self.connected_to = {}

class ServerComponent:

	def __init__(self,ports):
		self.stream_manager_port = ports['stream_manager_server_port']
		self.stream_capture_port = ports['stream_capture_server_port']
		self.monitor_port = ports['monitor_out_port']
		self.connected_to = {'monitor':'monitor'}
		self.collector_ports = []
		self.component_name = 'server'
		self.component_type = 'server'











