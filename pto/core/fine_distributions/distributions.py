
from copy import copy
import random
from ..base import Dist, check_immutable
from .supp import supp

class Random_real(Dist):
    def __init__(self, fun, *args, val=None):
        super().__init__(fun, *args, val=val)
        self.min, self.max, self.range = supp[fun][1](args)
    
    def repair_val(self):
        self.val = min(max(self.min, self.val), self.max)
    
    @check_immutable
    def mutation(self):
        offspring = copy(self)
        offspring.val = self.val + random.gauss(0, 0.1*self.range)
        offspring.repair_val()
        return offspring

    @check_immutable
    def crossover(self, other):
        if isinstance(other, Random_real):
            offspring = copy(self)
            offspring.val = random.uniform(self.val, other.val)
            return offspring
        return super().crossover(other)
    
    @check_immutable
    def convex_crossover(self, other1, other2):
        if isinstance(other1, Random_real) and isinstance(other2, Random_real):
            offspring = copy(self)
            min_val = min(self.val, other1.val, other2.val)
            max_val = max(self.val, other1.val, other2.val)
            offspring.val = random.uniform(min_val, max_val)
            return offspring
        return super().convex_crossover(other1, other2)

    @check_immutable
    def distance(self, other):
        if isinstance(other, Random_real):
            return min(1, abs(self.val - other.val)/self.range)
        return super().distance(other)
    
    def repair(self, other):
        if isinstance(other, Random_real):
            self.val = ((other.val-other.min)/other.range)*self.range+self.min
            self.repair_val()
        else:
            super().repair(other)

class Random_int(Dist):
    def __init__(self, fun, *args, val=None):
        super().__init__(fun, *args, val=val)
        self.min, self.max, self.step = supp[fun][1](args)
    
    def repair_val(self):
        round_val = self.min + round((self.val - self.min) / self.step) * self.step
        self.val = min(max(self.min, round_val), self.max)
    
    @check_immutable
    def mutation(self):
        offspring = copy(self)
        for _ in range(10):
            offspring.val = self.val + random.choice([-1, 1]) * self.step
            offspring.repair_val()
            if offspring.val != self.val: break
        return offspring

    @check_immutable
    def crossover(self, other):
        if isinstance(other, Random_int):
            offspring = copy(self)
            min_val = min(self.val, other.val)
            max_val = max(self.val, other.val)
            offspring.val = random.randint(min_val, max_val)
            return offspring
        return super().crossover(other)
    
    @check_immutable
    def convex_crossover(self, other1, other2):
        if isinstance(other1, Random_int) and isinstance(other2, Random_int):
            offspring = copy(self)
            min_val = min(self.val, other1.val, other2.val)
            max_val = max(self.val, other1.val, other2.val)
            offspring.val = random.randint(min_val, max_val)
            return offspring
        return super().convex_crossover(other1, other2)

    @check_immutable
    def distance(self, other):
        if isinstance(other, Random_int):
            return min(1, abs(self.val - other.val)/(self.max-self.min))
        return super().distance(other)

    def repair(self, other):
        if isinstance(other, Random_int):
            self.val = ((other.val-other.min)/other.step)*self.step+self.min
            self.repair_val()
        else:
            super().repair(other)

class Random_cat(Dist):
    def __init__(self, fun, *args, val=None):
        super().__init__(fun, *args, val=val)
        self.seq = supp[fun][1](args)
        self.args = (copy(self.args[0]),)
    
    def repair_val(self):
        if self.val not in self.seq:
            self.val = random.choice(self.seq)

    @check_immutable
    def mutation(self):
        offspring = copy(self)
        if len(set(self.seq)) >= 2:
            offspring.val = random.choice([v for v in self.seq if v != self.val])
        return offspring

    def repair(self, other):
        if isinstance(other, Random_cat):
            if other.val in self.seq:
                self.val = other.val
            else:
                diff_seq = [val for val in self.seq if val not in other.seq]
                self.val = random.choice(diff_seq) if diff_seq else random.choice(self.seq)
        else:
            super().repair(other)