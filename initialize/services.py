from pathlib import Path
import ruamel.yaml
from ruamel.yaml.scalarstring import SingleQuotedScalarString
S = ruamel.yaml.scalarstring.DoubleQuotedScalarString
yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True


from config import *

class DockerServicesManager:


	def __init__(self,deep_structure,registry_address,sources):
		self.deep_structure = deep_structure
		self.registry_address = registry_address
		self.sources = sources
		self.services = []
		self.dict_services = dict()
		self.extract_structure()


	
	def extract_structure(self):

		desc_params_list = []
		det_params_list = []

		pipelines = self.deep_structure['pipelines']
		for pipeline in pipelines:
			stream_manager_component = pipeline['stream_manager']
			self.manage_stream_manager_services(stream_manager_component)
			

			for chain in pipeline['chains']:

				detector = chain['detector'] 
				collector = chain['collector']
				descriptor_chains = chain['descriptors']
				det_params_list.append(detector.params)


				
				for desc_chain in descriptor_chains:
					broker = desc_chain['broker']
					subcollector = desc_chain['subcollector']
					descriptor_list = desc_chain['descriptors']


					for desc in descriptor_list:
						desc_params_list.append(desc.params)

					self.manage_broker_services(broker)
				
					self.manage_subcollector_services(subcollector)
								
					self.manage_descriptors_services(descriptor_list)


				self.manage_detector_services(detector)
				
				self.manage_collector_services(collector)
				
				
				

		self.create_base_services(desc_params_list,det_params_list)



	def manage_detector_services(self,detector_component):
		det_service = DetectorService(detector_component,self.registry_address)
		det_dict = det_service.create_detector_service()
		self.services.append(det_service)
		self.dict_services[det_service.service_name] = det_dict
		#print(det_dict)
		#det_service.write_service()

	
	def manage_collector_services(self,collector_component):
		coll_service = CollectorService(collector_component,self.registry_address)
		col_dict = coll_service.create_collector_service()
		self.services.append(coll_service)
		self.dict_services[coll_service.service_name] = col_dict
		#coll_service.write_service()
		#print(col_dict)
	
	def manage_broker_services(self,broker_component):
		broker_service = BrokerService(broker_component,self.registry_address)
		brok_dict = broker_service.create_broker_service()
		self.services.append(broker_service)
		self.dict_services[broker_service.service_name] = brok_dict
		#print(brok_dict)
		#broker_service.write_service()


	def manage_subcollector_services(self,subcollector_component):
		sub_collector_service = SubCollectorService(subcollector_component,self.registry_address)
		subcol_dict = sub_collector_service.create_sub_collector_service()
		self.services.append(sub_collector_service)
		self.dict_services[sub_collector_service.service_name] = subcol_dict
		#print(subcol_dict)
		#sub_collector_service.write_service()
	
	def manage_descriptors_services(self,descriptor_list_components):
		desc_name_list = []
		for desc_component in descriptor_list_components:
			descriptor_service = DescriptorService(desc_component,self.registry_address)
			descriptor_dict = descriptor_service.create_descriptor_service()
			self.services.append(descriptor_service)
			self.dict_services[descriptor_service.service_name] = descriptor_dict		
			#print(descriptor_dict)
			#descriptor_service.write_service()


	def manage_stream_manager_services(self,stream_manager_component):
		stream_man_service = StreamManagerService(stream_manager_component,self.registry_address)
		stream_man_dict = stream_man_service.create_stream_manager_service()
		self.services.append(stream_man_service)
		self.dict_services[stream_man_service.service_name] = stream_man_dict

	
	def create_base_services(self,desc_params_list,det_params_list):
		monitor = self.deep_structure['monitor']
		server = self.deep_structure['server']

		monitor_service = MonitorService(monitor,desc_params_list,self.registry_address)
		monitor_dict = monitor_service.create_monitor_service()
		self.services.append(monitor_service)
		self.dict_services[monitor_service.service_name] = monitor_dict


		server_service = ServerService(server,desc_params_list,det_params_list, self.sources,self.registry_address)
		server_dict = server_service.create_server_service()
		self.services.append(server_service)
		self.dict_services[server_service.service_name] = server_dict

		



	def get_services(self):
		return self.services


	def write_services(self):
		compose = dict()
		compose['services'] = self.dict_services
		compose['version'] = '3'
		compose['volumes'] = {'deep_media_volume':{'external':True}}
		compose['networks'] = {NETWORK: None}
		

		compose_file = Path(MAIN_COMPOSE_FILE)
		try:
			with compose_file.open('w') as ofp:
				yaml.indent(mapping=4)
				yaml.dump(compose, ofp)
		except Exception as e:
			raise e



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
	def __init__(self,detector_component,registry_address):
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
		self.image_name = self.set_image_name(registry_address,self.detector_name,self.image_tag)

	def __setup_deploy(self):

		node = self.params['deploy']['node_name']
		gpu_id = self.params['deploy']['gpu_id']
		return node,gpu_id

	def __set_environments(self,detector_component):
		environments = []
		framework = 'FRAMEWORK='+detector_component.params['framework']
		coll_env = 'COLLECTOR_ADDRESS='+detector_component.connected_to['collector']
		stream_man = 'VIDEOSRC_ADDRESS='+detector_component.connected_to['stream_manager']
		monitor = 'MONITOR_ADDRESS='+detector_component.connected_to['monitor']
		stream_in = 'STREAM_OUT='+str(detector_component.stream_manager_port)
		det_out_to_brok = 'FP_OUT='+str(detector_component.broker_port)
		det_out_to_col	= 'FP_OUT_TO_COL='+str(detector_component.collector_port)
		monitor_in = 'MONITOR_STATS_IN='+str(detector_component.monitor_in_port)
		environments = [framework,coll_env,stream_man,monitor,stream_in,det_out_to_brok,det_out_to_col,monitor_in]
		gpu_env = self.set_gpu_enviroment(self.gpu_id)
		environments.append(gpu_env)
		return environments

	def create_detector_service(self):
		detector = dict()
		detector['environment'] = self.environments
		detector['env_file'] = self.env_file
		detector['image'] = self.image_name
		detector['networks'] = [self.net]
		detector['deploy']= {'placement':{'constraints': ['node.hostname=='+self.deploy_node ]}}
		return detector






            
class CollectorService(DeepService):

	def __init__(self,collector_component,registry_address):
		super().__init__()
		self.service_name = collector_component.component_name
		
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(collector_component)
		self.image_name = self.set_image_name(registry_address,collector_component.component_type,self.image_tag)


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


	def create_collector_service(self):
		collector = dict()
		collector['environment'] = self.environments
		collector['env_file'] = self.env_file
		collector['image'] = self.image_name
		collector['networks'] = [self.net]
		return collector





            
class BrokerService(DeepService):

	def __init__(self,broker_component,registry_address):
		super().__init__()
		self.service_name = broker_component.component_name
		self.image_tag = self.set_component_tag()
		self.params = broker_component.params
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(broker_component)
		self.image_name = self.set_image_name(registry_address,broker_component.component_type,self.image_tag)
		self.node = self.params['deploy']['node_name']

	def __set_environments(self,broker_component):
		environments = []

		det_addr = 'FP_ADDRESS='+broker_component.connected_to['detector']
		broker_name = 'BROKER_NAME='+broker_component.component_name
		brok_out_port = 'BROKER_PORT='+str(broker_component.descriptor_port)
		brok_in_port = 'FP_OUT='+str(broker_component.detector_port)
		environments = [det_addr,broker_name,brok_out_port,brok_in_port]
		return environments


	def create_broker_service(self):
		broker = dict()
		broker['environment'] = self.environments
		broker['env_file'] = self.env_file
		broker['image'] = self.image_name
		broker['deploy']= {'placement':{'constraints': ['node.hostname=='+self.node ]}}
		broker['networks'] = [self.net]

		return broker



            
class SubCollectorService(DeepService):

	def __init__(self,sub_collector_component,registry_address):
		super().__init__()
		self.params = sub_collector_component.params
		self.service_name = sub_collector_component.component_name
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(sub_collector_component)
		self.image_name = self.set_image_name(registry_address,sub_collector_component.component_type,self.image_tag)
		self.node = self.params['deploy']['node_name']

	def __set_environments(self,sub_collector_component):
		environments = []
		sub_col_name = 'DESC_NAME='+sub_collector_component.component_name.split('_')[0]
		monitor_address = 'MONITOR_ADDRESS='+sub_collector_component.connected_to['monitor']
		monitor_stats_in = 'MONITOR_STATS_IN='+str(sub_collector_component.monitor_in_port)
		collector_address = 'COLLECTOR_ADDRESS='+sub_collector_component.connected_to['collector']
		sub_col_in_port = 'SUB_COL_PORT='+str(sub_collector_component.descriptor_port)
		sub_col_out_port = 'COL_PORT='+str(sub_collector_component.collector_port)
		sub_col_worker = 'WORKER='+str(self.params['worker'])
		environments = [sub_col_name,monitor_address,monitor_stats_in,collector_address,sub_col_in_port,sub_col_out_port,sub_col_worker]
		return environments


	def create_sub_collector_service(self):
		sub_col_dict = dict()
		sub_col_dict['environment'] = self.environments
		sub_col_dict['env_file'] = self.env_file
		sub_col_dict['image'] = self.image_name
		sub_col_dict['networks'] = [self.net]
		sub_col_dict['deploy']= {'placement':{'constraints': ['node.hostname=='+self.node ]}}

		return sub_col_dict




            
class DescriptorService(DeepService):

	def __init__(self,descriptor_component,registry_address):
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
		self.image_name = self.set_image_name(registry_address,self.descriptor_name,self.image_tag)

	def __setup_deploy(self):

		node = self.params['deploy']['node_name']
		gpu_id = self.params['deploy']['gpu_id']
		return node,gpu_id


	def __set_environments(self,descriptor_component):
		environments = []

		mode = 'MODE='+descriptor_component.params['mode'].upper()
		framework = 'FRAMEWORK='+descriptor_component.params['framework']
		broker_address = 'BROKER_ADDRESS='+descriptor_component.connected_to['broker']
		sub_collector_address = 'SUB_COLLECTOR_ADDRESS='+descriptor_component.connected_to['subcollector']
		monitor_address = 'MONITOR_ADDRESS='+descriptor_component.connected_to['monitor']
		monitor_stats_in = 'MONITOR_STATS_IN='+str(descriptor_component.monitor_in_port)
		gpu_env = self.set_gpu_enviroment(self.gpu_id)
		broker_port = 'BROKER_PORT='+str(descriptor_component.broker_port)
		sub_col_port = 'SUB_COL_PORT='+str(descriptor_component.subcollector_port)
		environments = [mode,framework,broker_address,sub_collector_address,monitor_address,monitor_stats_in,gpu_env,broker_port,sub_col_port]
		return environments


	def create_descriptor_service(self):
		desc_dict = dict()
		desc_dict['environment'] = self.environments
		desc_dict['env_file'] = self.env_file
		desc_dict['image'] = self.image_name
		desc_dict['networks'] = [self.net]
		desc_dict['deploy']= {'placement':{'constraints': ['node.hostname=='+self.node ]},'replicas': int(self.params['worker'])}
		return desc_dict


class StreamManagerService(DeepService):

	def __init__(self,stream_manager_component,registry_address):
		super().__init__()
		self.service_name = stream_manager_component.component_name
		self.source_params = stream_manager_component.params
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(stream_manager_component,self.source_params)
		self.image_name = self.set_image_name(registry_address,stream_manager_component.component_type,self.image_tag)
		self.volume = True if self.source_params['source_folder'] != 'None' else False

	def __set_environments(self,stream_manager_component,source):
		environments = []


		monitor_address = 'MONITOR_ADDRESS='+stream_manager_component.connected_to['monitor']
		monitor_stats_in = 'MONITOR_STATS_IN='+str(stream_manager_component.monitor_in_port)
		hp_server = 'HP_SERVER='+stream_manager_component.connected_to['server']
		collector_in_ports = 'COLLECTOR_PORTS='+','.join([str(col_port) for col_port in stream_manager_component.collector_ports])
		server_port = 'SERVER_PORT='+str(stream_manager_component.server_port)
		server_pair_port = 'SERVER_PAIR_PORT='+str(stream_manager_component.server_pair_port)
		vc_out = 'STREAM_OUT='+str(stream_manager_component.detector_port)
		source_type = 'SOURCE_TYPE='+str(source['source_type'])
		source_url = 'SOURCE_URL='+str(source['source_url'])
		source_path = 'SOURCE_PATH='+str(source['source_path'])
		source_id = 'SOURCE_ID='+str(source['source_id'])
		environments = [monitor_address,monitor_stats_in,hp_server,collector_in_ports,server_port,vc_out,source_type,source_url,source_path,source_id,server_pair_port]
		
		return environments


	def create_stream_manager_service(self):
		stream_man_dict = dict()
		stream_man_dict['environment'] = self.environments
		stream_man_dict['env_file'] = self.env_file
		stream_man_dict['image'] = self.image_name
		stream_man_dict['networks'] = [self.net]
		stream_man_dict['deploy']= {'placement':{'constraints': ['node.hostname=='+self.source_params['source_node'] ]}}
		stream_man_dict['depends_on'] = ['server']
		if self.volume:
			stream_man_dict['volumes'] = ['deep_media_volume:/mnt/remote_media']

		return stream_man_dict



class MonitorService(DeepService):

	def __init__(self,monitor_component,desc_params_list,registry_address):
		super().__init__()
		self.service_name = monitor_component.component_type
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(monitor_component,desc_params_list)
		self.image_name = self.set_image_name(registry_address,self.service_name,self.image_tag)

	def __set_environments(self,monitor_component,desc_params_list):
		environments = []

		algs = 'ALGS='+','.join([desc['name']for desc in desc_params_list])



		monitor_stats_in = 'MONITOR_STATS_IN='+str(monitor_component.monitor_in_port)
		monitor_stats_out = 'MONITOR_STATS_OUT='+str(monitor_component.monitor_out_port)
		environments = [algs,monitor_stats_in,monitor_stats_out] 
		return environments


	def create_monitor_service(self):
		monitor_dict = dict()
		monitor_dict['environment'] = self.environments
		monitor_dict['env_file'] = self.env_file
		monitor_dict['image'] = self.image_name
		monitor_dict['networks'] = [self.net]

		return monitor_dict


class ServerService(DeepService):

	def __init__(self,server_component,desc_params,det_params,sources,registry_address):
		super().__init__()
		self.service_name = server_component.component_type
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PARAMS]
		self.net = NETWORK
		self.environments = self.__set_environments(server_component,desc_params,det_params,sources)
		self.image_name = self.set_image_name(registry_address,self.service_name,self.image_tag)
		self.server_port =  str(server_component.server_port)

	def __set_environments(self,server_component,desc_params,det_params,sources):
		environments = []
		server_out_port = 'SERVER_PORT='+str(APP_PORT)

		

		algs = 'ALGS='+','.join( [desc['name']+':'+ desc['related_to']+':'+desc['source_id'] for desc in desc_params] )

		dets = 'DETS='+','.join( [det['name']+':'+det['source_id'] for det in det_params] )

		sources = 'SOURCES='+','.join( [source['source_id']+':'+ source['source_type'] for source in sources])


		col_ports = 'COLLECTOR_PORTS='+','.join([det_name+':'+source_id+':'+str(port) for det_name,source_id,port in server_component.collector_ports])
		stream_man_pair_ports = 'STREAM_MANAGER_PAIR_PORTS='+','.join([source_id+':'+str(port) for source_id,port in server_component.server_pair_ports])
		monitor_out_port = 'MONITOR_STATS_OUT='+str(server_component.monitor_port)
		monitor_address = 'MONITOR_ADDRESS='+server_component.connected_to['monitor']
		environments = [col_ports,monitor_out_port,monitor_address,server_out_port,algs,stream_man_pair_ports,sources,dets]

		return environments


	def create_server_service(self):
		server_dict = dict()
		server_dict['environment'] = self.environments
		server_dict['env_file'] = self.env_file
		server_dict['image'] = self.image_name
		server_dict['networks'] = [self.net]
		server_dict['ports'] = [self.server_port+':'+self.server_port]


		return server_dict
















