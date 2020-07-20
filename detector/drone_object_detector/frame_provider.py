import cv2
import os
from detector import Dectector
from tracker import Tracker
from time import process_time
import json
import numpy as np
from associator import associate

video_file_path = os.environ.get('VIDEO_FILE', "/mnt/remote_media/Dataset/Sauron_detection_tracking/video/visdrone_crossroad1_static.mp4")
# output_file_path = os.environ.get('OUTPUT_FILE', "predictions.txt")
output_file_path = os.environ.get('OUTPUT_FILE', "predictions.csv")
# output_format = os.environ.get('OUTPUT_FORMAT', "DEEP_JSON")
output_format = os.environ.get('OUTPUT_FORMAT', "SAURON_CSV")
detector = Dectector()
tracker = Tracker()

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
        detections = detector.predict(frame)
        det_time = toc(True)
        det_times[total_frames ]= det_time
        tracker_outputs = tracker.update(detections['boxes'], detections['scores'], frame)
        track_indexes, det_indexes = associate(tracker_outputs['boxes'], detections['boxes'])
        track_time = toc()
        track_times[total_frames] = track_time
        total_times[total_frames] = det_time + track_time
        total_frames += 1
        outputs = {
            'frame': frame_index,
            'detection_time': det_time,
            'tracking_time': track_time,
            'bboxes': [tracker_outputs['boxes'][i] for i in track_indexes],
            'ids': [tracker_outputs['ids'][i] for i in track_indexes],
            'classes': [detections['classes'][i] for i in det_indexes],
            'scores': [detections['scores'][i] for i in det_indexes]
        }
        if output_format == 'DEEP_JSON':
            output_json = json.dumps(outputs)
            output_file.write(output_json + '\n')
        elif output_format == 'SAURON_CSV':
            for box, id, cl, score in zip(outputs['bboxes'], outputs['ids'], outputs['classes'], outputs['scores']):
                bbox = box_xyxy_to_xywh(box)
                line =  f'{frame_index},{id},{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},{score},{cl}'
                output_file.write(line + '\n')
    print(f'Detection speed: mean: {1/det_times.mean()}, max: {1/det_times.max()}, min: {1/det_times.min()}, std: {1/det_times.std()}')
    print(f'Tracking speed: mean: {1/track_times.mean()}, max: {1/track_times.max()}, min: {1/track_times.min()}, std: {1/track_times.std()}')
    print(f'Total speed: mean: {1/total_times.mean()}, max: {1/total_times.max()}, min: {1/total_times.min()}, std: {1/total_times.std()}')
