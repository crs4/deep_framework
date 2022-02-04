

import argparse

import os
import platform
import shutil
import time
from pathlib import Path
import cv2
import torch
import torch.backends.cudnn as cudnn
import numpy as np


import sys
sys.path.insert(0, './yolov5')

from person_constants import *

from utils.downloads import attempt_download
from models.common import DetectMultiBackend
from utils.general import (LOGGER, check_img_size, non_max_suppression, scale_coords, 
                                  check_imshow, xyxy2xywh, increment_path)
from utils.augmentations import letterbox
from utils.torch_utils import select_device, time_sync
from utils.plots import Annotator, colors

class PersonDetector:

    def __init__(self):

        cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.__setup_detector()


    def __setup_detector(self):
        # Load model
        from person_constants import HALF, DEVICE, YOLO_MODEL, IMGSZ

        self.device = select_device(DEVICE)
        self.yolo_model = DetectMultiBackend(YOLO_MODEL, device=self.device, dnn=False)

        stride, names, pt, jit, _ = self.yolo_model.stride, self.yolo_model.names, self.yolo_model.pt, self.yolo_model.jit, self.yolo_model.onnx
        IMGSZ *= 2 if len(IMGSZ) == 1 else 1  # expand
        imgsz = check_img_size(IMGSZ, s=stride)  # check image size
        
        
        # Half
        HALF &= pt and self.device.type != 'cpu'  # half precision only supported by PyTorch on CUDA
        if pt:
            self.yolo_model.model.half() if HALF else self.yolo_model.model.float()

        # Get names and colors
        self.names = self.yolo_model.module.names if hasattr(self.yolo_model, 'module') else self.yolo_model.names

        if pt and self.device.type != 'cpu':
            self.yolo_model(torch.zeros(1, 3, *imgsz).to(self.device).type_as(next(self.yolo_model.model.parameters())))  # warmup
    
    def preprocess_image(self, img0, img_size=640, stride=32, auto=True):
        # Padded resize
        img = letterbox(img0, img_size, stride, auto=auto)[0]
        # Convert
        img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(self.device)
        img = img.half() if HALF else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)
        return img


    def detect_person(self, im0):

        

        boxes = []
        img = self.preprocess_image(im0)

        pred = self.yolo_model(img, augment=AUGMENT, visualize=False)
        t3 = time_sync()
        #dt[1] += t3 - t2

        # Apply NMS
        pred = non_max_suppression(pred, CONF_THRES, IOU_THRES, CLASSES, AGNOSTIC_NMS, max_det=MAX_DET)
        #dt[2] += time_sync() - t3
        

        return pred,self.names


