import unittest

from pto.solvers import genetic_algorithm as GA, hill_climber as HC, random_search as RS, particle_swarm_optimisation as PSO
from pto.core.base import Op, tracer, Dist

import random
import sys
import os

def random_program():
    return([tracer.sample('pos 1', Dist(random.random)),
            tracer.sample('pos 2', Dist(random.choice, ['a','b','c'])),
            tracer.sample('pos 3', Dist(random.randint, 1, 10))])

def fitness(sol): return sol[0]

class TestSolvers(unittest.TestCase):

    def test_genetic_algorithm(self):
        op = Op(generator=random_program, fitness=fitness)
        ga = GA(op)
        self.assertIn('op', ga.__dict__)
        res = ga()
        self.assertTrue(len(res[0].geno) == 3)

    def test_hill_climber(self):
        op = Op(generator=random_program, fitness=fitness)
        hc = HC(op)
        self.assertIn('op', hc.__dict__)
        res = hc()
        self.assertTrue(len(res[0].geno) == 3)

    def test_random_search(self):
        op = Op(generator=random_program, fitness=fitness)
        rs = RS(op)
        self.assertIn('op', rs.__dict__)
        res = rs()
        self.assertTrue(len(res[0].geno) == 3)

    def test_particle_swarm_optimisation(self):
        op = Op(generator=random_program, fitness=fitness)
        pso = PSO(op)
        self.assertIn('op', pso.__dict__)
        res = pso()
        self.assertTrue(len(res[0].geno) == 3)

if __name__ == '__main__':
    unittest.main()
