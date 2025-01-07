import itertools
from functools import wraps
from .node import Node

"""
This module provides annotators for tracking execution of functions, 
iterations and loops using a naming stack mechanism.
"""


class _Name:
    """
    Maintains stack and sequence for structured and linear naming.

    Used as a singleton instance to track program execution structure
    through a stack of nodes and provide sequential naming.

    Example:
        print(Name.get_stack_name())  # 'root/function@(10,24)/loop@(12,36):5'
        print(Name.get_seq_name())    # '42'
    """

    def __init__(self):
        self.stack = []  # name stack for structured naming
        self.sequence = itertools.count()  # name sequence for linear naming

    def get_stack_name(self):
        """Return stack as hierarchical path string."""
        return "root/" + "/".join(map(str, self.stack[1:]))  # output stack as string

    def get_seq_name(self):
        """Return next sequential number as string."""
        return str(next(self.sequence))  # iter sequence and output as string


Name = _Name()

######################
# Function Annotator #
######################


# decorator
def func_name(func, args_name=True):
    """
    Decorator that tracks function calls in the naming stack.

    Creates a node for each function call that includes the function name
    and optionally its arguments. The node is pushed onto the naming stack
    during execution and popped afterwards.

    Args:
        func: Function to be decorated
        args_name: If True, include arguments in node name

    Returns:
        Wrapped function that manages the naming stack

    Example:
        @func_name
        def process(x, y=10):
            print(Name.get_stack_name())  # 'root/process(1){'y': 20}'

        process(1, y=20)
    """

    @wraps(func)
    def fn(*args, **kwargs):
        # Include both args and kwargs in name
        str_args = ""
        if args_name:
            if args:
                str_args += str(args)
            if kwargs:
                str_args += str(kwargs)

        # build name node
        node = Node(func.__name__ + str_args)

        # push call identifier on the stack
        Name.stack.append(node)

        # get the output of func
        output = func(*args, **kwargs)

        # pop call identifier from the stack
        Name.stack.pop()

        return output

    return fn


# ---

######################
# Iterator Annotator #
######################


# generator
def iter_name(iterable):
    """
    Generator that wraps an iterable to track iteration progress.

    Creates a node to track iteration count and maintains it on the
    naming stack while iteration is in progress.

    Args:
        iterable: Any iterable object to wrap

    Yields:
        Items from the wrapped iterable

    Example:
        items = [1, 2, 3]
        for x in iter_name(items):
            print(Name.get_stack_name())  # 'root/iter@(15,48):1'
            # count increases with each iteration
    """

    # Convert iterable to iterator
    iterator = iter(iterable)

    # build name node
    node = Node("iter", count=0)

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


# ---

##################
# Loop Annotator #
##################


# context
class Loop_name:
    """
    Context manager for tracking loop iterations.

    Creates a node to count loop iterations. Node is managed on the stack
    during the loop's execution. Requires explicit counting via call.

    Example:
        data = [1, 2, 3]
        with Loop_name() as loop:
            for x in data:
                print(Name.get_stack_name())  # 'root/loop@(20,60):1'
                loop()  # increment counter
                process(x)
    """

    def __enter__(self):
        # build name node
        node = Node("loop", count=0)

        # push node on name stack
        Name.stack.append(node)

        return self

    def __exit__(self, type, value, traceback):
        # pop node from stack
        Name.stack.pop()

    def __call__(self):
        # increment count on top element of stack
        Name.stack[-1].inc_count()


# ---
