import cv2
import os
from detector import Dectector
from tracker import Tracker
from time import process_time
import json
import numpy as np

video_file_path = os.environ.get('VIDEO_FILE', "/mnt/remote_media/File_di_test/SAURON.MP4")
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

video = cv2.VideoCapture(video_file_path)
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))  # uses given video width and height
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
fps = video.get(5)
print('Video size:', width, height, 'fps:', fps, 'frames:', num_frames)
output_fps = 10
frames_to_skip = int(np.round(fps / output_fps))
print(f'Processing video skiping {frames_to_skip} frames')
with  open('predictions.txt', 'w') as output_file:
    for frame_index in range(1, num_frames + 1):
        # Read a new frame
        frame_ok, frame = video.read()
        if not frame_ok:
            raise(f'Frame {frame_index} not ok')
        
        # Skip 6 frames
        if np.mod(frame_index, frames_to_skip) != 0:
            # pass
            continue
        
        # output_video_writer.write(frame)
        print(f'performing inference on frame {frame_index} of {num_frames}')
        tic()
        outputs = detector.predict(frame)
        outputs['inference_time'] = toc(True)
        outputs['frame'] = frame_index
        tracker_outputs = tracker.update(outputs['boxes'], outputs['scores'], frame)
        outputs['tracked_boxes'] = tracker_outputs['boxes']
        outputs['tracked_ids'] = tracker_outputs['ids']
        outputs['tracking_time'] = toc()
        output_json = json.dumps(outputs)
        output_file.write(output_json + '\n')
