
import uuid

class Object:
    def __init__(self, rect, points = [], pid = None, whole_image = False):
        self.pid = pid if pid is not None else None if whole_image else uuid.uuid4()
        self.rect = rect
        self.points = points

    def serialize(self):
        obj_dict = dict()
        points = []
        for point in self.points:
            p_ser = point.serialize()
            points.append(p_ser)

        obj_dict['points'] = points
        obj_dict['rect'] = self.rect.serialize()
        obj_dict['pid'] = str(self.pid)
        return obj_dict



class Feature:
	def serialize(self):
		return self.__dict__


class Point(Feature):
	def __init__(self,x,y,**kwargs):
		self.x_coordinate = int(x)
		self.y_coordinate = int(y)
		self.properties = kwargs

	def serialize(self):
		return self.__dict__


class Rect(Feature):
	def __init__(self, top_left_point, bottom_right_point, **kwargs):
		self.top_left_point = top_left_point
		self.bottom_right_point = bottom_right_point
		self.properties = kwargs
		self.centroid = self.__compute_centroid()

	def __compute_centroid(self):
		dx = self.bottom_right_point.x_coordinate - self.top_left_point.x_coordinate
		dy = self.bottom_right_point.y_coordinate - self.top_left_point.y_coordinate
		x_centroid = self.top_left_point.x_coordinate + int(dx/2)
		y_centroid = self.top_left_point.y_coordinate + int(dy/2)
		return Point(x_centroid, y_centroid)

	def serialize(self):
		rect = dict()
		for k,v in self.__dict__.items():
			if type(v).__name__ ==  'Point':
				rect[k] = v.serialize()
			else:
				rect[k] = v
		return rect
