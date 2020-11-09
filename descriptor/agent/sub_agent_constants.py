import os


MODE= os.environ['MODE']
GPU_ID= os.environ['GPU_ID']
FRAMEWORK= os.environ['FRAMEWORK']
BROKER_ADDRESS= os.environ['BROKER_ADDRESS']
SUB_COLLECTOR_ADDRESS= os.environ['SUB_COLLECTOR_ADDRESS']
MAX_ALLOWED_DELAY= float(os.environ['MAX_ALLOWED_DELAY'])

BROKER_PORT = os.environ['BROKER_PORT']
SUB_COL_PORT = os.environ['SUB_COL_PORT']

PROT = os.environ['PROT']
MONITOR_ADDRESS = os.environ['MONITOR_ADDRESS']
MONITOR_STATS_IN = os.environ['MONITOR_STATS_IN']
INTERVAL_STATS = float(os.environ['INTERVAL_STATS'])