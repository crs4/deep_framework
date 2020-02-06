
import caffe
import os
import numpy as np
import time
cur_dir = os.path.split(os.path.abspath(__file__))[0] + '/models_2405'

def load_mean(model_type):
    mean_filename=os.path.join(cur_dir,model_type,'mean.binaryproto')
    proto_data = open(mean_filename, "rb").read()
    a = caffe.io.caffe_pb2.BlobProto.FromString(proto_data)
    mean = caffe.io.blobproto_to_array(a)[0]
    return mean


def create_network(mean,model_type,model):
    net_pretrained = os.path.join(cur_dir,model_type,model)
    net_model_file = os.path.join(cur_dir,model_type,'deploy.prototxt')
    VGG_S_Net = caffe.Classifier(net_model_file, net_pretrained,
                       mean=mean,
                       channel_swap=(2,1,0),
                       raw_scale=255,
                       image_dims=(256, 256))
    return VGG_S_Net

#return list of tuple as (category, probability) ordered by probability
def get_best_n_res(prediction, categories, n):
    
    best_nres = []
    if n > categories:
      print('Error. Too many classes requested. N set to all categories')
      n = len(categories)

    ind = np.argsort(prediction[0])
    res = np.array(categories)[ind][-n:]

    pred_sorted = np.flipud(prediction[0][ind][-n:])
    
    cat_sorted = np.flipud(res)
    for pred, cat in zip(pred_sorted,cat_sorted):
      best_nres.append((cat,pred))
    
    return best_nres


#return list of tuple as (category, probability) ordered by probability
def get_best_n_res_in_batch(predictions, categories, n):
    
    result = []
    if n > categories:
      print('Error. Too many classes requested. N set to all categories')
      n = len(categories)
    
    for prediction in predictions:
      best_nres = []

      ind = np.argsort(prediction)
      res = np.array(categories)[ind][-n:]

      pred_sorted = np.flipud(prediction[ind][-n:])
      
      cat_sorted = np.flipud(res)
      for pred, cat in zip(pred_sorted,cat_sorted):
        best_nres.append((cat,pred))
      result.append(best_nres)
      
    return result[0]

