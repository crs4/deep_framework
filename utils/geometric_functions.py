
import cv2
import numpy as np
import sys
from scipy.spatial import distance
from utils.features import Rect, Point

def get_int_over_union(rect1, rect2):
    """
    Get ratio of intersected areas to joined areas between two rectangles

    :type rect1: tuple
    :param rect1: first rectangle given as (x, y, width, height)

    :type rect1: tuple
    :param rect1: second rectangle given as (x, y, width, height)
    """
    
    rect1_x1 = rect1.top_left_point.x_coordinate
    rect1_y1 = rect1.top_left_point.y_coordinate
    rect1_x2 = rect1.bottom_right_point.x_coordinate
    rect1_y2 = rect1.bottom_right_point.y_coordinate

    rect2_x1 = rect2.top_left_point.x_coordinate
    rect2_y1 = rect2.top_left_point.y_coordinate
    rect2_x2 = rect2.bottom_right_point.x_coordinate
    rect2_y2 = rect2.bottom_right_point.y_coordinate

    # Calculate area of intersection
    int_width = max(min(rect1_x2, rect2_x2) - max(rect1_x1, rect2_x1), 0)
    int_height = max(min(rect1_y2, rect2_y2) - max(rect1_y1, rect2_y1), 0)
    int_area = int_width * int_height

    # Calculate area of union
    area_rect1 = (rect1_x2 - rect1_x1) * (rect1_y2 - rect1_y1)
    area_rect2 = (rect2_x2 - rect2_x1) * (rect2_y2 - rect2_y1)
    union_area = area_rect1 + area_rect2 - int_area

    ratio = float(int_area) / union_area

    return ratio




def get_rect_around_points(img_w,img_h,points, delta_facerect=1,delta_eye_w=1,delta_eye_h=1, de=None):
    """
    This function computes rectangle around points in a dynamic way related to keypoints distances
    """
    
    
    if len(points) > 1:
        points = list(points.values())
        (x,y,w,h) = cv2.boundingRect(np.array(points, np.float32) )
        dx = int(delta_facerect*w) #80
        dy = int(delta_facerect*h) #80
    else:
        (x,y,w,h) = (points[0][0], points[0][1],0,0)
        dx = int(delta_eye_w * de) 
        dy = int(delta_eye_h * de)

    # dx e dy servono per regolare l'ampiezza del rettangolo attorno alla faccia in maniera dinamica
    # in base ai keypoints calcolati dall'algoritmo. Sono stati calcolati in maniera euristica
    
   
    x_topleft = (x-dx) if (x-dx) > 0 else 0
    y_topleft = (y-dy) if (y-dy) > 0 else 0
    x_bottomright = (x+w+dx) if (x+w+dx) < img_w else img_w
    y_bottomright = (y+h+int(dy)) if (y+h+int(dy)) < img_h else img_h
    rect = {'x_topleft':x_topleft,'y_topleft':y_topleft, 'x_bottomright':x_bottomright, 'y_bottomright':y_bottomright}#(x_topleft,y_topleft, x_bottomright, y_bottomright)

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

def iou(rect_a,rect_b):

    dx = min(rect_a['x_bottomright'],rect_b['x_bottomright']) - max(rect_a['x_topleft'],rect_b['x_topleft'])

    dy = min(rect_a['y_bottomright'],rect_b['y_bottomright']) - max(rect_a['y_topleft'],rect_b['y_topleft'])


    intersection_area = dx*dy

    a_area = ((rect_a['x_bottomright']-rect_a['x_topleft']) * (rect_a['y_bottomright'] -rect_a['y_topleft']))
    b_area = ((rect_b['x_bottomright']-rect_b['x_topleft']) * (rect_b['y_bottomright'] -rect_b['y_topleft']))
    
    union_area = a_area * b_area - intersection_area
    iou = intersection_area / float(union_area)
    return iou

def check_point_in_rect(point,rect):
    x0 = point[0]
    y0 = point[1]

    if x0 < rect['x_bottomright'] and x0 > rect['x_topleft'] and y0 < rect['y_bottomright'] and y0 > rect['y_topleft']:
        return True

    return False




