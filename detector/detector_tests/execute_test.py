
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
det_config = {'path': config.get('CONFIGURATION','PATH'), 'class':config.get('CONFIGURATION','CLASS'),'name':config.get('CONFIGURATION','CATEGORY')}

module = importlib.import_module(det_config['path'])
det_instance = getattr(module, det_config['class'])
executor = det_instance()

image_base_path = det_config['path'].split('.')[0]
frame = cv2.imread(os.path.join(image_base_path,'test_image.jpg'))
executor_dict = {'frame_idx': 0,'vc_time': time.time(),'frame_shape':frame.shape ,'frame_counter': 0}



class TestExecutor(unittest.TestCase):



	def test_extract_features(self):
		methods = dir(executor)
		self.assertTrue('extract_features' in methods)

	def test_extract_features_objects_serialize(self):
		objs = executor.extract_features(frame,executor_dict)
		objs_serialized = [obj.serialize() for obj in objs]
		print('Detected', str(len(objs_serialized)), 'objects')
		for obj in objs_serialized:
			print(obj)
		self.assertTrue(len(objs_serialized)>0)


	def test_extract_features_objects(self):
		objs = executor.extract_features(frame,executor_dict)
		objs_type = [isinstance(obj,Object) for obj in objs]
		self.assertTrue(all(objs_type))

	def test_extract_features_rects(self):
		objs = executor.extract_features(frame,executor_dict)
		objs_rect_type = [isinstance(obj.rect,Rect) for obj in objs]
		self.assertTrue(all(objs_rect_type))

	def test_extract_features_points(self):
		objs = executor.extract_features(frame,executor_dict)
		objs_points_type = []
		for obj in objs:
			for point in obj.points:
				objs_points_type.append(isinstance(point,Point))

		self.assertTrue(all(objs_points_type))


if __name__ == '__main__':
	
	unittest.main()



