
from config import * 
import os

class ImageManager:

	def __init__(self,machine,services,registry_address,standard_components):
		"""
		self.machine = machine
		self.images_list = []
		self.macthes = alg_gpu_matches
		self.standard = standard_components
		self.__pull_images=[]
		self.excluded = ['clothing','sample','generic','img']
		"""
		self.registry_address = registry_address
		self.machine = machine
		self.standard_components = standard_components
		self.services = services
		self.service_dockerfile_map = dict()
		self.create_service_dockerfile_building_map()
		self.create_build_commands()

	
	def __set_dockerfile_option(self, dockerfile_path):
		return ' -f '+dockerfile_path

	def __set_image_name_option(self, image_name):
		return ' -t '+ image_name

	

	def __format_build_command(self,dfile,image_name):
		base_com = 'docker_build '
		image_name_option = self.__set_image_name_option(image_name)
		dfile_option = self.__set_dockerfile_option(dfile)
		context, filename = os.path.split(dfile)
		return base_com + dfile_option + image_name_option + ' ' + context

	def create_service_dockerfile_building_map(self):

		for service in self.services:
			image_name = service.image_name
			image_base_name = image_name[image_name.find('/')+1 : image_name.find(':')]
			if image_name not in self.service_dockerfile_map.keys():
				if image_base_name in self.standard_components['pipeline'].keys():
					if self.standard_components['build_pipeline'] == 'y':
						self.service_dockerfile_map[image_name] = self.standard_components['pipeline'][image_base_name]
				else:
					to_build = service.params['to_build']
					if to_build == 'y':
						dockerfiles = service.params['dockerfiles']
						dfile = [ d for d in dockerfiles if service.params['mode'] in d ][0]
						self.service_dockerfile_map[image_name] = dfile



	def create_build_commands(self):
		build_commands = []
		for image_name, dockerfile in self.service_dockerfile_map.items():
			command = self.__format_build_command(dockerfile,image_name)
			build_commands.append(command)


		print(build_commands)






	
	

	"""

	def create_standard_component_build_command(self):

		for comp in self.standard_components['pipeline']:
			image_name = comp['name']
			dockerfile = comp['dockerfile']
			command = self.__format_build_command(image_name,dockerfile)
			self.build_commands.append(command)

	def create_custom_component_build_command(self):
		for service in self.services:
			if 'params' not in service.__dict__:
				continue
			image_name = service.params['image_name']:
			dfiles = service.params['dockerfile']
			mode = service.params['mode']
			dockerfile = [d for d in dfiles if mode in d]
			command = self.__format_build_command(image_name,dockerfile)
			self.build_commands.append(command)


	def create_setup_component_build_command(self):
		for comp in self.standard_components['setup']:
			image_name = comp['name']
			dockerfile = comp['dockerfile']
			command = self.__format_build_command(image_name,dockerfile)
			self.build_commands.append(command)
		
	"""


	"""
	def create_build_command(self):

		dockerfiles = self.__find_dockerfiles(MAIN_DIR)
		base_com = 'docker build '
		for service in services:
			docker_image_name = service.image_name
			if docker_image_name in self.standard_components['pipeline'].keys():
				dockerfile = [ dfile for comp_name,dfile in self.standard_components['pipeline'].items() ][0]
			else:
				dfiles = service.params['dockerfiles']
				dockerfile = [d for d in dfiles if service.params['mode'] in d][0]
	"""




































	"""

	def create_build_commands(self):
		build_commands = []
	
	


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

	def build_images(self, alg_gpu_matches):
		temp_paths = self.__find_dockerfiles()
		
		paths = []
		for p in temp_paths:

			if build_standard_images == 'y':
				if 'cpu' not in p and 'gpu' not in p:
					paths.append(p)
					continue

			

			for (alg,mode) in list_to_build:
				if 'feature_extractors' in p:
					comp_folder = os.path.dirname(p)
					alg_config_file = [os.path.join(comp_folder, f) for f in os.listdir(comp_folder) if f.endswith('.' + 'ini')][0]
					reader_alg = ConfigParser()
					reader_alg.read(alg_config_file)
					alg_name = reader_alg.get('CONFIGURATION','NAME')
					if alg == alg_name and mode.lower() in p:
						paths.append(p)
				else:
					if alg in p and mode.lower() in p:
						paths.append(p)

		
		
		
		build_commands = self.__create_build_commands(paths)
		
		for i,build in enumerate(build_commands):
			
			if 'cpu' in build:
				mode = 'cpu'
			elif 'gpu' in build:
				mode = 'gpu'
			elif 'setup' in build:
				mode = 'setup'
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
			elif 'setup' in push:
				mode = 'setup'
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
	"""








