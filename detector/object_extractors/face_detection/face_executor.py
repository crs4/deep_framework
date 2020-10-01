
import imutils
from .face_detector import FaceNet_vcaffe
from .tracking.tracker import Tracker,TrackerCV
from .object_manager.manager import ObjectManager
from .face_detection_constants import *
from utils.features import Object, Rect, Point


class FaceDetectorExecutor:

    ratio = 1
    def __init__(self):
        self.tracker = Tracker(**LK_PARAMS) # method for points tracking
        #self.tracker = TrackerCV() # method for points tracking
        self.detector = FaceNet_vcaffe(**FACENET_PARAMS) # method for face detection.
        self.object_manager = ObjectManager()
        
        self.tracks = []
        self.tracking_success = False
        


    def __reset_app(self):
        self.tracks = []
        self.tracking_success = False

    def __create_objects(self,people):
        objects = []
        for p in people:
            obj_points = []
            top_left = Point(p.rect['x_topleft'],p.rect['y_topleft'])
            bottom_right = Point(p.rect['x_bottomright'],p.rect['y_bottomright'])
            obj_rect = Rect(top_left,bottom_right)
            for k,v in p.face_points.items():
                point = Point(v[0][0],v[0][1],**{'tag':k})
                obj_points.append(point)
            obj = Object(rect = obj_rect, points = obj_points, pid = p.pid)
            objects.append(obj)
        return objects



    def extract_features(self,current_frame,executor_dict):


        frame_counter = executor_dict['frame_counter']
        print('frame: ',frame_counter)
        try:
            self.ratio = FACE_IMAGE_WIDTH/float(current_frame.shape[1])
        except Exception as e:
            print('exception in rec frame ',e)
            

        current_frame = imutils.resize(current_frame, width=FACE_IMAGE_WIDTH)

        #computation of tracking features
        if len(self.tracks) > 0:
            

            print('tr')
            self.tracking_success, new_features = self.tracker.update_features(current_frame,self.tracks)   

            if self.tracking_success:
                self.tracks = new_features

        # computation of detector features
        if frame_counter % DETECTION_INTERVAL == 0 or not self.tracking_success:
            print('det')
            det_features = self.detector.detect(current_frame)
            self.object_manager.check_people(det_features)
            self.tracks = self.tracker.create_track_points(det_features['points'])

        people = self.object_manager.track_people(current_frame, self.tracks)
        

        self.tracker.set_last_frame(current_frame)


        object_list = self.__create_objects(people)
        return object_list


