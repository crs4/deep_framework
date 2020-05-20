

import cv2
import numpy as np


from geometric_functions import resize_image

thick_factor = 0.005


def __list_images_in_folder(folder_path):
    images_format = ['png']
    images_path = []
    for f in os.listdir(folder_path):
        ext = f.split('.')[1]
        if ext.lower() not in images_format:
            continue
        images_path.append(os.path.join(folder_path,f))
    return images_path


def draw_keypoints(img, keypoints,color):
    
    for i,p in enumerate(keypoints):
        x,y = int(p[0][0]),int(p[0][1])
        cv2.circle(img,(x,y), 3, (200*i,0,200/i), -1)




def draw_emotion_classification(img,rect,emotions):
    x = int(rect['x_topleft'])
    y = int(rect['y_topleft'])
    dx = int(rect['x_bottomright']) - x
    dy = int(rect['y_bottomright']) - y
    w_emoji = int(dx*0.13) #*int(img.shape[1]*0.1)
    overlay = img.copy()

    emoji_paths = __list_images_in_folder('utils/emoji/')
    emoji_dicts = {}
    for em_path in emoji_paths:
        emoji_orig = cv2.imread(em_path)
        key = os.path.basename(em_path).split('.')[0]
        emoji_dicts[os.path.basename(key)] = emoji_orig

    alpha = 0.5
    for index, emo in enumerate(sorted(emotions)):
        emo_str,emo_val = emo
        emoji_o = emoji_dicts[emo_str.lower()]
        emoji = cv2.resize(emoji_o, (w_emoji,w_emoji), interpolation = cv2.INTER_AREA)
        try:
            img[(index * w_emoji + y + int(img.shape[0]*0.01)):(index * w_emoji + y +int(img.shape[0]*0.01)+emoji.shape[0]), (int(img.shape[0]*0.02)+x):(int(img.shape[0]*0.02)+x+emoji.shape[1])] = emoji
        except Exception as e:
            print e
            continue
        
        cv2.rectangle(overlay, ( x+int(img.shape[0]*0.02) + w_emoji , index * w_emoji +int(img.shape[0]*0.01) + y), ( x+ int(img.shape[0]*0.02) + int(emo_val * 100) + w_emoji, index * w_emoji +int(img.shape[0]*0.01) + y + w_emoji ), (0, 0, 0), -1)
    
        #cv2.putText(img, emo_str, (10+x + w_emoji, index * w_emoji +25 + y), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1)
    cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)



def draw_people(img,face_rect,color):
    thickness = 2#int(img.shape[0]*thick_factor)
    #cv2.circle(img,(int(person.center[0]),int(person.center[1])), 5, person.color, -1)
    cv2.rectangle(img,(int(face_rect['x_topleft']),int(face_rect['y_topleft'])),(int(face_rect['x_bottomright']),int(face_rect['y_bottomright'])),color,thickness)

def draw_pose(img,rect,classification):
    thickness = 2#int(img.shape[0]*thick_factor)
    deg = classification
    
    x_br = int(rect['x_bottomright'])
    x_tl = int(rect['x_topleft'])
    dx = int((x_br - x_tl) / 2)
    x_degree = int((x_br - dx - int((float(deg)/80)*dx)))
    y_degree = int((rect['y_bottomright'])) + int(img.shape[0]*0.03)
    cv2.circle(img,(x_degree,y_degree), thickness*2, (0,0,255), -1)
    cv2.putText(img, 'pose: '+str(classification), ( int(rect['x_topleft']) , int( (rect['y_bottomright'] -  img.shape[0]*0.01) )), cv2.FONT_HERSHEY_PLAIN, thickness, (0, 0, 255), thickness)


def draw_glasses(img,rect,classification):
    thickness = 2
    
    cv2.putText(img, str(classification), (int(rect['x_topleft']),int(rect['y_topleft'])), cv2.FONT_HERSHEY_PLAIN, thickness, (255, 0, 0), thickness)


def draw_clothes(img,rect,classification):
    thickness = 2
    
    cv2.putText(img, str(classification), (int(rect['x_topleft']),int(rect['y_topleft'])), cv2.FONT_HERSHEY_PLAIN, thickness, (255, 0, 0), thickness)


def draw_eye(img,rect):

    
    cv2.rectangle(img,(int(rect['x_topleft']),int(rect['y_topleft'])),(int(rect['x_bottomright']),int(rect['y_bottomright'])),(255,255,255),3)


def draw_age(img,rect,classification):
    thickness = 2#int(img.shape[0]*thick_factor)
    
    cv2.putText(img, 'Age: '+str(classification).replace(',','-').strip('()'), (int(rect['x_topleft']) ,int((rect['y_topleft']- int(img.shape[0]*0.03)))), cv2.FONT_HERSHEY_PLAIN, thickness, (255, 0, 0), thickness)

def draw_gender(img,rect,classification):
    thickness = 2#int(img.shape[0]*thick_factor)
    
    cv2.putText(img, 'Gender: '+classification, (int(rect['x_topleft']),int(rect['y_topleft'])), cv2.FONT_HERSHEY_PLAIN, thickness, (255, 0, 0), thickness)

def draw_recognition(img,rect,classification):
    thickness = 2#int(img.shape[0]*thick_factor)
    
    cv2.putText(img, 'Name: '+classification, (int(rect['x_topleft']),int((rect['y_topleft']- int(img.shape[0]*0.06)))), cv2.FONT_HERSHEY_PLAIN, thickness, (255, 0, 0), thickness)

