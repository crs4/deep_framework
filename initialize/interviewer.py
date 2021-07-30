from configparser import ConfigParser
import subprocess
import os
import socket
from config import *

class Interviewer:

	def get_answer(self,prompt):
		while True:
			value = input(prompt)
			if value == '':
				print("Sorry, your response you have to type a response")
				continue
			else:
				break
		return value

	def get_number(self,prompt, number_type, default_number=None):
		while True:
			value = input(prompt)

			if default_number and value == '':
				if number_type == 'float':
					value = float(default_number)
				if number_type == 'int':
					value = int(default_number)
				break

			if number_type == 'float':
				try:
					value = float(value)
				except ValueError:
					print("Please, insert a float number.")
					continue

			if number_type == 'int':
				try:
					value = int(value)
				except ValueError:
					print("Please, insert a integer number.")
					continue

			if value < 0:
				print("Sorry, your response must not be negative.")
				continue
			else:
				break
		return value

	def get_acceptable_answer(self,prompt,acceptable_answers):
		while True:
			value = input(prompt)
			if value.lower() not in acceptable_answers:
				print("Please, insert one of listed answers.")
				continue
			else:
				break
		return value


	
	def get_ip(self,prompt):
		while True:
			addr = input(prompt)
			try:
				socket.inet_aton(addr)
				print("Valid IP")
				break
			except socket.error:
				print("Invalid IP. Please, insert a valid IP address.")
				continue
		return addr

	def get_remote_folder(self,prompt,user,ip):
		import subprocess
		while True:
			path = input(prompt)

			try:
				com = "ssh %s@%s [ -d %s ] && echo 'Exists' || echo 'Error' " % (user,ip,path)
				p = subprocess.Popen(com, stdout=subprocess.PIPE, shell=True)
				(output, err) = p.communicate()

				output = output.decode("utf-8").strip('\n')
				if err is not None:
					print(err)
				if output == 'Exists':
					print('Valid path.')
				if output == 'Error':
					creation = self.get_acceptable_answer('This path does not exist on remote node. Do you want to create it? (y/n) ', ['y','n'])
					if creation == 'y':
						try:
							command = "ssh %s@%s mkdir -p %s" % (user, ip, path)
							subprocess.call(command, shell=True)
						except Exception as e:
							print(e)
					else:
						continue
				break
			except Exception as e:
				print(e)
				continue
		return path


class ParamsProvider(Interviewer):

	def __init__(self):
		super().__init__()


	def ask_for_params(self):
		#max_delay = self.get_number('Insert max delay in seconds you consider acceptable for getting algorithms results (default: 1s): \n','float',1)
		interval_stats = self.get_number('How often do you want to generate statics of execution in seconds? (default: 1s): \n','float',1)
		#return {'max_allowed_delay': max_delay,'interval_stats':interval_stats }
		return {'interval_stats':interval_stats }

	def write_params(self,params):
		with open(ENV_PARAMS, 'w') as env_file:
			for kpar, vpar in params.items():
				env_file.write(str(kpar.upper())+'='+str(vpar)+'\n')

			env_file.write('PYTHONUNBUFFERED=0\n')
			env_file.write('PROT=tcp://\n')
	

	def set_stream_params(self, use_last_settings):

		if not use_last_settings:
			params = self.ask_for_params()
			self.write_params(params)



class SourceProvider(Interviewer):

	def __init__(self,nodes_data):
		super().__init__()
		self.remote_source_path = '/mnt/remote_media/'
		self.source_node = self.__get_source_node(nodes_data) 

	def __get_source_node(self,nodes_data):
		source_node = None
		for node_name, node_values in nodes_data.items():
			if node_values['role'] == 'manager':
				source_node = node_name
				break
		return source_node



	def __rm_config(self):
		if os.path.isfile(DETECTOR_CONFIG_FILE):
			os.remove(DETECTOR_CONFIG_FILE)
		if os.path.isfile(ALGS_CONFIG_FILE):
			os.remove(ALGS_CONFIG_FILE)

	def want_to_change(self):
		config_question = 'Sources configuration file found. Do you want to change it? (y/n): \n'
		if not os.path.isfile(SOURCES_CONFIG_FILE):
			return True

		if self.get_acceptable_answer(config_question,['y','n']).lower() == 'n':
			return False
		else:
			return True

	def ask_for_sources(self):
		sources = []
		source_folder = None
		cycle_counter = 0

		add_video_source_question = 'Do you want to add a video source? (y/n): \n'

		

		while self.get_acceptable_answer(add_video_source_question,['y','n']).lower() == 'y' or len(sources) == 0 and cycle_counter>0:
			self.__rm_config()
			source_url = None
			source_path = None

			#source_type_answer = self.get_acceptable_answer('Please enter the video source type (url/stored/cabled/remote). \n',['url','stored','cabled','remote']).lower()
			source_type_answer = self.get_acceptable_answer('Please enter the video source type (file/ip/webrtc): \n',['file','ip','webrtc']).lower()
			if source_type_answer == 'file':
				if source_folder is None:
					source_folder = self.get_answer('Please, insert the absolute path of the cluster manager video folder.\n(It will be used for every stored video source.)\n')
					if source_folder[-1] == '/':
						source_folder = source_folder[:-1]
				source_answer = self.get_answer('Please, insert the video name with its extension.\n')
				source_path = self.remote_source_path+source_answer
				source_type = 'file'
			elif source_type_answer == 'ip':
				source_url = self.get_answer('Insert video source address/url: \n')
				source_type = 'ip_stream'
			elif source_type_answer == 'webrtc':
				source_type = 'webrtc_stream'

			source_id = self.get_answer('Give a unique name/ID to this video source: \n')
			source_dict = {'source_id': source_id, 'source_path':source_path, 'source_folder': source_folder if source_path is not None else 'None', 'source_url': source_url, 'source_type':source_type,'source_node':self.source_node }
			sources.append(source_dict)
			cycle_counter+=1


		return sources

	def write_sources(self,sources):

		sources_config = ConfigParser()
		for source_conf  in sources:


			section_name = source_conf['source_id']
			sources_config[section_name] = {}
			sources_config[section_name]['source_path'] = str(source_conf['source_path'])
			sources_config[section_name]['source_url'] = str(source_conf['source_url'])
			sources_config[section_name]['source_type'] = str(source_conf['source_type'])
			sources_config[section_name]['source_folder'] = str(source_conf['source_folder'])
			sources_config[section_name]['source_node'] = str(source_conf['source_node'])

			
			with open(os.path.join(MAIN_DIR, SOURCES_CONFIG_FILE), 'w') as defaultconfigfile:
				sources_config.write(defaultconfigfile)


		

	def read_sources(self):

		sources = []
		reader_source_config = ConfigParser()

		reader_source_config.read(SOURCES_CONFIG_FILE)
		sources_list = reader_source_config.sections()
		for source in sources_list:
			source_dict = dict()
			source_dict['source_id'] = source
			for key in reader_source_config[source]:
				val = reader_source_config[source][key]
				source_dict[key] = val
			sources.append(source_dict)
		return sources

		

	def get_sources(self, use_last_settings):

		if not use_last_settings:

			if not self.want_to_change():
				sources = self.read_sources()
			else:
				sources = self.ask_for_sources()
				if len(sources) > 0:
					self.write_sources(sources)
		else:
			sources = self.read_sources()

		return sources
		



class DetectorProvider(Interviewer):

	def __init__(self,available_detectors, sources):
		super().__init__()
		self.available_detectors = available_detectors
		self.sources = sources

	

	def want_to_change(self):

		config_question = 'Detector configuration file found. Do you want to change it? (y/n): \n'
		if not os.path.isfile(DETECTOR_CONFIG_FILE):
			return True

		if self.get_acceptable_answer(config_question,['y','n']).lower() == 'n':
			return False
		else:
			return True


	def __rm_config(self):
		if os.path.isfile(ALGS_CONFIG_FILE):
			os.remove(ALGS_CONFIG_FILE)

	def ask_for_detectors(self):
		detectors_to_execute = []

		self.__rm_config()

		for source in self.sources:
			source_detectors = []
			while len(source_detectors) == 0:
				print('Please, enter your wished detector for the following source:',source['source_id'])
				for det in self.available_detectors:
					det_name = det['name']
					answer_det = self.get_acceptable_answer('Do you want to execute '+det_name+' detector? (y/n): \n',['y','n']).lower()
					if answer_det == 'y':
						detector_wished_params = dict()

						modes_availables = [ d.split('.')[1] for d in det['dockerfiles']]
						if len(modes_availables) == 0:
							print('No dockerfile found.')
							continue
						elif len(modes_availables) > 1:
							det_mode = self.get_acceptable_answer('Select mode of execution of '+det_name+'? (cpu/gpu): \n',['cpu','gpu']).lower()
						else:
							det_mode = modes_availables[0]
						


						build = self.get_acceptable_answer('Do you want to build relative docker image? (y/n) \n',['y','n']).lower()

						detector_wished_params['name'] = det['name']
						detector_wished_params['category'] = det['category']
						detector_wished_params['mode'] = det_mode
						detector_wished_params['to_build'] = build
						detector_wished_params['dockerfiles'] = det['dockerfiles']
						detector_wished_params['framework'] = det['framework']
						detector_wished_params['source_id'] = source['source_id']
						detector_wished_params['cuda_version'] = det['cuda_version']
						source_detectors.append(detector_wished_params)
						detectors_to_execute.append(detector_wished_params)

		return detectors_to_execute
		

	def write_detectors(self,detectors):
		det_wished_config = ConfigParser()
		for det in detectors:
			section_name = det['name'] + '_' + det['source_id']
			det_wished_config[section_name] = {}
			det_wished_config[section_name]['name'] = det['name']
			det_wished_config[section_name]['mode'] = det['mode']
			det_wished_config[section_name]['framework'] = det['framework']
			det_wished_config[section_name]['source_id'] = det['source_id']
			det_wished_config[section_name]['cuda_version'] = det['cuda_version']
			
			with open(os.path.join(MAIN_DIR, DETECTOR_CONFIG_FILE), 'w') as defaultconfigfile:
				det_wished_config.write(defaultconfigfile)
		
	def read_detectors(self):

		detectors = []
		reader_det_config = ConfigParser()

		reader_det_config.read(DETECTOR_CONFIG_FILE)
		detectors_list = reader_det_config.sections()
		for det in detectors_list:
			det_dict = dict()
			for key in reader_det_config[det]:
				val = reader_det_config[det][key]
				det_dict[key] = val
			det_dict['to_build'] = 'n'
			detectors.append(det_dict)
		return detectors

	def get_detectors(self, use_last_settings):
		if not use_last_settings:

			if not self.want_to_change():
				detectors = self.read_detectors()
			else:
				detectors = self.ask_for_detectors()
				self.write_detectors(detectors)
		else:
			detectors = self.read_detectors()

		return detectors
		



		


class DescriptorProvider(Interviewer):

	def __init__(self,available_descriptors, detectors):
		super().__init__()
		self.available_descriptors = available_descriptors
		#self.detectors_to_execute = [det['name'] for det in detectors]
		self.detectors_to_execute = detectors


	def want_to_change(self):

		config_question = 'Descriptor configuration file found. Do you want to change it? (y/n): \n'
		if not os.path.isfile(ALGS_CONFIG_FILE):
			return True


		if self.get_acceptable_answer(config_question,['y','n']).lower() == 'n':
			return False
		else:
			return True

	def ask_for_descriptors(self):
		descriptors_to_execute = []

		
		for det in self.detectors_to_execute:
			det_name = det['name']
			source_id = det['source_id']
			print('Please, choose your descriptors for source ', source_id, ' and detector ',det_name)


			for desc in self.available_descriptors:

				related_detector = desc['related_to']
				if related_detector != det_name:
					continue

				alg_name = desc['name']

				answer_alg = self.get_acceptable_answer('Do you want to execute '+alg_name+' algorythm? (y/n): \n',['y','n']).lower()
				if answer_alg == 'y':
					
					modes_availables = [ d.split('.')[1] for d in desc['dockerfiles']]
					if len(modes_availables) == 0:
						print('No dockerfile found.')
						continue
					elif len(modes_availables) > 1:
						alg_mode = self.get_acceptable_answer('Select mode of execution of '+alg_name+' algorithm? (cpu/gpu): \n',['cpu','gpu']).lower()
					else:
						alg_mode = modes_availables[0]

					alg_build = self.get_acceptable_answer('Do you want to build relative docker image? (y/n): \n',['y','n']).lower()
					num_worker = self.get_number('How many worker do you want to create for this descriptor? (default: 1): \n','int',1)
					
					descriptor_wished_params = dict()
					descriptor_wished_params['name'] = alg_name
					descriptor_wished_params['mode'] = alg_mode
					descriptor_wished_params['framework'] = desc['framework']
					descriptor_wished_params['to_build'] = alg_build
					descriptor_wished_params['related_to'] = related_detector
					descriptor_wished_params['worker'] = num_worker
					descriptor_wished_params['dockerfiles'] = desc['dockerfiles']
					descriptor_wished_params['source_id'] = source_id
					descriptor_wished_params['cuda_version'] = desc['cuda_version']


					descriptors_to_execute.append(descriptor_wished_params)
				
		return descriptors_to_execute
		

	def write_descriptors(self,descriptors):
		desc_wished_config = ConfigParser()
		for desc in descriptors:
			section_name = desc['name'] + '_' + desc['source_id']
			desc_wished_config[section_name] = {}
			desc_wished_config[section_name]['name'] = desc['name']
			desc_wished_config[section_name]['mode'] = desc['mode']
			desc_wished_config[section_name]['framework'] = desc['framework']
			desc_wished_config[section_name]['related_to'] = desc['related_to']
			desc_wished_config[section_name]['worker'] = str(desc['worker'])
			desc_wished_config[section_name]['source_id'] = desc['source_id']
			desc_wished_config[section_name]['cuda_version'] = desc['cuda_version']
			
			with open(os.path.join(MAIN_DIR, ALGS_CONFIG_FILE), 'w') as defaultconfigfile:
				desc_wished_config.write(defaultconfigfile)
		
	def read_descriptors(self):

		descriptors = []
		reader_desc_config = ConfigParser()
		reader_desc_config.read(ALGS_CONFIG_FILE)
		descriptors_list = reader_desc_config.sections()
		for desc in descriptors_list:
			desc_dict = dict()
			for key in reader_desc_config[desc]:
				val = reader_desc_config[desc][key]
				desc_dict[key] = val
			desc_dict['to_build'] = 'n'
			descriptors.append(desc_dict)
		return descriptors

	def get_descriptors(self, use_last_settings):

		if not use_last_settings:

			if not self.want_to_change():
				descriptors = self.read_descriptors()
			else:
				descriptors = self.ask_for_descriptors()
				if len(descriptors) > 0:
					self.write_descriptors(descriptors)
		else:
			descriptors = self.read_descriptors()

		return descriptors




class StandardProvider(Interviewer):

	def __init__(self,standard_components):
		super().__init__()
		self.standard_components = standard_components
		


	def ask_for_standard(self):

		build_setup = self.get_acceptable_answer('Do you want to build setup components? (y/n): \n',['y','n']).lower()
		build_pipeline = self.get_acceptable_answer('Do you want to to build standard pipeline components? (y/n): \n',['y','n']).lower()

		self.standard_components['build_setup'] = build_setup
		self.standard_components['build_pipeline'] = build_pipeline

		return self.standard_components

	def get_standard_components(self, use_last_settings):

		if use_last_settings:
			self.standard_components['build_setup'] = 'n'
			self.standard_components['build_pipeline'] = 'n'
		else:
			self.standard_components = self.ask_for_standard()

		return self.standard_components




class ServerProvider(Interviewer):

	def __init__(self,nodes):
		self.nodes_names = list(nodes.keys())
		super().__init__()


	def want_to_change(self):

		config_question = 'Server configuration file found. Do you want to change it? (y/n): \n'
		if not os.path.isfile(SERVER_CONFIG_FILE):
			return True

		if self.get_acceptable_answer(config_question,['y','n']).lower() == 'n':
			return False
		else:
			return True


	def ask_for_server(self):
		server_dict = {}
		server_node = 'not_specified'

		
		specific_node = self.get_acceptable_answer('Do you want to deploy the server component in a specific node of the cluster? (y/n): \n',['y','n'])
		if specific_node == 'y':
			server_node = self.get_acceptable_answer('Which of the following nodes? '+ str(self.nodes_names)+': \n',self.nodes_names)
		server_dict['node'] = server_node
		return server_dict

	def write_server(self,server):
		server_config = ConfigParser()
		section_name = 'server configuration'
		server_config[section_name] = {}
		server_config[section_name]['node'] = server['node']
		
		with open(os.path.join(MAIN_DIR, SERVER_CONFIG_FILE), 'w') as defaultconfigfile:
			server_config.write(defaultconfigfile)
		
	def read_server(self):

		reader_server_config = ConfigParser()
		reader_server_config.read(SERVER_CONFIG_FILE)
		server_section = reader_server_config.sections()[0]
		server_config = dict(reader_server_config[server_section])
		return server_config


	def get_server(self, use_last_settings):

		if not use_last_settings:

			if len(self.nodes_names) == 1:
				server = dict()
				server['node'] = 'not_specified'
				self.write_server(server)
				return server


			if not self.want_to_change():
				server = self.read_server()
			else:
				server = self.ask_for_server()
				self.write_server(server)
		else:
			server = self.read_server()

		return server














