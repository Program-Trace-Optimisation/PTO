
from collections import namedtuple
from copy import copy
import random
import math

from .check_immutable import check_immutable
from .tracer import tracer

# SEARCH OPERATORS ON TRACES

# solution data structure
Sol = namedtuple('Sol', ['pheno', 'geno'])

class Op:
    # bind operators (all instances of Op) to tracer
    tracer = tracer
    
    def __init__(self, generator = None, fitness = None, mutation = 'mutate_point_ind', crossover = 'crossover_uniform_ind', tracer = tracer):
        
        self.generator = generator # problem-specific generator
        self.fitness = fitness # problem-specific fitness
        self.mutate_ind = getattr(self, mutation)
        self.crossover_ind = getattr(self, crossover)
            
    def __repr__(self):
        gen_name = None if self.generator is None else self.generator.__name__
        fit_name = None if self.fitness is None else self.fitness.__name__
        return f"{self.__class__.__name__}({gen_name}, {fit_name}, {self.mutate_ind.__name__}, {self.crossover_ind.__name__})"

    def evaluate_ind(self, sol):
        return self.fitness(sol.pheno)    
    
    def create_ind(self):
        geno = {}
        pheno = Op.tracer.play(self.generator, geno)
        return Sol(pheno, geno)
    
    # 'geno' is in place parameter
    def fix_ind(self, geno):
        pheno = Op.tracer.play(self.generator, geno) # pheno = None
        return Sol(pheno, geno)
    
    @check_immutable
    def mutate_position_wise_ind(self, sol): 
        mut_prob = 1.0/len(sol.geno)         
        new_geno = { name : entry.mutation() if random.random() <= mut_prob else entry 
                    for name, entry in sol.geno.items() }
        return self.fix_ind(new_geno)
    
    @check_immutable 
    def mutate_point_ind(self, sol): 
        new_geno = copy(sol.geno) 
        name = random.choice(list(new_geno.keys()))
        new_geno[name] = new_geno[name].mutation()
        return self.fix_ind(new_geno)
    
    @check_immutable
    def mutate_random_ind(self, _):
        return self.create_ind()
        
    @check_immutable
    def crossover_one_point_ind(self, sol1, sol2): # coarse only

        # align traces on names
        alignment = self._align_genotypes(sol1, sol2)
    
        # one-point crossover on alignment
        crossover_point = random.randint(0, len(alignment))
        new_geno_alignment = { key : (sol1 if pos <= crossover_point else sol2).geno[key] 
                              for pos, key in enumerate(alignment) }

        # union of parent traces and recombined alignment
        new_geno = sol1.geno | sol2.geno | new_geno_alignment
        
        return self.fix_ind(new_geno)

    @check_immutable
    def crossover_uniform_ind(self, sol1, sol2):

        # align traces on names
        alignment = self._align_genotypes(sol1, sol2)

        # uniform crossover on alignment
        new_geno_alignment = { key : sol1.geno[key].crossover(sol2.geno[key]) for key in alignment }

        # union of parent traces and recombined alignment
        new_geno = sol1.geno | sol2.geno | new_geno_alignment
            
        return self.fix_ind(new_geno) 

    @check_immutable
    def convex_crossover_ind(self, sol1, sol2, sol3):
        
        # align traces on names (keys in genotype)
        alignment = self._align_genotypes(sol1, sol2, sol3)

        # uniform crossover on alignment
        new_geno_alignment = {
            key: sol1.geno[key].convex_crossover(sol2.geno[key], sol3.geno[key])
            for key in alignment
        }
    
        # union of parent traces and recombined alignment
        new_geno = sol1.geno | sol2.geno | sol3.geno | new_geno_alignment
    
        # fix the new individual's phenotype based on the new genotype
        return self.fix_ind(new_geno)
    
    @staticmethod
    def _align_genotypes(*sols):
        
        # Use the keys from the first solution (sol1) as the base order
        base_keys = list(sols[0].geno.keys())
        
        # Filter keys that are present in all solutions, maintaining the order from sol1
        alignment = [key for key in base_keys if all(key in sol.geno for sol in sols)]
        
        # Verify that the alignment is consistent across all solutions
        for sol in sols[1:]:  # Skip sol1 as it's our base order
            sol_alignment = [key for key in sol.geno.keys() if key in alignment]
            assert sol_alignment == alignment, 'PTO: common keys in different orders!'
        
        return alignment
        
    @check_immutable
    def distance_ind(self, sol1, sol2): # trace distance

        # common names
        common = set(sol1.geno.keys()) & set(sol2.geno.keys())

        # distance on common names
        distance_alignment = sum(sol1.geno[key].distance(sol2.geno[key]) for key in common)

        # symmetric difference on names
        symmetric_difference = len(set(sol1.geno.keys()) ^ set(sol2.geno.keys())) 
            
        return distance_alignment + symmetric_difference
    
    def space_dimension_ind(self, sol):
        return sum(math.log2(entry.size()) for _, entry in sol.geno.items())

