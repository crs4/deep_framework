
import cv2
import time
from configparser import ConfigParser
import unittest
import os
import importlib

from utils.features import Object, Rect, Point

cur_dir =  os.path.split(os.path.abspath(__file__))[0]
config_file = [os.path.join(dp, f) for dp, dn, filenames in os.walk(cur_dir) for f in filenames if os.path.splitext(f)[1] == '.ini'][0]
config = ConfigParser()
config.read(config_file)
alg_config = {'path': config.get('CONFIGURATION','PATH'), 'class':config.get('CONFIGURATION','CLASS'),'name':config.get('CONFIGURATION','NAME'),'type':config.get('CONFIGURATION','TYPE')}
    
module = importlib.import_module(alg_config['path'])
det_instance = getattr(module, alg_config['class'])
descriptor = det_instance()

image_base_path = alg_config['path'].split('.')[0]
#frame = cv2.imread(os.path.join(image_base_path,'test_image.jpg'))

descriptor_dict = dict()
descriptor_dict['frame_idx'] = 0
descriptor_dict['objects'] = []
descriptor_dict['fp_time'] = time.time()
descriptor_dict['vc_time'] = time.time()




class TestExecutor(unittest.TestCase):



	def test_detect_batch(self):
		methods = dir(descriptor)
		self.assertTrue('detect_batch' in methods)

	def test_refine_classification(self):
		methods = dir(descriptor)
		self.assertTrue('refine_classification' in methods)


if __name__ == '__main__':
	
	unittest.main()



