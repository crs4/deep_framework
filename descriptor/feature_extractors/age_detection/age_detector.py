import os, shutil, sys, time, re, glob, sys
import numpy as np
import caffe
import cv2
#from scipy import misc
import skimage.io
from .age_functions import load_mean, create_network, create_transformer
from operator import itemgetter
from .age_constants import *
from utils.abstract_descriptor import AbstractDescriptor
import time


"""
NOTE
Every class must have:
1) method: detect_batch
2) method: refine_classification
3) attribute: win_size
"""


class AgeNet(AbstractDescriptor):


	def __init__(self):
		"""
		Load age model.
		The categories are interval of ages. They are dinamically generated
		"""

		self.interval = AGE_INTERVAL
		self.categories = [(i,i+(self.interval-1)) for i in range(0,101,self.interval)]
		self.win_size = AGE_WIN_SIZE
		self.__setup_net(AGE_MODEL)
	
	
	def __setup_net(self,model):
		self.mean = load_mean()
		self.net = create_network(self.mean,model) 
		self.transformer = create_transformer(self.net,self.mean)

                                          

	def detect_batch(self,images):
		"""
		It assigns an interval of ages to each person detected in images

		:type images: list
		:param images: crops of faces

		:rtype: list
		:returns: list of tuples, one per crop, composed of the age interval and the probality associated
		"""
		batch = []
		for img_o in images:

			img = cv2.cvtColor(img_o, cv2.COLOR_BGR2RGB)
			img = skimage.img_as_float(img).astype(np.float32)
			batch.append(img)
		
		predictions = self.net.predict(batch, oversample=False)

		ages = []
		for prediction in predictions:
			"""
			best_three = np.argpartition(prediction, -3)[-3:]
			best_three_probs = prediction[best_three]
			norm_factor = 1/sum(best_three_probs)
			temp = sum(np.multiply(best_three,best_three_probs))*norm_factor
			cat = list(filter(lambda x: int(temp) in range(x[0],x[1]+1), self.categories))[0]
			ages.append((str(cat), sum(best_three_probs)*norm_factor/3 ))
			"""
			temp = np.argmax(prediction)
			cat = list(filter(lambda x: temp in range(x[0],x[1]+1), self.categories))[0]
			ages.append((str(cat),max(prediction)))

		return ages



	"""
	def detect_batch(self,images):
		batch = []
		for img_o in images:

			img = cv2.cvtColor(img_o, cv2.COLOR_BGR2RGB)
			img = skimage.img_as_float(img).astype(np.float32)
			batch.append(img)
		
		predictions = self.net.predict(batch, oversample=False)

		ages = []
		for prediction in predictions:
			acc = 0
			temp_ages = np.argpartition(prediction, -3)[-3:]
			print temp_ages,'ta'
			prob_ages = prediction[temp_ages]
			print prob_ages,'pa'
			for k,v in zip(temp_ages,prob_ages):
				acc = acc + (k*v)
			mean_pond = acc/sum(prob_ages)
			print mean_pond
			
			cat = list(filter(lambda x: int(mean_pond) in range(x[0],x[1]+1), self.categories))[0]
			print cat,'cat'
			#ages.append((str(cat),prediction[ind][-1]))
			ages.append((str(cat),mean_pond))
		
		return ages
	"""

	def refine_classification(self,class_results):
		"""
		It executes weighted mean of results for each class in a slide window

		:type class_results: list
		:param class_results: list of tuples composed of the class and the probability associated

		:rtype: string
		:returns: the resulting class
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

		
	
    

	

    