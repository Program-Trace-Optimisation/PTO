"""PTO next: an experimental new core for Program Trace Optimisation.

It runs alongside the original core (pto) and has the same user interface:

    from pto_next import run, rnd

    def generator():
        return [rnd.choice([0, 1]) for i in range(10)]

    (pheno, geno), fx, num_gen = run(generator, sum, better=max)

The concepts, one per module, each using only those before it:

    trace.py           the engine: a trace records random decisions (choices);
                       playing the generator on a trace turns it into a
                       solution, reusing, repairing or sampling each decision
    distributions/     the kinds of random decision, each knowing how it
                       samples and varies, and rnd, the functions that make them
    naming.py          how each decision gets its address (linear, dynamic,
                       static); the source rewriting is in _rewrite.py
    search_operators/  how whole solutions are varied and compared, by varying
                       their decisions and playing the new trace
    space.py           the search space: a problem bound to a naming, fine or
                       coarse variation, a random number generator and the
                       chosen search operators; what solvers see
    run.py             run(): build a search space and run a solver on it

Distributions and search operators are extended by adding a module to their
package (see their __init__). See pto_next/README.md.
"""

from .distributions import Distribution, rnd
from .naming import format_address
from .run import Result, run
from .space import SearchSpace, Solution
from .trace import Choice, current_play, decide, play

__all__ = [
    "run", "rnd", "Result", "SearchSpace", "Solution", "Choice", "Distribution",
    "decide", "play", "current_play", "format_address",
]
