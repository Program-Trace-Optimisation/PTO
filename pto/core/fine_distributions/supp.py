
import math
import random

supp = {
        # Real-valued functions
        # min, max, range = max - min or twice standard deviation if min or max infinite 
        random.random:          ('real', lambda args: (0, 1, 1)),
        random.uniform:         ('real', lambda args: (args[0], args[1], args[1]-args[0])),
        random.triangular:      ('real', lambda args: (args[0], args[1], args[1]-args[0])),
        random.betavariate:     ('real', lambda args: (0, 1, 1)),
        random.expovariate:     ('real', lambda args: (0, math.inf, 1.0/args[0] * 2)),
        random.gammavariate:    ('real', lambda args: (0, math.inf, args[0]**0.5/args[1] * 2)),
        random.gauss:           ('real', lambda args: (-math.inf, math.inf, args[1] * 2)),
        random.lognormvariate:  ('real', lambda args: (0, math.inf, (math.exp(args[1]**2-1)*math.exp(2*args[0]+args[1]**2))**0.5 * 2)),
        random.normalvariate:   ('real', lambda args: (-math.inf, math.inf, args[1] * 2)),
        random.vonmisesvariate: ('real', lambda args: (-math.pi, math.pi, math.pi * 2)),
        random.paretovariate:   ('real', lambda args: (0, math.inf, (args[0]/((args[0]-1)**2 * (args[0]-2)))**0.5 * 2)),
        random.weibullvariate:  ('real', lambda args: (0, math.inf, 1.0/args[1] * (math.gamma(1+2.0/args[0])-math.gamma(1+1.0/args[0])**2)**0.5 * 2)),

        # Integer-valued functions
        # min, max, step
        random.randrange:       ('int', lambda args: (0, args[0]-1, 1) if len(args)==1 else 
                                                     (args[0], args[1]-1, 1) if len(args)==2 else 
                                                     (args[0], args[1]-1, args[2])),
        random.randint:         ('int', lambda args: (args[0], args[1], 1)),

        # Categorical function
        # seq
        random.choice:          ('cat', lambda args: args[0])
    }

    # UNSUPPORTED (wrong tracing effect if made traceable):
    # 'getrandbits' - low level, used with MersenneTwister
    # 'choices'     - keyword arguments, returns a sequence
    # 'shuffle'     - in-place, returns a sequence
    # 'sample'      - keyword arguments, returns a sequence 
