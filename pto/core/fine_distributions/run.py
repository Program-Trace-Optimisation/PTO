
from ..base import CoreRunner
from .traceables import rnd

class FineRunner(CoreRunner):
    @classmethod
    def run(cls, *args, dist_type = 'fine', **kwargs):
        
        rnd.config(dist_type = dist_type)
        
        return super().run(*args, **kwargs)

run = FineRunner.run
