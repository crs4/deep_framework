


from utils.geometric_functions import get_int_over_union,get_rect_around_points


class Object:
    def __init__(self, rect = None, points = None):
        self.rect = rect
        self.points = points


class ObjectManager:
    def __init__(self):

        self.objects_list = [] # list of people present in video





    def manage_object_list(self, features,frame_w,frame_h):
        DELTA_RECT=1.2

        use_points = False
        use_boxes = False
        points = []
        boxes = []
        if features['boxes'] is not None:
            use_boxes = True
            boxes = features['boxes']

        if len(features['points']) is not None:
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

        actual_number = len(boxes)
        # checks if any object appears in scene
        diff_objects = ( actual_number - len(self.objects_list) )
        abs_diff_objects = abs(diff_objects)
        
        indices = self.__get_box_obj_best_match(boxes,self.objects_list)
        to_update = indices[abs_diff_objects:] #to update

        print(indices)

        objects_updated = self.update_and_remove_objects(to_update,boxes,points,self.objects_list)
        
        objects_created = []

        # something apperead
        if diff_objects > 0:
            to_create = indices[:abs_diff_objects] #box to create
            print(to_create)
            objects_created = self.create_objects(to_create,boxes,points)

        
        self.objects_list = objects_created + objects_updated
        return self.objects_list





    def update_and_remove_objects(self,indices,boxes,points,old_object_list):

        updated = [] 
        for box_index, obj_index, score in indices:
            obj = old_object_list[obj_index]
            box = boxes[box_index]
            if len(points)  > 0:
                points = points[box_index]
                obj.points = points
            
            obj.rects = box
            updated.append(obj)

        return updated



    def create_objects(self,indices, boxes, points):
        
        created = [] 
        for box_index, obj_index, score in indices:
            box = boxes[box_index]
            if len(points) > 0:
                points = points[box_index]
            else:
                points = None
            obj = Object(box,points)
            created.append(obj)

        return created



    def __get_max_overlap_obj_index(self, box, old_object_list):

        """
        This function tracks person from people to new faces if present
        """
        max_overlap = 0
        index = None

        for i,old_obj in enumerate(old_object_list):
            print(old_obj.rect, box)
            overlap = get_int_over_union(old_obj.rect, box)
            if overlap > max_overlap:
                max_overlap = overlap
                index = i


        return index,max_overlap

    def __get_box_obj_best_match(self, boxes, old_object_list):
        
        indices = []
        for box_index,box in enumerate(boxes):
            obj_index,score = self.__get_max_overlap_obj_index(box, old_object_list)
            indices.append((box_index,obj_index,score))

        #best scores bottom
        indices = sorted(indices, key=lambda t: t[2])

        return indices