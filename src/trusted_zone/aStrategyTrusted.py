from abc import ABC, abstractmethod

class StrategyTrustedZone(ABC):
    @abstractmethod
    def executar(self):
        pass