import cv2
import json
import os
visdrone_objects = ["ignored_regions", "pedestrian", "people", "bicycle", "car", "van", "truck", "tricycle", "awning_tricycle", "bus", "motor", "others"]

video_file_path = os.environ.get('VIDEO_FILE', "/mnt/remote_media/File_di_test/SAURON.MP4")
video = cv2.VideoCapture(video_file_path)
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))  # uses given video width and height
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
fps = video.get(5)
print('Video size:', width, height, 'fps:', fps, 'frames:', num_frames)

with  open('src/predictions.txt', 'r') as output_file:
    data = json.loads(output_file.readline())
    data_frame = data['frame']
    for frame_index in range(1, num_frames + 1):
        # Read a new frame
        frame_ok, frame = video.read()
        if not frame_ok:
            raise(f'Frame {frame_index} not ok')
        if frame_index != data_frame:
            continue
        print(f'showing frame {frame_index}')
        for i, box in enumerate(data['boxes']):
            object_class = data['classes'][i]
            class_score = data['scores'][i]
            object_class = f'{visdrone_objects[object_class]}: {int(class_score * 100)}%'
            color = (255, 0, 0)
            cv2.putText(frame, object_class,
                        (int(box[0]),
                            int(box[1])),
                        cv2.FONT_HERSHEY_DUPLEX, 1.5, color, 2)
            x1,y1,x2,y2 = [int(i) for i in box]
            cv2.rectangle(frame,(x1, y1),(x2,y2),color,2)
        
        for i, box in enumerate(data['tracked_boxes']):
            color = (0, 255, 0)
            oid = data['tracked_ids'][i]
            object_id = f'ID: {oid}'
            cv2.putText(frame, object_id,
                        (int(box[0]),
                            int(box[3])),
                        cv2.FONT_HERSHEY_DUPLEX, 1.5, color, 2)
            x1,y1,x2,y2 = [int(i) for i in box]
            cv2.rectangle(frame,(x1, y1),(x2,y2),color,2)
        cv2.namedWindow('basename', cv2.WINDOW_NORMAL)
        cv2.imshow('basename', frame)
        if cv2.waitKey(1) == 27:
            break  # esc to quit

        try:
            data = json.loads(output_file.readline())
            data_frame = data['frame']
        except:
            break
