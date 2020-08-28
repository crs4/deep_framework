import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()

from detectron2.engine import DefaultPredictor
from detection_constants import *
import sys
from adet.config import get_cfg
import configparser
import os

config = configparser.ConfigParser()
config.read('configuration.ini')
model_type = os.environ.get('MODEL_TYPE', 'DEFAULT')
config_file = config[model_type]['model_config']
model_weights = config[model_type]['model_weights']
confidence_threshold = 0.27
visdrone_objects = ["ignored_regions", "pedestrian", "people", "bicycle", "car", "van", "truck", "tricycle", "awning_tricycle", "bus", "motor", "others"]

class VisdroneDetector():
    def __init__(self):
        # load config from file and command-line arguments
        cfg = get_cfg()
        cfg.merge_from_file(config_file)

        # Set score_threshold for builtin models
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = confidence_threshold
        cfg.MODEL.FCOS.INFERENCE_TH_TEST = confidence_threshold
        cfg.MODEL.WEIGHTS = model_weights
        cfg.MODEL.DEVICE = device_type
        cfg.freeze()
        self.cfg = cfg
        self.predictor = DefaultPredictor(self.cfg)
        self.predictor_labels = ["ignored_regions", "pedestrian", "people", "bicycle", "car", "van", "truck", "tricycle", "awning_tricycle", "bus", "motor", "others"]
        self.labels = ["person", "two_wheeled_vehicle", "small_vehicle", "big_vehicle", "other"]


    def predict(self, frame):    
        object_instances = self.predictor(frame)['instances'].to('cpu')
        object_boxes = object_instances.get('pred_boxes').tensor.tolist()
        object_classes = object_instances.get('pred_classes').tolist()
        class_names = self.map_classes(object_classes)
        classification_scores = object_instances.get('scores').tolist()
        return object_boxes,classification_scores,class_names

    def map_classes(self, object_classes):
        new_classes = []
        for cl in object_classes:
            object_type = self.predictor_labels[cl]
            if object_type in ('pedestrian', 'people'):
                new_classes.append('person')
            elif object_type in ('bicycle', 'motor'):
                new_classes.append('two_wheeled_vehicle')
            elif object_type in ('car', 'van', 'tricycle', 'awning_tricycle'):
                new_classes.append('small_vehicle')
            elif object_type in ('truck', 'bus'):
                new_classes.append('big_vehicle')
            else:
                new_classes.append('other')
        return new_classes
