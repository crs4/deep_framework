
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
		self.temp_building_list = {'detector': None, 'algs': [], 'standard': None}



	def build_and_push(self,alg_gpu_matches):
		
		print('The building process will take several time...')
		build_list = []

		

		if self.temp_building_list['detector'] != None:
			det_name = self.temp_building_list['detector'][0]
			det_dict = alg_gpu_matches.pop(det_name)
			mode = det_dict['gpu_id']
			mode = 'gpu' if mode is not None else 'cpu'
			build_list.append((det_name,mode))


		
		algs_requested = [ alg for alg,mode in self.temp_building_list['algs']]
		for component, node_dict in alg_gpu_matches.items():
			if component in algs_requested:
				if node_dict['gpu_id'] != None:
					build_list.append((component,'gpu'))
				else:
					build_list.append((component,'cpu'))


		
		self.image_manager.build_images(build_list,self.temp_building_list['standard'])
		self.image_manager.create_pull_file()

		self.image_manager.push_images()
		self.__pull_images()
		

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


	def create_volume(self,path):
		top_manager_node = self.top_manager_node
		#inspect_command = 'docker service ps --format "{{.CurrentState}}" '
		
		try:
			print('Creating deep_media_volume...')
			create_volume_command = "docker volume create --name deep_media_volume --opt type=none --opt o=bind --opt device="
			rm_volume_command = "docker volume rm deep_media_volume"
			if top_manager_node['type'] == 'RemoteNode':
				create_volume_command = "ssh %s@%s '%s'" % (top_manager_node['user'], top_manager_node['ip'], create_volume_command)
				rm_volume_command = "ssh %s@%s '%s'" % (top_manager_node['user'], top_manager_node['ip'], rm_volume_command)

			self.machine.exec_shell_command(rm_volume_command)

			self.machine.exec_shell_command(create_volume_command+path)
		except Exception as e:
			print(e)

	def manage_sources(self):
		sources = []

		filename = 'env_params.list'
		change_params_answer =  'y'
		if not self.use_last_settings:
			if os.path.isfile('./'+filename):
				change_params_question = 'Do you want to change streaming params? (y/n): \n'
				change_params_answer = q.get_acceptable_answer(change_params_question,['y','n']).lower()
			if  change_params_answer == 'y':
				max_delay = q.get_number('Insert max delay in seconds you consider acceptable for getting algorithms results (default: 1s): \n','float',1)
				interval_stats = q.get_number('How often do you want to generate statics of execution in seconds? (default: 1s): \n','float',1)
				#timezone = q.get_answer('Please, insert your timezone (default Europe/Rome): \n')
				#if timezone=='':
				#	timezone = 'Europe/Rome'
				add_video_source = 'Do you want to add a video source? (y/n): \n'
				source_folder = None
				while q.get_acceptable_answer(add_video_source,['y','n']).lower() == 'y':
					source_type = q.get_acceptable_answer('Please enter the video source type (url/stored). \n',['url','stored']).lower()
					if source_type == 'stored':
						if source_folder is None:
							source_folder = input('Please, insert the absolute path of the cluster manager video folder.\n(It will be used for every stored video source.)\n')
							self.create_volume(source_folder)
						source = input('Please, insert the video name with its extension.\n')
						source='/mnt/remote_media/'+source
					else:
						source = input('Insert video source address/url: \n')
					id = input('Give a unique name/ID to this video source: \n')
					sources.append((id, source))

				with open(filename, 'w') as out:
					out.write('MAX_ALLOWED_DELAY=' + str(max_delay) + '\n')
					out.write('INTERVAL_STATS=' + str(interval_stats) + '\n')
					#out.write('TZ=' + timezone + '\n')
					for id, source  in sources:
						out.write('\nSOURCE_' + id + '=' + source + '\n')
		if self.use_last_settings or change_params_answer == 'n':
			with open(filename) as f:
				content = f.read().splitlines()
				for line in content:
					if line.startswith('SOURCE_'):
						id = line.split('=')[0][7:]
						source = line[len(id) + 1:]
						sources.append((id, source))

		return sources

	def manage_standard_images(self):
		if not self.use_last_settings:
			build_standard_question = 'Do you want to build standard framework docker images? (y/n): \n'
			build_standard_images = q.get_acceptable_answer(build_standard_question,['y','n']).lower()
			self.temp_building_list['standard'] = build_standard_images

	def manage_detector(self,conf):

		if not self.use_last_settings:

			exec_config = ConfigParser()
			read_config = ConfigParser()

			detector,det_build = conf.ask_detector(q)
			det,det_mode = detector
			det_framework = None
			detector_path = os.path.join(MAIN_DIR,'detector/'+det)

			for file in os.listdir(detector_path):
				if file.endswith(".ini"):
					ini_file = os.path.join(detector_path,file)
					read_config.read(ini_file)
					det_framework  = read_config['CONFIGURATION']['FRAMEWORK']
				
			det_framework = str(det_framework)

			detector = (det,det_mode,det_framework)

			exec_config[det] = {}
			exec_config[det]['detector_mode'] = det_mode
			exec_config[det]['framework'] = det_framework
			if det_build == 'y':
				self.temp_building_list['detector'] = det_build
			with open(os.path.join(MAIN_DIR, DETECTOR_CONFIG_FILE), 'w') as defaultconfigfile:
				exec_config.write(defaultconfigfile)
		else:
			temp_detector = []
			reader_det_config = ConfigParser()
			reader_det_config.read(DETECTOR_CONFIG_FILE)
			det_name = reader_det_config.sections()[0]
			detector = [det_name]
			for key in reader_det_config[det_name]:
				val = reader_det_config[det_name][key]
				detector.append(val)
			detector = tuple(detector)

		return detector

	def set_detector(self,alg_gpu_matches):
		det = list(alg_gpu_matches)[0]
		det_value = alg_gpu_matches[det]
		det_node_name = det_value['node_name']
		if det_value['gpu_id'] != None:
			mode = 'gpu'
		else:
			mode = 'cpu'

		if self.temp_building_list['detector'] == 'y':
			self.temp_building_list['detector'] = (det,mode)

		return det,mode,det_node_name,det_value['gpu_id']

	def manage_algs(self,conf):

		if not self.use_last_settings:

			config_question = 'Do you want to change default algorithms configuration? (y/n): \n'
			if not os.path.isfile('./'+ALGS_CONFIG_FILE) or q.get_acceptable_answer(config_question,['y','n']).lower() == 'y':		
				algs_to_build = conf.configure()
				self.temp_building_list['algs'] = algs_to_build




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
		inspect_command = 'docker service ps --format "{{.Node}}" deepframework_server'
		if top_manager_node['type'] == 'RemoteNode':
			inspect_command = "ssh %s@%s '%s'" % (top_manager_node['user'], top_manager_node['ip'], inspect_command)

		node_name = self.machine.exec_shell_command(inspect_command).split('\n')[0]
		config_app = ConfigParser()

		config_app.read(CLUSTER_CONFIG_FILE)
		node_ip = config_app[node_name]['ip']
		app_address = 'https://'+node_ip+':'+str(APP_PORT)
		return app_address



	def start_framework(self, compose_command_string):

		start_command = "docker stack deploy -c "+ MAIN_COMPOSE_FILE + compose_command_string + " deepframework"
		top_manager_node = self.top_manager_node
		


		if top_manager_node['type'] == 'RemoteNode':
			start_command = "ssh %s@%s 'cd %s && %s'" % (top_manager_node['user'], top_manager_node['ip'], top_manager_node['path'], start_command)
			copy_command = 'scp -q -p -r env_params.list env_ports.list ' + MAIN_COMPOSE_FILE+' '+ALGS_CONFIG_FILE+' '+DETECTOR_CONFIG_FILE+' compose-files '+ top_manager_node['user']+'@'+top_manager_node['ip']+':'+top_manager_node['path']
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
		self.excluded = ['clothing','sample','generic']
	
	def __find_dockerfiles(self):

		dockerfiles_path = []
		for root, dirs, files in os.walk(MAIN_DIR):
			for file in files:
				if 'Dockerfile' in file:
					dockerfile_path = os.path.join(root, file)
					if any(exc in dockerfile_path for exc in self.excluded):
						continue
					
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

	def build_images(self,list_to_build, build_standard_images):
		temp_paths = self.__find_dockerfiles()
		paths = []
		for p in temp_paths:
			if build_standard_images == 'y':
				if '.' not in p:
					paths.append(p)
					continue

			for (alg,mode) in list_to_build:
				if alg in p and mode.lower() in p:
					paths.append(p)
		


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

		os.chmod(filename, 0o777)








