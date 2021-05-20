from keras.preprocessing.image import img_to_array
from keras.models import load_model
from keras.backend.tensorflow_backend import set_session

import cv2
import numpy as np
import os
import pickle
import tensorflow as tf
import yaml

cwd = os.path.dirname(os.path.abspath(__file__))

# Clothing models
CLOTHING_MODELS_PATH = os.path.join(cwd, 'models')

# Directory with clothing lists
CLOTHING_LISTS_DIR = os.path.join(cwd, 'garments')


def load_models(params_path=os.path.join(cwd, 'classif_params.yaml')):
    """
    Load models, binarizers and text files with lists of garments

    :type params_path: string
    :param params_path: path of file with classification parameters

    """

    # Load parameters
    with open(params_path) as stream:
        params = yaml.load(stream)
    try:
        clothing_model = params['clothing_model']
        whole_body_list_file = params['whole_body_list']
        top_list_file = params['top_list']
        bottom_list_file = params['bottom_list']
    except KeyError as e:
        print('%s key is not present in parameters file' % e)
        return

    # Read files with lists
    whole_body_list = []
    whole_body_list_file_path = os.path.join(CLOTHING_LISTS_DIR, whole_body_list_file)
    with open(whole_body_list_file_path) as stream:
        whole_body_list = stream.read().splitlines()

    top_list = []
    top_list_file_path = os.path.join(CLOTHING_LISTS_DIR, top_list_file)
    with open(top_list_file_path) as stream:
        top_list = stream.read().splitlines()

    bottom_list = []
    bottom_list_file_path = os.path.join(CLOTHING_LISTS_DIR, bottom_list_file)
    with open(bottom_list_file_path) as stream:
        bottom_list = stream.read().splitlines()

    # Paths to model and binarizers for classification of whole body crop
    clothing_model_path = os.path.join(
        CLOTHING_MODELS_PATH, clothing_model, 'model.h5'
    )
    clothing_cat_bin_path = os.path.join(
        CLOTHING_MODELS_PATH, clothing_model, 'category_bin.pickle'
    )
    clothing_col_bin_path = os.path.join(
        CLOTHING_MODELS_PATH, clothing_model, 'color_bin.pickle'
    )
    whole_body_model_path = None
    whole_body_cat_bin_path = None
    whole_body_col_bin_path = None
    if 'whole_body_model' in params:
        whole_body_model = params['whole_body_model']
        whole_body_model_path = os.path.join(
            CLOTHING_MODELS_PATH, whole_body_model, 'model.h5'
        )
        whole_body_cat_bin_path = os.path.join(
            CLOTHING_MODELS_PATH, whole_body_model, 'category_bin.pickle'
        )
        whole_body_col_bin_path = os.path.join(
            CLOTHING_MODELS_PATH, whole_body_model, 'color_bin.pickle'
        )

    # Paths to model and binarizers for classification of top body crop
    top_model_path = None
    top_cat_bin_path = None
    top_col_bin_path = None
    if 'top_model' in params:
        top_model = params['top_model']
        top_model_path = os.path.join(
            CLOTHING_MODELS_PATH, top_model, 'model.h5'
        )
        top_cat_bin_path = os.path.join(
            CLOTHING_MODELS_PATH, top_model, 'category_bin.pickle'
        )
        top_col_bin_path = os.path.join(
            CLOTHING_MODELS_PATH, top_model, 'color_bin.pickle'
        )

    # Paths to model and binarizers for classification of bottom body crop
    bottom_model_path = None
    bottom_cat_bin_path = None
    bottom_col_bin_path = None
    if 'bottom_model' in params:
        bottom_model = params['bottom_model']
        bottom_model_path = os.path.join(
            CLOTHING_MODELS_PATH, bottom_model, 'model.h5'
        )
        bottom_cat_bin_path = os.path.join(
            CLOTHING_MODELS_PATH, bottom_model, 'category_bin.pickle'
        )
        bottom_col_bin_path = os.path.join(
            CLOTHING_MODELS_PATH, bottom_model, 'color_bin.pickle'
        )

    # Load the trained convolutional neural network and the label binarizers for classification of whole body crop
    clothing_model = load_model(clothing_model_path, custom_objects={'tf': tf})
    
    clothing_category_bin = pickle.loads(open(clothing_cat_bin_path, 'rb').read())
    clothing_color_bin = pickle.loads(open(clothing_col_bin_path, 'rb').read())
    whole_body_model = None
    whole_body_category_bin = None
    whole_body_color_bin = None
    if whole_body_model_path is not None:
        whole_body_model = load_model(whole_body_model_path, custom_objects={'tf': tf})
        whole_body_category_bin = pickle.loads(open(whole_body_cat_bin_path, 'rb').read())
        whole_body_color_bin = pickle.loads(open(whole_body_col_bin_path, 'rb').read())

    # Load the trained convolutional neural network and the label binarizers for classification of top body crop
    top_model = None
    top_category_bin = None
    top_color_bin = None
    if top_model_path is not None:
        top_model = load_model(top_model_path, custom_objects={'tf': tf})
        top_category_bin = pickle.loads(open(top_cat_bin_path, 'rb').read())
        top_color_bin = pickle.loads(open(top_col_bin_path, 'rb').read())

    # Load the trained convolutional neural network and the label binarizers for classification of bottom body crop
    bottom_model = None
    bottom_category_bin = None
    bottom_color_bin = None
    if bottom_model_path is not None:
        bottom_model = load_model(bottom_model_path, custom_objects={'tf': tf})
        bottom_category_bin = pickle.loads(open(bottom_cat_bin_path, 'rb').read())
        bottom_color_bin = pickle.loads(open(bottom_col_bin_path, 'rb').read())

    models_dict = dict(clothing_model=clothing_model,clothing_category_bin=clothing_category_bin,clothing_color_bin=clothing_color_bin,
        whole_body_list=whole_body_list,top_list=top_list,bottom_list=bottom_list,params=params,whole_body_model=whole_body_model,
        whole_body_category_bin=whole_body_category_bin, whole_body_color_bin=whole_body_color_bin,top_model=top_model, 
        top_category_bin=top_category_bin, top_color_bin=top_color_bin,bottom_model=bottom_model,
         bottom_category_bin=bottom_category_bin, bottom_color_bin=bottom_color_bin)

    return models_dict


def get_sub_results(all_labels, all_probs, clothing_list):
    """
    Get results related only to given clothing list

    :type all_labels: list
    :param all_labels: list with all labels

    :type all_probs: list
    :param all_probs: list with all probabilities

    :type clothing_list: list
    :param clothing_list: list of relevant clothing items

    :rtype: tuple
    :returns: a (rel_labels, rel_probs) tuple,
              where rel_labels contains the relevant labels
              and rel_probs contains the corresponding normalized probabilities
    """

    # Get total probability related to relevant clothing items
    tot_prob = 0.0
    label_counter = 0
    for label in all_labels:
        if label in clothing_list:
            prob = all_probs[label_counter]
            tot_prob += prob
        label_counter += 1

    # Select only relevant labels and normalize corresponding probabilities
    rel_labels = []
    rel_probs = []
    label_counter = 0
    for label in all_labels:
        if label in clothing_list:
            prob = all_probs[label_counter]
            prob = prob / tot_prob
            rel_labels.append(label)
            rel_probs.append(prob)
        label_counter += 1

    return rel_labels, rel_probs


def classify_loaded_images(images, models_dict):
    """
    :type images: list of NumPy arrays
    :param image: list containing BGR images

    :type models_dict: dictionary
    :param models_dict: dictionary with models, binarizers and lists of garments (see table)

    ================================  ====================================================  ============================
        Key                           Value                                                 Value Type
    ================================  ====================================================  ============================
    clothing_model                    trained general clothing model                        Tensorflow model
    clothing_category_bin             label binarizer for general clothing categories       sklearn LabelBinarizer
    clothing_color_bin                label binarizer for general clothing colors           sklearn LabelBinarizer
    whole_body_list                   list of whole body garments                           list
    top_list                          list of top garments                                  list
    bottom_list                       list of bottom garments                               list
    params                            dictionary with classification parameters             dictionary
    whole_body_model                  trained general whole_body model                      Tensorflow model
    whole_body_category_bin           label binarizer for general whole_body categories     sklearn LabelBinarizer
    whole_body_color_bin              label binarizer for general whole_body colors         sklearn LabelBinarizer
    top_model                         trained general top model                             Tensorflow model
    top_category_bin                  label binarizer for general top categories            sklearn LabelBinarizer
    top_color_bin                     label binarizer for general top colors                sklearn LabelBinarizer
    bottom_model                      trained general bottom model                          Tensorflow model
    bottom_category_bin               label binarizer for general bottom categories         sklearn LabelBinarizer
    bottom_color_bin                  label binarizer for general bottom colors             sklearn LabelBinarizer
    ================================  ====================================================  ============================

    :rtype: list
    :returns: list of (label, probability) tuples, one for each given image
    """

    clothing_model = models_dict['clothing_model'] 
    clothing_category_bin=models_dict['clothing_category_bin']
    clothing_color_bin = models_dict['clothing_color_bin']
    whole_body_list = models_dict['whole_body_list']
    top_list = models_dict['top_list']
    bottom_list = models_dict['bottom_list']
    params = models_dict['params']
    whole_body_model = models_dict['whole_body_model']
    whole_body_model = models_dict['whole_body_model']
    whole_body_category_bin = models_dict['whole_body_category_bin']
    whole_body_color_bin = models_dict['whole_body_color_bin']
    top_model = models_dict['top_model']
    top_category_bin = models_dict['top_category_bin']
    top_color_bin = models_dict['top_color_bin']
    bottom_model = models_dict['bottom_model']
    bottom_category_bin = models_dict['bottom_category_bin']
    bottom_color_bin = models_dict['bottom_color_bin']

    result = []

    # Get parameters
    try:
        batch_size = params['batch_size']
        image_height = params['image_height']
        image_width = params['image_width']
        top_pct = params['top_pct']
        bottom_pct = params['bottom_pct']
    except KeyError as e:
        print('%s key is not present in parameters file' % e)
        return

    # Count number of crops for each image that are analyzed by general clothing model
    crops_for_clothing_model = 3
    if top_model is not None and bottom_model is None:
        crops_for_clothing_model = 2
    elif top_model is None and bottom_model is not None:
        crops_for_clothing_model = 2
    elif top_model is not None and bottom_model is not None:
        crops_for_clothing_model = 1

    # Pre-process images for classification
    pp_images = []
    whole_body_pp_images = []
    top_pp_images = []
    bottom_pp_images = []
    for image in images:
        im_height, im_width, im_channels = image.shape
        top_height = int(im_height * top_pct)
        top_crop = image[0:top_height, 0:im_width]
        bottom_height = int(im_height * bottom_pct)
        bottom_crop = image[im_height - bottom_height:im_height, 0:im_width]
        counter = 1
        for crop in (image, top_crop, bottom_crop):
            image = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (image_width, image_height))
            image = image.astype("float") / 255.0
            image = img_to_array(image)
            image = np.expand_dims(image, axis=0)
            if whole_body_model is not None and counter == 1:
                whole_body_pp_images.append(image)
            if top_model is not None and counter == 2:
                top_pp_images.append(image)
            elif bottom_model is not None and counter == 3:
                bottom_pp_images.append(image)
            else:
                pp_images.append(image)
            counter += 1
    pp_images = np.vstack(pp_images)
    if len(whole_body_pp_images) > 0: 
        whole_body_pp_images = np.vstack(whole_body_pp_images)
    if len(top_pp_images) > 0: 
        top_pp_images = np.vstack(top_pp_images)
    if len(bottom_pp_images) > 0: 
        bottom_pp_images = np.vstack(bottom_pp_images)

    # Classify input images
    classif_result = clothing_model.predict(pp_images, batch_size=batch_size)
    if whole_body_model is not None:
        whole_body_result = whole_body_model.predict(whole_body_pp_images, batch_size=batch_size)
    if top_model is not None:
        top_result = top_model.predict(top_pp_images, batch_size=batch_size)
    if bottom_model is not None:
        bottom_result = bottom_model.predict(bottom_pp_images, batch_size=batch_size)

    for im_counter in range(0, len(images)):

        # Get results for whole body crop
        whole_body_category_probs = classif_result[0][im_counter * crops_for_clothing_model]
        whole_body_color_probs = classif_result[1][im_counter * crops_for_clothing_model]
        most_prob_category_idx = whole_body_category_probs.argmax()
        whole_body_most_prob_cat = str(clothing_category_bin.classes_[most_prob_category_idx])
        whole_body_most_prob_cat_prob = float(whole_body_category_probs[most_prob_category_idx])

        # Get results for top crop
        if top_model is not None:
            top_category_probs = top_result[0][im_counter]
            top_color_probs = top_result[1][im_counter]
            most_prob_category_idx = top_category_probs.argmax()
            top_most_prob_cat = str(top_category_bin.classes_[most_prob_category_idx])
            most_prob_color_idx = top_color_probs.argmax()
            top_most_prob_col = str(top_color_bin.classes_[most_prob_color_idx])

        else:
            top_category_probs = classif_result[0][im_counter * crops_for_clothing_model + 1]
            top_color_probs = classif_result[1][im_counter * crops_for_clothing_model + 1]
            most_prob_category_idx = top_category_probs.argmax()
            top_most_prob_cat = str(clothing_category_bin.classes_[most_prob_category_idx])
            most_prob_color_idx = top_color_probs.argmax()
            top_most_prob_col = str(clothing_color_bin.classes_[most_prob_color_idx])
        top_most_prob_cat_prob = float(top_category_probs[most_prob_category_idx])
        top_most_prob_col_prob = float(top_color_probs[most_prob_color_idx])

        # Get results for bottom crop
        if bottom_model is not None:
            bottom_category_probs = bottom_result[0][im_counter]
            bottom_color_probs = bottom_result[1][im_counter]
            most_prob_category_idx = bottom_category_probs.argmax()
            bottom_most_prob_cat = str(bottom_category_bin.classes_[most_prob_category_idx])
            most_prob_color_idx = bottom_color_probs.argmax()
            bottom_most_prob_col = str(bottom_color_bin.classes_[most_prob_color_idx])
        else:
            if top_model is None:
                bottom_category_probs = classif_result[0][im_counter * crops_for_clothing_model + 1]
                bottom_color_probs = classif_result[1][im_counter * crops_for_clothing_model + 1]
            else:
                bottom_category_probs = classif_result[0][im_counter * crops_for_clothing_model + 2]
                bottom_color_probs = classif_result[1][im_counter * crops_for_clothing_model + 2]
            most_prob_category_idx = bottom_category_probs.argmax()
            bottom_most_prob_cat = str(clothing_category_bin.classes_[most_prob_category_idx])
            most_prob_color_idx = bottom_color_probs.argmax()
            bottom_most_prob_col = str(clothing_color_bin.classes_[most_prob_color_idx])

        bottom_most_prob_cat_prob = float(bottom_category_probs[most_prob_category_idx])
        bottom_most_prob_col_prob = float(bottom_color_probs[most_prob_color_idx])

        # Check if most probable category of whole_body crop corresponds to a whole_body category
        # and if most probable colors in top and bottom crops are equals
        if whole_body_most_prob_cat in whole_body_list and (top_most_prob_col == bottom_most_prob_col):

            # Use whole_body classification
            if whole_body_model is None:

                # Get most probable color
                most_prob_color_idx = whole_body_color_probs.argmax()
                whole_body_most_prob_col = str(clothing_color_bin.classes_[most_prob_color_idx])
                whole_body_most_prob_col_prob = float(whole_body_color_probs[most_prob_color_idx])

            else:

                # Use results of whole body specific model
                whole_body_category_probs = whole_body_result[0][im_counter]
                whole_body_color_probs = whole_body_result[1][im_counter]
                most_prob_category_idx = whole_body_category_probs.argmax()
                whole_body_most_prob_cat = str(whole_body_category_bin.classes_[most_prob_category_idx])
                whole_body_most_prob_cat_prob = float(whole_body_category_probs[most_prob_category_idx])
                most_prob_color_idx = whole_body_color_probs.argmax()
                whole_body_most_prob_col = str(whole_body_color_bin.classes_[most_prob_color_idx])
                whole_body_most_prob_col_prob = float(whole_body_color_probs[most_prob_color_idx])

            # Create tuple with results
            cat_col_label = whole_body_most_prob_col + ' ' + whole_body_most_prob_cat
            cat_col_prob = (whole_body_most_prob_cat_prob + whole_body_most_prob_col_prob) / 2 * \
                top_most_prob_col_prob * bottom_most_prob_col_prob
            result.append((cat_col_label, cat_col_prob))

        else:

            # Use top and bottom classifications
            if top_model is None or bottom_model is None:
                all_labels = []
                all_probs = []
                category_idx = 0
                for category_prob in top_category_probs:
                    category_label = str(clothing_category_bin.classes_[category_idx])
                    all_labels.append(category_label)
                    all_probs.append(float(category_prob))
                    category_idx += 1

            # Get normalized probabilities for top crop
            if top_model is None:
                rel_labels, rel_probs = get_sub_results(all_labels, all_probs, top_list)
                rel_probs_np = np.array(rel_probs)
                top_most_prob_cat = rel_labels[rel_probs_np.argmax()]
                top_most_prob_cat_prob = max(rel_probs)

            # Get normalized probabilities for bottom crop
            if bottom_model is None:
                rel_labels, rel_probs = get_sub_results(all_labels, all_probs, bottom_list)
                rel_probs_np = np.array(rel_probs)
                bottom_most_prob_cat = rel_labels[rel_probs_np.argmax()]
                bottom_most_prob_cat_prob = max(rel_probs)

            # Create tuple with results
            cat_col_label = (top_most_prob_col + ' ' + top_most_prob_cat + ' - '
                             + bottom_most_prob_col + ' ' + bottom_most_prob_cat)
            cat_col_prob = (top_most_prob_cat_prob + top_most_prob_col_prob
                            + bottom_most_prob_cat_prob + bottom_most_prob_col_prob) / 4 * \
                top_most_prob_col_prob * bottom_most_prob_col_prob
            result.append((cat_col_label, cat_col_prob))

            im_counter += 1

    return result


