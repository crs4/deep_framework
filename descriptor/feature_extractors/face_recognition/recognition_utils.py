
from face_recognition.recognition_constants import *
import pickle
import os,yaml

cur_dir = os.path.split(os.path.abspath(__file__))[0]
template_model_path = cur_dir + '/template_models'
probabilities_path = cur_dir + '/face_extractor/conf_probs.yaml'

def load_models():
    """
    Load face models

    :rtype: boolean
    :returns: True if models were successfully loaded,
              False otherwise
    """

    models = None
    
    # File where models are saved
    db_file_path = os.path.join(template_model_path, FACE_MODELS_FILE)

    # Check if file with models exist
    if os.path.exists(db_file_path):
        with open(db_file_path, 'rb') as f:
            # Load models
            models = pickle.load(f,encoding='bytes')
    return models

def get_tags():
    """
    Get all tags

    :rtype: set
    :returns: a set containing all tags
    """

    tag = UNDEFINED_TAG

    # Load file with tag-label associations
    tag_label_associations_file_name = TAG_LABEL_ASSOCIATIONS_FILE + '_facenet.yaml'
    tag_label_associations_file_path = os.path.join(
        template_model_path, tag_label_associations_file_name)
    tag_label_associations = load_YAML_file(
        tag_label_associations_file_path)

    tags = list(tag_label_associations.values())

    return tags

def load_probabilities():
    probs_dict = load_YAML_file(probabilities_path)
    return probs_dict

def get_probability(conf_probs ,distance, label):
    ratio = conf_probs['ratio']
    rounded_conf = int(round(distance * ratio))
    if label == UNDEFINED_LABEL:
        prob = 1.0
        if rounded_conf in conf_probs['unknown']:
            prob = conf_probs['unknown'][rounded_conf]
    else:
        prob = 0.0
        if rounded_conf in conf_probs['known']:
            prob = conf_probs['known'][rounded_conf]
    return prob

def load_YAML_file(file_path):
    """
    Load YAML file.

    :type file_path: string
    :param file_path: path of YAML file to be loaded

    :rtype: dictionary or list
    :returns: the contents of the file
    """

    try:

        with open(file_path, 'r') as stream:
            data = yaml.load(stream)
            return data

    except IOError as e:
        error_str = "I/O error({0}): {1}".format(e.errno, e.strerror)
        print(error_str)
        print('Unable to load %s' % file_path)
        return None

    except:
        print("Unexpected error:", sys.exc_info()[0])
        return None