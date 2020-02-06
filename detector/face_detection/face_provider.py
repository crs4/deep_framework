
from multiprocessing import Process
import numpy as np

from face_detection_constants import *
import imutils

from face_detector import FaceNet_vcaffe
from tracking.tracker import Tracker
from utils.check_functions import check_faces_accuracy,check_lost_face,check_departed_people,init_people,check_points_similarity
from utils.geometric_functions import get_rect_around_points,get_nearest_person_index,resize_image
from utils.socket_commons import send_data, recv_data
from utils.stats_maker import StatsMaker

import copy
import zmq
import time,json
import cv2
import sys





class FaceProvider(Process):

    def __init__(self, configuration):

        Process.__init__(self)
        self.stats_maker = StatsMaker()
        self.pub_port = configuration['out']
        self.col_port = configuration['out_col']
        self.rec_port = configuration['in']


        self.tracker = Tracker(**LK_PARAMS) # method for points tracking
        self.people = [] # list of people present in video

        
        self.__setup() # app initialization
    
   
    
    def __setup(self):

        self.faces_in_frame = 0 # number of faces detected in current frame
        self.tracks = [] # tracked points
        self.lost_face = False
        




    def __create_faces_track_points(self,frame):


        # face detection
        features = self.face_det.detect_face(frame)
        features = check_faces_accuracy(features, FACE_DETECTION_THR)
        mtcnn_faces, mtcnn_points = features['boxes'], features['points']

        
        diff_faces = ( len(mtcnn_faces) - self.faces_in_frame )

        # checks if any person appears in scene
        if diff_faces > 0:
            self.people = init_people(mtcnn_points,mtcnn_faces,self.people)
        #checks if any person disappears from scene
        if diff_faces < 0:
            self.people = check_departed_people(mtcnn_points, self.people, diff_faces)
        
        self.faces_in_frame = len(mtcnn_faces)

        # formats mtcnn_points in order to be tracked
        kpoints = [list(p.values()) for p in mtcnn_points]


        
        # creates tracking points
        tracks = self.tracker.create_track_points(kpoints)
        return tracks

    def __track_points(self,prev_gray_frame,frame_gray,tracks):

        # calculate new trackpoints
        new_tracks = self.tracker.manage_track_points(prev_gray_frame, frame_gray, tracks)
        return new_tracks

    def track_people(self,frame,tracks):
        people_updated = []
        tracks_split = [tracks[i:i+LOST_THR] for i in range(0,len(tracks),LOST_THR)]
        for tr in tracks_split:
            
            face_points = {'right_eye':tr[0],'left_eye':tr[1],'nose':tr[2],'right_mouth':tr[3],'left_mouth':tr[4]}

            face_rect = get_rect_around_points(frame.shape[1],frame.shape[0],face_points,delta_facerect=DELTA_FACERECT)
            center = tr[2][0]
            person_index = get_nearest_person_index(center,self.people)
            person = self.people[person_index]
            if not check_points_similarity(person.face_points, face_points):
                person.center = center
                person.rect = face_rect
                person.face_points = face_points

            people_updated.append(person)
            del self.people[person_index]
        return people_updated

    def reset_app(self):
        self.tracks = []
        self.people = []
        self.faces_in_frame = 0
        self.lost_face = True


    def run(self):


        """
        caffe.set_mode_gpu()
        caffe.set_device(0)
        """
       
        self.face_det = FaceNet_vcaffe(**FACENET_PARAMS) # method for face detection.

        context = zmq.Context()


        # subscribes to VideoCapture
        vc_socket = context.socket(zmq.SUB)
        vc_socket.setsockopt_string(zmq.SUBSCRIBE, "",encoding='ascii')
        vc_socket.connect(PROT+VIDEOSRC_ADDRESS+':'+self.rec_port)

        # configure output
        publisher = context.socket(zmq.PUB)
        #if publisher detetcts slow subscribers, skips frames
        publisher.sndhwm = 1
        publisher.bind(PROT+'*:'+self.pub_port)


        # PAIR connection to collector
        col_socket = context.socket(zmq.PAIR)
        #col_socket.bind(PROT+'*:'+self.col_port)
        col_socket.connect(PROT+COLLECTOR_ADDRESS+':'+self.col_port)

        # connection to monitor for stats
        self.monitor_stats_sender= context.socket(zmq.PUB)
        self.monitor_stats_sender.connect(PROT+MONITOR_ADDRESS+':'+MONITOR_STATS_IN)

        # manage sending stats to monitor
        self.stats_maker.run_stats_timer(INTERVAL_STATS,self.__send_stats)
        self.stats_maker.run_fps_timer()

        
        
        current_frame = None
        prev_gray = None

        frame_counter = 0

        while True:

            rec_dict,imgs = recv_data(vc_socket,0,False)
            self.stats_maker.received_frames += 1
            current_frame = imgs[0]
            
            vc_frame_idx = rec_dict['frame_idx']
            vc_time = rec_dict['vc_time']

            if time.time() - vc_time > MAX_ALLOWED_DELAY:
                self.stats_maker.skipped_frames += 1
                continue

            try:
                self.displayed_frame = current_frame.copy() # for visualization purpose
                self.ratio = FACE_IMAGE_WIDTH/float(self.displayed_frame.shape[1])
            except Exception as e:
                print('exception in rec frame ',e)
                continue

            #current_frame = resize_image(current_frame) # for computation purpose
            current_frame = imutils.resize(current_frame, width=FACE_IMAGE_WIDTH)
            frame_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY) # gray frame required by tracking system

            #computation of new tracks point from old ones
            if len(self.tracks) > 0 and not self.lost_face:
               
                try:
                    new_tracks  = self.__track_points(prev_gray,frame_gray, self.tracks)
                    
                except Exception as e:
                    print(str(e),'tracks')
                    #a = raw_input('optical_flow')
                    new_tracks = []
                    self.reset_app()
                

                if  len(new_tracks) == 0:
                    self.lost_face = True

                self.tracks = new_tracks

            # computation of new track point through MTCNN
            if frame_counter % DETECTION_INTERVAL == 0 or self.lost_face:
                self.tracks = self.__create_faces_track_points(current_frame)


            self.lost_face = check_lost_face(self.faces_in_frame, self.tracks, LOST_THR)
            # reconstruction of people keypoint from track points
            if not self.lost_face:
                
                try:
                    self.people = self.track_people(current_frame, self.tracks)
                    

                except Exception as e:
                    print(str(e),'res')
                    self.reset_app()
         

            if len(self.people) == 0:
                if len(self.tracks) > 0:
                    self.reset_app()
            
            
            

            res = dict()
            crops = []
            people_ser_to_col =[]
            people_ser_to_algs =[]
            people_to_world = copy.deepcopy(self.people)
            
            for p in people_to_world:

                face = p.rect
                crop = current_frame[int(face['y_topleft']):int(face['y_bottomright']),int(face['x_topleft']):int(face['x_bottomright'])]

                p.rect['y_topleft'] = int(p.rect['y_topleft']/self.ratio)
                p.rect['y_bottomright'] = int(p.rect['y_bottomright']/self.ratio)
                p.rect['x_topleft'] = int(p.rect['x_topleft']/self.ratio)
                p.rect['x_bottomright'] = int(p.rect['x_bottomright']/self.ratio)

                people_ser_to_col.append(p.jsonable())
                
                
                people_ser_to_algs.append(p.jsonable())
                crops.append(np.ascontiguousarray(crop, dtype=np.uint8))

                
            
            res['frame_idx'] = vc_frame_idx
            res['data'] = people_ser_to_algs
            res['fp_time'] = time.time()
            res['vc_time'] = vc_time
            
            # send images to descriptors only if people is detected
            if len(crops) > 0:
                send_data(publisher,crops,0,False,**res)

            #sending data to collector
            col_dict = {'people': people_ser_to_col,'frame_idx':vc_frame_idx,'fp_time':time.time(),'vc_time':vc_time}
            
            #send_data(col_socket,[self.displayed_frame],0,False,**col_dict)
            send_data(col_socket,None,0,False,**col_dict)

            prev_gray = frame_gray
            frame_counter += 1
            
            #clearing memory
            self.displayed_frame= None

            self.stats_maker.elaborated_frames += 1
            self.stats_maker.stat_people = len(people_ser_to_col)
            
            

        print("fp: interrupt received, stopping")
        # clean up
        vc_socket.close()
        col_socket.close()
        publisher.close()
        context.term()

    def __send_stats(self):
        
        stats = self.stats_maker.create_stats()
        stats_dict = {self.__class__.__name__:stats}
        send_data(self.monitor_stats_sender,None,0,False,**stats_dict)


            
            
if __name__ == '__main__':
    

    
    prod = FaceProvider({'in':VC_OUT,'out': FP_OUT,'out_col': FP_OUT_TO_COL })
    prod.start() 

            
            
