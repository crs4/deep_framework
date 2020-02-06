


import time


import numpy as np
import cv2
import sys
import os
import imutils
from .person_detection_constants import *



class MobileDetector:

    def __init__(self):
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        model_path= os.path.join(cur_dir,'mobilenet_ssd/'+MOBILE_MODEL_NAME)
        proto_path= os.path.join(cur_dir,'mobilenet_ssd/'+MOBILE_PROTO_NAME)
        self.net = cv2.dnn.readNetFromCaffe(proto_path, model_path)
        self.W = None
        self.H = None
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
                    "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                    "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                    "sofa", "train", "tvmonitor"]

    def detect_person(self, frame):

        boxes = []
        

        # if the frame dimensions are empty, set them
        if self.W is None or self.H is None:
            (self.H, self.W) = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(frame, 0.007843, (self.W, self.H), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()

        for i in np.arange(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated
            # with the prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections by requiring a minimum
            # confidence
            if confidence > CONFIDENCE_THR:
                # extract the index of the class label from the
                # detections list
                idx = int(detections[0, 0, i, 1])

                # if the class label is not a person, ignore it
                if self.CLASSES[idx] != "person":
                    continue

                # compute the (x, y)-coordinates of the bounding box
                # for the object
                box = detections[0, 0, i, 3:7] * np.array([self.W, self.H, self.W, self.H])
                (startX, startY, endX, endY) = box.astype("int")
                boxes.append((startX, startY, endX, endY))

        return boxes

    	


