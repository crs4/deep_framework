
import os

MAIN_DIR =  os.path.split(os.path.abspath(__file__))[0]
MAIN_COMPOSE_FILE = 'docker-compose_main.yml'
ALGS_CONFIG_FILE = 'initialize/algorithms_configuration.ini'
DETECTOR_CONFIG_FILE = 'initialize/detector_configuration.ini'
CLUSTER_CONFIG_FILE = 'initialize/cluster_configuration.ini'
APP_PORT = 8000