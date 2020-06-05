# MIT License
# 
# Copyright (c) 2016 David Sandberg
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import time
from face_detection.mtcnn_caffe import mtcnn_utils as face_caffe
#from face_detection_constants import *
from utils.features import Point,Rect

import caffe
from imutils import face_utils
import numpy as np
import cv2
import sys
import os
"""
NOTE
Every class must implement the method 'detect_face'. This method can returns:
1) bounding boxes
2) points
The element returned must be a dictionary as follow: {'points': [...], 'boxes': [...]}
'boxes' must be an array: points = [x_top_left, y_top_left, x_bottom_right, y_bottom_right]
"""



class FaceNet_vcaffe:

    def __init__(self, **params):
        self.minsize = params['minsize'] # minimum size of face
        self.threshold = params['threshold'] # three steps's threshold
        self.factor = params['factor'] # scale factor
        self.models = self.__setup_net()

    def __setup_net(self):
        models = dict()
        caffe_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'mtcnn_caffe/model')
        models['pNet'] = caffe.Net(caffe_model_path+"/det1.prototxt", caffe_model_path+"/det1.caffemodel", caffe.TEST)
        models['rNet'] = caffe.Net(caffe_model_path+"/det2.prototxt", caffe_model_path+"/det2.caffemodel", caffe.TEST)
        models['oNet'] = caffe.Net(caffe_model_path+"/det3.prototxt", caffe_model_path+"/det3.caffemodel", caffe.TEST)
        return models

    def __check_faces_accuracy(self,features, thr):
        """
        This function filters out faces detected with accuracy under thr
        """
        faces = features['boxes']
        points = features['points']
        filtered_features = {'boxes':[],'points':[]}
        for face,point in zip(faces,points):
            if face.properties['accuracy'] > thr:
                filtered_features['boxes'].append(face)
                filtered_features['points'].append(point)
        
        return filtered_features





    def format_points(self,points):
        formatted = []
        
        for face_points in points:
            point_list = []
            num_points = len(face_points)
            keypoints = ['right_eye','left_eye','nose','right_mouth','left_mouth']
            for px, py,key in zip(face_points[:int(num_points / 2)], face_points[int(num_points / 2):],keypoints):
                #cv2.circle(img, (px, py), 5, (255, 0, 0), -1)
                point = Point(px,py, **{'tag':key})
                point_list.append(point)

            formatted.append(point_list)

        return formatted


    def format_bbox(self,rects):
        formatted = []
        
        for rect in rects:
            top_left_point = Point(rect[0],rect[1])
            bottom_right_point = Point(rect[2],rect[3])
            rect = Rect(top_left_point,bottom_right_point,**{'accuracy':rect[4]})            
            formatted.append(rect)

        return formatted

    def detect(self, img):
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        pnet = self.models['pNet']
        rnet = self.models['rNet']
        onet = self.models['oNet']
        
        bounding_boxes, points = face_caffe.detect_face(img, self.minsize, pnet, rnet, onet, self.threshold, False, self.factor)
        features = {'points': self.format_points(points), 'boxes': self.format_bbox(bounding_boxes)}
        
        filtered_features = self.__check_faces_accuracy(features, 0.95)
        

        return filtered_features


