import abc from ABC, abstractmethod

class StrategyLandingZone(ABC):
    @abstractmethod
    def executar(self):
        pass