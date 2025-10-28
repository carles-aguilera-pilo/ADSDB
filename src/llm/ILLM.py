from abc import ABC, abstractmethod

class ILLM(ABC):
    @abstractmethod
    def query(texts, images, audios):
        pass
    
   
                    