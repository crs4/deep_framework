import argparse

from configparser import ConfigParser
from initialize.gputils import GPUallocator
from initialize.cluster_utils import ClusterManager
from initialize.nodes_utils import Machine,Registry
from initialize.starter import Starter

from initialize.revealer import *
from initialize.interviewer import *
from initialize.gputils import *
from initialize.pipeline import *
from initialize.services import *
from initialize.builder import *


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--run", help="Run with last settings", action="store_true")
	args = parser.parse_args()

	print("### DEEP FRAMEWORK STARTING PROCEDURE ### ")
	if args.run:
		print('Using last configuration and settings...')

	machine = Machine()
	cluster_manager = ClusterManager()
	registry = Registry()
	starter = Starter(machine,registry,cluster_manager,use_last_settings=args.run)
	nodes_data = starter.get_nodes()


		
	rev = Revealer()
	det_revealed = rev.reveal_detectors()
	desc_revealed = rev.reveal_descriptors()
	
	standard_revelead = rev.reveal_standard_components()
	
	par = ParamsProvider()
	par.set_stream_params(use_last_settings=args.run)
	
	sp = SourceProvider()
	sources = sp.get_sources(use_last_settings=args.run)
	
	
	det_prov = DetectorProvider(det_revealed,sources)
	dets = det_prov.get_detectors(use_last_settings=args.run)

	
	desc_prov = DescriptorProvider(desc_revealed,dets)
	descs = desc_prov.get_descriptors(use_last_settings=args.run)


	standard_prov = StandardProvider(standard_revelead)
	stds = standard_prov.get_standard_components(use_last_settings=args.run)

	gpu_alloc = GPUallocator(nodes_data,descs,dets)
	alg_gpu_matches = gpu_alloc.match_algs_gpus()
	
	
	p = PipelineManager(alg_gpu_matches,sources)
	deep_structure = p.create_deep_structure()

	dm = DockerServicesManager(deep_structure,registry.insecure_addr,sources)
	docker_services = dm.get_services()
	dm.write_services()
	img_man = ImageManager(machine,docker_services,registry.insecure_addr,stds)
	img_man.start_build_routine()

	if not args.run:
		starter.create_source_volume(sources)
	starter.start_framework()
	






