### FIX ME ###

from .annotators import Name
from .autoplay import AutoPlayTracer as Tracer, tracer
from .autogens import rnd

# ---


# Functions to convert names from linear to structured
def lin2str_sample(self, name, dist):
    val = self._original_sample_lin2str(name, dist)
    str_name = Name.get_stack_name()
    self.TRACE_STR[str_name] = dist
    return val


def lin2str(gen, trace_lin):
    Tracer._original_sample_lin2str = Tracer.sample
    Tracer.sample = lin2str_sample

    Tracer.TRACE_STR = {}
    # save_str_name = config.STR_NAME # NB CHECK
    # config.STR_NAME = False # NB CHECK

    tracer.play(gen, trace_lin)
    # config.STR_NAME = save_str_name # NB CHECK
    Tracer.sample = Tracer._original_sample_lin2str
    return Tracer.TRACE_STR


# ---
