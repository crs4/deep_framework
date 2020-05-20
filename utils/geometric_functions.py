
import cv2
import numpy as np
import sys
from scipy.spatial import distance
from utils.features import Rect, Point



def get_rect_around_points(img_w,img_h,points, delta_rect=1):
    """
    This function computes rectangle around points in a dynamic way related to keypoints distances

    """
    
    points = [ [[p.x_coordinate,p.y_coordinate]] for p in points ]
    (x,y,w,h) = cv2.boundingRect(np.array(points, np.float32) )
    dx = int(delta_rect*w) #80
    dy = int(delta_rect*h) #80
    

    # dx e dy servono per regolare l'ampiezza del rettangolo attorno alla faccia in maniera dinamica
    # in base ai keypoints calcolati dall'algoritmo. Sono stati calcolati in maniera euristica
    
   
    x_topleft = (x-dx) if (x-dx) > 0 else 0
    y_topleft = (y-dy) if (y-dy) > 0 else 0
    x_bottomright = (x+w+dx) if (x+w+dx) < img_w else img_w
    y_bottomright = (y+h+int(dy)) if (y+h+int(dy)) < img_h else img_h
    p_top_left = Point(x_topleft,y_topleft)
    p_bottom_right = Point(x_bottomright,y_bottomright)
    rect = Rect(p_top_left,p_bottom_right)

    return rect

def crop_img(img,crop_factor):

    w = img.shape[1]
    h = img.shape[0]

    dx = int(crop_factor*w) #80
    dy = int(crop_factor*h) #80

    x_topleft = dx
    y_topleft = dy
    x_bottomright = w-dx
    y_bottomright = h-dy

    crop = img[y_topleft:y_bottomright,x_topleft:x_bottomright]
    return crop




def get_nearest_person_index(center,people):
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








def resize_image(img,frame_width_for_computation):
    ratio = frame_width_for_computation/float(img.shape[1])
    temp_h = int(img.shape[0] * ratio)
   
    dim = (frame_width_for_computation, temp_h)
     
    # perform the actual resizing of the image 
    resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    return resized

def area_intersection(rect_a,rect_b):

    dx = min(rect_a['x_bottomright'],rect_b['x_bottomright']) - max(rect_a['x_topleft'],rect_b['x_topleft'])

    dy = min(rect_a['y_bottomright'],rect_b['y_bottomright']) - max(rect_a['y_topleft'],rect_b['y_topleft'])


    
    a_area = ((rect_a['x_bottomright']-rect_a['x_topleft']) * (rect_a['y_bottomright'] -rect_a['y_topleft']))
    b_area = ((rect_b['x_bottomright']-rect_b['x_topleft']) * (rect_b['y_bottomright'] -rect_b['y_topleft']))
    if (dx>=0) and (dy>=0):
        return float(dx*dy)/min(a_area,b_area)

def check_point_in_rect(point,rect):
    x0 = point[0]
    y0 = point[1]

    if x0 < rect['x_bottomright'] and x0 > rect['x_topleft'] and y0 < rect['y_bottomright'] and y0 > rect['y_topleft']:
        return True

    return False




