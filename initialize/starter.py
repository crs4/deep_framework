
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



	def build_images(self):

		base_com = 'docker build '
		build_utils = base_com + '-t utils:deep utils/'
		build_agent = base_com + '-t agent:deep descriptor/agent'
		build_recog_setup = base_com + '-f descriptor/feature_extractors/face_recognition/Dockerfile.recognition_setup' + ' -t face_recognition_setup:deep descriptor/feature_extractors/face_recognition/'


		build_face_detector  = base_com + '-t '+self.registry+'/face_detection:deep detector/face_detection'
		build_person_detector  = base_com + '-t '+self.registry+'/person_detection:deep detector/person_detection'
		build_object_detector_cpu  = base_com +'-f detector/drone_object_detector/cpu.Dockerfile '+  '-t '+self.registry+'/drone_object_detector:deep_cpu detector/drone_object_detector'
		build_object_detector_gpu  = base_com + +'-f detector/drone_object_detector/gpu.Dockerfile '+ '-t '+self.registry+'/drone_object_detector:deep_gpu detector/drone_object_detector'
		



		build_collector = base_com + '-t '+self.registry+'/collector:deep collector/'
		build_broker = base_com + ' -t '+self.registry+'/broker:deep descriptor/broker'
		build_sub_col = base_com + ' -t '+self.registry+'/sub_collector:deep descriptor/sub_collector'
		build_monitor = base_com + ' -t '+self.registry+'/monitor:deep monitor/'

		build_yaw_cpu = base_com + '-f descriptor/feature_extractors/yaw_detection/Dockerfile.yaw_detection_cpu' + ' -t '+self.registry+'/yaw:deep_cpu descriptor/feature_extractors/yaw_detection/'
		build_recog_cpu = base_com + '-f descriptor/feature_extractors/face_recognition/Dockerfile.recognition_cpu' + ' -t '+self.registry+'/face_recognition:deep_cpu descriptor/feature_extractors/face_recognition/'
		build_age_cpu = base_com + '-f descriptor/feature_extractors/age_detection/Dockerfile.age_cpu' + ' -t '+self.registry+'/age:deep_cpu descriptor/feature_extractors/age_detection'
		build_emotion_cpu = base_com + '-f descriptor/feature_extractors/emotion_detection/Dockerfile.emotion_cpu' + ' -t '+self.registry+'/emotion:deep_cpu descriptor/feature_extractors/emotion_detection/'
		build_gender_cpu = base_com + '-f descriptor/feature_extractors/gender_detection/Dockerfile.gender_cpu' + ' -t '+self.registry+'/gender:deep_cpu descriptor/feature_extractors/gender_detection'
		build_glasses_cpu = base_com + '-f descriptor/feature_extractors/glasses_detection/Dockerfile.glasses_recognition_cpu' + ' -t '+self.registry+'/glasses:deep_cpu descriptor/feature_extractors/glasses_detection/'
		build_pitch_cpu = base_com + '-f descriptor/feature_extractors/pitch_detection/Dockerfile.pitch_detection_cpu' + ' -t '+self.registry+'/pitch:deep_cpu descriptor/feature_extractors/pitch_detection/'

		build_yaw_gpu = base_com + '-f descriptor/feature_extractors/yaw_detection/Dockerfile.yaw_detection_gpu'+ ' -t '+self.registry+'/yaw:deep_gpu descriptor/feature_extractors/yaw_detection/'
		build_recog_gpu = base_com + '-f descriptor/feature_extractors/face_recognition/Dockerfile.recognition_gpu'+ ' -t '+self.registry+'/face_recognition:deep_gpu descriptor/feature_extractors/face_recognition/'
		build_age_gpu = base_com + '-f descriptor/feature_extractors/age_detection/Dockerfile.age_gpu' + ' -t '+self.registry+'/age:deep_gpu descriptor/feature_extractors/age_detection'
		build_emotion_gpu = base_com + '-f descriptor/feature_extractors/emotion_detection/Dockerfile.emotion_gpu' + ' -t '+self.registry+'/emotion:deep_gpu descriptor/feature_extractors/emotion_detection/'
		build_gender_gpu = base_com + '-f descriptor/feature_extractors/gender_detection/Dockerfile.gender_gpu' + ' -t '+self.registry+'/gender:deep_gpu descriptor/feature_extractors/gender_detection'
		build_glasses_gpu = base_com + '-f descriptor/feature_extractors/glasses_detection/Dockerfile.glasses_recognition_gpu' + ' -t '+self.registry+'/glasses:deep_gpu descriptor/feature_extractors/glasses_detection/'
		build_pitch_gpu = base_com + '-f descriptor/feature_extractors/pitch_detection/Dockerfile.pitch_detection_gpu' + ' -t '+self.registry+'/pitch:deep_gpu descriptor/feature_extractors/pitch_detection/'
		
		build_server = base_com + ' -t '+self.registry+'/server:deep server/'
		build_stream_capture = base_com + ' -t '+self.registry+'/stream_capture:deep stream_capture/'
		build_stream_manager = base_com + ' -t '+self.registry+'/stream_manager:deep stream_manager/'
		build_commands = [build_utils,build_agent,build_recog_setup,build_face_detector,build_collector,build_broker,build_sub_col,build_monitor,build_yaw_gpu,build_recog_gpu,build_age_gpu,build_emotion_gpu,build_gender_gpu,build_glasses_gpu,build_pitch_gpu,build_yaw_cpu,build_recog_cpu,build_age_cpu,build_emotion_cpu,build_gender_cpu,build_glasses_cpu,build_pitch_cpu,build_server,build_stream_capture,build_stream_manager,build_person_detector,build_object_detector_cpu,build_object_detector_gpu]
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

		base_com = 'docker push '
		push_face_detector = base_com  +self.registry+'/face_detection:deep'
		push_person_detector = base_com  +self.registry+'/person_detection:deep'
		push_obj_detector_cpu = base_com  +self.registry+'/drone_object_detector:deep_cpu'
		push_obj_detector_gpu = base_com  +self.registry+'/drone_object_detector:deep_gpu'
		push_collector = base_com  +self.registry+'/collector:deep'
		push_broker = base_com  +self.registry+'/broker:deep'
		push_sub_collector = base_com  +self.registry+'/sub_collector:deep'
		push_monitor = base_com  +self.registry+'/monitor:deep'
		push_yaw_cpu = base_com  +self.registry+'/yaw:deep_cpu'
		push_face_recognition_cpu = base_com  +self.registry+'/face_recognition:deep_cpu'
		push_age_cpu = base_com  +self.registry+'/age:deep_cpu'
		push_emotion_cpu = base_com  +self.registry+'/emotion:deep_cpu'
		push_gender_cpu = base_com  +self.registry+'/gender:deep_cpu'
		push_glasses_cpu = base_com  +self.registry+'/glasses:deep_cpu'
		push_pitch_cpu = base_com  +self.registry+'/pitch:deep_cpu'
		push_yaw_gpu = base_com  +self.registry+'/yaw:deep_gpu'
		push_face_recognition_gpu = base_com  +self.registry+'/face_recognition:deep_gpu'
		push_age_gpu = base_com  +self.registry+'/age:deep_gpu'
		push_emotion_gpu = base_com  +self.registry+'/emotion:deep_gpu'
		push_gender_gpu = base_com  +self.registry+'/gender:deep_gpu'
		push_glasses_gpu = base_com  +self.registry+'/glasses:deep_gpu'
		push_pitch_gpu = base_com  +self.registry+'/pitch:deep_gpu'
		push_server = base_com  +self.registry+'/server:deep'
		push_stream_capture = base_com  +self.registry+'/stream_capture:deep'
		push_stream_manager = base_com  +self.registry+'/stream_manager:deep'
		
		push_commands = [push_face_detector,push_person_detector,push_obj_detector_cpu,push_obj_detector_gpu,push_collector,push_broker,push_sub_collector,push_monitor,push_yaw_cpu,push_face_recognition_cpu,push_age_cpu,push_emotion_cpu,push_gender_cpu,push_glasses_cpu,push_pitch_cpu,push_yaw_gpu,push_face_recognition_gpu,push_age_gpu,push_emotion_gpu,push_gender_gpu,push_glasses_gpu ,push_pitch_gpu,push_server,push_stream_capture ,push_stream_manager]
		
		for i,push in enumerate(push_commands):

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