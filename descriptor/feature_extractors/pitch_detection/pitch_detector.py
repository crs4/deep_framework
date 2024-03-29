import numpy as np
import cv2
#from scipy import misc
#import skimage.io
import os
from operator import itemgetter
import sys
import tensorflow as tf
from .pitch.deepgaze.head_pose_estimation import CnnHeadPoseEstimator
from .pitch_constants import *
from utils.abstract_descriptor import AbstractDescriptor



"""
NOTE
Every class must have:
1) method: detect_batch
2) method: refine_classification
3) attribute: win_size
"""



class PitchNet(AbstractDescriptor):

    win_size = PITCH_WIN_SIZE
    def __init__(self):
      """
      Load pose model.
      """
      
      self.__setup_net()



    def __setup_net(self):

      
      gaze_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'pitch/etc/tensorflow/head_pose/')
    
      config = tf.ConfigProto()
      config.gpu_options.allow_growth = True
      
      with tf.Graph().as_default():
        self.sess = tf.Session(config=config)
        with self.sess.as_default():
          self.my_head_pose_estimator = CnnHeadPoseEstimator(self.sess) #Head pose estimation object
          # Load the weights from the configuration folders
          self.my_head_pose_estimator.load_pitch_variables(gaze_path +'pitch/cnn_cccdd_30k.tf')          



    def detect_batch(self,detector_results,images):
      """
      Evaluates pose (pitch) for each person detected in images

      :type images: list
      :param images: crops of faces

      :rtype: list
      :returns: list of tuples composed of the pitch of the person
      """
      
      results = []
      for img in images:
        max_dim = max(img.shape)
        if max_dim < 64:
          max_dim = 64
        resized = cv2.resize(img, (max_dim,max_dim), interpolation = cv2.INTER_AREA)
        pitch = self.my_head_pose_estimator.return_pitch(resized)[0,0,0]  # Evaluate the pitch angle using a CNN
        results.append(pitch)

      return results
      

    def refine_classification(self,class_results):
      """
      Executes mean of results in a slide window

      :type class_results: list
      :param class_results: list of poses each for frame analyzed 

      :rtype: integer
      :returns: mean of poses values
      """
      acc = 0
      for res in class_results:
        acc = acc + res

      ref = int(acc/len(class_results))
      return ref
      
   