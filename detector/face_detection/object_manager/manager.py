

import uuid

from utils.geometric_functions import get_rect_around_points,get_int_over_union
from scipy.spatial import distance


class Object:
    def __init__(self, rect = None, points = None):
        self.pid= uuid.uuid4()
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

        self.objects_list = [] # list of people present in video





    def manage_object_list(self, features,frame_w,frame_h):
        DELTA_RECT=1.2

        use_points = False
        use_boxes = False
        points = []
        boxes = []
        if len(features['boxes']) > 0:
            use_boxes = True
            boxes = features['boxes']

        if len(features['points']) > 0:
            points = features['points']
            use_points = True
            boxes = []
            # only in case points are used as features
            # we consider boxes as a bounding boxes around points with customizable spread around them
            for object_points in points:
                rect = get_rect_around_points(frame_w,frame_h,object_points,delta_rect=DELTA_RECT)
                boxes.append(rect)
        
        if not use_boxes and not use_points:
            self.objects_list = []
            return self.objects_list

        
        updated = []
        created = []
        
        #compare distance matrix between boxes and objects
        indices = self.compare_boxes_obj_distance(boxes,self.objects_list)
        
        if len(self.objects_list) == 0 and len(boxes) > 0:
            created = self.create_objects(boxes, points)
            self.objects_list = created
            return self.objects_list
        
        if len(self.objects_list) > 0 and len(boxes) == 0:
            self.objects_list = []
            return self.objects_list

        if len(self.objects_list) > 0 and len(boxes) > 0:
            diff = ( len(boxes) - len(self.objects_list) )
            if diff > 0: # create 
                indices_used, updated = self.update(boxes,points, self.objects_list, indices, len(self.objects_list))
                created = self.create_objects(boxes, points, indices_used)
                if len(created) != diff:
                    a = input('error creating')
                self.objects_list = updated + created
                return self.objects_list
            if diff == 0:
                __, updated = self.update(boxes,points, self.objects_list, indices, len(self.objects_list))
                self.objects_list = updated
                return self.objects_list
            if diff < 0:
                __, updated = self.update(boxes,points, self.objects_list, indices, len(boxes))
                self.objects_list = updated
                return self.objects_list






    def compare_boxes_obj_distance(self,boxes,objects_list):
        indices = []
        for box_index, box in enumerate(boxes):
            box_centroid = [box.centroid.x_coordinate, box.centroid.y_coordinate]
            for obj_index, obj in enumerate(objects_list):
                obj_centroid = [obj.rect.centroid.x_coordinate, obj.rect.centroid.y_coordinate]
                dist = distance.euclidean(obj_centroid, box_centroid)
                indices.append((box_index,obj_index,dist))

        # lower distances in top
        sorted_indices = sorted(indices, key=lambda t: t[2])
        return sorted_indices

    def update(self, boxes,points, objects_list, indices, to_update):

        objects_updated = []
        last_updated = None
        count_updated = 0
        indices_used = []
        for ind in indices:

            box_index,obj_index,distance = ind

            if count_updated < to_update:
                if obj_index != last_updated:

                    obj = objects_list[obj_index]
                    box = boxes[box_index]
                    points_list = points[box_index]
                    iou = get_int_over_union(obj.rect,box)
                    print('iou: ', iou)
                    if iou < 0.9:
                        obj.rect = box
                        obj.points = points_list

                    count_updated += 1
                    last_updated = obj_index

                    indices_used.append((box_index,obj_index,distance))
                    objects_updated.append(obj)

                else:
                    continue


        if len(objects_updated) != count_updated:
            a = input('Error updating')
            return []
        else:
            return indices_used,objects_updated

    def create_objects(self, boxes, points, indices_used=[]):
        box_used_indices = [box_index for box_index,obj_index,distance in indices_used ]
        created = []
        for i,box in enumerate(boxes):
            if i not in box_used_indices:
                if len(points) > 0:
                    obj_points = points[i]
                else:
                    obj_points = None

                obj = Object(box,obj_points)
                created.append(obj)
        return created

    




