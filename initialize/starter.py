
import subprocess

from configparser import ConfigParser
from initialize.configurator import Interviewer
from config import *
import time
import re

q = Interviewer()





class Starter:

	def __init__(self,machine,registry,cluster_manager, use_last_settings=False):
		self.cluster_manager = cluster_manager
		self.machine = machine
		self.registry = registry
		self.use_last_settings = use_last_settings
		self.image_manager = ImageManager(machine,registry)
		self.__setup()

	def __setup(self):
		self.manage_registry()
		nodes_config = self.cluster_manager.manage_cluster(use_last_config=self.use_last_settings)
		self.nodes = self.__load_nodes_data(nodes_config)
		self.top_manager_node = self.__get_top_manager()



	def build_and_push(self):
		print('The building process will take several time...')
		self.image_manager.build_images()
		self.image_manager.create_pull_file()

		self.image_manager.push_images()



	def manage_registry(self):
		
		running = self.registry.check_registry_running()
		 
		if not running:
			self.registry.start_registry()
		self.registry.manage_docker_daemon_json()
		
		if not self.use_last_settings:	 
			building = q.get_acceptable_answer("Do you want to build docker images?: (y/n): ", ['y', 'n'])
			if building == 'y':
				self.build_and_push()


	def __get_top_manager(self):
		nodes_list = list(self.nodes.keys())
		top_manager_node = [self.nodes[node] for node in nodes_list if self.nodes[node]['role'] == 'manager'][0]
		return top_manager_node

	def get_nodes(self):
		return self.nodes

	def get_execution_algs(self):
		reader_alg_config = ConfigParser()
		reader_alg_config.read(ALGS_CONFIG_FILE)
		execution_algs = {s:dict(reader_alg_config.items(s)) for s in reader_alg_config.sections()}
		return execution_algs



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






	def find_stream_manager(self):
		top_manager_node = self.top_manager_node
		#inspect_command = 'docker service ps --format "{{.CurrentState}}" '
		inspect_command = 'docker service ps --format "{{.Node}}" deepframework_stream_manager'
		if top_manager_node['type'] == 'RemoteNode':
			inspect_command = "ssh %s@%s '%s'" % (top_manager_node['user'], top_manager_node['ip'], inspect_command)

		node_name = self.machine.exec_shell_command(inspect_command).split('\n')[0]
		config_app = ConfigParser()

		config_app.read(CLUSTER_CONFIG_FILE)
		node_ip = config_app[node_name]['ip']
		app_address = 'https://'+node_ip+':8000'
		return app_address



	def start_framework(self, compose_command_string):

		start_command = "docker stack deploy -c "+ MAIN_COMPOSE_FILE + compose_command_string + " deepframework"
		top_manager_node = self.top_manager_node
		


		if top_manager_node['type'] == 'RemoteNode':
			start_command = "ssh %s@%s 'cd %s && %s'" % (top_manager_node['user'], top_manager_node['ip'], top_manager_node['path'], start_command)
			copy_command = 'scp -q -p -r env_params.list env_ports.list ' + MAIN_COMPOSE_FILE+' '+ALGS_CONFIG_FILE+' compose-files '+ top_manager_node['user']+'@'+top_manager_node['ip']+':'+top_manager_node['path']
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
					address = self.find_stream_manager()
					print('### DEEP FRAMEWORK STARTED ###')
					print('Check your stream at: ', address)
				else:
					print(res_status)
					command = 'python3 rm_services.py'
					self.machine.exec_shell_command(command)


		except Exception as e:

			raise e


class ImageManager:

	def __init__(self,machine,registry):
		self.machine = machine
		self.registry = registry.insecure_addr
		self.images_list = []
		self.__pull_images=[]
	
	def __find_dockerfiles(self):
		dockerfiles_path = []
		for root, dirs, files in os.walk(MAIN_DIR):
			for file in files:
				if 'Dockerfile' in file:
					if 'clothing' in file:
						continue
					dockerfile_path = os.path.join(root, file)
					dockerfiles_path.append(dockerfile_path)
		return dockerfiles_path


	def __create_push_commands(self):

		base_com = 'docker push '
		commands = list(map(lambda img: base_com + img , self.images_list))
		return commands

	def __create_build_commands(self,dockerfiles_path):
		build_commands = []
		images_list = []
		base_com = 'docker build '
		for path in dockerfiles_path:
			f_flag = '-f ' + path
			data_split = path.split('/')[-2:]
			temp_image_name = data_split[0]
			docker_file = data_split[1]
			mode = docker_file.split('.')
			context = ' ' +path.replace(docker_file,'')
			tag = ':deep'
			if len(mode) > 1:
				tag = tag + '_' + mode[1]
			if 'setup' in tag:
				image_name = temp_image_name + tag
			else:
				image_name = self.registry + '/' + temp_image_name + tag
			t_flag = ' -t ' + image_name
			self.images_list.append(image_name)
			if 'setup' not in tag:
				self.__pull_images.append(temp_image_name + tag)
			build_command = base_com + f_flag + t_flag + context
			if 'setup' in t_flag:
				build_commands = [build_command] + build_commands
			else:
				build_commands.append(build_command)
		return build_commands

	def build_images(self):
		paths = self.__find_dockerfiles()
		build_commands = self.__create_build_commands(paths)
		
		for i,build in enumerate(build_commands):
			
			if 'cpu' in build:
				mode = 'cpu'
			elif 'gpu' in build:
				mode = 'gpu'
			else:
				mode = ''



			try:
				result = re.search('5000/(.*):deep', build)
				image_name = result.group(1)
			except:
				result = re.search('-t (.*):deep', build)
				image_name = result.group(1)


			print('Building %s %s: %s of %s' % (image_name, mode, str(i+1), str(len(build_commands))))
			self.machine.exec_shell_command(build,ignore_err = False)

	def push_images(self):
		
		push_commands = self.__create_push_commands()
		for i,push in enumerate(push_commands):

			if 'setup' in push:
				continue
			if 'cpu' in push:
				mode = 'cpu'
			elif 'gpu' in push:
				mode = 'gpu'
			else:
				mode = ''

			try:
				result = re.search('5000/(.*):deep', push)
				image_name = result.group(1)
			except:
				result = re.search('-t (.*):deep', push)
				image_name = result.group(1)

			print('Pushing %s %s: %s of %s' % (image_name,mode, str(i+1), str(len(push_commands))))
			self.machine.exec_shell_command(push)

	def create_pull_file(self):
		filename = 'docker_pull.sh'
		base_com = 'docker pull $registry/'
		with open(filename, 'w') as pull_file:
			pull_file.write('#!/bin/bash\n')
			pull_file.write('registry="$1"\n')
			for img in self.__pull_images:
				pull_file.write(base_com + img +'\n')








