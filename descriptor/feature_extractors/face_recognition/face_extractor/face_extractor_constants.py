

container_base_dir = '/home/deepframework/descriptor/face_recognition/'

# Paths
FACENET_DATA_PATH = container_base_dir + 'facenet/src/align'
FACENET_MODEL_PATH = container_base_dir + 'facenet/src/models/20170131-234652'
FACENET_SRC_PATH =  container_base_dir + 'facenet/src'
FACE_REC_DATA_DIR_PATH = container_base_dir +'template_models'

# Face detection
FACE_BBOX_KEY = 'bbox'
FACE_SCORE_KEY = 'score'
FACENET_ALIGNED_FACE_SIZE = 160  # Size in pixels of aligned face for FaceNet
FACENET_DETECTION_THRESHOLD_1 = 0.5  # 0.6
FACENET_DETECTION_THRESHOLD_2 = 0.6  # 0.7
FACENET_DETECTION_THRESHOLD_3 = 0.89  # 0.7
FACENET_DETECTION_THRESHOLD_1_KEY = 'detection_threshold_1'
FACENET_DETECTION_THRESHOLD_2_KEY = 'detection_threshold_2'
FACENET_DETECTION_THRESHOLD_3_KEY = 'detection_threshold_3'
FACENET_FACE_DETECTION_MIN_SIZE = 20
FACENET_FACE_DETECTION_MIN_SIZE_KEY = 'min_size'
FACENET_FACE_DETECTION_SCALE_FACTOR = 0.709
FACENET_FACE_DETECTION_SCALE_FACTOR_KEY = 'scale_factor'
FACENET_GPU_MEMORY_FRACTION = 0.9
FACENET_GPU_MEMORY_FRACTION_KEY = 'gpu_memory_fraction'
FACENET_MARGIN = 44  # Margin in pixels for the crop around the face bounding box
FACENET_MODEL_PATH_KEY = 'facenet_model_path'

# Face recognition
FACE_MODELS_FILE = 'Face_models'
FACE_MODELS_MIN_DIFF = -1
FACE_MODELS_MIN_DIFF_KEY = 'face_models_min_diff'
FACE_REC_DATA_DIR_PATH_KEY = 'face_recognition_dir_path'
FACE_REC_THRESHOLD = 1.17  # Default 1.17 for FaceNet, 1.03 for Openface  #0.9 for FaceNet DEMO
FACE_REC_THRESHOLD_KEY = 'face_recognition_threshold'
TAG_LABEL_ASSOCIATIONS_FILE = 'Tag_label_associations'
UNDEFINED_LABEL = 'Unknown'
UNDEFINED_TAG = 'Unknown'

