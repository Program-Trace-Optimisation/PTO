
from collections import namedtuple
from copy import copy
import random

from .check_immutable import check_immutable
from .tracer import tracer

# SEARCH OPERATORS ON TRACES

# solution data structure

Sol = namedtuple('Sol', ['pheno', 'geno'])

class Op:
    
    ##########
    # SET UP #
    ##########

    # bind operators (all instances of Op) to tracer
    tracer = tracer
    
    def __init__(self, generator = None, fitness = None, mutation = 'mutate_point_ind', crossover = 'crossover_uniform_ind', tracer = tracer):
        
        # bind algorithm and problem to operators
        self.generator = generator # problem-specific generator
        self.fitness = fitness # problem-specific fitness
        
        # set search operators parameters
        self.mutate_ind = getattr(self, mutation)
        self.crossover_ind = getattr(self, crossover)
            
    def __repr__(self):
        gen_name = None if self.generator is None else self.generator.__name__
        fit_name = None if self.fitness is None else self.fitness.__name__
        return self.__class__.__name__ + str((gen_name, fit_name, self.mutate_ind.__name__, self.crossover_ind.__name__))

    #############
    # OPERATORS #
    #############
    
    def evaluate_ind(self, sol):
        return self.fitness(sol.pheno)    
    
    def create_ind(self):
        geno = {}
        pheno = Op.tracer.play(self.generator, geno)
        return Sol(pheno, geno)
    
    # WARNING: 'geno' is in place parameter
    def fix_ind(self, geno):
        pheno = Op.tracer.play(self.generator, geno)
        return Sol(pheno, geno)
    
    ##########
    # MUTATE #
    ##########
    
    @check_immutable # parent sol not changed
    def mutate_position_wise_ind(self, sol): # position-wise mutation
        
        mut_prob = 1.0/len(sol.geno)         
        new_geno = { name : entry.mutation() if random.random() <= mut_prob else entry for name, entry in sol.geno.items() }

        return self.fix_ind(new_geno)
    
    @check_immutable # parent sol not changed
    def mutate_point_ind(self, sol): # point mutation
        
        new_geno = copy(sol.geno) # shallow copy
        name = random.choice(list(new_geno.keys()))
        # print(name)
        new_geno[name] = new_geno[name].mutation() # mutated copy

        # print(new_geno)

        return self.fix_ind(new_geno)
    
    
    @check_immutable # parent sol not changed
    def mutate_random_ind(self, _): # random mutation
        
        return self.create_ind()
    
    #############
    # CROSSOVER #
    #############
    
    @check_immutable # parent sols not changed
    def crossover_one_point_ind(self, sol1, sol2): # one-point crossover (coarse only)

        # align traces on names
        alignment = [key for key in sol1.geno if key in sol2.geno]
        assert alignment == [key for key in sol2.geno if key in sol1.geno], 'PTO: common keys in different orders!'

        # one-point crossover on alignment
        crossover_point = random.randint(0, len(alignment))
        new_geno_alignment = { key : (sol1 if pos <= crossover_point else sol2).geno[key] for pos, key in enumerate(alignment) }

        # union of parent traces and recombined alignment
        new_geno = sol1.geno | sol2.geno | new_geno_alignment
        
        return self.fix_ind(new_geno)

    @check_immutable # parent sols not changed
    def crossover_uniform_ind(self, sol1, sol2): # uniform crossover

        # align traces on names
        alignment = [key for key in sol1.geno if key in sol2.geno]
        assert alignment == [key for key in sol2.geno if key in sol1.geno], 'PTO: common keys in different orders!'

        # uniform crossover on alignment
        new_geno_alignment = { key : sol1.geno[key].crossover(sol2.geno[key]) for key in alignment }

        # union of parent traces and recombined alignment
        new_geno = sol1.geno | sol2.geno | new_geno_alignment
            
        return self.fix_ind(new_geno) #Sol(None, new_geno)

    ####################
    # CONVEX CROSSOVER #
    #################### 

    @check_immutable # parent sols not changed
    def convex_crossover_ind(self, sol1, sol2, sol3):
        # align traces on names (keys in genotype)
        alignment = [key for key in sol1.geno if key in sol2.geno and key in sol3.geno]
        assert alignment == [key for key in sol2.geno if key in sol1.geno and key in sol3.geno], 'PTO: common keys in different orders!'
    
        # uniform crossover on alignment
        new_geno_alignment = {
            key: random.choice([sol1.geno[key], sol2.geno[key], sol3.geno[key]])
            for key in alignment
        }
    
        # union of parent traces and recombined alignment
        new_geno = sol1.geno | sol2.geno | sol3.geno | new_geno_alignment
    
        # fix the new individual's phenotype based on the new genotype
        return self.fix_ind(new_geno)
