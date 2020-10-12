
import os
from config import *
import subprocess
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

def build_setup_images(setup_d_files):
	base_com = 'docker build -f '

	for f in setup_d_files:
		img_name = f.split('/')[-2]
		context, __ = os.path.split(f)

		com = base_com + f + ' -t '+ img_name + ':deep_setup ' + context
		print('Building '+ img_name)
		try:
			result = subprocess.Popen([com], shell=True)
			result.communicate()
			if result.returncode == 0:
				print('SUCCESS: '+img_name+' setup builded')
		except Exception as e:
			raise e

	

def remove_coms(img):
	image_name,__ = img
	rm_container = 'docker container rm '+image_name.split(':')[0]
	rm_com_img = 'docker rmi '+image_name
	rm_cs = [rm_container,rm_com_img]
	return rm_cs





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
	python_com = ' python3 execute_test.py'
	container_name = '--name ' + image_name.split(':')[0]+' '
	base_com = 'docker run '
	run_com = base_com + container_name + gpu_arg + image_name + python_com
	
	return run_com

def create_test_file(rm,build_com,run_com,img, path):
	image_name,mode = img
	f_image = image_name.split(':')[0]
	test_file = 'test_'+f_image+'_'+mode+'.sh'
	test_path = os.path.join(path+'/test_scripts',test_file)
	
	
	with open(test_path, 'w') as tfile:
		tfile.write(build_com+'\n')
		tfile.write(run_com+'\n')
		tfile.write(rm[0]+'\n')
		tfile.write(rm[1]+'\n')


	os.chmod(test_path, 0o777)



if __name__ == '__main__':
	det_files = []
	desc_files = []
	setup_files = []
	
	dockerfiles = find_dockerfiles(MAIN_DIR)
	for f in dockerfiles:
		base, f_name = os.path.split(f)
		if 'setup' in f_name:
			setup_files.append(f)
			continue

		if 'detector/object_extractors' in f:
			det_files.append(f)
			continue

		if 'descriptor/feature_extractors' in f:
			desc_files.append(f)
			continue


	build_setup_images(setup_files)
	for f in det_files:

		img,build_command = create_build_command(f)
		run_com = create_run_command(img)
		rm = remove_coms(img)
		create_test_file(rm,build_command,run_com,img,os.path.join(MAIN_DIR,'detector/detector_tests'))


	for f in desc_files:

		img,build_command = create_build_command(f)
		run_com = create_run_command(img)
		rm = remove_coms(img)
		create_test_file(rm,build_command,run_com,img,os.path.join(MAIN_DIR,'descriptor/descriptor_tests'))

	print('### TEST CREATED AND AVAILABLE AT THE FOLLOWING PATHS:')
	print('*** DETECTOR ***')
	print('- detector/detector_tests/test_scripts')
	print('Execute your test from main directory. Example:')
	print('- ./detector/detector_tests/test_scripts/my_test.sh')
	print('*** DESCRIPTOR ***')
	print('- descriptor/descriptor_tests/test_scripts')
	print('Execute your test from main directory. Example:')
	print('- ./descriptor/descriptor_tests/test_scripts/my_test.sh')



