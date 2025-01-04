
import math
import random
from collections import namedtuple

"""
Parameter formats by type:
- 'real': (min, max, range)  # range = max-min or 2*std_dev
- 'int':  (min, max, step)   # inclusive bounds
- 'cat':  (sequence,)        # single tuple with sequence
- 'seq':  (sequence, k)      # k is number of items to select/generate
"""

RNGSpec = namedtuple('RNGSpec', ['type', 'params'])

rng_specs = {
   # Real-valued functions - all return (min, max, range)
   random.random: RNGSpec(
       type='real',
       params=lambda args: (0, 1, 1)
   ),
   random.uniform: RNGSpec(
       type='real',
       params=lambda args: (args[0], args[1], args[1]-args[0])
   ),
   random.triangular: RNGSpec(
       type='real',
       params=lambda args: (args[0], args[1], args[1]-args[0])
   ),
   random.betavariate: RNGSpec(
       type='real',
       params=lambda args: (0, 1, 1)  # Always [0,1]
   ),
   random.expovariate: RNGSpec(
       type='real',
       params=lambda args: (0, math.inf, 1.0/args[0] * 2)  # std_dev = 1/lambda
   ),
   random.gammavariate: RNGSpec(
       type='real',
       params=lambda args: (0, math.inf, args[0]**0.5/args[1] * 2)  # std_dev = sqrt(alpha)/beta
   ),
   random.gauss: RNGSpec(
       type='real',
       params=lambda args: (-math.inf, math.inf, args[1] * 2)  # range = 2*sigma
   ),
   random.lognormvariate: RNGSpec(
       type='real',
       params=lambda args: (0, math.inf, 
           (math.exp(args[1]**2-1)*math.exp(2*args[0]+args[1]**2))**0.5 * 2)  # 2*std_dev
   ),
   random.normalvariate: RNGSpec(
       type='real',
       params=lambda args: (-math.inf, math.inf, args[1] * 2)  # range = 2*sigma
   ),
   random.vonmisesvariate: RNGSpec(
       type='real',
       params=lambda args: (-math.pi, math.pi, math.pi * 2)  # Circular distribution [-π,π]
   ),
   random.paretovariate: RNGSpec(
       type='real',
       params=lambda args: (1, math.inf,  # Always starts at 1
           (args[0]/((args[0]-1)**2 * (args[0]-2)))**0.5 * 2)  # 2*std_dev
   ),
   random.weibullvariate: RNGSpec(
       type='real',
       params=lambda args: (0, math.inf,
           1.0/args[1] * (math.gamma(1+2.0/args[0])-math.gamma(1+1.0/args[0])**2)**0.5 * 2)  # 2*std_dev
   ),

   # Integer-valued functions - all return (min, max, step)
   random.randrange: RNGSpec(
       type='int',
       params=lambda args: (0, args[0]-1, 1) if len(args)==1 else 
                         (args[0], args[1]-1, 1) if len(args)==2 else 
                         (args[0], args[1]-1, args[2])
   ),
   random.randint: RNGSpec(
       type='int',
       params=lambda args: (args[0], args[1], 1)
   ),

   # Categorical function - all return (sequence,)
   random.choice: RNGSpec(
       type='cat',
       params=lambda args: (args[0],)
   ),

   # Sequence functions - all return (sequence, k)
   random.choices: RNGSpec(
       type='seq',
       params=lambda args, **kwargs: (args[0], kwargs.get('k', 1))
   ),
   random.sample: RNGSpec(
       type='seq',
       params=lambda args: (args[0], args[1])
   ),
   random.shuffle: RNGSpec(
       type='seq',
       params=lambda args: (args[0], len(args[0]))
   )
}
