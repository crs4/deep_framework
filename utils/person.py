
import uuid



class Entity:


	def __init__(self,rect):

		#self.face_rect= face_rect
		self.rect= rect
		self.pid= uuid.uuid4()


class Person(Entity):
	
	def __init__(self,face_rect, face_points, center):
		Entity.__init__(self, face_rect)
		self.face_points = face_points
		self.center = center

	def jsonable(self):
		points_ser = {k: str(v[0]) for k, v in self.face_points.items()}
		d = dict(points=points_ser, rect=self.rect, center=str(self.center[0]), pid=str(self.pid))
		return d






		
		
