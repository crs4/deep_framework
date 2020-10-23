
from config import *
class DockerServicesManager:


	def __init__(self,pipeline,registry_address,sources):
		self.pipeline = pipeline
		
		self.registry_address = registry_address
		self.sources = sources


	
	def extract_pipeline(self):

		desc_name_list = []


		for chain in self.pipeline['chains']:

			detector = chain['detector'] 
			collector = chain['collector']
			broker = chain['broker']
			subcollector = chain['subcollector']
			descriptor_list = chain['descriptors']
			for desc in descriptor_list:
				desc_name = desc.params['name'] 
				desc_name_list.append(desc_name)


			self.manage_detector_services(detector)
			
			self.manage_collector_services(collector)
			
			self.manage_broker_services(broker)
			
			self.manage_subcollector_services(subcollector)
						
			self.manage_descriptors_services(descriptor_list)
			

		self.create_base_services(desc_name_list)


	def manage_detector_services(self,detector_component):
		det_service = DetectorService(detector_component)
		det_dict = det_service.create_detector_service(self.registry_address)
		#print(det_dict)
		#det_service.write_service()

	
	def manage_collector_services(self,collector_component):
		coll_service = CollectorService(collector_component)
		col_dict = coll_service.create_collector_service(self.registry_address)
		#coll_service.write_service()
		#print(col_dict)
	
	def manage_broker_services(self,broker_component):
		broker_service = BrokerService(broker_component)
		brok_dict = broker_service.create_broker_service(self.registry_address)
		#print(brok_dict)
		#broker_service.write_service()


	def manage_subcollector_services(self,subcollector_component):
		sub_collector_service = SubCollectorService(subcollector_component)
		subcol_dict = sub_collector_service.create_sub_collector_service(self.registry_address)
		#print(subcol_dict)
		#sub_collector_service.write_service()
	
	def manage_descriptors_services(self,descriptor_list_components):
		desc_name_list = []
		for desc_component in descriptor_list_components:
			descriptor_service = DescriptorService(desc_component)
			descriptor_dict = descriptor_service.create_descriptor_service(self.registry_address)
			#print(descriptor_dict)
			#descriptor_service.write_service()





	def create_base_services(self,desc_name_list):
		stream_manager = self.pipeline['stream_manager']
		stream_capture = self.pipeline['stream_capture']
		monitor = self.pipeline['monitor']
		server= self.pipeline['server']

		stream_man_service = StreamManagerService(stream_manager)
		stream_man_dict = stream_man_service.create_stream_manager_service(self.registry_address)


		for source in self.sources:
			stream_cap_service = StreamCaptureService(stream_capture,source)
			stream_cap_dict = stream_cap_service.create_stream_capture_service(self.registry_address)
			#print(stream_cap_dict)

		monitor_service = MonitorService(monitor,desc_name_list)
		monitor_dict = monitor_service.create_monitor_service(self.registry_address)

		server_service = ServerService(server,desc_name_list)
		server_dict = server_service.create_server_service(self.registry_address)
		print(server_dict)


class DeepService:

	def set_component_tag(self,gpu_id=None, base_component = True):
		tag = 'deep'
		if base_component:
			return tag

		if gpu_id is not None:
			return tag + '_gpu'
		else:
			return tag + '_cpu'

	

	def set_gpu_enviroment(self,gpu_id):
		return 'GPU_ID='+str(gpu_id)

	def set_image_name(self,addr,name,tag):
		return addr+'/'+name+':'+tag





class DetectorService(DeepService):
	def __init__(self,detector_component):
		super().__init__()
		self.params = detector_component.params
		self.detector_name = self.params['name']
		self.node,self.gpu_id = self.__setup_deploy()
		self.service_name = detector_component.component_name
		self.image_tag = self.set_component_tag(self.gpu_id, base_component = False)
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.deploy_node = self.node
		self.environments = self.__set_environments(detector_component)

	def __setup_deploy(self):

		node = self.params['deploy']['node_name']
		gpu_id = self.params['deploy']['gpu_id']
		return node,gpu_id

	def __set_environments(self,detector_component):
		environments = []
		coll_env = 'COLLECTOR_ADDRESS='+detector_component.connected_to['collector']
		stream_man = 'VIDEOSRC_ADDRESS='+detector_component.connected_to['stream_manager']
		monitor = 'MONITOR_ADDRESS='+detector_component.connected_to['monitor']
		stream_in = 'STREAM_OUT='+str(detector_component.stream_manager_port)
		det_out_to_brok = 'FP_OUT='+str(detector_component.broker_port)
		det_out_to_col	= 'FP_OUT_TO_COL='+str(detector_component.collector_port)
		monitor_in = 'MONITOR_STATS_IN='+str(detector_component.monitor_in_port)
		environments = [coll_env,stream_man,monitor,stream_in,det_out_to_brok,det_out_to_col,monitor_in]
		gpu_env = self.set_gpu_enviroment(self.gpu_id)
		environments.append(gpu_env)
		return environments

	def create_detector_service(self,registry_address):
		detector = dict()
		detector['environment'] = self.environments
		detector['env_file'] = self.env_file
		detector['image'] = self.set_image_name(registry_address,self.detector_name,self.image_tag)
		detector['networks'] = [self.net]
		#detector['ports'] = self.ports_map
		detector['deploy']= {'placement':{'constraints': ['node.hostname=='+self.deploy_node ]}}
		return detector






            
class CollectorService(DeepService):

	def __init__(self,collector_component):
		super().__init__()
		self.service_name = collector_component.component_name
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(collector_component)

	def __set_environments(self,collector_component):
		environments = []

		det_coll_port = 'PROV_OUT_TO_COL='+str(collector_component.detector_port)
		col_stream_man_port = 'OUT_STREAM_PORT='+str(collector_component.stream_manager_port)
		col_server_port = 'OUT_SERVER_PORT='+str(collector_component.server_port)
		monitor_in = 'MONITOR_STATS_IN='+str(collector_component.monitor_in_port)
		stream_manager_address = 'STREAM_MANAGER_ADDRESS='+collector_component.connected_to['stream_manager']
		server_address = 'SERVER_ADDRESS='+collector_component.connected_to['server']
		monitor_address = 'MONITOR_ADDRESS='+collector_component.connected_to['monitor']
		name = 'COMPONENT_NAME='+collector_component.component_name
		algs = 'ALGS='+','.join([desc_name+':'+str(port) for desc_name, port in collector_component.subcollector_collector_port])
		environments = [det_coll_port,col_stream_man_port,col_server_port,monitor_in,stream_manager_address,server_address,monitor_address,name,algs]
		
		return environments


	def create_collector_service(self,registry_address):
		collector = dict()
		collector['environment'] = self.environments
		collector['env_file'] = self.env_file
		collector['image'] = self.set_image_name(registry_address,self.service_name,self.image_tag)
		collector['networks'] = [self.net]
		return collector





            
class BrokerService(DeepService):

	def __init__(self,broker_component):
		super().__init__()
		self.service_name = broker_component.component_name
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(broker_component)

	def __set_environments(self,broker_component):
		environments = []

		det_addr = 'FP_ADDRESS='+broker_component.connected_to['detector']
		broker_name = 'BROKER_NAME='+broker_component.component_name
		brok_out_port = 'BROKER_PORT='+str(broker_component.descriptor_port)
		brok_in_port = 'FP_OUT='+str(broker_component.detector_port)
		environments = [det_addr,broker_name,brok_out_port,brok_in_port]
		return environments


	def create_broker_service(self,registry_address):
		broker = dict()
		broker['environment'] = self.environments
		broker['env_file'] = self.env_file
		broker['image'] = self.set_image_name(registry_address,self.service_name,self.image_tag)
		broker['networks'] = [self.net]
		return broker



            
class SubCollectorService(DeepService):

	def __init__(self,sub_collector_component):
		super().__init__()
		self.service_name = sub_collector_component.component_name
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(sub_collector_component)

	def __set_environments(self,sub_collector_component):
		environments = []
		collector_address = 'COLLECTOR_ADDRESS='+sub_collector_component.connected_to['collector']
		sub_col_in_port = 'SUB_COL_PORT='+str(sub_collector_component.descriptor_port)
		sub_col_out_port = 'COL_PORT='+str(sub_collector_component.collector_port)
		environments = [collector_address,sub_col_in_port,sub_col_out_port]
		return environments


	def create_sub_collector_service(self,registry_address):
		sub_col_dict = dict()
		sub_col_dict['environment'] = self.environments
		sub_col_dict['env_file'] = self.env_file
		sub_col_dict['image'] = self.set_image_name(registry_address,self.service_name,self.image_tag)
		sub_col_dict['networks'] = [self.net]
		return sub_col_dict




            
class DescriptorService(DeepService):

	def __init__(self,descriptor_component):
		super().__init__()
		self.params = descriptor_component.params
		self.descriptor_name = self.params['name']
		self.node,self.gpu_id = self.__setup_deploy()
		self.service_name = descriptor_component.component_name
		self.image_tag = self.set_component_tag(self.gpu_id, base_component = False)
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.deploy_node = self.node
		self.environments = self.__set_environments(descriptor_component)

	def __setup_deploy(self):

		node = self.params['deploy']['node_name']
		gpu_id = self.params['deploy']['gpu_id']
		return node,gpu_id


	def __set_environments(self,descriptor_component):
		environments = []

		mode = 'MODE='+descriptor_component.params['mode']
		framework = 'FRAMEWORK='+descriptor_component.params['framework']
		broker_address = 'BROKER_ADDRESS='+descriptor_component.connected_to['broker']
		sub_collector_address = 'SUB_COLLECTOR_ADDRESS='+descriptor_component.connected_to['subcollector']
		monitor_address = 'MONITOR_ADDRESS='+descriptor_component.connected_to['monitor']
		monitor_stats_in = 'MONITOR_STATS_IN='+str(descriptor_component.monitor_in_port)
		gpu_env = self.set_gpu_enviroment(self.gpu_id)
		broker_port = 'BROKER_PORT='+str(descriptor_component.broker_port)
		sub_col_port = 'SUB_COL_PORT='+str(descriptor_component.subcollector_port)
		environments = [framework,broker_address,sub_collector_address,monitor_address,monitor_stats_in,gpu_env,broker_port,sub_col_port]
		return environments


	def create_descriptor_service(self,registry_address):
		sub_col_dict = dict()
		sub_col_dict['environment'] = self.environments
		sub_col_dict['env_file'] = self.env_file
		sub_col_dict['image'] = self.set_image_name(registry_address,self.service_name,self.image_tag)
		sub_col_dict['networks'] = [self.net]
		return sub_col_dict


class StreamManagerService(DeepService):

	def __init__(self,stream_manager_component):
		super().__init__()
		self.service_name = stream_manager_component.component_name
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(stream_manager_component)

	def __set_environments(self,stream_manager_component):
		environments = []

		hp_server = 'HP_SERVER='+stream_manager_component.connected_to['server']
		collector_in_ports = 'COLLECTOR_PORTS='+','.join([str(col_port) for col_port in stream_manager_component.collector_ports])
		server_port = 'SERVER_PORT='+str(stream_manager_component.server_port)
		vc_out = 'STREAM_OUT='+str(stream_manager_component.detector_port)
		environments = [hp_server,collector_in_ports,server_port,vc_out]
		
		return environments


	def create_stream_manager_service(self,registry_address):
		stream_man_dict = dict()
		stream_man_dict['environment'] = self.environments
		stream_man_dict['env_file'] = self.env_file
		stream_man_dict['image'] = self.set_image_name(registry_address,self.service_name,self.image_tag)
		stream_man_dict['networks'] = [self.net]
		stream_man_dict['depends_on'] = ['server']

		return stream_man_dict


class StreamCaptureService(DeepService):

	def __init__(self,stream_capture_component,source):
		super().__init__()
		self.service_name = stream_capture_component.component_name
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(stream_capture_component,source)

	def __set_environments(self,stream_capture_component,source):
		environments = []

		hp_server = 'HP_SERVER='+stream_capture_component.connected_to['server']
		server_port = 'SERVER_PORT='+str(stream_capture_component.server_port)
		stream_capture_id = 'STREAM_CAPTURE_ID='+source['source_id']
		environments = [hp_server,server_port,stream_capture_id]
		
		return environments


	def create_stream_capture_service(self,registry_address):
		stream_man_dict = dict()
		stream_man_dict['environment'] = self.environments
		stream_man_dict['env_file'] = self.env_file
		stream_man_dict['image'] = self.set_image_name(registry_address,self.service_name,self.image_tag)
		stream_man_dict['networks'] = [self.net]
		stream_man_dict['depends_on'] = ['server']

		return stream_man_dict


class MonitorService(DeepService):

	def __init__(self,monitor_component,desc_name_list):
		super().__init__()
		self.service_name = monitor_component.component_name
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(monitor_component,desc_name_list)

	def __set_environments(self,monitor_component,desc_name_list):
		environments = []

		algs = 'ALGS='+','.join(desc_name_list)
		monitor_stats_in = 'MONITOR_STATS_IN='+str(monitor_component.monitor_in_port)
		monitor_stats_out = 'MONITOR_STATS_OUT='+str(monitor_component.monitor_out_port)
		environments = [algs,monitor_stats_in,monitor_stats_out] 
		return environments


	def create_monitor_service(self,registry_address):
		monitor_dict = dict()
		monitor_dict['environment'] = self.environments
		monitor_dict['env_file'] = self.env_file
		monitor_dict['image'] = self.set_image_name(registry_address,self.service_name,self.image_tag)
		monitor_dict['networks'] = [self.net]

		return monitor_dict


class ServerService(DeepService):

	def __init__(self,server_component,desc_name_list):
		super().__init__()
		self.service_name = server_component.component_name
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(server_component,desc_name_list)

	def __set_environments(self,server_component,desc_name_list):
		environments = []
		server_out_port = 'SERVER_PORT='+str(APP_PORT)
		algs = 'ALGS='+','.join(desc_name_list)
		col_ports = 'COLLECTOR_PORTS='+','.join([str(port) for port in server_component.collector_ports])
		monitor_out_port = 'MONITOR_STATS_OUT='+str(server_component.monitor_port)
		monitor_address = 'MONITOR_ADDRESS='+server_component.connected_to['monitor']
		environments = [col_ports,monitor_out_port,monitor_address,server_out_port,algs]

		return environments


	def create_server_service(self,registry_address):
		server_dict = dict()
		server_dict['environment'] = self.environments
		server_dict['env_file'] = self.env_file
		server_dict['image'] = self.set_image_name(registry_address,self.service_name,self.image_tag)
		server_dict['networks'] = [self.net]

		return server_dict
















