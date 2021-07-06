
from utils.timer_functions import RepeatedTimer


class StatsMaker:

	def __init__(self):
		self.__fps_acc = 0
		self.fps = None
		self.elaborated_frames = None
		self.skipped_frames = None
		self.received_frames = None
		self.start_time = None
		self.object_counter = None
		self.__timer_interval = 10


	def create_stats(self):
		stats = dict()
		for k,v in self.__dict__.items():
			if not k.startswith('_') and v != None:
				stats[k] = v
		return stats

	def run_stats_timer(self,interval,function):
		stats_timer = RepeatedTimer(interval,function)
		stats_timer.start()

	
	def run_fps_timer(self):
		timer = RepeatedTimer(self.__timer_interval,self.__get_fps)
		timer.start()




	def __get_fps(self):
		self.fps = (self.elaborated_frames - self.__fps_acc)/float(self.__timer_interval)
		self.__fps_acc = self.elaborated_frames

