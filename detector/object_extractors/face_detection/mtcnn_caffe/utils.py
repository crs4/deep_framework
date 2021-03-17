




def format_points(points):
    formatted = []
    
    for face_points in points:
        num_points = len(face_points)
        keypoints = {'right_eye':[],'left_eye':[],'nose':[],'right_mouth':[],'left_mouth':[]}
        for px, py,key in zip(face_points[:int(num_points / 2)], face_points[int(num_points / 2):],keypoints.keys()):
            #cv2.circle(img, (px, py), 5, (255, 0, 0), -1)
            temp = [[px,py]]
            keypoints[key] = temp
        formatted.append(keypoints)

    return formatted


def format_bbox(rects):
    formatted = []
    
    for rect in rects:
        if rect[0] < 0:
            rect[0] = 0
        if rect[1] < 0:
            rect[1] = 0
        rectd = {'x_topleft':rect[0],'y_topleft':rect[1], 'x_bottomright':rect[2], 'y_bottomright':rect[3],'accuracy':rect[4]}
        
        formatted.append(rectd)

    return formatted