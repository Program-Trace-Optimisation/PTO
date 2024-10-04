import random # NB CHECK

from .distributions import Random_real, Random_int, Random_cat

class Random_real_repair(Random_real): # class for real-valued distributions

  def repair(self, other): # alter self
    #print("repairing real")  
    if type(self) == type(other): # if trace entry compatible
        #print('compatible')
        # trace value adpatation: align on min and rescale on range size
        self.val = ((other.val-other.min)/other.range)*self.range+self.min # recycle and adapt trace value 
        self.repair_val() # and repair it
    else: # if incompatible
        #print('incompatible')
        self.sample() # resample

class Random_int_repair(Random_int): # class for integer-valued distributions

  def repair(self, other): # alter self
    if type(self) == type(other): # if trace entry compatible
        #print('compatible')
        # trace value adpatation: align on min and rescale on step size
        self.val = ((other.val-other.min)/other.step)*self.step+self.min # recycle and adapt trace value 
        self.repair_val() # and repair it
    else: # if incompatible
        #print('incompatible')
        self.sample() # resample 

class Random_cat_repair(Random_cat):
    
  def repair(self, other): # alter self
    if type(self) == type(other): # if trace entry compatible
        #print('compatible')
        # trace value adpatation: reuse value if available, 
        # or try an available value not available in trace
        if other.val in self.seq:
            self.val = other.val  
        else:
            diff_seq = [val for val in self.seq if val not in other.seq]
            self.val = random.choice(diff_seq) if diff_seq else random.choice(self.seq)  # recycle and adapt trace value 
        #self.repair_val() # and repair it
    else: # if incompatible
        #print('incompatible')
        self.sample() # resample     
