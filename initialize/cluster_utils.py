

from initialize.nodes_utils import LocalNode, RemoteNode, Cluster
from initialize.interviewer import Interviewer

from configparser import ConfigParser
import os
import sys
from config import *




class ClusterManager:



	def __init__(self,machine,registry):
		self.local_node_answered = False
		self.q = Interviewer()
		self.machine = machine
		self.registry = registry

	def create_node(self,node_role = None, cluster = None):
		if not node_role:
			role_node_answer = self.q.get_acceptable_answer("Set the node's role (manager/worker): ", ['manager','worker'])
		else:
			role_node_answer = node_role


		if not self.local_node_answered and self.q.get_acceptable_answer("Is this a local node?: (y/n): ", ['y', 'n']) == 'y':

			node = LocalNode(role_node_answer,self.machine,cluster)
			self.local_node_answered = True
		else:
			ip = self.q.get_ip("ip: ")
			user = self.q.get_answer("username: ")
			port = self.q.get_number("ssh port (default 22): ","int", '22')
			#pulling = self.q.get_acceptable_answer("Do you want to pull docker images?: (y/n): ", ['y', 'n'])
			#node = RemoteNode(ip, user, role_node_answer,pulling, port,cluster)
			node = RemoteNode(ip, user, role_node_answer, self.machine,self.registry,port,cluster)
			dest_folder = self.q.get_remote_folder("Please insert a valid project destination folder: ",user,ip)
			node.dest_folder = dest_folder
			node.start_routine()

		return node




	def manage_cluster(self, use_last_config=False):
		
		cluster_config = ConfigParser()

		
		cluster_filename = os.path.join(MAIN_DIR,CLUSTER_CONFIG_FILE)
		alg_file = os.path.join(MAIN_DIR, ALGS_CONFIG_FILE)
		server_file = os.path.join(MAIN_DIR, SERVER_CONFIG_FILE)
		
		cluster_exist = os.path.isfile(cluster_filename)

		if cluster_exist:
			if use_last_config:
				cluster_config.read(cluster_filename)
				return cluster_config
				
			new_old_answer = self.q.get_acceptable_answer("Cluster configuration file found. Do you want to write a new one? (y/n): \n(Please, first check node's IP has not been changed). \n",['y','n'])
			if new_old_answer == 'n':

				cluster_config.read(cluster_filename)
				
				return cluster_config
			else:
				if os.path.exists(alg_file):
					os.remove(alg_file)

				if os.path.exists(server_file):
					os.remove(server_file)

		
		nodes_number = self.q.get_number('How many nodes? \n','int')

		if nodes_number == 0:
			print('The number must be > 0')
			sys.exit()

		print('Please, insert information of your main cluster manager:')
		top_node = self.create_node('manager')
		cluster = Cluster(self.machine,top_node)
		cluster.initialize()


		for i in range(nodes_number-1):

			print("### NODE NUMBER " +str(i+2) +" ###")
			node = self.create_node(cluster = cluster)
			node.join_swarm()
			cluster.node_list.append(node)

		nodes = cluster.save_cluster(cluster_filename)
		return nodes



