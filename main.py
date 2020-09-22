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


	sources = starter.manage_sources()
	detector = starter.manage_detector(conf)
	starter.manage_algs(conf)
	starter.manage_standard_images()

	execution_algs = starter.get_execution_algs()


	gpu_alloc = GPUallocator(nodes_data,execution_algs,detector)
	alg_gpu_matches = gpu_alloc.match_algs_gpus()
	print(alg_gpu_matches)

	det = starter.set_detector(alg_gpu_matches)

	conf.set_main_compose_variables(execution_algs)
	conf.set_compose_images(MAIN_COMPOSE_FILE, sources, nodes_data, det)

	"""
	gpu_alloc = GPUallocator(nodes_data,execution_algs)
	alg_gpu_matches = gpu_alloc.match_algs_gpus()
	print(alg_gpu_matches)
	"""

	compose_command_string = conf.set_compose_algs_variables(execution_algs,alg_gpu_matches)
	if not args.run:
		starter.build_and_push(alg_gpu_matches)

	

	starter.start_framework(compose_command_string)
	






