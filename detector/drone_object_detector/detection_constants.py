import cv2

import os


DETECTION_INTERVAL = 1 # number of frames between keypoints detection

max_cosine_distance = 0.3
nn_budget = None
nms_max_overlap = 1.0
base_path = os.path.split(os.path.abspath(__file__))[0]
model_filename = os.path.join(base_path,'models/market1501.pb')





IMAGE_WIDTH = 1280


PROT= os.environ['PROT']
MAX_ALLOWED_DELAY       = float(os.environ['MAX_ALLOWED_DELAY'])
VC_OUT  = os.environ['VC_OUT']
COLLECTOR_ADDRESS       = os.environ['COLLECTOR_ADDRESS']
FP_OUT  = os.environ['FP_OUT']
FP_OUT_TO_COL   = os.environ['FP_OUT_TO_COL']
VIDEOSRC_ADDRESS = os.environ['VIDEOSRC_ADDRESS']
MONITOR_ADDRESS = os.environ['MONITOR_ADDRESS']
MONITOR_STATS_IN = os.environ['MONITOR_STATS_IN']
INTERVAL_STATS = float(os.environ['INTERVAL_STATS'])
GPU_ID = os.environ['GPU_ID']



