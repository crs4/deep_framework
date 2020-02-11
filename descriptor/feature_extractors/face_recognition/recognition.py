import numpy as np
import cv2
from scipy import misc
from face_recognition.recognition_constants import *
from face_recognition.recognition_utils import load_models, get_tags, load_probabilities, get_probability
from face_recognition.facenet.src import facenet
import os
from operator import itemgetter
import sys
import tensorflow as tf
from utils.abstract_descriptor import AbstractDescriptor

#from constants import *


"""
NOTE
Every class must have:
1) method: detect_batch
2) method: refine_classification
3) attribute: win_size
"""



class FaceRecognition(AbstractDescriptor):

    
    def __init__(self):
      """
      Load face recognition model.
      """
      self.win_size = RECOG_WIN_SIZE
      self.template_models = load_models()
      self.tags = get_tags()
      self.probabilities = load_probabilities()
      self.__setup_net()
      

    def __setup_net(self):
      model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),FACENET_MODEL_PATH)

      with tf.Graph().as_default():
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.Session(config=config)

        with self.sess.as_default():
          facenet.load_model(model_path)
          # Get input and output tensors
          self.images_placeholder = tf.get_default_graph().get_tensor_by_name('input:0')
          self.embeddings = tf.get_default_graph().get_tensor_by_name('embeddings:0')
          self.phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")



    def __features_computation(self,imgs):
      """
      Computes probe features.

      :type imgs: list
      :param imgs: probe images

      :rtype: list
      :returns: list of features for each image
      """

      # Run forward pass to calculate embedding
      feed_dict = {self.images_placeholder: imgs, self.phase_train_placeholder: False}
      probe_features = self.sess.run(self.embeddings, feed_dict=feed_dict)
      return probe_features

    def __probe_templates_distance_computation(self,probe_features, template_features, template_labels):
      """
      Computes distance between probe features and each trempalte features.

      :type probe_features: list
      :param imgs: list of probe features

      :type template_features: list
      :param imgs: list of template features

      :type template_labels: list
      :param imgs: list of template labels

      :rtype: list
      :returns: list of tuples composed of the label of the template 
      """

      result = []
      for probe in probe_features:
        label = UNDEFINED_LABEL
        conf = sys.maxsize
        for t in range(0, len(template_features)):
          template = template_features[t, :]

          # Calculate distance between faces
          diff = np.sqrt(np.sum(np.square(np.subtract(probe, template))))

          if ((diff < conf) and
                  (diff < FACE_REC_THRESHOLD)):
              conf = diff
              label_index = template_labels[t]
              label = self.tags[label_index]

        prob = get_probability(self.probabilities,conf,label)
        result.append((label, prob))
      return result
    

    def detect_batch(self,images):
      """
      Assigns a label to each person detected in images

      :type images: list
      :param images: crops of faces

      :rtype: list
      :returns: list of tuples composed of the label of the template
      """
      
      batch = []
      for img in images:
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        aligned_face = misc.imresize(
                img, (FACENET_ALIGNED_FACE_SIZE,FACENET_ALIGNED_FACE_SIZE), interp='bilinear')
        face = facenet.prewhiten(aligned_face)
        batch.append(face)

      imgs = np.stack(batch)
      probe_features = self.__features_computation(imgs)

      template_features= self.template_models['reps']
      template_labels = self.template_models['labels']
      results = self.__probe_templates_distance_computation(probe_features,template_features,template_labels)
      return results
      

    def refine_classification(self,class_results):
      """
      Executes mean of results for each class in a slide window for each class

      :type class_results: list
      :param class_results: 

      :rtype: list
      :returns: list of tuples composed of the label of the template
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

      sorted_by_prob = sorted(results, key=itemgetter(1), reverse = True)
      return sorted_by_prob[0][0]
      
   