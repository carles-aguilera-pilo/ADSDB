from abc import ABC, abstractmethod

class ADataObj(ABC):
    @abstractmethod
    def save(self, bucket_destination):
        pass

    @abstractmethod    
    def format(self):
        pass

    @abstractmethod    
    def clean(self):
        pass