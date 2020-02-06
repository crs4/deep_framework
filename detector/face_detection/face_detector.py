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
from mtcnn_caffe import mtcnn_utils as face_caffe
from mtcnn_caffe.utils import format_points,format_bbox

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

    def detect_face(self, img):
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        pnet = self.models['pNet']
        rnet = self.models['rNet']
        onet = self.models['oNet']
        
        bounding_boxes, points = face_caffe.detect_face(img, self.minsize, pnet, rnet, onet, self.threshold, False, self.factor)

        return {'points': format_points(points), 'boxes': format_bbox(bounding_boxes)}
