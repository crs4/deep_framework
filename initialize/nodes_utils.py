from pathlib import Path

from config import *


import subprocess

from abc import ABC, abstractmethod

import os
import sys
import subprocess
import argparse
import socket
import getpass
import json
import time
import shlex
from configparser import ConfigParser




from paramiko import client

#MAIN_DIR =  os.path.split(os.path.abspath(__file__))[0]



class SSHConnector:
	client = None

	def __init__(self, address, username,key_path):
		self.client = client.SSHClient()

		self.client.set_missing_host_key_policy(client.AutoAddPolicy())
		self.client.connect(hostname=address, username=username, key_filename=key_path)
		#self.client.connect(hostname=address, username=username, password=key_path)
		if self.client.get_transport() is not None:
			active = self.client.get_transport().is_active()
			if not active:
				print('Connection problem')

	def _read_command_output(self, stdout, stderr, ret_mode):
		"""Read result of not-interactive command execution.
        Args:
			stdout(str):  StdOut info
			stderr(str):  StdErr info
			ret_mode(str):  return mode. both|stderr|stdout
        """
		if ret_mode.lower() == 'both':
			return stdout.read(),stderr.read()
		elif ret_mode.lower() == 'stderr':
			return stderr.read()
		else:
			return stdout.read()


	def send_remote_command(self, command, ignore_err = False):
		if(self.client):
			stdin, stdout, stderr = self.client.exec_command(command)
			data, err = self._read_command_output(stdout, stderr, 'both')
			data = str(data, "utf8").strip('\n')
			err = str(err, "utf8").strip('\n')
			if err and not ignore_err:
				print('Error: ', err)
				print('Command failed: ', command)
				sys.exit(0)
			return data
		else:
			print("Connection not opened.")

	def copyTo(self,local_file_path, remote_file_path):

		ftp_client = self.client.open_sftp()
		ftp_client.put(local_file_path,remote_file_path)
		ftp_client.close()

	def close_connection(self):
		self.client.close()




class Machine:

	def __init__(self):
		self.get_hostname_command = "hostname"
		self.CUR_USER = getpass.getuser()
		self.cur_dir = MAIN_DIR
		self.PLATFORM = sys.platform
		if self.PLATFORM == "darwin":
		    self.PRIV_SSH_DIR = "/Users/%s/.ssh" % (self.CUR_USER)
		elif self.PLATFORM == "linux":
		    self.PRIV_SSH_DIR = "/home/%s/.ssh" % (self.CUR_USER)
		self.SSH_KEY = os.path.join(self.PRIV_SSH_DIR,'id_rsa')

	
	
	def exec_shell_command(self,command, ignore_err = True):
		try:
			p = subprocess.Popen(command, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
			(output, err) = p.communicate()
			if not ignore_err and err:
				err = str(err.decode("utf-8").strip('\n'))
				raise Exception(err)
			return str(output.decode("utf-8").strip('\n'))
		except Exception as e:
			print('Error: ', e)
			print('Command failed: ', command)
			sys.exit(0)
	
	"""
	def exec_shell_command(self,command, exit = True, ignore_error = False):
		p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()
		
		if not err:
			output = str(output.decode("utf-8").strip('\n'))
			return output

		err = str(err.decode("utf-8").strip('\n'))
		if 'closed' in err:
			return

		if not ignore_error:
			if exit is False:
				return err
			else:
				print('Error: ', err)
				print('Command failed: ', command)
				print('Exiting...')
				sys.exit(0)
	"""

	def check_daemon_is_running(self, remote_prefix = None):
		info_command = 'docker info'
		if remote_prefix is not None:
			info_command = remote_prefix + info_command

		docker_is_active = False
		attempts_start = time.time()
		attempts_end = 0
		while not docker_is_active and attempts_end < 300:
			#res = self.exec_shell_command(info_command, exit = False)
			res = self.exec_shell_command(info_command)
			time.sleep(3)
			if res == '':
				attempts_end = time.time() - attempts_start
			else:
				docker_is_active = True
		return docker_is_active

			

	

	


	def get_ip(self):
		ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
		if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), 
		s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, 
		socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
		return ip

	
		

	def gen_key(self):
		"""Generate a SSH Key."""
		os.chdir(self.PRIV_SSH_DIR)
		if "id_rsa" in os.listdir(self.PRIV_SSH_DIR):
			print("A key is already present.")
		else:
			# Genarate private key
			subprocess.call('ssh-keygen -t rsa -b 4096 -m PEM', shell=True)
		os.chdir(self.cur_dir)

	def push_key(self,port,user,ip):
		"""Push a SSH Key to a remote server."""
		print('Pushing keys....')
		os.chdir(self.PRIV_SSH_DIR)
		if "id_rsa" in os.listdir(self.PRIV_SSH_DIR):
			try:
				print("SSH key found. Pushing key to remote server")
				command = "ssh-copy-id -p %s %s@%s" % (port, user,ip)
				subprocess.call(command, shell=True)
			except Exception as e:
				print(
				"ssh-copy-id required for Mac Users. Use --help for more information." + str(e))
		else:
			print("A SSH key is required. Run script again with action set as GenKey")
		os.chdir(self.cur_dir)

	def get_hostname(self):
		return self.exec_shell_command(self.get_hostname_command)


	
class Node(Machine):
		
	def __init__(self, role, cluster = None):
		Machine.__init__(self)
		self.machine = super(Node,self)
		self.role = role
		self.cluster = cluster
		if cluster:
			self.token = self.cluster.get_token(self.role)
			self.join_command = "docker swarm join --token %s %s:2377" % (self.token, self.cluster.main_cluster_manager_node.ip)
		self.leave_command = "docker swarm leave --force"
		


	def join_swarm(self):
		print("Joining node..")
		self.machine.exec_shell_command(self.join_command)
		

	def leave_swarm(self):
		try:
			print('Checking if node is already part of cluster and leaving...')
			self.machine.exec_shell_command(self.leave_command)
		except Exception as e:
			print(e)



	




	


class LocalNode(Node):
	def __init__(self, role,cluster = None):
		Node.__init__(self,role,cluster)
		Machine.gen_key(self)
		self.ip = Machine.get_ip(self)
		self.hostname = Machine.get_hostname(self)
		self.user = getpass.getuser()
		Machine.push_key(self,'22',self.user,self.ip)
		self.working_path = MAIN_DIR
		self.leave_swarm()



	


class RemoteNode(Node):

	def __init__(self, ip, user, role, ssh_port = 22, cluster = None):
		Node.__init__(self,role,cluster)
		self.machine = super(Node,self)
		self.machine.push_key(ssh_port,user,ip)
		self.connection = SSHConnector(ip, user, self.SSH_KEY)
		self.user = user
		self.ip = ip
		self.ssh_port = str(ssh_port)
		self.hostname = Machine.get_hostname(self)
		#self.pull = True if pull == 'y' else False
		self.leave_swarm()
		self.dest_folder = None
		self.registry = Registry()
		


	def start_routine(self):
		self.platform = self.__check_platform()
		self.working_path = os.path.join(self.dest_folder,'deep_framework')
		self.__prepare_working_env()
		self.__mod_insecure_registry()
 
		#if self.pull:
			#self.__pull_images()
	
		self.__install_GPUtil()



	

	def __prepare_working_env(self):
		exist = self.__exists_remote_path(self.working_path)
		if not exist:
			print('Creating folder deep_framework on remote node...')
			command = "ssh %s@%s mkdir -p %s" % (self.user, self.ip, self.working_path)
			#copy_pull_com = "scp -q -p docker_pull.sh %s@%s:%s" %(self.user,self.ip,self.working_path)
			self.machine.exec_shell_command(command) ##### CHECK IF SENDCOMMAND
			#self.machine.exec_shell_command(copy_pull_com)
			
			

	def __exists_remote_path(self,path):
		"""Test if a file exists at path on a host accessible with SSH."""
		try:
			option = 'd'
			if '.'in path:
				option = 'f'
			command = "[[ -"+option+" %s ]] && echo 'Exists' || echo 'Error'"  % (path)
			output = self.connection.send_remote_command(command)
			
			if "Exists" in output:
				return True
			else:
				return False
		except Exception as e:
			raise e

	

	def __install_GPUtil(self):

		try:
			print('Installing GPUtil on your remote node. Please type node password:\nPassword: ')
			com = 'ssh -t %s@%s "sudo apt -y install python3-pip"' % (self.user,self.ip)
			command = "pip3 install gputil"
			self.machine.exec_shell_command(com)
			output = self.connection.send_remote_command(command, ignore_err=True)
		except Exception as e:
			raise e


	def __pull_images(self):

		print('Pulling docker images...')
		try:

			command = 'cd %s && ./docker_pull.sh %s' % (self.working_path, self.registry.insecure_addr)
			output = self.connection.send_remote_command(command)
			print(output)
		except Exception as e:
			raise e

	def __check_platform(self):
		command_platform = 'echo -e "import sys\nprint(sys.platform)" | python3'
		platform = self.connection.send_remote_command(command_platform)
		return platform

	def __mod_insecure_registry(self):

		try:
			
			if self.platform == "darwin":
				remote_daemon_path = "/Users/%s/.docker/daemon.json" % (self.user)
				docker_restart_command = "osascript -e 'quit app \"Docker\"'; open -a Docker ;"
			elif self.platform == "linux":
				remote_daemon_path = '/etc/docker/daemon.json'
				docker_restart_command = "sudo service docker restart"
			
			print('Please, type your remote node password in order to check docker configuration:\nPassword:')
			command = 'ssh -t %s@%s "if sudo test -f "%s"; then sudo cat %s; else echo "Error"; fi"' % (self.user,self.ip,remote_daemon_path,remote_daemon_path)
			
			
			output = self.machine.exec_shell_command(command)
			
			
			with open('deep_daemon.json', 'w') as outfile:

				if 'Error' not in output:
					import re

					result = re.search('(.*):', output).group(0)
					output = output.strip(result)
					
					data_json = json.loads(output)
					if 'insecure-registries' in list(data_json.keys()):
						ins = data_json['insecure-registries']
						if self.registry.insecure_addr not in ins:
							ins.append(self.registry.insecure_addr)

					else:
						data_json["insecure-registries"] = [self.registry.insecure_addr]
				else:
					data_json = {"insecure-registries":[self.registry.insecure_addr]}


				json.dump(data_json, outfile)

			print('Please, type your password in order to configure the docker daemon on your remote node:\nPassword:')
			save_command = 'scp -q deep_daemon.json %s@%s:.  && rm deep_daemon.json' % (self.user,self.ip)
			mv_command = 'ssh -t %s@%s "sudo mv deep_daemon.json %s && %s"' % (self.user,self.ip,remote_daemon_path,docker_restart_command)
			self.machine.exec_shell_command(save_command)
			self.machine.exec_shell_command(mv_command)
			prefix = 'ssh %s@%s ' % (self.user,self.ip)
			running = self.machine.check_daemon_is_running(prefix)
			if not running:
				print('Error while restarting docker daemon')
				sys.exit(0)

		except Exception as e:
			raise e


	def join_swarm(self):
		output = self.connection.send_remote_command(self.join_command)

	def leave_swarm(self):
		check_swarm_command = "docker info --format '{{.Swarm.LocalNodeState}}'"

		check_output = self.connection.send_remote_command(check_swarm_command)
		if check_output == 'active':
			output = self.connection.send_remote_command(self.leave_command)
		

class Cluster:

	def __init__(self,top_node):
		self.main_cluster_manager_node = top_node
		self.node_list = [top_node]



	def initialize(self):
		try:
			command = "docker swarm init  --advertise-addr %s" %(self.main_cluster_manager_node.ip)
			if type(self.main_cluster_manager_node).__name__ ==  'RemoteNode':
				self.main_cluster_manager_node.connection.send_remote_command(command)
			else:
				subprocess.call(command, shell=True)
		except Exception as e:
			print(e)

	def get_token(self, token_type):
	
		try:
			command ="docker swarm join-token "+token_type+" -q"
			if type(self.main_cluster_manager_node).__name__ ==  'RemoteNode':
				output = self.main_cluster_manager_node.connection.send_remote_command(command)			
				return output
			else:
				p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
				(output, err) = p.communicate()
				return output.decode("utf-8").strip('\n')
		except Exception as e:
			print(e)

	def get_cluster_data(self):
		data = dict()
		command = "docker node ls --quiet"
		ins_command = "docker node inspect "
		if type(self.main_cluster_manager_node).__name__ ==  'RemoteNode':
			nodes_id = self.main_cluster_manager_node.connection.send_remote_command(command).split('\n')
		else:
			nodes_id = Machine.exec_shell_command(self,command).split('\n')

		for node in nodes_id:
			if type(self.main_cluster_manager_node).__name__ ==  'RemoteNode':
				node_ins = self.main_cluster_manager_node.connection.send_remote_command(ins_command + node)
			else:
				node_ins = Machine.exec_shell_command(self,ins_command + node)

			j_ins = json.loads(node_ins)[0]
			node_addr = j_ins['Status']['Addr']
			node_host = j_ins["Description"]["Hostname"]
			data[node_addr] = node_host

		return data


	def save_cluster(self,cluster_filename):
		data = self.get_cluster_data()
		

		cluster_config = ConfigParser()

		for node in self.node_list:
			node_dict = dict()
			node_dict['user'] = node.user
			node_dict['ip'] = node.ip
			node_dict['role'] = node.role
			node_dict['type'] = type(node).__name__
			node_dict['path'] = node.working_path
			docker_hostname = data[node.ip]
			cluster_config[docker_hostname] = node_dict

		with open(cluster_filename, 'w') as configfile:
			cluster_config.write(configfile)

		return cluster_config





class Registry(Machine):

	def __init__(self):
		Machine.__init__(self)
		self.address = Machine.get_ip(self)
		if self.PLATFORM == "darwin":
			self.daemon_path = "/Users/%s/.docker/daemon.json" % (self.CUR_USER)
			self.docker_restart_command = "osascript -e 'quit app \"Docker\"'; open -a Docker ;"
		elif self.PLATFORM == "linux":

			self.daemon_path = '/etc/docker/daemon.json'
			self.docker_restart_command = "sudo service docker restart"


		self.insecure_addr = self.address+':5000'


	

	def manage_docker_daemon_json(self):
		restart = True
		daemon_file = Path(self.daemon_path)
		temp_file = os.path.join(MAIN_DIR,'temp.json')
		mv_com = 'sudo mv '+temp_file+ ' ' + self.daemon_path
		try:
			com = 'sudo cat ' + self.daemon_path
			daemon = Machine.exec_shell_command(self,com)
			data = json.loads(daemon)
			if 'insecure-registries' in data.keys():
				ins = data['insecure-registries']
				if self.insecure_addr not in ins:
					ins.append(self.insecure_addr)
				else:
					restart = False
			else:
				data['insecure-registries'] = [self.insecure_addr]


		except Exception as e:
			data = { "insecure-registries" : [self.insecure_addr]}
		
		if restart:
			with open(temp_file, 'w', encoding='utf-8') as f:
				json.dump(data, f)

			Machine.exec_shell_command(self,mv_com + ' && ' +self.docker_restart_command)
			print('Loading docker configuration...')
			running = Machine.check_daemon_is_running(self)
			if not running:
				print('Error while restarting docker daemon')
				sys.exit(0)
			print('Loaded.')
		



	def check_registry_running(self):
		command = "curl -I -k -s http://"+self.insecure_addr +"/ | head -n 1 | cut -d ' ' -f 2"
		res = Machine.exec_shell_command(self,command)
		if res == '200':
			return True
		else:
			return False

	def start_registry(self):
		command = "docker run -d -p 5000:5000 --restart=always --name registry registry:2"
		Machine.exec_shell_command(self,command)
		print('Starting docker....')
		registry_up = False
		attempts_start = time.time()
		attempts_end = 0
		while not registry_up and attempts_end < 100:
			registry_up = self.check_registry_running()
			time.sleep(2)
			attempts_end = time.time() - attempts_start
		print('Registry started.')

	def stop_registry(self):
		command = "docker container stop registry && docker container rm -v registry"
		Machine.exec_shell_command(self,command)
		time.sleep(5)
		with open(self.daemon_path, 'r', encoding='utf-8') as f:
			data = json.load(f)
			ins = data['insecure-registries']
			if self.insecure_addr in ins:
				ins.remove(self.insecure_addr)
				f.seek(0)
				json.dump(data, f)
				f.truncate()







if __name__ == "__main__":
	addr = '192.168.1.40'
	user = 'alessandro'
	conn = SSHConnector(addr,user,'/Users/alessandro/.ssh/id_rsa')
	res = conn.send_remote_command('nvidia-smi',ignore_err = True)

	ind = res.find('Driver Version')
	inter = res[ind+16:ind+30].strip(' ')

	import re

	s = 'asdf=5;iwantthis123jasd'
	result = re.search('MB / (.*)MB', res)

	mem = result.group(1)


	print(mem)




	
