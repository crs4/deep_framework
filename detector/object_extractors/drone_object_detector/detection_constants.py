import cv2

import os


DETECTION_INTERVAL = 1 # number of frames between keypoints detection

max_cosine_distance = 0.3
nn_budget = None
nms_max_overlap = 1.0
base_path = os.path.split(os.path.abspath(__file__))[0]
model_filename = os.path.join(base_path,'models/market1501.pb')





IMAGE_WIDTH = 1280





