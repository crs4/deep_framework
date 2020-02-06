import math
import sys
import yaml


def get_rotated_image_size(w, h, angle):
    """
    Compute the width and height of the largest possible crop
    without black regions from a rotated image.

    :type w: int
    :param w: width of original image

    :type h: int
    :param h: height of original image

    :type angle: float
    :param angle: degrees of rotation

    :rtype: tuple
    :returns: size of rotated image with no black regions
    """

    if w <= 0 or h <= 0:
        return 0, 0

    long_side = max(w, h)
    short_side = min(w, h)

    # Transform angle in radians
    angle_rad = math.radians(angle)

    # the solutions for angle, -angle and 180-angle are equals,
    # so it is sufficient to look at the first quadrant and the absolute values of sine and cosine
    sin_a = abs(math.sin(angle_rad))
    cos_a = abs(math.cos(angle_rad))

    if short_side <= 2.0 * sin_a * cos_a * long_side:
        # two corners of the rotated image touch the longer side,
        # the other two corners are on the mid-line parallel to the longer side
        x = 0.5 * short_side
        if w >= h:
            w_rot = x / sin_a
            h_rot = x / cos_a
        else:
            w_rot = x / cos_a
            h_rot = x / sin_a
    else:
        # rotated image touches all four sides
        cos_2a = cos_a * cos_a - sin_a * sin_a
        w_rot = (w * cos_a - h * sin_a) / cos_2a
        h_rot = (h * cos_a - w * sin_a) / cos_2a

    return int(math.ceil(w_rot)), int(math.ceil(h_rot))


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
        print error_str
        print 'Unable to load %s' % file_path
        return None

    except:
        print "Unexpected error:", sys.exc_info()[0]
        return None

def save_YAML_file(file_path, data):
    """
    Save YAML file

    :type file_path: string
    :param file_path: path of YAML file to be saved

    :type data: dictionary or list
    :param data: data to be saved

    :rtype: boolean
    :returns: a boolean indicating the result of the write operation
    """

    try:

        with open(file_path, 'w') as stream:
            result = yaml.dump(data, stream, default_flow_style=False)
            return result

    except IOError as e:
        error_str = "I/O error({0}): {1}".format(e.errno, e.strerror)
        print error_str
        print 'Unable to save %s' % file_path
        return None

    except:
        print "Unexpected error:", sys.exc_info()[0]
        return None