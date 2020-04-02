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
		change_params_answer =  'y'
		if os.path.isfile('./'+filename):
			change_params_question = 'Do you want to change streaming params? (y/n): \n'
			change_params_answer = q.get_acceptable_answer(change_params_question,['y','n']).lower()
		if  change_params_answer == 'y':
			max_delay = q.get_number('Insert max delay in seconds you consider acceptable for getting algorithms results (default: 1s): \n','float',1)
			interval_stats = q.get_number('How often do you want to generate statics of execution in seconds? (default: 1s): \n','float',1)
			#timezone = q.get_answer('Please, insert your timezone (default Europe/Rome): \n')
			#if timezone=='':
			#	timezone = 'Europe/Rome'
			add_video_source = 'Do you want to add a video source? (y/n): \n'
			sources = []
			while q.get_acceptable_answer(add_video_source,['y','n']).lower() == 'y':
				source = input('Insert video source address/url/path: \n')
				id = input('Give a unique name/ID to this video source: \n')
				sources.append((id, source))

			with open(filename, 'w') as out:
				out.write('MAX_ALLOWED_DELAY=' + str(max_delay) + '\n')
				out.write('INTERVAL_STATS=' + str(interval_stats) + '\n')
				#out.write('TZ=' + timezone + '\n')
				for id, source  in sources:
					out.write('\nSOURCE_' + id + '=' + source + '\n')
	else:
		sources = []
		with open(filename) as f:
			content = f.read().splitlines()
			for line in content:
				if line.startswith('SOURCE_'):
					id = line.split('=')[0][7:]
					source = line[len(id) + 1:]
					sources.append((id, source))

	if not args.run:

		config_question = 'Do you want to change default configuration? y/n: \n'
		if not os.path.isfile('./'+ALGS_CONFIG_FILE) or q.get_acceptable_answer(config_question,['y','n']).lower() == 'y':		
			conf.configure()

	
	execution_algs = starter.get_execution_algs()
	print(execution_algs)

	conf.set_main_compose_variables(execution_algs)

	conf.set_compose_images(MAIN_COMPOSE_FILE, sources)


	gpu_alloc = GPUallocator(nodes_data,execution_algs)
	alg_gpu_matches = gpu_alloc.match_algs_gpus()
	print(alg_gpu_matches)

	compose_command_string = conf.set_compose_algs_variables(execution_algs,alg_gpu_matches)

	starter.start_framework(compose_command_string)
	






