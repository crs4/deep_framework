import os
from .darknet import darknet
import time
import cv2
import numpy as np



class YoloDetector:
    ratio=1
    def __init__(self):
        base_path = os.path.split(os.path.abspath(__file__))[0] + '/darknet/models/yolo608_visdrone'
        weights_path = os.path.join(base_path, 'yolo-obj_best.weights')
        cfg_path = os.path.join(base_path, 'yolo-obj.cfg')
        data_path = os.path.join(base_path, 'obj.data')
        
        self.network, self.class_names, self.class_colors = self.__load_network(cfg_path,data_path,weights_path)
        self.net_width = darknet.network_width(self.network)
        self.net_height = darknet.network_height(self.network)
        self.thresh = 0.5
        

    def __load_network(self,config_file,data_file,weights):
        network, class_names, class_colors = darknet.load_network(
            config_file,
            data_file,
            weights,
            batch_size=1
        )
        return network, class_names, class_colors


    def detect(self,image):
        # Darknet doesn't accept numpy images.
        # Create one with image we reuse for each detect
        darknet_image = darknet.make_image(self.net_width, self.net_height, 3)
        x_ratio = self.net_width/float(image.shape[1])
        y_ratio = self.net_height/float(image.shape[0])
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_resized = cv2.resize(image_rgb, (self.net_width, self.net_height),
                                interpolation=cv2.INTER_LINEAR)

        darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())
        detections = darknet.detect_image(self.network, self.class_names, darknet_image, thresh=self.thresh)
        scaled_boxes = []
        classes = []
        scores = []
        for det in detections:
            obj_class, score, bbox = det
            xt,yt,xb,yb = darknet.bbox2points(bbox)
            xt = int(xt/x_ratio)
            xb = int(xb/x_ratio)
            yt = int(yt/y_ratio)
            yb = int(yb/y_ratio)

            scaled_boxes.append( [xt,yt,xb,yb] )
            classes.append(obj_class)
            scores.append( float(score)/100)

        #image = darknet.draw_boxes(detections, image_resized, self.class_colors)
        #return cv2.cvtColor(image, cv2.COLOR_BGR2RGB), scaled_detections
        return classes, scores, scaled_boxes

if __name__ == "__main__":
    # unconmment next line for an example of batch processing
    # batch_detection_example()

    detector = YoloDetector()
    image_name = 'test.png'
    image_wext = image_name.split('.')[0]
    image = cv2.imread('test_images/'+image_name)
    detections = detector.detect(image)
    
    for det in detections:
        obj_class, score, bbox = det
        xt,yt,xb,yb = bbox
        cv2.rectangle(image,(xt,yt),(xb,yb),(255,0,0),1)
        cv2.putText(image, obj_class, (xt,yt), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1)


    cv2.imwrite('test_images/'+image_wext+'_output.jpg',image) 
