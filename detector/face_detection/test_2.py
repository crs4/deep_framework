

from utils.geometric_functions import *
from utils.features import Point,Rect



top_left_point_a = Point(0,0)
bottom_right_point_a = Point(2,2)

top_left_point_b = Point(-1,+1)
bottom_right_point_b = Point(+1,+3)


rect_a = Rect(top_left_point_a, bottom_right_point_a)

rect_b = Rect(top_left_point_b, bottom_right_point_b)


res1 = get_int_over_union(rect_a,rect_b)


#res2 = bb_intersection_over_union(rect_a,rect_a)


print('res1: ', res1)
#print('res2: ', res2)