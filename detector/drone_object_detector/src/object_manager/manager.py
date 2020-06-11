

import uuid

from utils.geometric_functions import compute_rect,get_int_over_union
from scipy.spatial import distance


class Object:
    def __init__(self, rect = None, points = None, pid = None):
        self.pid = pid if pid is not None else uuid.uuid4()
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




class ObjectManager:
    def __init__(self):

        self.objects_list = [] # list of objects present in video





    def create_objects(self, boxes):
        created = []
        for obj in objects:
            obj_pid = rect.properties['pid']
            obj = Object(rect = box.rect, pid = rect.properties['pid'])
            created.append(obj)
        return created

    




