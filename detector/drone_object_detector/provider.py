import cv2
import os
import json
import numpy as np
from time import process_time

from deep_sort import preprocessing
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from deep_sort.detection import Detection as ddet
from deep_sort.tools import generate_detections as gdet

from yolo_detector import YoloDetector

from associator import associate

from detection_constants import *

# initialize a list of colors to represent each possible class label
np.random.seed(100)
COLORS = np.random.randint(0, 255, size=(200, 3),
	dtype="uint8")


colors_cl = {'person': (255,0,0),'small_vehicle':(0,255,0), 'two_wheeled_vehicle':(0,0,255), 'big_vehicle':(0,0,0)}
video_file_path = os.environ.get('VIDEO_FILE', "mount/incrocio.mp4")
# output_file_path = os.environ.get('OUTPUT_FILE', "predictions.txt")
output_file_path = os.environ.get('OUTPUT_FILE', "mount/predictions.csv")
# output_format = os.environ.get('OUTPUT_FORMAT', "DEEP_JSON")
output_format = os.environ.get('OUTPUT_FORMAT', "SAURON_CSV")


#deep_sort
encoder = gdet.create_box_encoder(model_filename,batch_size=1,to_xywh = True)
metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
ds_tracker = Tracker(metric)
detector = YoloDetector() # method for detection

timer = process_time()
def tic():
    global timer
    timer = process_time()

def toc(reset=False):
    global timer
    t = process_time() - timer
    if reset:
        tic()
    return t

def box_xyxy_to_xywh(box):
    bbox = [box[0], box[1]]
    bbox.append(box[2] - box[0])
    bbox.append(box[3] - box[1])
    return bbox

video = cv2.VideoCapture(video_file_path)

writeVideo_flag = True


if writeVideo_flag:
    # Define the codec and create VideoWriter object
    w = int(video.get(3))
    h = int(video.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter('./mount/output_yolo4_608_deepsort.avi', fourcc, 15, (w, h))



width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))  # uses given video width and height
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
fps = video.get(5)
print('Video size:', width, height, 'fps:', fps, 'frames:', num_frames)
output_fps = 10
frames_to_skip = int(np.round(fps / output_fps))
print(f'Processing video skiping {frames_to_skip} frames')
total_it = 0
total_tt = 0
total_frames = 0
det_times = np.empty(num_frames)
track_times = np.empty(num_frames)
total_times = np.empty(num_frames)
with  open(output_file_path, 'w') as output_file:
    if output_format == 'SAURON_CSV':
        head = 'frame_index,target_id,bbox_left,bbox_top,bbox_width,bbox_height,score,object_category\n'
        output_file.write(head)
    for frame_index in range(1, num_frames + 1):
        # Read a new frame
        frame_ok, frame = video.read()
        if not frame_ok:
            raise(f'Frame {frame_index} not ok')
        
        # Skip 6 frames
        if np.mod(frame_index, frames_to_skip) != 0:
            pass
            # continue
        
        # output_video_writer.write(frame)
        print(f'performing inference on frame {frame_index} of {num_frames}')
        tic()


        """
        detections = detector.predict(frame)
        det_time = toc(True)
        det_times[total_frames ]= det_time
        tracker_outputs = tracker.update(detections['boxes'], detections['scores'], frame)
        track_indexes, det_indexes = associate(tracker_outputs['boxes'], detections['boxes'])
        track_time = toc()
        track_times[total_frames] = track_time
        total_times[total_frames] = det_time + track_time
        total_frames += 1
        """
        class_names, confidences ,boxs= detector.detect(frame) #boxs x,y,b,r
        features = encoder(frame,boxs)
        detections = [Detection(bbox, confidence, feature,obj_class) for bbox, feature,confidence,obj_class in zip(boxs, features,confidences,class_names)]
        # Run non-maxima suppression.
        boxes = np.array([d.tlwh for d in detections])
        scores = np.array([d.confidence for d in detections])
        indices = preprocessing.non_max_suppression(boxes, nms_max_overlap, scores)
        detections = [detections[i] for i in indices]
        boxes_det = [box.to_tlbr() for box in detections]
        det_time = toc(True)
        det_times[total_frames ]= det_time
        
        # Call the tracker
        
        ds_tracker.predict()
        ds_tracker.update(detections)
        
        
        tracker_boxes = []
        tracker_ids = []
        i = 0
        for track in ds_tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue

            bbox = track.to_tlbr()
            
            tracker_boxes.append(bbox)
            tracker_ids.append(track.track_id)
            if False:
                color = [int(c) for c in COLORS[tracker_ids[i] % len(COLORS)]]
                #print(frame_index)
                
                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])),(color), 3)
                b0 = str(bbox[0])#.split('.')[0] + '.' + str(bbox[0]).split('.')[0][:1]
                b1 = str(bbox[1])#.split('.')[0] + '.' + str(bbox[1]).split('.')[0][:1]
                b2 = str(bbox[2]-bbox[0])#.split('.')[0] + '.' + str(bbox[3]).split('.')[0][:1]
                b3 = str(bbox[3]-bbox[1])

                cv2.putText(frame,str(track.track_id),(int(bbox[0]), int(bbox[1] -50)),0, 5e-3 * 150, (color),2)
                i += 1
            
 
        

        track_indexes, det_indexes = associate(tracker_boxes, boxes_det, 0.8)

        track_time = toc()
        track_times[total_frames] = track_time
        total_times[total_frames] = det_time + track_time
        total_frames += 1
        
        
        bboxes = [tracker_boxes[i] for i in track_indexes]
        ids = [tracker_ids[i] for i in track_indexes]
        classes = [detections[i].obj_class for i in det_indexes]
        scores_def = [detections[i].confidence for i in det_indexes]
        if writeVideo_flag:
            i = 0
            for bbox, id, cl, score in zip(bboxes, ids, classes, scores_def):
                color = [int(c) for c in COLORS[track_indexes[i] % len(COLORS)]]
                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])),colors_cl[cl], 3)
                cv2.putText(frame,str(id),(int(bbox[0]), int(bbox[1] -50)),0, 5e-3 * 150, colors_cl[cl],2)
                cv2.putText(frame,str(cl),(int(bbox[0]), int(bbox[3] -50)),0, 5e-3 * 150, colors_cl[cl],2)
                i+=1
        outputs = {
            'frame': frame_index,
            'detection_time': det_time,
            'tracking_time': track_time,
            'bboxes': bboxes,
            'ids': ids,
            'classes': classes,
            'scores': scores_def
        }
        if output_format == 'DEEP_JSON':
            output_json = json.dumps(outputs)
            output_file.write(output_json + '\n')
        elif output_format == 'SAURON_CSV':
            for box, id, cl, score in zip(bboxes, ids, classes, scores_def):
                bbox = box_xyxy_to_xywh(box)
                line =  f'{frame_index},{id},{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},{score},{cl}'
                output_file.write(line + '\n')


        if writeVideo_flag:
            # save a frame
            out.write(frame)


    if writeVideo_flag:
        out.release()
    print(f'Detection speed: mean: {1/det_times.mean()}, max: {1/det_times.max()}, min: {1/det_times.min()}, std: {1/det_times.std()}')
    print(f'Tracking speed: mean: {1/track_times.mean()}, max: {1/track_times.max()}, min: {1/track_times.min()}, std: {1/track_times.std()}')
    print(f'Total speed: mean: {1/total_times.mean()}, max: {1/total_times.max()}, min: {1/total_times.min()}, std: {1/total_times.std()}')
