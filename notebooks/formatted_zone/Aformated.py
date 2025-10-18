from aStrategy import StrategyFormattedZone

class FormatedZone:
    
    strategy: StrategyFormattedZone = None
    
    def __init__(self, strategy: StrategyFormattedZone):
        self.strategy = strategy
    
    def executar(self):
        self.strategy.executar()
        
    def set_strategy(self, strategy: StrategyFormattedZone):
        self.strategy = strategy