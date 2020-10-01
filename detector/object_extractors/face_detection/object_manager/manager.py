

import uuid
import sys
from utils.geometric_functions import get_rect_around_points
from utils.check_functions import check_points_similarity
from scipy.spatial import distance
from face_detection.face_detection_constants import *


class Person():
    
    def __init__(self,face_rect, face_points, center):
        self.rect=face_rect
        self.face_points = face_points
        self.center = center
        self.pid= uuid.uuid4()

    def jsonable(self):
        points_ser = {k: str(v[0]) for k, v in self.face_points.items()}
        d = dict(points=points_ser, rect=self.rect, center=str(self.center[0]), pid=str(self.pid))
        return d





class ObjectManager:
    def __init__(self):
        self.faces_in_frame = 0
        self.people = []



    def check_people(self,features):

        mtcnn_points = features['points']
        mtcnn_faces = features['boxes']
        diff_faces = ( len(mtcnn_faces) - len(self.people) )

        # checks if any person appears in scene
        if diff_faces > 0:
            self.people = self.__init_people(mtcnn_points,mtcnn_faces,self.people)
        #checks if any person disappears from scene
        if diff_faces < 0:
            self.people = self.__check_departed_people(mtcnn_points, self.people, diff_faces)
        
        self.faces_in_frame = len(mtcnn_faces)
  
    def track_people(self,frame,tracks):
        people_updated = []
        tracks_split = [tracks[i:i+LOST_THR] for i in range(0,len(tracks),LOST_THR)]
        for tr in tracks_split:
            
            face_points = {'right_eye':tr[0],'left_eye':tr[1],'nose':tr[2],'right_mouth':tr[3],'left_mouth':tr[4]}

            face_rect = get_rect_around_points(frame.shape[1],frame.shape[0],face_points,delta_facerect=DELTA_RECT)
            center = tr[2][0]
            person_index = self.__get_nearest_person_index(center,self.people)
            person = self.people[person_index]
            if not check_points_similarity(person.face_points, face_points,DST_THR):
                person.center = center
                person.rect = face_rect
                person.face_points = face_points

            people_updated.append(person)
            del self.people[person_index]
            
        self.people = people_updated
        return people_updated




    def __get_nearest_person_index(self,center,people):
        """
        Returns the index of person in people nearest to center
        """

        min_dist = sys.maxsize
        min_person_ind = None
        for j,person in enumerate(people):

            #if len(person['center']) == 0:
            #   continue 

            dst = distance.euclidean(center, person.center)#['center'])
            if dst < min_dist:
                min_dist = dst
                min_person_ind = j

        return min_person_ind




    def __check_departed_people(self,new_faces,people, num_departed):
        """
        This function tracks person from people to new faces if present
        """
        temp_results = []
        results = []
        for i,new_face in enumerate(new_faces):

            for j,old_face in enumerate(people):
                
                center_new_face = new_face['nose']#new_face[2],new_face[7]
                center_old_face = old_face.center#['center']
                
                dist = distance.euclidean(tuple(center_old_face),center_new_face)

                temp_results.append((j,dist))

        temp_results.sort(key=lambda tup: tup[1])
        
        for res in temp_results[:num_departed]:
            results.append(people[res[0]])

        return results

    def __init_people(self,mtcnn_points, mtcnn_faces, old_people):
        """
        This function update people already present in previous frames and creates new one
        """
        result_people = []

        count_match = 0

        for i,face in enumerate(mtcnn_points):
            #print i, 'face'
            mouth_measure = distance.euclidean(face['right_mouth'],face['left_mouth'])
            nose = tuple(face['nose'])
            assigned = False
            for person in old_people[count_match:]:
                #print 'p'
                dist = distance.euclidean(person.center,nose)
                if dist < mouth_measure:
                    count_match+=1
                    assigned = True
                    #print 'match' ,count_match
                    result_people.append(person)
                    break
                    

            if not assigned:
                #print 'new'
                face_rect = mtcnn_faces[i]
                
                new_person = Person(face_rect, face, nose)
                result_people.append(new_person)

        return result_people




