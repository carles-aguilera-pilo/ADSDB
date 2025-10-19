from abc import ABC, abstractmethod
from notebooks.trusted_zone.aStrategyTrusted import StrategyTrustedZone

class TrustedZone:
    strategy: StrategyTrustedZone = None
    
    def __init__(self):
        self.strategy = None
    
    def __init__(self, strategy: StrategyTrustedZone):
        self.strategy = strategy
    
    def executar(self):
        self.strategy.executar()
        
    def set_strategy(self, strategy: StrategyTrustedZone):
        self.strategy = strategy