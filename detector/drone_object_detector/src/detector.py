import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()

from detectron2.engine import DefaultPredictor
import sys
sys.path.append('../')
# from detectron2.config import get_cfg
from adet.config import get_cfg
import configparser
import os

from utils.features import Point,Rect

#from visdrone_dataset import VisDroneDetectronDataset



class VisdroneDectector:
    def __init__(self):

        config = configparser.ConfigParser()
        config.read('configuration.ini')

        config_file = config['DEFAULT']['model_config']
        model_weights = config['DEFAULT']['model_weights']
        device_type = os.environ['DEVICE_TYPE']
        confidence_threshold = 0.1
        # load config from file and command-line arguments
        self.visdrone_objects = ["ignored_regions", "pedestrian", "people", "bicycle", "car", "van", "truck", "tricycle", "awning_tricycle", "bus", "motor", "others"]
        try:
            cfg = get_cfg()
            print('get')
        except Exception as e:
            print(e)
            raise e

        try:
            cfg.merge_from_file(config_file)
            print('merge')
        except Exception as e:
            print(e)
            raise e
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = confidence_threshold
        cfg.MODEL.FCOS.INFERENCE_TH_TEST = confidence_threshold
        cfg.MODEL.WEIGHTS = model_weights
        cfg.MODEL.DEVICE = device_type
        try:
            cfg.freeze()
            print('freeezwe')
        except Exception as e:
            print(e)
            raise e
        self.cfg = cfg
        try:
            self.predictor = DefaultPredictor(self.cfg)
            print('predict')
        except Exception as e:
            print(e)
            raise e

        """
        cfg = get_cfg()
        cfg.merge_from_file(config_file)
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = confidence_threshold
        cfg.MODEL.FCOS.INFERENCE_TH_TEST = confidence_threshold
        cfg.MODEL.WEIGHTS = model_weights
        cfg.MODEL.DEVICE = device_type
        cfg.freeze()
        self.cfg = cfg
        self.predictor = DefaultPredictor(self.cfg)
        """

    def predict(self, frame):    
        object_instances = self.predictor(frame)['instances'].to('cpu')
        object_boxes = object_instances.get('pred_boxes').tensor.tolist()
        object_classes = object_instances.get('pred_classes').tolist()
        classification_scores = object_instances.get('scores').tolist()
        return {'boxes': object_boxes, 'classes': object_classes, 'scores': classification_scores}


    def detect(self, frame):  

        object_instances = self.predictor(frame)['instances'].to('cpu')
        features = {'points': [], 'boxes': self.format_bbox(object_instances)}    
        return features

    def format_bbox(self,object_instances):
        formatted = []

        object_boxes = object_instances.get('pred_boxes').tensor.tolist()
        object_classes_indices = object_instances.get('pred_classes').tolist()
        object_classes = [ self.visdrone_objects[index] for index in object_classes_indices]
        classification_scores = object_instances.get('scores').tolist()

        for box, obj_class, score in zip(object_boxes,object_classes,classification_scores):
            top_left_point = Point(box[0],box[1])
            bottom_right_point = Point(box[2],box[3])
            rect = Rect(top_left_point,bottom_right_point,**{'accuracy':score, 'category': obj_class})            
            formatted.append(rect)

        return formatted

