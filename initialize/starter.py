
import subprocess

from configparser import ConfigParser
from config import *
import time
import re






class Starter:

	def __init__(self,machine,registry,cluster_manager, use_last_settings=False):
		self.cluster_manager = cluster_manager
		self.machine = machine
		self.registry = registry
		self.use_last_settings = use_last_settings

		self.__setup()

	def __setup(self):
		self.manage_registry()
		nodes_config = self.cluster_manager.manage_cluster(use_last_config=self.use_last_settings)
		self.nodes = self.__load_nodes_data(nodes_config)
		self.top_manager_node = self.__get_top_manager()



	def create_source_volume(self,sources):
		if len(sources) == 0:
			return

		path_list = [ s['source_folder'] for s in sources if s['source_folder'] != 'None']
		if len(path_list) == 0:
			return
		else:
			path = path_list[0]

		top_manager_node = self.top_manager_node
		#inspect_command = 'docker service ps --format "{{.CurrentState}}" '
		
		try:
			print('Creating deep_media_volume...')
			create_volume_command = "docker volume create --name deep_media_volume --opt type=none --opt o=bind --opt device="
			rm_volume_command = "docker volume rm deep_media_volume"
			if top_manager_node['type'] == 'RemoteNode':
				create_volume_command = "ssh %s@%s '%s'" % (top_manager_node['user'], top_manager_node['ip'], create_volume_command)
				rm_volume_command = "ssh %s@%s '%s'" % (top_manager_node['user'], top_manager_node['ip'], rm_volume_command)
				print(rm_volume_command)
			self.machine.exec_shell_command(rm_volume_command)
			com = create_volume_command+path
			self.machine.exec_shell_command(com)
		except Exception as e:
			print(e)

	

	def manage_registry(self):
		
		running = self.registry.check_registry_running()

		if not running:
			self.registry.start_registry()
		self.registry.manage_docker_daemon_json()



	def __get_top_manager(self):
		nodes_list = list(self.nodes.keys())
		top_manager_node = [self.nodes[node] for node in nodes_list if self.nodes[node]['role'] == 'manager'][0]
		return top_manager_node

	def get_nodes(self):
		return self.nodes


	


	def __load_nodes_data(self,nodes_config):

		cluster_dict = dict()
		for section in nodes_config.sections():
			node_dict = dict()
			for key, val in nodes_config.items(section):
				node_dict[key] = val

			cluster_dict[section] = node_dict
		return cluster_dict


	def check_framework_started(self):
		top_manager_node = self.top_manager_node
		command = "docker stack services --quiet deepframework"
		inspect_command = 'docker service ps --format "{{.CurrentState}}" '
		if top_manager_node['type'] == 'RemoteNode':
			command = "ssh %s@%s '%s'" % (top_manager_node['user'], top_manager_node['ip'], command)
			inspect_command = "ssh %s@%s '%s'" % (top_manager_node['user'], top_manager_node['ip'], inspect_command)

		services = self.machine.exec_shell_command(command).split('\n')

		ready = []
		ready_counter = 0
		num_services = len(services)
		time_thr = 400
		start_time = time.time()
		result = 'OK'
		while num_services != ready_counter:
			ready = []
			for service in services:
				time.sleep(1)
				service_inspect_command = inspect_command + service
				res_insp = self.machine.exec_shell_command(service_inspect_command)
				status = res_insp.split(' ')[0]
				if status == 'Running':
					ready.append(service)
					ready_counter+=1

			for r in ready:
				services.remove(r)

			elapsed_time = time.time() - start_time
			if elapsed_time >= time_thr:
				result = 'ERROR'

				break
			time.sleep(3)

		return result



	def __pull_images(self):
		for node_name,node_values in self.nodes.items():
			user = node_values['user']
			ip = node_values['ip']
			path = node_values['path']
			node_type = node_values['type']
			if node_type == 'RemoteNode':
				print(node_name,' is pulling docker images...')

				try:
					copy_pull_com = "scp -q -p docker_pull.sh %s@%s:%s" %(user,ip,path)
					self.machine.exec_shell_command(copy_pull_com)

					sub_command = "'cd %s && ./docker_pull.sh %s'" % (path, self.registry.insecure_addr)
					command = "ssh -t %s@%s %s" % (user, ip, sub_command)
					output = self.machine.exec_shell_command(command)
				except Exception as e:
					raise e


	def find_server(self):
		top_manager_node = self.top_manager_node
		#inspect_command = 'docker service ps --format "{{.CurrentState}}" '
		inspect_command = 'docker service ps --format "{{.Node}}" deepframework_server'
		if top_manager_node['type'] == 'RemoteNode':
			inspect_command = "ssh %s@%s '%s'" % (top_manager_node['user'], top_manager_node['ip'], inspect_command)

		node_name = self.machine.exec_shell_command(inspect_command).split('\n')[0]
		config_app = ConfigParser()

		config_app.read(CLUSTER_CONFIG_FILE)
		node_ip = config_app[node_name]['ip']
		
		return node_ip



	def start_framework(self):
		self.__pull_images()

		start_command = "docker stack deploy -c "+ MAIN_COMPOSE_FILE + " deepframework"
		top_manager_node = self.top_manager_node
		


		if top_manager_node['type'] == 'RemoteNode':
			start_command = "ssh %s@%s 'cd %s && %s'" % (top_manager_node['user'], top_manager_node['ip'], top_manager_node['path'], start_command)
			copy_command = 'scp -q -p -r env_params.list ' + MAIN_COMPOSE_FILE+ ' ' +top_manager_node['user']+'@'+top_manager_node['ip']+':'+top_manager_node['path']
			try:
				result = subprocess.Popen([copy_command], shell=True)
			except Exception as e:

				raise e

		try:
			print('Loading...')
			time.sleep(5)
			result = subprocess.Popen([start_command], shell=True)
			result.communicate()
			print('Waiting for services creation...')
			if result.returncode != 0:
				print('Error')
			else:
				res_status = self.check_framework_started()
				if res_status == 'OK':
					server_address = self.find_server()
					app_address = 'https://'+server_address+':'+str(APP_PORT)
					print('### DEEP FRAMEWORK STARTED ###')
					print('Check your stream at: ', app_address)
				else:
					print(res_status)
					command = 'python3 rm_services.py'
					self.machine.exec_shell_command(command)


		except Exception as e:

			raise e

