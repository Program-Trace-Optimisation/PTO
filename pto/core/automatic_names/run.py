
from ..base import Op
from ..fine_distributions import FineRunner

from .autoplay import tracer
from .autogens import rnd

class NameRunner(FineRunner):
    @classmethod
    def run(cls, *args, name_type = 'str', dist_type = 'repair', **kwargs):
        # name_type can be 'lin' or 'str'
        # dist_type can be 'coarse' or 'repair'
        
        rnd.CONFIG(name_type = name_type, dist_type = dist_type)
        Op.tracer = tracer # binds autoplay tracer to operators
        
        return super().run(*args, dist_type = None, **kwargs)

run = NameRunner.run

