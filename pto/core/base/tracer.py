
class Tracer:
   """
   A tracing mechanism for reproducible stochastic operations.
   
   The Tracer enables recording and replaying sequences of stochastic operations. When active, 
   it traces all sampling operations and can replay them exactly using the recorded trace.
   
   Attributes:
       active (bool): Whether tracing is currently active
       input_trace (dict): Map of names to distributions from previous trace
       output_trace (dict): Map of names to distributions being recorded
   """
   def __init__(self):
       """Initialize an inactive tracer with empty traces."""
       self.active = False
       self.input_trace = {}
       self.output_trace = {}
   
   def sample(self, name, dist):
       """
       Sample from a distribution with optional tracing.
       
       When tracing is active, this either:
       - Uses a value from the input trace if the distribution matches
       - Repairs the distribution using the traced value if different
       - Samples a new value if no trace exists
       The distribution is recorded in the output trace.
       
       Args:
           name (str): Unique identifier for this sampling operation
           dist (Dist): Distribution to sample from
           
       Returns:
           The sampled value
           
       Raises:
           ValueError: In debug mode, if name appears multiple times in trace
       """
       if not self.active:
           dist.sample()
           return dist.val

       if __debug__:
           if name in self.output_trace:
               raise ValueError(f"Name '{name}' in trace is not unique")

       if name in self.input_trace:
           trace_dist = self.input_trace[name]
           if ((trace_dist.fun.__name__, trace_dist.args, trace_dist.kwargs) == 
               (dist.fun.__name__, dist.args, dist.kwargs)):
               dist.val = trace_dist.val
           else:
               dist.repair(trace_dist)
       else:
           dist.sample()

       self.output_trace[name] = dist
       return dist.val

   def play(self, gen, trace):
       """
       Run a generator function with tracing.
       
       Activates tracing, runs the generator using the provided trace as input,
       collects the output trace, and returns both the solution and new trace.
       
       Args:
           gen (callable): Generator function to run
           trace (dict): Input trace to use for replay
           
       Returns:
           tuple: (solution from generator, output trace dictionary)
       """
       self.active = True
       self.input_trace = trace
       self.output_trace = {}

       solution = gen()
       
       result_trace = self.output_trace
       self.active = False
       return solution, result_trace

tracer = Tracer()
