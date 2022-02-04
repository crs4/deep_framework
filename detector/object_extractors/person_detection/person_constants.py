

CONFIG_DEEPSORT = "deep_sort/configs/deep_sort.yaml"
DEEP_SORT_MODEL = 'osnet_x0_25'
DEVICE ='' #help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
IMGSZ = [640]
HALF = False #help="use FP16 half-precision inference")
YOLO_MODEL = 'yolov5m.pt'
AUGMENT = False #help='augmented inference')
CONF_THRES = 0.3 #help='object confidence threshold'
IOU_THRES = 0.5 #help='IOU threshold for NMS')
CLASSES = 0
AGNOSTIC_NMS = False #help='class-agnostic NMS'
MAX_DET = 1000 #help='maximum detection per image')
