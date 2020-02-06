

import os,sys
import getpass
from ast import literal_eval
import re
import math
from initialize.nodes_utils import SSHConnector,Machine



class GPUallocator(Machine):



	def __init__(self,nodes,algorithms):
		Machine.__init__(self)
		self.nodes = nodes
		self.algs = algorithms
		self.memory_thr = 2000
		self.driver_version_thr = 384.0


	def __check_gpu_exists_and_suitable(self,node_name):
		data = self.connection.send_remote_command('nvidia-smi', ignore_err = True)
		if data == '':
			print('Node %s: no GPU detected on this node.' % (node_name))
			return False

		index = data.find('Driver Version')
		non_decimal = re.compile(r'[^\d.]+')
		temp_version = data[index+16:index+30]
		driver_version = float(non_decimal.sub('', temp_version))
		if driver_version < self.driver_version_thr:
			print('Node %s: NVIDIA DRIVER version %s is too old. This node will be used in CPU mode.' % (node_name,driver_version))
			return False

		try:
			mb = re.search('MB / (.*)MB', data)
			mb = mb.group(1)
		except:
			mb = re.search('MiB / (.*)MiB', data)
			mb = mb.group(1)
		
		total_memory = int(mb)

			

		if total_memory < self.memory_thr:
			print('Node %s: detected GPU with no sufficient memory. Required %s at least. This node will be used in CPU mode.' % (node_name,str(self.memory_thr)))
			return False

		return True





	def __get_gpus(self):

		nodes_gpu_info = dict()
		for node_name, node in self.nodes.items():
			nodes_gpu_info[node_name] = node
			node_gpus = []
			self.connection = SSHConnector(node['ip'], node['user'], self.SSH_KEY)
			suitable = self.__check_gpu_exists_and_suitable(node_name)
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
						gpu_order.append((node_name,gpu['gpu_id'],frameworks[fr_index]))
						gpu['net_capacity'] -= 1
						fr_index+=1

		return gpu_order


	def match_algs_gpus(self):

		nodes_gpu = self.__get_gpus()
		gpu_elegibles = dict()
		cpu_elegibles = []
		gpu_order = []
		for knode,vnode in nodes_gpu.items():

			if vnode['gpus'] is not None:
				gpu_elegibles[knode] = [ {'gpu_id':gpu['id'], 'net_capacity':math.floor(gpu['memoryFree']/self.memory_thr)} for gpu in vnode['gpus'] if gpu['memoryFree'] > self.memory_thr]
				#{'strix': [{'gpu_id': 0, 'net_capacity': 3},{'gpu_id': 1, 'net_capacity': 3}]}
			else:
				cpu_elegibles.append(knode)

		if len(cpu_elegibles) == 0:
			cpu_elegibles = list(nodes_gpu.keys())


		gpu_frameworks = list(set([ v_alg['framework'] for v_alg in self.algs.values() if v_alg['alg_mode'] == 'GPU']))
		

		if len(gpu_frameworks) > 0:
			gpu_order = self.__create_gpu_order(gpu_elegibles,gpu_frameworks)
		
		
		matches = dict()
		cpu_node_index = 0
		for k_alg, v_alg in self.algs.items():

			alg_mode = v_alg['alg_mode']
			alg_framework = v_alg['framework']
			alg_index = [gpu_order.index(el) for el in gpu_order if el[2] == alg_framework]

			if alg_mode == 'GPU' and len(gpu_order) > 0 and len(alg_index) > 0:
				node_name, gpu_id, gp_framework= gpu_order.pop(alg_index[0])
			else:
				if not cpu_node_index < len(cpu_elegibles):
					cpu_node_index = 0

				node_name = cpu_elegibles[cpu_node_index]

				cpu_node_index+=1
				gpu_id = None

			matches[k_alg] = {'node_name': node_name, 'gpu_id': gpu_id}

		return matches
		





