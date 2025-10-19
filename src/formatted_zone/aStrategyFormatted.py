from abc import ABC, abstractmethod

class StrategyFormattedZone(ABC):
    
    @abstractmethod
    def executar(self):
        pass