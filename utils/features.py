

class Feature:
	def serialize(self):
		return self.__dict__


class Point(Feature):
	def __init__(self,x,y,**kwargs):
		self.x_coordinate = x
		self.y_coordinate = y
		self.properties = kwargs


class Rect(Feature):
	def __init__(self, top_left_point, bottom_right_point, **kwargs):
		self.top_left_point = top_left_point
		self.bottom_right_point = bottom_right_point
		self.properties = kwargs