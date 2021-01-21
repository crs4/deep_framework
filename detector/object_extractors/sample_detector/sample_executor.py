

from utils.features import Object, Rect, Point
from utils.abstract_detector import AbstractDetector

from .detector import SampleDetector
from .tracker import Tracker


class SampleExecutor(AbstractDetector):


    def __init__(self):
        self.detector = SampleDetector() 
        self.tracker = Tracker()



    def extract_features(self,current_frame,executor_dict):
    	pass
