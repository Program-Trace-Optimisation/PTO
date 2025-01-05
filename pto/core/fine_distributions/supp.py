
import math
import random
from collections import namedtuple

"""
Parameter formats by type:
- 'real': (min, max, range)  # range = max-min or 2*std_dev
- 'int':  (min, max, step)   # inclusive bounds
- 'cat':  sequence           # sequence
- 'seq':  (sequence, k)      # k is number of items to select/generate
"""

RNGSpec = namedtuple('RNGSpec', ['type', 'params'])

class RNGSpecs:
   """
   Specifications for random number generators, handling both positional and keyword arguments.
   Each RNG function has a type and a parameter extraction method.
   """
   
   def __init__(self):
       """Initialize the RNG specifications dictionary."""
       self.specs = {
           # Real-valued functions
           random.random: RNGSpec(
               type='real',
               params=lambda args, kwargs: (0, 1, 1)
           ),
           random.uniform: RNGSpec(
               type='real',
               params=lambda args, kwargs: (
                   args[0] if args else kwargs['a'],
                   args[1] if len(args) > 1 else kwargs['b'],
                   (args[1] if len(args) > 1 else kwargs['b']) - 
                   (args[0] if args else kwargs['a'])
               )
           ),
           random.triangular: RNGSpec(
               type='real',
               params=lambda args, kwargs: (
                   args[0] if args else kwargs['low'],
                   args[1] if len(args) > 1 else kwargs['high'],
                   (args[1] if len(args) > 1 else kwargs['high']) - 
                   (args[0] if args else kwargs['low'])
               )
           ),
           random.betavariate: RNGSpec(
               type='real',
               params=lambda args, kwargs: (0, 1, 1)
           ),
           random.gauss: RNGSpec(
               type='real',
               params=lambda args, kwargs: (-math.inf, math.inf, 
                   2 * (args[1] if len(args) > 1 else kwargs['sigma']))
           ),
           random.normalvariate: RNGSpec(
               type='real',
               params=lambda args, kwargs: (-math.inf, math.inf, 
                   2 * (args[1] if len(args) > 1 else kwargs['sigma']))
           ),
           random.expovariate: RNGSpec(
               type='real',
               params=lambda args, kwargs: (0, math.inf, 
                   2.0/(args[0] if args else kwargs['lambd']))
           ),
           random.gammavariate: RNGSpec(
               type='real',
               params=lambda args, kwargs: (0, math.inf, 
                   2 * ((args[0] if args else kwargs['alpha'])**0.5 / 
                        (args[1] if len(args) > 1 else kwargs['beta'])))
           ),
           random.lognormvariate: RNGSpec(
               type='real',
               params=lambda args, kwargs: (0, math.inf, 
                   2 * (math.exp((args[1] if len(args) > 1 else kwargs['sigma'])**2 - 1) * 
                        math.exp(2 * (args[0] if args else kwargs['mu']) + 
                               (args[1] if len(args) > 1 else kwargs['sigma'])**2))**0.5)
           ),
           random.vonmisesvariate: RNGSpec(
               type='real',
               params=lambda args, kwargs: (-math.pi, math.pi, 2*math.pi)
           ),
           random.paretovariate: RNGSpec(
               type='real',
               params=lambda args, kwargs: (1, math.inf, 
                   2 * ((args[0] if args else kwargs['alpha'])/
                        ((args[0] if args else kwargs['alpha']-1)**2 * 
                         (args[0] if args else kwargs['alpha']-2)))**0.5)
           ),
           random.weibullvariate: RNGSpec(
               type='real',
               params=lambda args, kwargs: (0, math.inf,
                   2 * (1.0/(args[1] if len(args) > 1 else kwargs['beta']) * 
                        (math.gamma(1 + 2.0/(args[0] if args else kwargs['alpha'])) - 
                         math.gamma(1 + 1.0/(args[0] if args else kwargs['alpha']))**2)**0.5))
           ),
           
           # Integer-valued functions
           random.randrange: RNGSpec(
               type='int',
               params=lambda args, kwargs: 
                   (0, args[0]-1, 1) if len(args) == 1 else
                   (args[0], args[1]-1, args[2] if len(args) > 2 else 1) if args else
                   (kwargs.get('start', 0), kwargs['stop']-1, kwargs.get('step', 1))
           ),
           random.randint: RNGSpec(
               type='int',
               params=lambda args, kwargs: (
                   args[0] if args else kwargs['a'],
                   args[1] if len(args) > 1 else kwargs['b'],
                   1
               )
           ),
           
           # Categorical/Sequence functions
           random.choice: RNGSpec(
               type='cat',
               params=lambda args, kwargs: args[0] if args else kwargs['seq']
           ),
           random.choices: RNGSpec(
               type='seq',
               params=lambda args, kwargs: (
                   args[0] if args else kwargs['population'],
                   kwargs.get('k', 1) if 'k' in kwargs else args[3] if len(args) > 3 else 1
               )
           ),
           random.sample: RNGSpec(
               type='seq',
               params=lambda args, kwargs: (
                   args[0] if args else kwargs['population'],
                   args[1] if len(args) > 1 else kwargs['k']
               )
           )
       }
       
   def __getitem__(self, key):
       """Access specifications using dictionary syntax."""
       return self.specs[key]

# Create global instance
rng_specs = RNGSpecs()

# Add special cases
def shuffle(seq):
   """Wrapper for in-place shuffle returning a copy."""
   seq_copy = list(seq)
   random.shuffle(seq_copy) 
   return seq_copy

rng_specs.specs[shuffle] = RNGSpec(
   type='seq',
   params=lambda args, kwargs: (args[0], len(args[0]))
)

if __name__ == "__main__":
   # Test examples
   for fun, spec in rng_specs.specs.items():
       print(f"\nTesting {fun.__name__}:")
       
       # Example test cases
       test_args = {
           random.random: ([], {}),
           random.uniform: ([0, 1], {}),
           random.triangular: ([0, 1], {}),
           random.betavariate: ([1, 1], {}),
           random.gauss: ([0, 1], {}),
           random.normalvariate: ([0, 1], {}),
           random.expovariate: ([1.0], {}),
           random.gammavariate: ([1, 1], {}),
           random.lognormvariate: ([0, 1], {}),
           random.vonmisesvariate: ([0, 1], {}),
           random.paretovariate: ([1.5], {}),
           random.weibullvariate: ([1, 1], {}),
           random.randrange: ([10], {}),
           random.randint: ([0, 10], {}),
           random.choice: ([list(range(5))], {}),
           random.choices: ([list(range(5))], {'k': 2}),
           random.sample: ([list(range(5)), 2], {}),
           shuffle: ([list(range(5))], {})
       }
       
       args, kwargs = test_args[fun]
       try:
           params = spec.params(args, kwargs)
           print(f"Type: {spec.type}")
           print(f"Params: {params}")
           # Test actual function
           result = fun(*args, **kwargs)
           print(f"Sample result: {result}")
       except Exception as e:
           print(f"Error testing {fun.__name__}: {e}")