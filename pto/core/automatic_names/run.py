
from ..base import Op
from ..fine_distributions import run as fine_run

from .autoplay import tracer
from .autogens import rnd

def run(*args, name_type = 'str', dist_type = 'fine', **kwargs):
    # name_type can be 'lin' or 'str'
    # dist_type can be 'coarse' or 'fine'
    
    rnd.CONFIG(name_type = name_type, dist_type = dist_type)
    Op.tracer = tracer # binds autoplay tracer to operators
    
    return fine_run(*args, dist_type = None, **kwargs)

