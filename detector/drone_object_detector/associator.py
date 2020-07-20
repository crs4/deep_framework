import numpy as np
from lapsolver import solve_dense

def associate(tracks, detections, sigma_iou=0.9):
    """ perform association between tracks and detections in a frame.
    Args:
        tracks (list): input tracks
        detections (list): input detections
        sigma_iou (float): minimum intersection-over-union of a valid association

    Returns:
        (tuple): tuple containing:

        track_indexes (numpy.array): 1D array with indexes of the tracks
        det_indexes (numpy.array): 1D array of the associated indexes of the detections
    """
    costs = np.empty(shape=(len(tracks), len(detections)), dtype=np.float32)
    for row, track in enumerate(tracks):
        for col, detection in enumerate(detections):
            iou_tr_box = iou(track[0:4], detection)
            print('iou',iou_tr_box)
            costs[row, col] = 1 - iou_tr_box

    np.nan_to_num(costs)
    costs[costs > 1 - sigma_iou] = np.nan
    track_indexes, det_indexes = solve_dense(costs)
    return track_indexes, det_indexes

def iou(bbox1, bbox2):
    """
    Calculates the intersection-over-union of two bounding boxes.

    Args:
        bbox1 (numpy.array, list of floats): bounding box in format x1,y1,x2,y2.
        bbox2 (numpy.array, list of floats): bounding box in format x1,y1,x2,y2.

    Returns:
        int: intersection-over-onion of bbox1, bbox2
    """

    bbox1 = [float(x) for x in bbox1]
    bbox2 = [float(x) for x in bbox2]

    (x0_1, y0_1, x1_1, y1_1) = bbox1
    (x0_2, y0_2, x1_2, y1_2) = bbox2

    # get the overlap rectangle
    overlap_x0 = max(x0_1, x0_2)
    overlap_y0 = max(y0_1, y0_2)
    overlap_x1 = min(x1_1, x1_2)
    overlap_y1 = min(y1_1, y1_2)

    # check if there is an overlap
    if overlap_x1 - overlap_x0 <= 0 or overlap_y1 - overlap_y0 <= 0:
        return 0

    # if yes, calculate the ratio of the overlap to each ROI size and the unified size
    size_1 = (x1_1 - x0_1) * (y1_1 - y0_1)
    size_2 = (x1_2 - x0_2) * (y1_2 - y0_2)
    size_intersection = (overlap_x1 - overlap_x0) * (overlap_y1 - overlap_y0)
    size_union = size_1 + size_2 - size_intersection

    return size_intersection / size_union