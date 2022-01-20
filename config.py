
import os

MAIN_DIR =  os.path.split(os.path.abspath(__file__))[0]
MAIN_COMPOSE_FILE = 'docker-compose_main.yml'
ALGS_CONFIG_FILE = 'initialize/configuration_files/algorithms_configuration.ini'
DETECTOR_CONFIG_FILE = 'initialize/configuration_files//detector_configuration.ini'
CLUSTER_CONFIG_FILE = 'initialize/configuration_files/cluster_configuration.ini'
SOURCES_CONFIG_FILE = 'initialize/configuration_files/sources_configuration.ini'
SERVER_CONFIG_FILE = 'initialize/configuration_files/server_configuration.ini'
MACHINE_CONFIG_FILE = 'initialize/configuration_files/machine_configuration.ini'
DETECTOR_PATH = 'detector/object_extractors'
DESCRITPTOR_PATH = 'descriptor/feature_extractors'
ENV_PARAMS = 'env_params.list'
NETWORK = 'net_deep'
APP_PORT = 8000