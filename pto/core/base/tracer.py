
class Tracer:
    def __init__(self):
        self.active = False
        self.input_trace = {}
        self.output_trace = {}
    
    def sample(self, name, dist):
        if not self.active:
            dist.sample()
            return dist.val

        if name in self.output_trace:
            raise ValueError(f"Name '{name}' in trace is not unique")

        if name in self.input_trace:
            trace_dist = self.input_trace[name]
            if (trace_dist.fun.__name__, trace_dist.args) == (dist.fun.__name__, dist.args):
                dist.val = trace_dist.val
            else:
                dist.repair(trace_dist)
        else:
            dist.sample()

        self.output_trace[name] = dist
        return dist.val

    def play(self, gen, trace):
        self.active = True
        self.input_trace = trace
        self.output_trace = {}

        solution = gen()
        
        result_trace = self.output_trace
        self.active = False
        return solution, result_trace

tracer = Tracer()
