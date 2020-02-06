import os
import importlib
import cv2
from ConfigParser import SafeConfigParser
import time

path1 = '/Users/alessandro/Documents/giacca.jpg'
path2 = '/Users/alessandro/Documents/vestito.jpg'
path3 = '/Users/alessandro/Documents/tailleur.jpg'

frame = cv2.imread(path1)
frame2 = cv2.imread(path2)
frame3 = cv2.imread(path3)


cur_dir =  os.path.split(os.path.abspath(__file__))[0]
config_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(cur_dir) for f in filenames if os.path.splitext(f)[1] == '.ini']
print config_files

config = SafeConfigParser()
for res in config_files:
	config.read(res)
	path = config.get('CONFIGURATION','PATH')
	class_alg = config.get('CONFIGURATION','CLASS')
	name = config.get('CONFIGURATION','NAME')
	if name != "clothing":
		continue

	print name
	module = importlib.import_module(path)
	alg_instance = getattr(module, class_alg)
	det = alg_instance()
	start = time.time()
	res = det.detect_batch([frame3])
	print 'time elapsed:', time.time() -start
	print res