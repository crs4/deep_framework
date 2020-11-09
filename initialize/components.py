
from config import ENV_PORTS,ENV_PARAMS,NETWORK,MAIN_COMPOSE_FILE


service_connenction_map = dict()








service_connenction_map['detector'] = {'COLLECTOR_ADDRESS': 'collector', 'VIDEOSRC_ADDRESS': 'stream_manager'}
service_connenction_map['collector'] = {'SERVER_ADDRESS':'server', 'STREAM_MANAGER_ADDRESS':'stream_manager'}






service_ports_map = dict()
service_ports_map['collector'] = {'PROV_OUT_TO_COL':'5555', 'OUT_STREAM_PORT':'9999', 'OUT_SERVER_PORT':'9990'}



class DeepComponent:

	def set_service_name(self,comp_name,name_type=None):
		return comp_name+'_'+name_type if name_type is not None else comp_name

	def set_component_tag(self,gpu_id=None, base_component = True):
		tag = 'deep'
		if base_component:
			return tag

		if gpu_id is not None:
			return tag + '_gpu'
		else:
			return tag + '_cpu'

	def set_connection_environments(self,service_map):
		connection_environments = []
		for addr, service_name in service_map.items():
			connection = addr+'='+service_name
			connection_environments.append(connection)
		return connection_environments

	def set_gpu_enviroment(self,gpu_id):
		return 'GPU_ID='+str(gpu_id)

	def set_image_name(self,addr,name,tag):
		return addr+'/'+name+':'+tag




{
'name': 'drone', 
'mode': 'gpu', 
'framework': 'tensorflow', 
'dockerfile': 'detector/object_extractors/drone_object_detector/Dockerfile.gpu', 
'to_build': 'n', 
'deploy': {'node_name': 'linuxkit-025000000001', 'gpu_id': None}
}


class Detector(DeepComponent):



	def __init__(self, det_dict,reg_addr):
		super().__init__()
		self.registry_address = reg_addr
		self.detector_name,self.node,self.gpu_id = self.__setup_deploy(matches)
		self.service_name = self.service_name(self.detector_name,'detector')
		self.image_tag = self.set_component_tag(self.gpu_id, base_component = False)
		self.env_file = [ENV_PORTS,ENV_PARAMS]
		self.net = NETWORK
		self.ports_map = ['5559:5559', '5556:5556', '5555:5555']
		self.deploy_node = self.node

	def __setup_deploy(self,matches):
		detector_name = det_dict[name]
		node = det_dict['deploy']['node_name']
		gpu_id = det_dict['deploy']['gpu_id']
		return detector_name,node,gpu_id

	def __set_connection_environments(self):
		connection_environments = []
		collector_env = 'COLLECTOR_ADDRESS='

	
	def create_detector_service(self):
		detector = dict()
		environments = self.set_connection_environments(service_connenction_map[self.service_name])
		gpu_env = self.set_gpu_enviroment(self.gpu_id)
		environments.append(gpu_env)
		detector['environment'] = environments
		detector['env_file'] = self.env_file
		detector['image'] = self.set_image_name(self.registry_address,self.detector_name,self.image_tag)
		detector['networks'] = [self.net]
		detector['ports'] = self.ports_map
		detector['deploy']= {'placement':{'constraints': ['node.hostname=='+self.deploy_node ]}}
		return detector


        
            
class Collector(DeepComponent):

	def __init__(self,reg_addr):
		super().__init__()
		self.registry_address = reg_addr
		self.service_name = 'collector'
		self.image_tag = self.set_component_tag()
		self.env_file = [ENV_PORTS,ENV_PARAMS]
		self.net = NETWORK


	def create_collector_service(self,detector_name):
		collector = dict()
		monitor_environment = ['STAT='+detector_name]
		connection_environments = self.set_connection_environments(service_connenction_map[self.service_name])
		ports_environments = self.set_connection_environments(service_ports_map[self.service_name])
		collector['environment'] = connection_environments + ports_environments + monitor_environment
		collector['env_file'] = self.env_file
		collector['image'] = self.set_image_name(self.registry_address,self.service_name,self.image_tag)
		collector['networks'] = [self.net]
		return collector



