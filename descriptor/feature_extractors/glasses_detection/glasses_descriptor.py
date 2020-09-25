
from keras.backend.tensorflow_backend import set_session
from keras.models import load_model

from .glasses_functions import classify_image, classify_loaded_images
from operator import itemgetter

import os
import tensorflow as tf
import pickle

from utils.abstract_descriptor import AbstractDescriptor

from .glasses_constants import *
 





class GlassesDescriptor(AbstractDescriptor):

	win_size = WIN_SIZE	
	def __init__(self):
		"""
		Create descriptor network
		"""
		self.__setup_net()
		


	def __setup_net(self):
		# Load the trained convolutional neural network and the label binarizers
		cur_dir = os.path.split(os.path.abspath(__file__))[0]
		model_path = os.path.join(cur_dir, MODEL_NAME)
		category_binarizer_path = os.path.join(os.path.split(os.path.abspath(__file__))[0], CATEGORY_BIN_NAME)

		config = tf.ConfigProto()
		config.gpu_options.allow_growth = True
		sess = tf.Session(config=config)
		set_session(sess)

		self.model = load_model(model_path, custom_objects={'tf': tf})
		category_bin = None
		color_bin = None
		if category_binarizer_path is not None:
			self.category_bin = pickle.loads(open(category_binarizer_path, 'rb').read())
			self.categories = self.category_bin.classes_



	def detect_batch(self,images):
		"""
		Assign a class to each object detected in images

		:type images: list
		:param images: crops of detected objects

		:rtype: list
		:returns: list of tuples, one per crop, composed of the class and the probality associated
		"""
		
		results = classify_loaded_images(self.model, images, category_binarizer=self.category_bin, color_binarizer=None)
		"""
		for image in images:
			image_results = classify_image(self.model, image, category_binarizer=self.category_bin, color_binarizer=None)

			results.append((image_results['most_prob_category'],image_results['most_prob_category_prob']))
		"""
		
		return results



		

	def refine_classification(self,class_results):
		"""
		Execute weighted mean of results for each class in a slide window

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
   
