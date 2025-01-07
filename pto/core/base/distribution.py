from copy import copy
import random
from .check_immutable import check_immutable

# from pto.core.base.check_immutable import check_immutable # Use this when running the script directly


class Dist:
    def __init__(self, fun, *args, val=None, **kwargs):
        """
        Initialize a distribution with a function, its arguments and an optional value.

        Args:
            fun: Function to generate values
            *args: Positional arguments for the function
            val: Optional initial value
            **kwargs: Keyword arguments for the function
        """
        self.fun = fun
        self.args = tuple(copy(arg) for arg in args)
        self.kwargs = {k: copy(v) for k, v in kwargs.items()}
        self.val = val

    def sample(self):
        """Generate a new value using the stored function and arguments."""
        self.val = self.fun(*self.args, **self.kwargs)

    def repair(self, _):
        """Regenerate the value."""
        self.sample()

    @check_immutable
    def mutation(self):
        """Create a new instance with a fresh sample."""
        offspring = copy(self)
        offspring.sample()
        return offspring

    @check_immutable
    def crossover(self, other):
        """Randomly select one of two parents."""
        return random.choice([self, other])

    @check_immutable
    def convex_crossover(self, other1, other2):
        """Randomly select one of three parents."""
        return random.choice([self, other1, other2])

    @check_immutable
    def distance(self, other):
        """Binary distance metric between distributions."""
        return float(self != other)

    def size(self):
        """Return fixed size of the distribution."""
        return 2

    def __repr__(self):
        """String representation of the distribution."""
        return (
            f"{self.__class__.__name__}({self.fun.__name__}, "
            f"{self.args}, {self.kwargs}, val={self.val})"
        )

    def __eq__(self, other):
        """Check equality based on function, arguments, and value."""
        return (
            self.fun.__name__ == other.fun.__name__
            and self.args == other.args
            and self.kwargs == other.kwargs
            and self.val == other.val
        )
