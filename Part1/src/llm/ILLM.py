from abc import ABC, abstractmethod

class ILLM(ABC):
    @abstractmethod
    def query(self, text, files):
        pass
    
   
                    