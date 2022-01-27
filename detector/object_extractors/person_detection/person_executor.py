
import cv2

from person_constants import *
from deep_sort.utils.parser import get_config


from person_detector import PersonDetector
from deep_sort.deep_sort import DeepSort
from deep_sort.utils.parser import get_config
from yolov5.yolo_utils.general import (LOGGER, check_img_size, non_max_suppression, scale_coords, 
                                  check_imshow, xyxy2xywh, increment_path)


from features import Object, Rect, Point
from abstract_detector import AbstractDetector

class PersonExecutor(AbstractDetector):

    ratio = 1

    def __setup_tracker(self):
        # initialize deepsort
        cfg = get_config()
        cfg.merge_from_file(CONFIG_DEEPSORT)
        self.deepsort_tracker = DeepSort(DEEP_SORT_MODEL,
                            max_dist=cfg.DEEPSORT.MAX_DIST,
                            max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                            max_age=cfg.DEEPSORT.MAX_AGE, n_init=cfg.DEEPSORT.N_INIT, nn_budget=cfg.DEEPSORT.NN_BUDGET,
                            use_cuda=True)

    def __init__(self):
        self.person_detector = PersonDetector()
        self.__setup_tracker()

    def __preprocess_image(self, img0, img_size=640, stride=32, auto=True):
        # Padded resize
        img = letterbox(img0, img_size, stride, auto=auto)[0]
        # Convert
        img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(self.device)
        img = img.half() if HALF else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)
        return img
        
    def __create_objects(self,objs):
        objects = []
        for obj in objs:
            obj_points = []
            top_left = Point(obj['rect']['x_topleft'],obj['rect']['y_topleft'])
            bottom_right = Point(obj['rect']['x_bottomright'],obj['rect']['y_bottomright'])
            obj_rect = Rect(top_left,bottom_right)
            
            obj = Object(rect = obj_rect, points = obj_points, pid = obj['pid'])
            objects.append(obj)
        return objects


    def extract_features(self,current_frame,executor_dict):

        objects_list = []
        #frame_counter = executor_dict['frame_counter']

        img = self.person_detector.preprocess_image(current_frame)

        detector_preditions,names = self.person_detector.detect_person(current_frame)
        print('detector: ',detector_preditions)
        for i, det in enumerate(detector_preditions):  # detections per image
            im0 = current_frame.copy()
            
            if det is not None and len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(
                    img.shape[2:], det[:, :4], im0.shape).round()

                
                xywhs = xyxy2xywh(det[:, 0:4])
                confs = det[:, 4]
                clss = det[:, 5]

                # pass detections to deepsort
                outputs = self.deepsort_tracker.update(xywhs.cpu(), confs.cpu(), clss.cpu(), im0)
                # draw boxes for visualization
                if len(outputs) > 0:
                    for j, (output, conf) in enumerate(zip(outputs, confs)):
                        obj_dict = dict()
                        bboxes = output[0:4]
                        id = output[4]
                        cls = output[5]

                        c = int(cls)  # integer class
                        label = f'{id} {names[c]} {conf:.2f}'
                        x_topleft_coord = output[0]
                        y_topleft_coord = output[1]
                        x_bottomright_coord = output[2]
                        y_bottomright_coord = output[3]

                        rect_scaled = dict(y_topleft=y_topleft_coord,y_bottomright=y_bottomright_coord,x_topleft=x_topleft_coord,x_bottomright=x_bottomright_coord)
                        obj_dict['pid'] = str(id)
                        obj_dict['rect'] = rect_scaled

                        objects_list.append(obj_dict)
        """
        objects_list_final = self.__create_objects(objects_list)
        print(objects_list_final)
        return objects_list_final
        """
        print(objects_list)












