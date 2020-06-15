
import subprocess
import os
import socket
from configparser import ConfigParser
from config import *
import ruamel.yaml
from pathlib import Path

from ruamel.yaml.scalarstring import SingleQuotedScalarString
S = ruamel.yaml.scalarstring.DoubleQuotedScalarString
yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True

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

	
class Configurator:

	def __init__(self, registry):
		self.reg = registry




	def __create_alg_services(self,path,alg_name):
		image_registry = self.reg.insecure_addr
		alg_compose = dict()
		alg_compose['version'] = '3'
		broker_service = self.__create_broker_service()
		sub_collector_service = self.__create_sub_collector_service()
		descritptor_service = self.__create_descritptor_service(alg_name)
		alg_compose['services'] = {alg_name+'_broker':broker_service, alg_name+'_collector':sub_collector_service,alg_name+'_descriptor':descritptor_service}
		outf = Path(path)
		try:
			with outf.open('w') as ofp:
				yaml.indent(mapping=4)
				yaml.dump(alg_compose, ofp)
		except Exception as e:
			print('createservice')
			raise e
		




	def __create_broker_service(self):
		broker_dict = dict()
		broker_dict['depends_on'] = ['detector']
		broker_dict['env_file'] = ['env_params.list', 'env_ports.list']
		broker_dict['environment'] = ['FP_ADDRESS=detector']
		broker_dict['networks'] = ['net_deep']
		broker_dict['image'] = self.reg.insecure_addr+'/broker:deep'

		return broker_dict

	def __create_sub_collector_service(self):
		sub_col_dict = dict()
		sub_col_dict['depends_on'] = ['detector']
		sub_col_dict['env_file'] = ['env_params.list', 'env_ports.list']
		sub_col_dict['environment'] = ['COLLECTOR_ADDRESS=face_collector']
		sub_col_dict['networks'] = ['net_deep']
		sub_col_dict['image'] = self.reg.insecure_addr+'/sub_collector:deep'

		return sub_col_dict

	def __create_descritptor_service(self,alg_name):

		descriptor_dict = dict()
		descriptor_dict['depends_on'] = ['detector']
		descriptor_dict['env_file'] = ['env_params.list', 'env_ports.list']
		descriptor_dict['environment'] = ['BROKER_ADDRESS='+alg_name+'_broker', 'SUB_COLLECTOR_ADDRESS='+alg_name+'_collector']
		descriptor_dict['networks'] = ['net_deep']
		return descriptor_dict

	def __edit_environment_ALGS(self,s_compose_file,service,algs_env):
	
		path = Path(s_compose_file)
		with open(str(path)) as fp:
			try:
				compose = yaml.load(fp)
			except Exception as e:

				raise e
		
			env_list = compose['services'][service]['environment']
			if env_list is not None:
				old_algs_env= [ x for x in env_list if "ALGS" in x ]
				for env in old_algs_env:
					env_list.remove(env)
				env_list.append(SingleQuotedScalarString('ALGS='+algs_env))
			else:
				compose['services'][service]['environment'] = [SingleQuotedScalarString('ALGS='+algs_env)]

		outf = Path(s_compose_file)
		try:
			with outf.open('w') as ofp:
				yaml.indent(mapping=4)
				yaml.dump(compose, ofp)
		except Exception as e:
			raise e


	def concatenate_ALGS_string(self,alg_dict,with_ports=True):
		algs_list_string = ''
		for alg_name, alg_config in alg_dict.items():
			if with_ports:
				alg_string = self.create_ALGS_string(alg_name,alg_config)
				algs_list_string = algs_list_string + alg_string + ','
			else:
				algs_list_string = algs_list_string + alg_name + ','

		return algs_list_string[:-1]

	def create_ALGS_string(self,alg_name,alg_values):
		ports = alg_values['ports'].replace(',',':')
		alg_string = alg_name +':'+ ports
		return alg_string

	def set_main_compose_variables(self,execution_algs):

		algs_env_collector = self.concatenate_ALGS_string(execution_algs)
		self.__edit_environment_ALGS(MAIN_COMPOSE_FILE, 'face_collector',algs_env_collector)

		algs_env_monitor = self.concatenate_ALGS_string(execution_algs,False)
		self.__edit_environment_ALGS(MAIN_COMPOSE_FILE,'monitor',algs_env_monitor)

		algs_env_server = self.concatenate_ALGS_string(execution_algs,False)
		self.__edit_environment_ALGS(MAIN_COMPOSE_FILE,'server',algs_env_server)



	def set_stream_capture(self, id):
		stream_capture = dict()
		stream_capture['environment'] = [f'STREAM_CAPTURE_ID={id}']
		stream_capture['env_file'] = ['env_params.list', 'env_ports.list']
		stream_capture['image'] = self.reg.insecure_addr+'/stream_capture:deep'
		stream_capture['networks'] = ['net_deep']
		# stream_capture['devices'] = ['/dev/video0:/dev/video0']
		stream_capture['volumes'] = ['/Users/alessandro/Desktop/temp/:/mnt/remote_media']
		return stream_capture

	def set_detector(self, detector_tuple):
		detector = dict()
		image_name,det_mode = detector_tuple
		detector['environment'] = ['COLLECTOR_ADDRESS=face_collector', 'VIDEOSRC_ADDRESS=stream_manager']
		detector['env_file'] = ['env_params.list', 'env_ports.list']
		detector['image'] = self.reg.insecure_addr+'/'+image_name+':deep_'+det_mode
		detector['networks'] = ['net_deep']
		detector['ports'] = ['5559:5559', '5556:5556', '5555:5555']
		# stream_capture['devices'] = ['/dev/video0:/dev/video0']
		return detector

	def ask_detector(self,inter):
		#set detector
		detectors_folders = next(os.walk('detector'))
		detectors_list = detectors_folders[1]

		for det in detectors_list:
			det_files = next(os.walk('detector/'+det))[2]
			gpu_dockerfile_bool = any([True for f in det_files if 'gpu' in f.lower()])
			answer_det = inter.get_acceptable_answer('Do you want to execute '+det+'? y/n: \n',['y','n']).lower()
			if answer_det == 'y':
				if gpu_dockerfile_bool:
					det_mode = inter.get_acceptable_answer('Select mode of execution of '+det+' ? cpu/gpu: \n',['cpu','gpu']).lower()
					return (det,det_mode)
				else:
					return (det,'cpu')


				
		return (detectors_list[0],'cpu')
				
				

        




	def set_compose_images(self,s_compose_file, sources, detector= None):
	
		path = Path(s_compose_file)
		with open(str(path)) as fp:
			try:
				compose = yaml.load(fp)
			except Exception as e:

				raise e
			
			if detector is not None:
				detector_dict = self.set_detector(detector)
				compose['services']['detector'] = detector_dict

			for service, val in compose['services'].items():
				image = val['image']
				image_name = image.split('/')[1] 
				val['image'] = self.reg.insecure_addr +'/'+ image_name
			
			for service_name in list(compose['services'].keys()):
				if service_name.startswith('stream_capture'):
					del compose['services'][service_name]
			if len(sources):
				i = 0
				for id, source in sources:
					stream_capture = self.set_stream_capture(id)
					compose['services'][f'stream_capture_{i}'] = stream_capture
					i += 1


		outf = Path(s_compose_file)
		try:
			with outf.open('w') as ofp:
				yaml.indent(mapping=4)
				yaml.dump(compose, ofp)
		except Exception as e:
			raise e



	def set_compose_algs_variables(self,execution_algs,alg_gpu_matches):
		compose_command_string = ''

		for alg_name, alg_config in execution_algs.items():

			node = alg_gpu_matches[alg_name]
			gpu_id = str(node['gpu_id'])
			if gpu_id == 'None':
				mode = 'cpu'
			else:	
				mode = 'gpu'


			compose_command_string =compose_command_string +' -c '+ alg_config['compose_path']
			alg_compose_file = alg_config['compose_path']
			env_filename = 'compose-files/env_'+alg_name+'.list'

			with open(env_filename, 'w') as out_env:
				out_env.write('FRAMEWORK=' + alg_config['framework'] + '\n')
				out_env.write('GPU_ID=' + gpu_id + '\n')
				out_env.write('MODE=' + mode.upper() + '\n')


			
			path_comp = Path(alg_compose_file)
			with open(str(path_comp)) as path_comp_f:
				try:
					alg_compose = yaml.load(path_comp_f)

				except Exception as e:
					raise e
				services = alg_compose['services']
				if 'version' not in alg_compose.keys():
					alg_compose['version'] = '3'
				for k,v in services.items():
					if 'env_file' in v.keys():
						if env_filename not in v['env_file']:
							v['env_file'].append(env_filename)

					v['deploy']= {'placement':{'constraints': ['node.hostname=='+node['node_name'] ]}}
					if 'descriptor' in k:
						v['image'] = self.reg.insecure_addr+'/'+alg_name +':deep_'+mode

			outf_comp = Path(alg_compose_file)
			try:
				with outf_comp.open('w') as outf_comp_f:
					yaml.indent(mapping=4)
					yaml.dump(alg_compose, outf_comp_f)
			except Exception as e:
				raise e
			


			for serv in services.keys():
				alg_string = self.create_ALGS_string(alg_name,alg_config)
				self.__edit_environment_ALGS(alg_compose_file, serv, alg_string)

		return compose_command_string

		

	def configure(self):

		broker_port, sub_col_port, col_port = 6000,6050,7000
		alg_config = ConfigParser()
		exec_config = ConfigParser()
		installed_algs = dict()
		inter = Interviewer()

		

		#compose_dir = os.path.join(MAIN_DIR,'compose-files')
		compose_dir = 'compose-files'
		if not os.path.exists(compose_dir):
			os.makedirs(compose_dir)

		desc_dir =os.path.join(MAIN_DIR,'descriptor/feature_extractors')
		algs_config_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(desc_dir) for f in filenames if os.path.splitext(f)[1] == '.ini']

		
		for index,config_file in enumerate(algs_config_files):
			alg_config_dict = dict()
			alg_config.read(config_file)
			alg_name = alg_config.get('CONFIGURATION','NAME')
			alg_framework = alg_config.get('CONFIGURATION','FRAMEWORK').lower()
			alg_config_dict['framework'] = alg_framework
			alg_config_dict['ports'] = (broker_port+index, sub_col_port+index, col_port+index)
			compose_path = os.path.join(compose_dir,'docker-compose_'+alg_name+'.yml')
			alg_config_dict['compose_path'] = compose_path
			installed_algs[alg_name] = alg_config_dict
			self.__create_alg_services(compose_path,alg_name)




		for alg_name,alg_config in installed_algs.items():

			answer_alg = inter.get_acceptable_answer('Do you want to execute '+alg_name+' algorythm? y/n: \n',['y','n']).lower()
			if answer_alg == 'y':

				alg_mode = inter.get_acceptable_answer('Select mode of execution of '+alg_name+' algorithm? cpu/gpu: \n',['cpu','gpu']).upper()

				exec_config[alg_name] = {}
				exec_config[alg_name]['alg_mode'] = alg_mode
				exec_config[alg_name]['compose_path'] = alg_config['compose_path']
				exec_config[alg_name]['framework'] = alg_config['framework']
				exec_config[alg_name]['ports'] = ",".join([str(i) for i in alg_config['ports']])


		with open(os.path.join(MAIN_DIR, ALGS_CONFIG_FILE), 'w') as defaultconfigfile:
			exec_config.write(defaultconfigfile)



