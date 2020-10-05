
from .detection_constants import *

from .deep_sort import preprocessing
from .deep_sort import nn_matching
from .deep_sort.detection import Detection
from .deep_sort.tracker import Tracker
from .deep_sort.detection import Detection as ddet
from .deep_sort.tracker import Tracker
from .deep_sort.tools import generate_detections as gdet

from .yolo_detector import YoloDetector

from .associator import associate

from utils.features import Object, Point, Rect
from utils.abstract_detector import AbstractDetector


import time
import numpy as np


class DroneExecutor(AbstractDetector):

    ratio = 1

    def __init__(self):
        #deep_sort
        self.encoder = gdet.create_box_encoder(model_filename,batch_size=1,to_xywh = True)
        metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
        self.ds_tracker = Tracker(metric)
        self.detector = YoloDetector() # method for detection.


    def extract_features(self, current_frame, executor_dict):
        obj_list = [] 
        frame_counter = executor_dict['frame_counter']


        
        det_start = time.time()
        class_names,confidences,boxs = self.detector.detect(current_frame) #boxs x,y,b,r
        #print(boxs, confidences, class_names)
        det_end = time.time()
        print('Det time: ', det_end - det_start, ' counter ', frame_counter)
        #points = [ [box.centroid] for box in detector_features['boxes']]
        tr_start = time.time()
        # score to 1.0 here).
        enc_time = time.time()
        features = self.encoder(current_frame,boxs)
        detections = [Detection(bbox, confidence, feature,obj_class) for bbox, feature,confidence,obj_class in zip(boxs, features,confidences,class_names)]

        # Run non-maxima suppression.
        boxes = np.array([d.tlwh for d in detections])
        #print('boxes',boxes)
        scores = np.array([d.confidence for d in detections])
        #print('scores',scores)
        max_time = time.time()
        indices = preprocessing.non_max_suppression(boxes, nms_max_overlap, scores)
        detections = [detections[i] for i in indices]
        boxes_det = [box.to_tlbr() for box in detections]
        """
        for bbox in boxes_det:

            top_left_point = Point(bbox[0],bbox[1])
            bottom_right_point = Point(bbox[2], bbox[3])
            rect = Rect(top_left_point,bottom_right_point)
            obj = Object(rect)
            obj_list.append(obj)
        """
        #print('det2',detections)
        # Call the tracker
        t_f_tr = time.time() 
        self.ds_tracker.predict()
        self.ds_tracker.update(detections)
        tr_end = time.time()
        print('Track predict time: ',tr_end - t_f_tr,' counter ', frame_counter)
        print('Track time: ', tr_end - tr_start,' counter ', frame_counter)
        
        tracker_boxes = []
        tracker_ids = []
        
        for track in self.ds_tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue

            bbox = track.to_tlbr()
            
            tracker_boxes.append(bbox)
            tracker_ids.append(track.track_id)
            """
            top_left_point = Point(bbox[0],bbox[1])
            bottom_right_point = Point(bbox[2], bbox[3])
            rect = Rect(top_left_point,bottom_right_point)
            obj = Object(rect, pid = track.track_id)
            obj_list.append(obj)

            """
            
 
        
        #print('tracked',tracker_boxes)
        #print('boxes',boxes_det)
        track_indexes, det_indexes = associate(tracker_boxes, boxes_det, 0.8)
        try:
        
            bboxes = [tracker_boxes[i] for i in track_indexes]
            ids = [tracker_ids[i] for i in track_indexes]
            classes = [detections[i].obj_class for i in det_indexes]
            scores_def = [detections[i].confidence for i in det_indexes]

            for box, pid, class_name, score in zip(bboxes,ids,classes,scores_def):
                #print(box, pid, class_name, score)
                top_left_point = Point(box[0],box[1])
                bottom_right_point = Point(box[2], box[3])
                rect = Rect(top_left_point,bottom_right_point, **{'score':score,'class':class_name})
                obj = Object(rect, pid = pid)
                obj_list.append(obj)

        except Exception as e:
            print('err',e)
            raise e

        
        return obj_list
        
        
