from ..base import run as base_run
from .traceables import rnd


def run(*args, dist_type="fine", **kwargs):

    rnd.config(dist_type=dist_type)

    return base_run(*args, **kwargs)
