import cv2

import os


PROT= os.environ['PROT']
MAX_ALLOWED_DELAY	= float(os.environ['MAX_ALLOWED_DELAY'])
STREAM_OUT	= os.environ['STREAM_OUT']
COLLECTOR_ADDRESS	= os.environ['COLLECTOR_ADDRESS']
FP_OUT	= os.environ['FP_OUT']
FP_OUT_TO_COL	= os.environ['FP_OUT_TO_COL']
VIDEOSRC_ADDRESS = os.environ['VIDEOSRC_ADDRESS']
MONITOR_ADDRESS = os.environ['MONITOR_ADDRESS']
MONITOR_STATS_IN = os.environ['MONITOR_STATS_IN']
INTERVAL_STATS = float(os.environ['INTERVAL_STATS'])
