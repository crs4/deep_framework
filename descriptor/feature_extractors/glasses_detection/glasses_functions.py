from keras.preprocessing.image import img_to_array

import cv2
import numpy as np
import os
import pickle
import tensorflow as tf
import yaml

def classify_image(model, image, category_binarizer=None, color_binarizer=None,
                   image_size=(224, 224), show_results=False):
    """
    :type model: Tensorflow model
    :param model: trained model

    :type image: NumPy array
    :param image: BGR image

    :type category_binarizer: sklearn LabelBinarizer
    :param category_binarizer_path: label binarizer for categories

    :type color_binarizer: sklearn LabelBinarizer
    :param color_binarizer: label binarizer for colors

    :type image_size: tuple
    :param image_size: size to which image must be resized

    :type show_results: bool
    :param show_results: if True, show classification results

    :rtype: dictionary
    :returns: dictionary with results
    """

    image_results = {}
    if len(image_size) == 2:
        image_width, image_height = image_size
    else:
        print('[WARNING] Given image size has not the correct shape')
        return image_results

    # Resize in such a way that the largest dimension is 1000 pixels
    if show_results:
        (height, width, channels) = image.shape
        aspect_ratio = float(width) / height
        if height > width:
            new_height = 1000
            new_width = int(new_height * aspect_ratio)
        else:
            new_width = 1000
            new_height = int(new_width / aspect_ratio)
        output = cv2.resize(image, (new_width, new_height))

    # Pre-process image for classification
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (image_width, image_height))
    image = image.astype("float") / 255.0
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)

    if category_binarizer is not None and color_binarizer is not None:

        # Classify input image using Keras' multi-output functionality
        (category_probs, color_probs) = model.predict(image)

    elif category_binarizer is not None and color_binarizer is None:

        # Classify category of input image using Keras' single output functionality
        category_probs = model.predict(image)

    elif category_binarizer is None and color_binarizer is not None:

        # Classify color of input image using Keras' single output functionality
        color_probs = model.predict(image)

    # Find indexes and probabilities of most probable category
    if category_binarizer is not None:
        most_prob_category_idx = category_probs[0].argmax()
        most_prob_category_label = str(category_binarizer.classes_[most_prob_category_idx])
        most_prob_category_prob = float(category_probs[0][most_prob_category_idx])

        # Save category results
        #<mage_results = {'categories': {}}
        image_results = dict()
        
        image_category_labels = []
        image_category_probs = []
        category_idx = 0
        for category_prob in category_probs[0]:
            category_label = str(category_binarizer.classes_[category_idx])
            image_category_labels.append(category_label)
            image_category_probs.append(float(category_prob))
            category_idx += 1
        #image_results['labels'] = image_category_labels
        #image_results['probs'] = image_category_probs
        image_results['most_prob_category'] = most_prob_category_label
        image_results['most_prob_category_prob'] = most_prob_category_prob

    

    if show_results:

        # Draw category label on the image
        if category_binarizer is not None:
            category_txt = "category: {} ({:.2f}%)".format(most_prob_category_label,
                                                           most_prob_category_prob * 100)
            cv2.putText(output, category_txt, (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)

            # Display predictions also to the terminal
            print("[INFO] {}".format(category_txt))

        # Draw color label on the image
        if color_binarizer is not None:
            color_txt = "color: {} ({:.2f}%)".format(most_prob_color_label,
                                                     most_prob_color_prob * 100)
            cv2.putText(output, color_txt, (10, 55), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0), 2)

            # Display predictions also to the terminal
            print("[INFO] {}".format(color_txt))

        # Show image
        cv2.imshow("Clothing recognition", output)
        cv2.waitKey(0)

    return image_results




def classify_loaded_images(model, images, image_labels=None, category_binarizer=None, color_binarizer=None,
                       image_size=(224, 224), batch_size=32, show_results=False):
    """
    :type model: Tensorflow model
    :param model: trained model

    :type images: list of NumPy arrays
    :param image: list containing BGR images

    :type images: list of strings
    :param images: list of identifiers for given images

    :type category_binarizer: sklearn LabelBinarizer
    :param category_binarizer_path: label binarizer for categories

    :type color_binarizer: sklearn LabelBinarizer
    :param color_binarizer: label binarizer for colors

    :type image_size: tuple
    :param image_size: size to which images must be resized

    :type batch_size: integer
    :param batch_size: batch size at which images must be analyzed

    :type show_results: bool
    :param show_results: if True, show classification results

    :rtype: dictionary
    :returns: dictionary with results
    """

    result = []
    if len(image_size) == 2:
        image_width, image_height = image_size
    else:
        print('[WARNING] Given image size has not the correct shape')
        return result

    nr_images = len(images)
    if image_labels is not None and (len(image_labels) != nr_images):
        print('[WARNING] Length of given list of identifiers does not equal lenght of given images')
        return result

    if image_labels is None:
        image_labels = range(0, nr_images)

    # Pre-process images for classification
    pp_images = []
    for image in images:
        #h,w,ch = image.shape
        #image = image[int(float(h)/4):int(h-float(h)/4),int(float(w)/4):int(w-float(w)/4)]
        #cv2.imwrite('occhi.jpg',image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (image_width, image_height))
        image = image.astype("float") / 255.0
        image = img_to_array(image)
        image = np.expand_dims(image, axis=0)
        pp_images.append(image)
    pp_images = np.vstack(pp_images)

    # Classify input images
    classif_result = model.predict(pp_images, batch_size=batch_size)

    for im_counter in range(0, nr_images):
        image_results = {}
        if category_binarizer is not None and color_binarizer is not None:

            # Input images are classified by using Keras' multi-output functionality
            category_probs = classif_result[0][im_counter]
            color_probs = classif_result[1][im_counter]

        elif category_binarizer is not None and color_binarizer is None:

            # Input images are classified by using Keras' single output functionality
            category_probs = classif_result[im_counter]

        elif category_binarizer is None and color_binarizer is not None:

            # Input images are classified by using Keras' single output functionality
            color_probs = classif_result[im_counter]

        # Find indexes and probabilities of most probable category
        if category_binarizer is not None:
            most_prob_category_idx = category_probs.argmax()
            most_prob_category_label = str(category_binarizer.classes_[most_prob_category_idx])
            most_prob_category_prob = float(category_probs[most_prob_category_idx])

            # Save category results
            image_results = {'categories': {}}
            image_category_labels = []
            image_category_probs = []
            category_idx = 0
            for category_prob in category_probs:
                category_label = str(category_binarizer.classes_[category_idx])
                image_category_labels.append(category_label)
                image_category_probs.append(float(category_prob))
                category_idx += 1
            image_results['categories']['labels'] = image_category_labels
            image_results['categories']['probs'] = image_category_probs
            image_results['categories']['most_prob_category'] = most_prob_category_label
            image_results['categories']['most_prob_category_prob'] = most_prob_category_prob

        # Find indexes and probabilities of most probable color
        if color_binarizer is not None:
            most_prob_color_idx = color_probs.argmax()
            most_prob_color_label = str(color_binarizer.classes_[most_prob_color_idx])
            most_prob_color_prob = float(color_probs[most_prob_color_idx])

            # Save color results
            image_results['colors'] = {}
            image_color_labels = []
            image_color_probs = []
            color_idx = 0
            for color_prob in color_probs:
                color_label = str(color_binarizer.classes_[color_idx])
                image_color_labels.append(color_label)
                image_color_probs.append(float(color_prob))
                color_idx += 1
            image_results['colors']['labels'] = image_color_labels
            image_results['colors']['probs'] = image_color_probs
            image_results['colors']['most_prob_color'] = most_prob_color_label
            image_results['colors']['most_prob_color_prob'] = most_prob_color_prob

        image_label = image_labels[im_counter]
        result.append((image_results['categories']['most_prob_category'],image_results['categories']['most_prob_category_prob']))
        im_counter += 1

    if show_results:
        im_counter = 0
        for image in images:
            image_label = image_labels[im_counter]

            # Resize in such a way that the largest dimension is 1000 pixels
            (height, width, channels) = image.shape
            aspect_ratio = float(width) / height
            if height > width:
                new_height = 1000
                new_width = int(new_height * aspect_ratio)
            else:
                new_width = 1000
                new_height = int(new_width / aspect_ratio)
            output = cv2.resize(image, (new_width, new_height))

            # Draw category label on the image
            if category_binarizer is not None:
                most_prob_category_label = result[image_label]['categories']['most_prob_category']
                most_prob_category_prob = result[image_label]['categories']['most_prob_category_prob']
                category_txt = "category: {} ({:.2f}%)".format(most_prob_category_label,
                                                               most_prob_category_prob * 100)
                cv2.putText(output, category_txt, (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 0), 2)

                # Display predictions also to the terminal
                print("[INFO] {}".format(category_txt))

            # Draw color label on the image
            if color_binarizer is not None:
                most_prob_color_label = result[image_label]['colors']['most_prob_color']
                most_prob_color_prob = result[image_label]['colors']['most_prob_color_prob']
                color_txt = "color: {} ({:.2f}%)".format(most_prob_color_label,
                                                         most_prob_color_prob * 100)
                cv2.putText(output, color_txt, (10, 55), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 0), 2)

                # Display predictions also to the terminal
                print("[INFO] {}".format(color_txt))

            # Show image
            cv2.imshow("Clothing recognition", output)
            cv2.waitKey(0)

            im_counter += 1

    return result

