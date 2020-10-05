

from abc import ABC, abstractmethod

class AbstractDetector(ABC):

    

    @abstractmethod
    def extract_features(self):
        pass
