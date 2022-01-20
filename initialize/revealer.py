
import os
from configparser import ConfigParser
from config import * 


class Revealer:



	def __find_config_files(self,base_folder_path):
		config_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(base_folder_path) for f in filenames if os.path.splitext(f)[1] == '.ini']
		return config_files

	def __convert_config_parser_to_dict(self,conf_parser):

		conf_dict = dict()
		for key,value in conf_parser['CONFIGURATION'].items():
			conf_dict[key.lower()] = value

		return conf_dict

	"""
	def __reveal_dockerfiles(self,comp_base_path):

		dockerfiles_path = []
		for file in os.listdir(comp_base_path):
			if 'Dockerfile' in file:
				d_path = os.path.join(comp_base_path,file)
				dockerfiles_path.append(d_path)
		return dockerfiles_path
	"""
	def __reveal_dockerfiles(self,comp_base_path):

		dockerfiles_path = []
		for root, dirs, files in os.walk(comp_base_path):
			for file in files:
				if 'Dockerfile' in file:
					dockerfile_path = os.path.join(root, file)
					
					
					dockerfiles_path.append(dockerfile_path)
		return dockerfiles_path





	def reveal_detectors(self):
		detector_list = []
		detector_config_files = self.__find_config_files(DETECTOR_PATH)
		for conf in detector_config_files:
			det_config = ConfigParser()
			det_config.read(conf)
			det_dict = self.__convert_config_parser_to_dict(det_config)
			det_dict['name'] = det_dict['category']
			comp_base_path, __ = os.path.split(conf)
			dockerfiles_path = self.__reveal_dockerfiles(comp_base_path)
			det_dict['dockerfiles'] = dockerfiles_path
			detector_list.append(det_dict)

		return detector_list


	def reveal_descriptors(self):
		descriptor_list = []
		descriptor_config_files = self.__find_config_files(DESCRITPTOR_PATH)
		for conf in descriptor_config_files:
			desc_config = ConfigParser()
			desc_config.read(conf)
			desc_dict = self.__convert_config_parser_to_dict(desc_config)
			#desc_dict['name'] = self.__set_custom_algorithm_name(conf)
			comp_base_path, __ = os.path.split(conf)
			dockerfiles_path = self.__reveal_dockerfiles(comp_base_path)
			desc_dict['dockerfiles'] = dockerfiles_path
			descriptor_list.append(desc_dict)

		return descriptor_list

	def reveal_all_custom_components(self):
		components = dict()
		components['detectors'] = self.reveal_detectors()
		components['descriptors'] = self.reveal_descriptors()
		return components


	def reveal_standard_components(self):
		dockerfiles = self.__reveal_dockerfiles(MAIN_DIR)
		standard_components = dict()
		standard_components['pipeline'] = dict()
		standard_components['setup'] = dict()
		for f in dockerfiles:

			comp_name = f.split('/')[-2]
			if 'setup' in f :#and 'test' not in f:
				standard_components['setup'][comp_name] = f
			else:

				if DESCRITPTOR_PATH in f or DETECTOR_PATH in f:
					continue

				standard_components['pipeline'][comp_name] = f

		return standard_components















