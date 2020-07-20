import os
import sys
sys.path.append('../deep_sort')
from utils.parser import get_config
from deep_sort import build_tracker
import torch

use_cuda = (os.environ['DEVICE_TYPE'] == 'cuda')

class Tracker():
    def __init__(self):
        self.cfg = get_config()
        self.cfg.merge_from_file('../deep_sort/configs/deep_sort.yaml')
        self.cfg.DEEPSORT.REID_CKPT = '../deep_sort/deep_sort/deep/checkpoint/ckpt.t7'
        self.tracker = build_tracker(self.cfg, use_cuda=use_cuda)

    def update(self, object_boxes_xyxy, classification_scores, frame):
        object_boxes_xywh = self._box_xyxy_to_xcycwh(torch.Tensor(object_boxes_xyxy))
        for ind, score in enumerate(classification_scores):
            if score < 0.8:
                classification_scores[ind] += 0.2
        tracker_outputs = self.tracker.update(object_boxes_xywh, classification_scores, frame)
        
        return {'boxes': [(o[:4]).tolist() for o in tracker_outputs], 'ids': [int(o[4]) for o in tracker_outputs]}

    def _box_xyxy_to_xcycwh(self, box_xyxy):
        bbox_xywh = box_xyxy.clone()
        bbox_xywh[:,2] = box_xyxy[:,2] - box_xyxy[:,0]
        bbox_xywh[:,3] = box_xyxy[:,3] - box_xyxy[:,1]
        bbox_xywh[:,0] = box_xyxy[:,0] + bbox_xywh[:,2]/2
        bbox_xywh[:,1] = box_xyxy[:,1] + bbox_xywh[:,3]/2
        return bbox_xywh
