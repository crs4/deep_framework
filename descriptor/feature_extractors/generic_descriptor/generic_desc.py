
from .generic_network import GenericNet

from utils.abstract_descriptor import AbstractDescriptor


class GenericDescriptor(AbstractDescriptor):

	def __init__(self):
		self.net = GenericNet()

	win_size = 10

	def detect_batch(self,detector_results,images):
		inference_results = self.net.classify(images)
		return inference_results


	def refine_classification(self,class_results):
		return class_results.mean()