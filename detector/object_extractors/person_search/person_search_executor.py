import torch
import torch.utils.data
from torchvision.transforms import functional as F
print("2Pre-Loading Person Search Executor...")
import os 
print(os.getcwd())
from person_search.searcher_defaults import get_default_cfg
print("Post-Loading Person Search Executor...")
from person_search.models.seqnet import SeqNet
from person_search.searcher_utils.utils import resume_from_ckpt
import numpy as np

from utils.features import Object, Rect, Point
from utils.abstract_detector import AbstractDetector


model_cfg_file = "person_search/trained_models/exp_cuhk/config.yaml"
model_ckpt_file = "person_search/trained_models/exp_cuhk/epoch_19.pth"

print("Loading Person Search Executor...")

class PersonSearchExecutor(AbstractDetector):


    def __init__(self):
        cfg = get_default_cfg()
        cfg.merge_from_file(model_cfg_file)
        cfg.freeze()

        self.device = torch.device(cfg.DEVICE)

        print("Creating model...")
        self.model = SeqNet(cfg)
        self.model.to(self.device)
        self.model.eval()
        resume_from_ckpt(model_ckpt_file, self.model)
        self.query_feat = None
        print("Model loaded")


    def extract_features(self,current_frame,executor_dict):
        print('Frame data: ' + str(executor_dict))
        if "app_data" in executor_dict:
            query_img = [F.to_tensor(executor_dict["app_data"]["query_img"]).to(self.device)]
            query_target = [{"boxes": torch.tensor([[0, 0, 195, 355]]).to(self.device)}]
            with torch.no_grad():
                self.query_feat = self.model(query_img, query_target)[0]

        frame_t = [F.to_tensor(current_frame).to(self.device)]
        with torch.no_grad():
            found_persons = self.model(frame_t)[0]
        
        detections = found_persons["boxes"].cpu().numpy()
        person_feats = found_persons["embeddings"]

        if self.query_feat is None:
            similarities = np.zeros(detections.shape[0])
        else:
            similarities = person_feats.mm(self.query_feat.view(-1, 1)).squeeze()
            if similarities.ndim == 0 and detections.shape[0] > 0:
                similarities = similarities.unsqueeze(0)

        obj_list = []
        for detection, sim in zip(detections, similarities):
            x1, y1, x2, y2 = detection
            top_left_point = Point(x1, y1)
            bottom_right_point = Point(x2, y2)
            rect = Rect(top_left_point,bottom_right_point, **{'score':sim,'class':'person'})
            obj = Object(rect)
            obj_list.append(obj)

        print(obj_list)
        return obj_list
