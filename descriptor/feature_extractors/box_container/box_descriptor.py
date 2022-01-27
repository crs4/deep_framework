





class BoxDescriptor:


	def __init__(self):
		"""
		Create descriptor network
		"""
		
		self.win_size = 1


		

	def detect_batch(self,detector_results,images):
		"""
		Assign a class to each object detected in images

		:type images: list
		:param images: crops of detected objects

		:rtype: list
		:returns: list of tuples, one per crop, composed of the class and the probality associated
		"""
		min_x_topleft = 99999999999
		min_y_topleft = 99999999999
		max_x_bottomright = 0
		max_y_bottomright = 0
		master_box = dict()
		objects = detector_results['objects']
		for obj in objects:
			x_topleft = obj['rect']['x_topleft']
			y_topleft = obj['rect']['y_topleft']
			x_bottomright = obj['rect']['x_bottomright']
			y_bottomright = obj['rect']['y_bottomright']

			if x_topleft < min_x_topleft:
				min_x_topleft = x_topleft

			if y_topleft < min_y_topleft:
				min_y_topleft = y_topleft

			if x_bottomright > max_x_bottomright:
				max_x_bottomright = x_bottomright

			if y_bottomright > max_y_bottomright:
				max_y_bottomright = y_bottomright

		
		master_box['x_topleft'] = min_x_topleft
		master_box['y_topleft'] = min_y_topleft
		master_box['x_bottomright'] = max_x_bottomright
		master_box['y_bottomright'] = max_y_bottomright
		
		print(master_box)
		return master_box



		

	def refine_classification(self,class_results):
		"""
		Execute weighted mean of results for each class in a slide window

		:type class_results: list
		:param class_results: list of tuples composed of the class and the probability associated

		:rtype: list
		:returns: list of tuples composed by each class and the relative weighted probability
		"""
		
		return class_results
   
