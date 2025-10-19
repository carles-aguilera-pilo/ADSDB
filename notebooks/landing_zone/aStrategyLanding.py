from abc import ABC, abstractmethod

class StrategyLandingZone(ABC):
    @abstractmethod
    def executar(self):
        pass