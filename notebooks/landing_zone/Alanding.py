from abc import ABC, abstractmethod
from notebooks.landing_zone.aStrategyLanding import StrategyLandingZone


class LandingZone:
    strategy: StrategyLandingZone = None
    
    def __init__(self):
        self.strategy = None
    
    def __init__(self, strategy: StrategyLandingZone):
        self.strategy = strategy
    
    def executar(self):
        self.strategy.executar()
        
    def set_strategy(self, strategy: StrategyLandingZone):
        self.strategy = strategy