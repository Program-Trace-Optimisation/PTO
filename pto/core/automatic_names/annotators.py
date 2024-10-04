
import itertools
from functools import wraps

from .node import Node


class _Name():
    def __init__(self):
        self.stack = [] # name stack for structured naming
        self.sequence = itertools.count() # name sequence for linear naming

    def get_stack_name(self):
        return 'root/'+'/'.join(map(str, self.stack[1:]))  # output stack as string

    def get_seq_name(self):
        return str(next(self.sequence))  # iter sequence and output as string

Name = _Name()
        

######################
# Function Annotator #
######################

# decorator

def func_name(func, args_name=True):
  
  # this wrapper keeps track of the "runtime name"
  @wraps(func)
  def fn(*args, **kwargs):

    # include arguments

    str_args = str(args) if (args and args_name) else ''
    
    # build name node
    node = Node(func.__name__+str_args)
        
    # push call identifier on the stack
    Name.stack.append(node)
    
    # get the output of func
    output = func(*args, **kwargs)
    
    # pop call identifier from the stack
    Name.stack.pop()
    
    return output
    
  return fn

#---

######################
# Iterator Annotator #
######################

# generator

def iter_name(iterable):

    # Convert iterable to iterator
    iterator = iter(iterable)
    
    # build name node
    node = Node('iter', count=0)    
        
    # push node on name stack
    Name.stack.append(node)
    
    # iterate
    # for i in iter:
    #     yield i
    #     
    #     # increment count on top element of stack
    #     Name.stack[-1].inc_count()

    try:
        while True:
            # increment count on top element of stack
            # Note: count is incremented in the scope 
            # where next() is called (impicitly or explicitly) 
            yield next(iterator)
            Name.stack[-1].inc_count()
    except StopIteration:
        pass
    finally:
        # pop node from stack
        Name.stack.pop()

#---

##################
# Loop Annotator #
##################

# context

class Loop_name():
    
    def __enter__(self):
            
        # build name node
        node = Node('loop', count=0)    
        
        # push node on name stack
        Name.stack.append(node)
        
        return self
    
    def __exit__(self, type, value, traceback): 
        
        # pop node from stack
        Name.stack.pop()
        
    def __call__(self):
        
        # increment count on top element of stack
        Name.stack[-1].inc_count()
        
#---
