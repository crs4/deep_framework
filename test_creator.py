
import os
from config import *
excluded = ['clothing','sample','generic','img']


def find_dockerfiles(path):

	dockerfiles_path = []
	for root, dirs, files in os.walk(path):
		for file in files:
			if 'Dockerfile' in file:
				dockerfile_path = os.path.join(root, file)
				
				if any(exc in dockerfile_path for exc in excluded):
					continue
				dockerfiles_path.append(dockerfile_path)
	return dockerfiles_path




def create_setup_command():
	com = 'docker build -f detector/tests/Dockerfile.setup -t tests:deep_setup detector/tests/'
	return com
"""
def remove_test_images(img):
	image_name,__ = img
	rm_com_img = 'docker rmi '+image_name
	rm_setup = 'docker rmi tests:deep_setup'
	return rm_com_img,rm_setup
"""





def create_build_command(dfile):

	mode = dfile.split('.')[-1]
	comp_name = dfile.split('/')[-2]
	context, __ = os.path.split(dfile)
	image_name = comp_name+':test_'+mode
	base_com = 'docker build -f '+dfile+' -t '+image_name+' '+context
	return (image_name,mode), base_com

def create_run_command(img):
	image_name,mode = img
	if mode == 'gpu':
		gpu_arg = '-e GPU_ID=0 '
	else:
		gpu_arg = '-e GPU_ID=None '
	python_com = ' python3 detector_test.py'
	base_com = 'docker run '
	run_com = base_com + gpu_arg + image_name + python_com
	
	return run_com

def create_test_file(setup_com,build_com,run_com,img):
	image_name,mode = img
	f_image = image_name.split(':')[0]
	test_file = 'test_'+f_image+'_'+mode+'.sh'
	test_path = os.path.join('detector/tests/test_scripts',test_file)
	with open(test_path, 'w') as tfile:
		tfile.write(setup_com+'\n')
		tfile.write(build_com+'\n')
		tfile.write(run_com+'\n')

	os.chmod(test_path, 0o777)



if __name__ == '__main__':
	detector_paths = os.path.join(MAIN_DIR, 'detector/object_extractors')
	dfiles = find_dockerfiles(detector_paths)
	setup_com = create_setup_command()
	for f in dfiles:

		img,build_command = create_build_command(f)
		run_com = create_run_command(img)
		#rm = remove_test_images(img)
		create_test_file(setup_com,build_command,run_com,img)

	print('### TEST CREATED AND AVAILABLE AT THE FOLLOWING PATH:')
	print('- detector/tests/test_scripts')
	print('Execute your test from main directory. Example:')
	print('- ./detector/tests/test_scripts/my_test.sh')


