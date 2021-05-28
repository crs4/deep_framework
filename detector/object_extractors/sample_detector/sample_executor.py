

from utils.features import Object, Rect, Point
from utils.abstract_detector import AbstractDetector

from .detector import SampleDetector
from .tracker import SampleTracker


class SampleExecutor(AbstractDetector):


    def __init__(self):
        self.detector = SampleDetector() 
        self.tracker = SampleTracker()



    def extract_features(self,current_frame,executor_dict):
    	detected_objects = self.detector.detect(current_frame)
	tracked_objects = self.tracker.update(detected_objects)
	return tracked_objects
