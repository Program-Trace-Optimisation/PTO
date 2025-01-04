
from copy import copy
import random
from ..base import Dist, check_immutable
from .supp import rng_specs

#---

class Random_real(Dist):
    def __init__(self, fun, *args, val=None):
        super().__init__(fun, *args, val=val)
        self.min, self.max, self.range = rng_specs[fun].params(args)
    
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
    
    def size(self):
        return 10
    
    def repair(self, other):
        if isinstance(other, Random_real):
            self.val = ((other.val-other.min)/other.range)*self.range+self.min
            self.repair_val()
        else:
            super().repair(other)

#---

class Random_int(Dist):
    def __init__(self, fun, *args, val=None):
        super().__init__(fun, *args, val=val)
        self.min, self.max, self.step = rng_specs[fun].params(args)
    
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
    
    def size(self):
        return (self.max-self.min)/self.step

    def repair(self, other):
        if isinstance(other, Random_int):
            self.val = ((other.val-other.min)/other.step)*self.step+self.min
            self.repair_val()
        else:
            super().repair(other)

#---

class Random_cat(Dist):
    def __init__(self, fun, *args, val=None):
        super().__init__(fun, *args, val=val)
        self.seq = rng_specs[fun].params(args)
        #(self.seq)
        #self.args = (copy(self.args[0]),)
    
    def repair_val(self):
        if self.val not in self.seq:
            self.val = random.choice(self.seq)

    @check_immutable
    def mutation(self):
        offspring = copy(self)
        if len(set(self.seq)) >= 2:
            offspring.val = random.choice([v for v in self.seq if v != self.val])
        return offspring
    
    def size(self):
        return len(self.seq)

    def repair(self, other):
        if isinstance(other, Random_cat):
            if other.val in self.seq:
                self.val = other.val
            else:
                diff_seq = [val for val in self.seq if val not in other.seq]
                self.val = random.choice(diff_seq) if diff_seq else random.choice(self.seq)
        else:
            super().repair(other)

#---

# TODO: 1) check implementation and test this class
#       2) implement handling of keyword args and inplace args (DONE)

class Random_seq(Dist):
    def __init__(self, fun, *args, val=None):
        super().__init__(fun, *args, val=val)
        self.sequence, self.k = rng_specs[fun].params(args)
        
    def repair_val(self):
        if not self.val or len(self.val) != self.k:
            self.val = random.sample(self.sequence, self.k)
    
    @check_immutable
    def mutation(self):
        offspring = copy(self)
        if len(self.sequence) >= 2:
            idx = random.randrange(len(offspring.val))
            valid_choices = [x for x in self.sequence if x not in offspring.val]
            if valid_choices:
                offspring.val = list(offspring.val)
                offspring.val[idx] = random.choice(valid_choices)
                offspring.val = tuple(offspring.val)
        return offspring
    
    @check_immutable
    def crossover(self, other):
        if isinstance(other, Random_seq):
            offspring = copy(self)
            if len(set(self.sequence)) >= 2:
                # Take some elements from each parent while maintaining uniqueness
                combined = list(set(self.val) | set(other.val))
                if len(combined) >= self.k:
                    offspring.val = tuple(random.sample(combined, self.k))
                else:
                    # If we need more elements, sample from remaining sequence
                    needed = self.k - len(combined)
                    remaining = [x for x in self.sequence if x not in combined]
                    additional = random.sample(remaining, needed)
                    offspring.val = tuple(combined + additional)
            return offspring
        return super().crossover(other)

    @check_immutable
    def convex_crossover(self, other1, other2):
        if isinstance(other1, Random_seq) and isinstance(other2, Random_seq):
            offspring = copy(self)
            if len(set(self.sequence)) >= 2:
                # Combine elements from all three parents
                combined = list(set(self.val) | set(other1.val) | set(other2.val))
                if len(combined) >= self.k:
                    offspring.val = tuple(random.sample(combined, self.k))
                else:
                    # If we need more elements, sample from remaining sequence
                    needed = self.k - len(combined)
                    remaining = [x for x in self.sequence if x not in combined]
                    additional = random.sample(remaining, needed)
                    offspring.val = tuple(combined + additional)
            return offspring
        return super().convex_crossover(other1, other2)
    
    def size(self):
        return min(len(self.sequence), self.k)
    
    def repair(self, other):
        if isinstance(other, Random_seq):
            if len(other.val) == self.k:
                preserved = [x for x in other.val if x in self.sequence]
                needed = self.k - len(preserved)
                if needed > 0:
                    available = [x for x in self.sequence if x not in preserved]
                    additional = random.sample(available, min(needed, len(available)))
                    self.val = tuple(preserved + additional)
                else:
                    self.val = tuple(preserved[:self.k])
            else:
                self.val = random.sample(self.sequence, self.k)
        else:
            super().repair(other)