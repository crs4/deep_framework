

from abc import ABC, abstractmethod

   
class AbstractDescriptor(ABC):

	@abstractmethod
	def win_size(self):
		pass
	
    @abstractmethod
    def detect_batch(self):
        pass

    @abstractmethod
    def refine_classification(self):
        pass
