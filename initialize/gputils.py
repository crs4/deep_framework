

import os,sys
import getpass
from ast import literal_eval
import re
import math
import collections
import copy


from initialize.nodes_utils import SSHConnector



class GPUallocator:



	def __init__(self,machine,nodes,algorithms,detector,server):
		self.algs = collections.OrderedDict()
		self.memory_thr = 2000
		self.driver_version_thr = 384.0
		self.nodes = self.__set_allocale_nodes(nodes,server)

		self.__set_algs(detector,algorithms)
		self.num_detector = len(detector)
		self.machine = machine

	
	def __set_allocale_nodes(self,nodes,server):
		allocable_nodes = dict()
		server_node = server['node']
		server_isolate = server['isolate']
		if server['isolate'] == 'n':
			allocable_nodes = nodes
		else:
			for node, node_value in nodes.items():
				if node != server_node:
					allocable_nodes[node] = node_value

		return allocable_nodes



	def __set_algs(self,detectors,algorithms):
		"""
		This method creates an ordered dict with detector on the top.
		In this way, detector has higher priority in GPU allocation.
		"""
		self.detector_framework = []
		for det in detectors:
			source_id = det['source_id']
			det['type'] = 'detector'
			framework = det['framework']
			det_name = det['name']
			det_source = det_name + '_' + source_id
			mode = det['mode']
			if framework != 'None':
				self.detector_framework.append(framework)

			self.algs[det_source] = det

		for alg in algorithms:
			alg_dict = dict()
			alg['type'] = 'descriptor'
			alg_name = alg['name']
			source_id = alg['source_id']
			desc_source = alg_name + '_' + source_id

			alg_dict[desc_source] = alg

			self.algs.update(alg_dict)

		self.original_algs = copy.deepcopy(self.algs)



	def __check_gpu_exists_and_suitable(self,node_name,node):
		
		if node['cuda_version'] == 'None':
			#print('Node %s: GPU not detected in this node.' % (node_name))
			return False

		return True

	def __format_cuda_version(self, cuda_version):
		cuda_version = 
		cuda_acc = 0
		cuda_num = 0
		cuda_split = cuda_version.split('.')
		if cuda_version == 'None':
			return -1
		if len(cuda_split) == 3:
			#cuda_acc = cuda_split[1] + '.' + cuda_split[2]
			cuda_num = float(cuda_split[0]) + float(cuda_split[1])
			return cuda_num

		else:
			return float(cuda_version)

		

	def __get_gpus(self):

		nodes_gpu_info = dict()
		for node_name, node in self.nodes.items():
			nodes_gpu_info[node_name] = node
			node_gpus = []
			self.connection = SSHConnector(node['ip'], node['user'], self.machine.SSH_KEY)
			suitable = self.__check_gpu_exists_and_suitable(node_name,node)
			if suitable:
				command = 'echo -e "import GPUtil\nGPUs = GPUtil.getGPUs()\nfor gpu in GPUs: print(gpu.__dict__)" | python3'
				data = self.connection.send_remote_command(command, ignore_err = True)
				if data != '[]':
					d = "}"
					for line in data.split(d)[:-1]:
						node_gpu_dict = literal_eval(line+d)
						node_gpus.append(node_gpu_dict)
				else:
					node_gpus = None
			else:
				node_gpus = None
			
			

			nodes_gpu_info[node_name]['gpus'] = node_gpus
			nodes_gpu_info[node_name]['cuda_version'] =   self.__format_cuda_version(node['cuda_version'])


		return nodes_gpu_info

	def __create_gpu_order(self, gpu_elegibles, frameworks):
		total_capacity = None
		gpu_order = []
		while total_capacity != 0:
			total_capacity = 0
			fr_index = 0

			for node_name, gpu_availables in gpu_elegibles.items():

				for gpu in gpu_availables:

					total_capacity = total_capacity + gpu['net_capacity']
					if gpu['net_capacity'] > 0:
						if not fr_index < len(frameworks):
							fr_index = 0
						gpu_order.append((node_name,gpu['gpu_id'],frameworks[fr_index],gpu['cuda_version']))
						gpu['net_capacity'] -= 1
						fr_index+=1

		return gpu_order

	def __check_to_build(self, matches):

		for k_alg, v_alg in self.original_algs.items():

			alg_type = v_alg['type']
			alg_mode = v_alg['mode']
			alg_name = v_alg['name']

			if alg_type == 'detector':
				alg_matched = [ alg_matched for alg_matched in matches['detectors'] if alg_matched['name'] == alg_name][0]
			else:
				alg_matched = [ alg_matched for alg_matched in matches['descriptors'] if alg_matched['name'] == alg_name][0]

			if alg_matched['mode'] != alg_mode:
				alg_matched['to_build'] = 'y'


	def match_algs_gpus(self):

		nodes_gpu = self.__get_gpus()
		gpu_elegibles = dict()
		cpu_elegibles = []
		gpu_order = []
		for knode,vnode in nodes_gpu.items():

			if vnode['gpus'] is not None:
				gpu_elegibles[knode] = [ {'gpu_id':gpu['id'],'cuda_version':vnode['cuda_version'] ,'net_capacity':math.floor(gpu['memoryFree']/self.memory_thr)} for gpu in vnode['gpus'] if gpu['memoryFree'] > self.memory_thr]
				#{'strix': [{'gpu_id': 0, 'net_capacity': 3},{'gpu_id': 1, 'net_capacity': 3}]}
			else:
				cpu_elegibles.append(knode)

		if len(cpu_elegibles) == 0:
			cpu_elegibles = list(nodes_gpu.keys())

		num_detector_frameworks = len(self.detector_framework)
		if num_detector_frameworks > 0:
			temp_gpu_frameworks = list(set([ v_alg['framework'] for v_alg in self.algs.values() if v_alg['mode'] == 'gpu' and v_alg['framework'] not in self.detector_framework ]))
		else:
			temp_gpu_frameworks = list(set([ v_alg['framework'] for v_alg in self.algs.values() if v_alg['mode'] == 'gpu']))

		
		gpu_frameworks = self.detector_framework + temp_gpu_frameworks
		
		
		if len(gpu_frameworks) > 0:
			gpu_order = self.__create_gpu_order(gpu_elegibles,gpu_frameworks)

		matches = collections.OrderedDict()
		matches['detectors'] = []
		matches['descriptors'] = []
		cpu_node_index = 0
		for i,(k_alg, v_alg) in enumerate(self.algs.items()):
			

			alg_mode = v_alg['mode']
			alg_framework = v_alg['framework']
			alg_cuda = self.__format_cuda_version(v_alg['cuda_version'])
			alg_index = [gpu_order.index(el) for el in gpu_order if el[2] == alg_framework and alg_cuda <= el[3]]

			if alg_mode == 'gpu' and len(gpu_order) > 0 and len(alg_index) > 0:
				node_name, gpu_id, gp_framework, cuda= gpu_order.pop(alg_index[0])
				v_alg['mode'] = 'gpu'
			else:
				if not cpu_node_index < len(cpu_elegibles):
					cpu_node_index = 0

				node_name = cpu_elegibles[cpu_node_index]

				cpu_node_index+=1
				gpu_id = None
				v_alg['mode'] = 'cpu'

			
			if 'dockerfiles' in v_alg.keys() and all(v_alg['mode'] not in dock for dock in v_alg['dockerfiles']):
				print("The algorithm "+ v_alg['name'] + " can't be executed due to the lack of the necessary dockerfile (Dockerfile."+v_alg['mode']+") or of a node with the correct version of the cuda driver.")
				if v_alg['type'] == 'descriptor':
					break
				else:
					sys.exit(0)

			v_alg['deploy'] = {'node_name': node_name, 'gpu_id': gpu_id}
			if i < self.num_detector:
				matches['detectors'].append(v_alg)
			else:
				matches['descriptors'].append(v_alg)


		
		self.__check_to_build(matches)
		


		return matches
		





