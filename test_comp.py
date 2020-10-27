
if __name__ == "__main__":
	"""
	from collections import OrderedDict
	from initialize.components import *
	addr = '192.168.195.224'

	o = OrderedDict()
	o['face_detection'] = {'node_name': 'linuxkit-025000000001', 'gpu_id': None}

	det = Detector(o,addr)
	det_dict = det.create_detector_service()
	print(det_dict)

	d_name = det.get_detector_image_name()

	coll = Collector(addr)
	col_dict=coll.create_collector_service(d_name)
	print(col_dict)
	"""

	nodes_data = {'linuxkit-025000000001': {'user': 'alessandro', 'ip': '192.168.195.224', 'role': 'manager', 'type': 'LocalNode', 'path': '/Users/alessandro/sviluppo/deep/deep_framework'}}



	from initialize.revealer import *
	from initialize.interviewer import *
	from initialize.gputils import *
	from initialize.pipeline import *
	from initialize.services import *
	from initialize.builder import *

	use_last_settings = False
	
	r = Revealer()
	det_revealed = r.reveal_detectors()
	desc_revealed = r.reveal_descriptors()
	
	standard_revelead = r.reveal_standard_components()
	

	"""
	sp = SourceProvider()
	sources = sp.get_sources(use_last_settings)
	print(sources)
	"""
	sources = [{'source_id': '1', 'source_path':'/folder', 'source_folder': None}]
	det_prov = DetectorProvider(det_revealed)
	dets = det_prov.get_detectors(use_last_settings)
	dets_names = [det['name'] for det in dets]

	
	desc_prov = DescriptorProvider(desc_revealed,dets_names)
	descs = desc_prov.get_descriptors(use_last_settings)

	standard_prov = StandardProvider(standard_revelead)
	stds = standard_prov.get_standard_components(use_last_settings)

	gpu_alloc = GPUallocator(nodes_data,descs,dets)
	alg_gpu_matches = gpu_alloc.match_algs_gpus()

	
	p = PipelineManager(alg_gpu_matches)
	pipeline = p.create_pipeline()

	dm = DockerServicesManager(pipeline,'192.168.195.224',sources)
	docker_services = dm.get_services()
	
	builder = ImageManager('si',docker_services,'192.168.195.224',stds)
	

	