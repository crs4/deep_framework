
import os

MAIN_DIR =  os.path.split(os.path.abspath(__file__))[0]
MAIN_COMPOSE_FILE = 'docker-compose_main.yml'
ALGS_CONFIG_FILE = 'initialize/algorithms_configuration.ini'
DETECTOR_CONFIG_FILE = 'initialize/detector_configuration.ini'
CLUSTER_CONFIG_FILE = 'initialize/cluster_configuration.ini'
DETECTOR_PATH = 'detector/object_extractors'
DESCRITPTOR_PATH = 'descriptor/feature_extractors'
ENV_PORTS = 'env_ports.list'
ENV_PARAMS = 'env_params.list'
NETWORK = 'net_deep'
APP_PORT = 8000