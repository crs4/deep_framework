from collections import Counter
from scipy.spatial import distance
from .geometric_functions import get_rect_around_points
from .person import Person
import cv2
import random



	





"""
def check_departed_people(new_faces,people, num_departed):
	"""
	#This function tracks person from people to new faces if present
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
"""



def check_lost_face(num_faces, track_points,lost_thr):
	"""
	This function check if some track point is lost
	"""

	# supposed  5 points for face
	temp = lost_thr * num_faces
	if len(track_points) < temp or num_faces == 0:
		return True
	return False
   
"""
def init_people(mtcnn_points, mtcnn_faces, old_people):
	"""
	#This function update people already present in previous frames and creates new one
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

"""
def check_points_similarity(old_points,new_points):
	if len(old_points.keys()) != len(new_points.keys()):
		return False
	acc_dist = 0
	for old_name,old_value in old_points.items():
		new_value = new_points[old_name]
		dist = distance.euclidean(tuple(new_value[0]),tuple(old_value[0]))
		acc_dist = acc_dist + dist
	if acc_dist < 15:
		return True
	else:
		return False










	





