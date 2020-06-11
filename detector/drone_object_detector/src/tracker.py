import os
import sys
sys.path.append('../deep_sort')
from sort_utils.parser import get_config
from deep_sort import build_tracker
import torch
from utils.features import Point,Rect


use_cuda = (os.environ['DEVICE_TYPE'] == 'cuda')

class DeepSortTracker:
    def __init__(self):
        self.cfg = get_config()
        self.cfg.merge_from_file('../deep_sort/configs/deep_sort.yaml')
        self.cfg.DEEPSORT.REID_CKPT = '../deep_sort/deep_sort/deep/checkpoint/ckpt.t7'
        self.tracker = build_tracker(self.cfg, use_cuda=use_cuda)

    



    def update_features(self, frame, features):
        boxes = features['boxes']
        
        boxes_formatted, classification_scores = self.convert_box_coordinates(boxes)
        object_boxes_xywh = torch.Tensor(boxes_formatted)
        for ind, score in enumerate(classification_scores):
            if score < 0.8:
                classification_scores[ind] += 0.2
        tracker_outputs = self.tracker.update(object_boxes_xywh, classification_scores, frame)
        return {'points': [], 'boxes': self.format_boxes(tracker_outputs)}
    

    def convert_box_coordinates(self,boxes):
        boxes_formatted = []
        scores = []
        for box in boxes:
            score = box.properties['accuracy']
            scores.append(score)
            xc = box.centroid.x_coordinate
            yc = box.centroid.y_coordinate
            width = box.bottom_right_point.x_coordinate - box.top_left_point.x_coordinate
            height = box.bottom_right_point.y_coordinate - box.top_left_point.y_coordinate
            boxes_formatted.append([xc,yc,width,height])
        return boxes_formatted,scores

    def format_boxes(self, boxes):
        formatted = []
        for box in boxes:
            top_left_point = Point(box[0],box[1])
            bottom_right_point = Point(box[2],box[3])
            pid = box[4]
            rect = Rect(top_left_point,bottom_right_point,**{'pid':pid})            
            formatted.append(rect)

        return formatted




    """
    def update(self, object_boxes_xyxy, classification_scores, frame):
        

        object_boxes_xywh = self._box_xyxy_to_xcycwh(torch.Tensor(object_boxes_xyxy))

        for ind, score in enumerate(classification_scores):
            if score < 0.8:
                classification_scores[ind] += 0.2
        tracker_outputs = self.tracker.update(object_boxes_xywh, classification_scores, frame)
        print(tracker_outputs)

        return {'boxes': [(o[:4]).tolist() for o in tracker_outputs], 'ids': [int(o[4]) for o in tracker_outputs]}



    def _box_xyxy_to_xcycwh(self, box_xyxy):
        bbox_xywh = box_xyxy.clone()
        bbox_xywh[:,2] = box_xyxy[:,2] - box_xyxy[:,0]
        bbox_xywh[:,3] = box_xyxy[:,3] - box_xyxy[:,1]
        bbox_xywh[:,0] = box_xyxy[:,0] + bbox_xywh[:,2]/2
        bbox_xywh[:,1] = box_xyxy[:,1] + bbox_xywh[:,3]/2
        return bbox_xywh
    """
    

    


