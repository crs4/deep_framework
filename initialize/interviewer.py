from configparser import ConfigParser

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

class ParamsProvider(Interviewer):

	def __init__(self):
		super().__init__()


	def ask_for_params(self):
		max_delay = self.get_number('Insert max delay in seconds you consider acceptable for getting algorithms results (default: 1s): \n','float',1)
		interval_stats = self.get_number('How often do you want to generate statics of execution in seconds? (default: 1s): \n','float',1)
		return {'max_allowed_delay': max_delay,'interval_stats':interval_stats }

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

	def __init__(self):
		super().__init__()
		self.remote_source_path = '/mnt/remote_media/'
		self.local_source_params_path = ENV_PARAMS


	def ask_for_sources(self):
		sources = []
		source_folder = None
		add_video_source_question = 'Do you want to add a video source? (y/n): \n'

		while self.get_acceptable_answer(add_video_source_question,['y','n']).lower() == 'y':
			source_type = self.get_acceptable_answer('Please enter the video source type (url/stored). \n',['url','stored']).lower()
			if source_type == 'stored':
				if source_folder is None:
					source_folder = self.get_answer('Please, insert the absolute path of the cluster manager video folder.\n(It will be used for every stored video source.)\n')
				source = self.get_answer('Please, insert the video name with its extension.\n')
				source = self.remote_source_path+source
			else:
				source = self.get_answer('Insert video source address/url: \n')
			source_id = self.get_answer('Give a unique name/ID to this video source: \n')
			source_dict = {'source_id': source_id, 'source_path':source, 'source_folder': source_folder}
			sources.append(source_dict)

		return sources

	def write_sources(self,sources):
		with open(self.local_source_params_path, 'a') as env_file:
			for source_conf  in sources:
				source_id = source_conf['source_id']
				source_path = source_conf['source_path']
				env_file.write('\nSOURCE_' + source_id + '=' + source_path + '\n')

	def read_sources(self):
		sources = []
		with open(self.local_source_params_path) as env_file:
			content = env_file.read().splitlines()
			for line in content:
				if line.startswith('SOURCE_'):
					source_path_split = line.split('=')
					source_id = source_path_split[0].split('_')[1]
					source = source_path_split[1]
					source_dict = {'source_id': source_id, 'source_path':source, 'source_folder': None}
					sources.append(source_dict)
		return sources

	def get_sources(self, use_last_settings):

		if use_last_settings:
			sources = self.read_sources()
		else:
			sources = self.ask_for_sources()
			self.write_sources(sources)

		return sources



class DetectorProvider(Interviewer):

	def __init__(self,available_detectors):
		super().__init__()
		self.available_detectors = available_detectors


	def ask_for_detectors(self):
		detectors_to_execute = []

		while len(detectors_to_execute) == 0:
			print('Please, enter your wished detector.\n')
			for det in self.available_detectors:
				det_name = det['name']
				gpu_dockerfile_bool = any([True for f in det['dockerfiles'] if 'gpu' in f.lower()])
				answer_det = self.get_acceptable_answer('Do you want to execute '+det_name+'? (y/n): \n',['y','n']).lower()
				if answer_det == 'y':
					detector_wished_params = dict()
					
					if gpu_dockerfile_bool:
						det_mode = self.get_acceptable_answer('Select mode of execution of '+det_name+'? (cpu/gpu): \n',['cpu','gpu']).lower()
					else:
						det_mode = 'cpu'


					build = self.get_acceptable_answer('Do you want to build relative docker image? (y/n) \n',['y','n']).lower()

					detector_wished_params['name'] = det['name']
					detector_wished_params['mode'] = det_mode
					detector_wished_params['to_build'] = build
					detector_wished_params['dockerfiles'] = det['dockerfiles']
					detector_wished_params['framework'] = det['framework']
					detectors_to_execute.append(detector_wished_params)

		return detectors_to_execute
		

	def write_detectors(self,detectors):
		det_wished_config = ConfigParser()
		for det in detectors:
			name = det['name']
			det_wished_config[name] = {}
			det_wished_config[name]['mode'] = det['mode']
			det_wished_config[name]['framework'] = det['framework']
			
			with open(os.path.join(MAIN_DIR, DETECTOR_CONFIG_FILE), 'w') as defaultconfigfile:
				det_wished_config.write(defaultconfigfile)
		
	def read_detectors(self):

		detectors = []
		reader_det_config = ConfigParser()
		reader_det_config.read(DETECTOR_CONFIG_FILE)
		detectors_list = reader_det_config.sections()
		for det in detectors_list:
			det_dict = dict()
			det_dict['name'] = det
			for key in reader_det_config[det]:
				val = reader_det_config[det][key]
				det_dict[key] = val
			det_dict['to_build'] = 'n'
			detectors.append(det_dict)
		return detectors

	def get_detectors(self, use_last_settings):

		if use_last_settings:
			detectors = self.read_detectors()
		else:
			detectors = self.ask_for_detectors()
			self.write_detectors(detectors)

		return detectors



class DescriptorProvider(Interviewer):

	def __init__(self,available_descriptors, detectors):
		super().__init__()
		self.available_descriptors = available_descriptors
		self.detectors_to_execute = detectors


	def ask_for_descriptors(self):
		descriptors_to_execute = []

		for desc in self.available_descriptors:

			related_detector = desc['related_to']
			if related_detector not in self.detectors_to_execute:
				continue

			alg_name = desc['name']
			answer_alg = self.get_acceptable_answer('Do you want to execute '+alg_name+' algorythm? (y/n): \n',['y','n']).lower()
			if answer_alg == 'y':

				alg_mode = self.get_acceptable_answer('Select mode of execution of '+alg_name+' algorithm? (cpu/gpu): \n',['cpu','gpu']).lower()
				alg_build = self.get_acceptable_answer('Do you want to build relative docker image? (y/n): \n',['y','n']).lower()
				
				descriptor_wished_params = dict()
				descriptor_wished_params['name'] = alg_name
				descriptor_wished_params['mode'] = alg_mode
				descriptor_wished_params['framework'] = desc['framework']
				descriptor_wished_params['to_build'] = alg_build
				descriptor_wished_params['related_to'] = related_detector
				descriptor_wished_params['dockerfiles'] = desc['dockerfiles']

				descriptors_to_execute.append(descriptor_wished_params)
				
		return descriptors_to_execute
		

	def write_descriptors(self,descriptors):
		desc_wished_config = ConfigParser()
		for desc in descriptors:
			name = desc['name']
			desc_wished_config[name] = {}
			desc_wished_config[name]['mode'] = desc['mode']
			desc_wished_config[name]['framework'] = desc['framework']
			desc_wished_config[name]['related_to'] = desc['related_to']
			
			with open(os.path.join(MAIN_DIR, ALGS_CONFIG_FILE), 'w') as defaultconfigfile:
				desc_wished_config.write(defaultconfigfile)
		
	def read_descriptors(self):

		descriptors = []
		reader_desc_config = ConfigParser()
		reader_desc_config.read(ALGS_CONFIG_FILE)
		descriptors_list = reader_desc_config.sections()
		for desc in descriptors_list:
			desc_dict = dict()
			desc_dict['name'] = desc
			for key in reader_desc_config[desc]:
				val = reader_desc_config[desc][key]
				desc_dict[key] = val
			desc_dict['to_build'] = 'n'
			descriptors.append(desc_dict)
		return descriptors

	def get_descriptors(self, use_last_settings):

		if use_last_settings:
			descriptors = self.read_descriptors()
		else:
			descriptors = self.ask_for_descriptors()
			self.write_descriptors(descriptors)

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





















