

import os, shutil, sys, time, re, glob, sys
import numpy as np
#import caffe
import cv2
from scipy import misc
import skimage.io
from .gender_functions import load_mean, create_network, create_transformer
from .gender_constants import *
from operator import itemgetter
#from constants import *
from utils.abstract_descriptor import AbstractDescriptor

import time


"""
NOTE
Every class must have:
1) method: detect_batch
2) method: refine_classification
3) attribute: win_size
"""




class GenderNet(AbstractDescriptor):


	def __init__(self):
		"""
		Load gender model
		"""
		self.categories = ['Female','Male']
		self.__setup_net(GENDER_MODEL)
		self.win_size = GEN_WIN_SIZE

	def __setup_net(self,model):
		self.mean = load_mean()
		self.net = create_network(self.mean,model) 
		self.transformer = create_transformer(self.net,self.mean)
		
		

	def detect_batch(self,images):
		"""
		It assigns a gender to each person detected in images

		:type images: list
		:param images: crops of faces

		:rtype: list
		:returns: list of tuples, one per crop, composed of the gender and the probality associated
		"""
		
		batch = []
		for img_o in images:

			img = cv2.cvtColor(img_o, cv2.COLOR_BGR2RGB)
			img = skimage.img_as_float(img).astype(np.float32)
			batch.append(img)


		predictions = self.net.predict(batch, oversample=False)
		genders = []
		for prediction in predictions:
			ind = np.argsort(prediction)
			res = np.array(self.categories)[ind][-1:][0]
			

			genders.append((res,prediction[ind][-1]))
		return genders

	def refine_classification(self,class_results):
		"""
		It executes weighted mean of results for each class in a slide window

		:type class_results: list
		:param class_results: list of tuples composed of the class and the probability associated

		:rtype: list
		:returns: list of tuples composed by each class and the relative weighted probability
		"""

		counter = dict()
		results = []
		for key,prob in class_results:

			if key not in counter.keys():
				counter[key] = prob
			else: 
				counter[key]+= prob

		for k,v in counter.items():
			norm_value = float(v)/self.win_size
			results.append((k,norm_value))

		sorted_by_prob = sorted(results, key=itemgetter(1), reverse = True)
		return sorted_by_prob[0][0]