import os, shutil, sys, time, re, glob, sys
import numpy as np
import caffe
import cv2
#from PIL import Image
from scipy import misc
import skimage.io
from .happynet.happy_functions import load_mean, create_network,get_best_n_res,get_best_n_res_in_batch
import time
from .emotion_constants import *
from utils.geometric_functions import crop_img
from utils.abstract_descriptor import AbstractDescriptor


#from costants import *

"""
NOTE
Every class must have:
1) method: detect_batch
2) method: refine_classification
3) attribute: win_size
"""




class HappyNet(AbstractDescriptor):

    
    def __init__(self):
      """
      Load Emotion model.
      """
      self.categories =  [ 'Angry' , 'Disgust' , 'Fear' , 'Happy'  , 'Neutral' ,  'Sad' , 'Surprise']  
      self.__setup_net()
      self.win_size = EMO_WIN_SIZE

    def __setup_net(self):
      
      mean = load_mean(MODEL_TYPE)
      self.VGG_S_Net = create_network(mean,MODEL_TYPE,EMO_MODEL)

    

    def detect_batch(self,images):
      """
      It assigns an emotion to each person detected in images

      :type images: list
      :param images: crops of faces

      :rtype: list
      :returns: list of tuples, one per crop, composed of the emotion and the probality associated
      """
      
      batch = []
      for img_o in images:
        img = crop_img(img_o,EMO_CROP_FACTOR)
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = skimage.img_as_float(img).astype(np.float32)
        batch.append(img)
      predictions = self.VGG_S_Net.predict(batch, oversample=False)
      
      emotions = []
      for prediction in predictions:
        max_ind = np.argmax(prediction)
        
        cat = self.categories[max_ind]
        emotions.append((cat,max(prediction)))
      return emotions

    def refine_classification(self,class_results):
      """
      It executes weighted mean of results for each class in a slide window

      :type class_results: list
      :param class_results: list of tuples composed of the class and the probability associated

      :rtype: list
      :returns: list of tuples composed by each emotion and the relative weighted probability
      """
      counter = dict()
      results = []
      for key,prob in class_results:
        
        if key not in counter.keys():
          counter[key] = prob
        else: 
          counter[key]+= prob

      
      for k,v in counter.items():
        norm_value = float(v)/self.win_size
        results.append((k,norm_value))

      
      for em in (set(self.categories) - set(counter.keys())):
        results.append((em,0.0))

      return sorted(results)






"""


class EmotionDetector:

    
    def __init__(self):
    
      self.categories =  [ 'Angry' , 'Disgust' , 'Fear' , 'Happy'  , 'Neutral' ,  'Sad' , 'Surprise']  
      self.__setup_net()
      self.win_size = EMO_WIN_SIZE

    def __setup_net(self):
      cur_dir = os.path.split(os.path.abspath(__file__))[0] # + '/models_2405'

      proto_path = os.path.join(cur_dir, 'models_2405/VGG_S_rgb/deploy.prototxt')
      model_path = os.path.join(cur_dir, 'models_2405/VGG_S_rgb/models2405_iter_610000.caffemodel')
      self.net = cv2.dnn.readNetFromCaffe(proto_path, model_path)

      
      mean = load_mean(MODEL_TYPE)
      self.VGG_S_Net = create_network(mean,MODEL_TYPE,EMO_MODEL) 

    

    def detect_batch(self,images):
     
      
      batch = []
      for img_o in images:
        img = crop_img(img_o,EMO_CROP_FACTOR)
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = skimage.img_as_float(img).astype(np.float32)
        batch.append(img)
      predictions = self.VGG_S_Net.predict(batch, oversample=False)
      
      emotions = []
      for prediction in predictions:
        max_ind = np.argmax(prediction)
        
        cat = self.categories[max_ind]
        emotions.append((cat,max(prediction)))
      return emotions

    def refine_classification(self,class_results):
     
      counter = dict()
      results = []
      for key,prob in class_results:
        
        if key not in counter.keys():
          counter[key] = prob
        else: 
          counter[key]+= prob

      
      for k,v in counter.iteritems():
        norm_value = float(v)/self.win_size
        results.append((k,norm_value))

      
      for em in (set(self.categories) - set(counter.keys())):
        results.append((em,0.0))

      return sorted(results)
"""
   
   