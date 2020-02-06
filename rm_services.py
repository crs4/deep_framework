from configparser import ConfigParser
import sys
import os
import subprocess
from config import *

cluster_filename = os.path.join(MAIN_DIR,CLUSTER_CONFIG_FILE)
cluster_config = ConfigParser()

cluster_exist = os.path.isfile(cluster_filename)

if cluster_exist:
	cluster_config.read(cluster_filename)
	cluster_dict = dict()
	for section in cluster_config.sections():
		node_dict = dict()
		for key, val in cluster_config.items(section):
			node_dict[key] = val

		cluster_dict[section] = node_dict

	nodes = list(cluster_dict.keys())
	top_manager_node = [cluster_dict[node] for node in nodes if cluster_dict[node]['role'] == 'manager'][0]
	stop_command = 'docker stack rm deepframework'
	if top_manager_node['type'] == 'RemoteNode':
		stop_command = "ssh %s@%s 'cd %s && %s'" % (top_manager_node['user'], top_manager_node['ip'], top_manager_node['path'], stop_command)

	try:
		result = subprocess.Popen([stop_command], shell=True)
		result.communicate()
		if result.returncode == 0:
			print('DEEP Framework STOPPED.')
	except Exception as e:
		raise e
else:
	print('ERROR: no cluster configuration file found.')
	sys.exit()
