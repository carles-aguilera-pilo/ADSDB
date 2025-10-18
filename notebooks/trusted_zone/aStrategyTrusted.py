import abc from ABC, abstractmethod

class StrategyTrustedZone(ABC):
    @abstractmethod
    def executar(self):
        pass