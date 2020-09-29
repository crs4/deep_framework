

from .classify_images import load_models, classify_loaded_images
from operator import itemgetter
from keras.backend.tensorflow_backend import set_session
import tensorflow as tf







class ClothingDescriptor:


	def __init__(self):
		"""
		Create descriptor network
		"""
		self.__setup_session()
		self.__setup_net()
		self.win_size = 10


	def __setup_session(self):
		config = tf.ConfigProto()
		config.gpu_options.allow_growth = True
		sess = tf.Session(config=config)
		set_session(sess)
		

	def __setup_net(self):
		# Load the trained convolutional neural network and the label binarizers
		self.models = load_models()

	def detect_batch(self,self,detector_results,images):
		"""
		Assign a class to each object detected in images

		:type images: list
		:param images: crops of detected objects

		:rtype: list
		:returns: list of tuples, one per crop, composed of the class and the probality associated
		"""
		
		results = classify_loaded_images(images, self.models)
		
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
   
