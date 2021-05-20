


import caffe
import os
import numpy as np
import time

cur_dir = os.path.split(os.path.abspath(__file__))[0] + '/age_model_rothe'

def load_mean():
    """
    Load mean file
    """
    mean_image_file_path = os.path.join(cur_dir,'ilsvrc_2012_mean.npy')
    mean_values = np.load(mean_image_file_path)
    mean_values_shape = mean_values.shape
    if len(mean_values_shape) == 3:
        mean_values = mean_values.mean(1).mean(1)  # average over pixels to obtain the mean (BGR) pixel values
    elif len(mean_values_shape) == 4:
        mean_values = mean_values.mean(2).mean(2)
        mean_values = mean_values[0]
    else:
        print('Warning! Mean shape has %d axis instead of 3 or 4' % len(mean_values_shape))
    
    return mean_values


def create_transformer(network, mean_values):
    """
    Create transforem related to the netwrok
    """
    age_transformer = caffe.io.Transformer({'data': network.blobs['data'].data.shape})

    age_transformer.set_transpose('data', (2, 0, 1))     # Move image channels to outermost dimension
    age_transformer.set_mean('data', mean_values)        # Subtract the dataset-mean value in each channel
    age_transformer.set_raw_scale('data', 255)           # Rescale from [0, 1] to [0, 255]
    age_transformer.set_channel_swap('data', (2, 1, 0))  # Swap channels from RGB to BGR
    return age_transformer


def create_network(mean,model):
    """
    Create network
    """
    net_pretrained = os.path.join(cur_dir,model)
    net_model_file = os.path.join(cur_dir,'age.prototxt')
    net = caffe.Classifier(net_model_file, net_pretrained,
                       mean=mean,
                       channel_swap=(2,1,0),
                       raw_scale=255,
                       image_dims=(224, 224))
    return net

