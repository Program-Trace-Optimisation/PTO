
class Tracer():

    def __init__(self):
        self.TRACER_ACTIVE = False
        self.TRACE = {}
        self.USED_NAMES = set()
        
    # sample a distribution object and add it to trace
    # dist object changed in place
    def sample(self, name, dist):
        
        if not self.TRACER_ACTIVE:
            dist.sample()
            return dist.val

        assert name not in self.USED_NAMES, f"PTO ERROR: NAME '{name}' IN TRACE NOT UNIQUE"

        if name not in self.TRACE:
            dist.sample()

        else:

            trace_dist = self.TRACE.pop(name) # pop entry from trace to fix execution order
            
            if (trace_dist.fun.__name__, trace_dist.args) == (dist.fun.__name__, dist.args):
                dist.val = trace_dist.val # use value in trace
            else:
                # print('repair: ', (trace_dist.fun.__name__, trace_dist.args), (dist.fun.__name__, dist.args))
                dist.repair(trace_dist) # repair value in trace

        self.TRACE[name] = dist
        self.USED_NAMES.add(name)

        return self.TRACE[name].val

    
    # Modes: play, fix, record a trace 
    # trace object changed in place 
    def play(self, gen, trace):

        self.TRACER_ACTIVE = True
        self.TRACE = trace # if trace contains {}, record mode
        self.USED_NAMES = set()

        # generate a solution
        sol = gen() # this position appears in the trace!

        # clean up unused trace entries
        unused_names = set(self.TRACE.keys()) - self.USED_NAMES
        for name in unused_names:
            del self.TRACE[name]
                
        assert trace is self.TRACE, "PTO ERROR: TRACE MISMATCH"       
                
        self.TRACER_ACTIVE = False
            
        return sol

tracer = Tracer()
