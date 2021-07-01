
from config import * 
import os
import re


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
		self.build_commands,self.push_commands,self.pull_commands = self.create_commands()
		

	def start_build_routine(self):
		self.create_pull_file()
		self.build_images()
		self.push_images()
	
	def __set_dockerfile_option(self, dockerfile_path):
		return ' -f '+dockerfile_path

	def __set_image_name_option(self, image_name):
		return ' -t '+ image_name

	

	def __format_command(self,command,image_name,dfile=None):
		base_com = 'docker '+command
		if command == 'build':
			image_name_option = self.__set_image_name_option(image_name)
			dfile_option = self.__set_dockerfile_option(dfile)
			context, filename = os.path.split(dfile)
			return base_com + dfile_option + image_name_option + ' ' + context
		elif command == 'push':
			return base_com + ' ' + image_name
		elif command == 'pull':
			image_name = image_name.replace(self.registry_address, '$registry')
			return base_com + ' ' + image_name

	def set_setup_images(self):
		for setup_image_name, dfile in self.standard_components['setup'].items():
			image_name = setup_image_name+':deep_setup'
			self.service_dockerfile_map[image_name] = dfile




		
	def create_service_dockerfile_building_map(self):

		if self.standard_components['build_setup'] == 'y':
			self.set_setup_images()


		for service in self.services:
			
			image_name = service.image_name
			result = re.search('5000/(.*):deep', image_name)
			image_base_name = result.group(1)
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



	def create_commands(self):
		build_commands = []
		push_commands = []
		pull_commands = []
		for image_name, dockerfile in self.service_dockerfile_map.items():
			build_command = self.__format_command('build',image_name,dockerfile)
			push_command = self.__format_command('push',image_name)
			pull_command = self.__format_command('pull',image_name)
			
			build_commands.append(build_command)
			push_commands.append(push_command)
			pull_commands.append(pull_command)


		return build_commands,push_commands,pull_commands

	def build_images(self):
		for i,build in enumerate(self.build_commands):
			print(build)
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


			print('Building %s %s: %s of %s' % (image_name, mode, str(i+1), str(len(self.build_commands))))
			self.machine.exec_shell_command(build,ignore_err = False)

	def push_images(self):
		for i,push in enumerate(self.push_commands):

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

			print('Pushing %s %s: %s of %s' % (image_name,mode, str(i+1), str(len(self.push_commands))))
			self.machine.exec_shell_command(push)

	def create_pull_file(self):
		filename = 'docker_pull.sh'
		with open(filename, 'w') as pull_file:
			pull_file.write('#!/bin/bash\n')
			pull_file.write('registry="$1"\n')
			for com in self.pull_commands:
				pull_file.write(com + '\n')

		os.chmod(filename, 0o777)


