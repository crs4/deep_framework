import subprocess
import urllib
import os
import time
import json
import ruamel.yaml
from pathlib import Path
from config import *
import argparse

from configparser import ConfigParser
from initialize.gputils import GPUallocator
from initialize.configurator import Interviewer, Configurator
from initialize.cluster_utils import ClusterManager
from initialize.nodes_utils import Machine,Registry
from initialize.starter import Starter









	


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--run", help="Run with last settings", action="store_true")
	args = parser.parse_args()

	print("### DEEP FRAMEWORK STARTING PROCEDURE ### ")
	if args.run:
		print('Using last configuration and settings...')
	q = Interviewer()
	machine = Machine()
	cluster_manager = ClusterManager()
	registry = Registry()
	conf = Configurator(registry)
	starter = Starter(machine,registry,cluster_manager,use_last_settings=args.run)

	nodes_data = starter.get_nodes()
	
	print(nodes_data)

	filename = 'env_params.list'
	if not args.run:
		source = input('Insert video source address if different from your local webcam: \n')
		max_delay = q.get_number('Insert max delay in seconds you consider acceptable for getting algorithms results (default: 1s): \n','float',1)
		interval_stats = q.get_number('How often do you want to generate statics of execution in seconds? (default: 1s): \n','float',1)
		#timezone = q.get_answer('Please, insert your timezone (default Europe/Rome): \n')
		#if timezone=='':
		#	timezone = 'Europe/Rome'
		with open(filename, 'w') as out:
			out.write('\n' +'SOURCE=' + source + '\n')
			out.write('MAX_ALLOWED_DELAY=' + str(max_delay) + '\n')
			out.write('INTERVAL_STATS=' + str(interval_stats) + '\n')
			#out.write('TZ=' + timezone + '\n')

		config_question = 'Do you want to change default configuration? y/n: \n'
		if not os.path.isfile('./'+ALGS_CONFIG_FILE) or q.get_acceptable_answer(config_question,['y','n']).lower() == 'y':		
			conf.configure()
	else:
		source = ''
		with open(filename) as f:
			content = f.read().splitlines()
			for line in content:
				if line.startswith('SOURCE'):
					source = line.split('=')[1]

	
	execution_algs = starter.get_execution_algs()
	print(execution_algs)

	conf.set_main_compose_variables(execution_algs)

	conf.set_compose_images(MAIN_COMPOSE_FILE, source)


	gpu_alloc = GPUallocator(nodes_data,execution_algs)
	alg_gpu_matches = gpu_alloc.match_algs_gpus()
	print(alg_gpu_matches)

	compose_command_string = conf.set_compose_algs_variables(execution_algs,alg_gpu_matches)

	starter.start_framework(compose_command_string)
	






