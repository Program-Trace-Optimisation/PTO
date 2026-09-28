"""The engine: choices, traces, and playing a generator on a trace.

A choice is one random decision: its distribution and the value chosen. A
trace maps addresses (the names of decisions) to choices. Playing a generator
on a trace runs it once, and each random decision it makes

    reuses the recorded choice, if the trace has one with the same distribution,
    is repaired from the recorded choice, if the distribution changed,
    is sampled, if the trace has no choice with that address.

The result is the solution the trace stands for (the phenotype) and the trace
of the decisions actually made. The engine knows nothing about particular
distributions, naming or search: repair and naming are given to play().
"""

import random
from contextvars import ContextVar
from typing import Any, NamedTuple


class Choice(NamedTuple):
    """One random decision. Immutable, so traces can share it."""

    dist: Any  # a Distribution (see distributions/)
    value: Any


_current = ContextVar("pto_next_play", default=None)


def current_play():
    """The Play running now, or None outside a play."""
    return _current.get()


class Play:
    """One run of a generator on a trace."""

    __slots__ = ("input", "output", "rng", "repair", "namer")

    def __init__(self, trace, rng, repair, namer):
        self.input = trace  # the trace being played
        self.output = {}  # the trace of the decisions made
        self.rng = rng
        self.repair = repair  # repair(prev_choice, dist, rng) -> Choice
        self.namer = namer  # gives addresses to decisions made without a name

    def choose(self, dist, name):
        """The value of the decision `name` with distribution dist."""
        if name is None:
            if self.namer is None:
                raise ValueError("a random decision was made without a name, and no naming is in use")
            name = self.namer.unnamed()
        output = self.output
        if name in output:
            raise ValueError(
                f"PTO: two random decisions in one run of the generator have the name {name!r}"
            )
        prev = self.input.get(name)
        if prev is None:
            choice = Choice(dist, dist.sample(self.rng))
        elif prev.dist == dist:
            choice = prev
        else:
            choice = self.repair(prev, dist, self.rng)
        output[name] = choice
        return choice.value


def play(generator, trace, rng, repair, namer=None, args=()):
    """Run generator(*args) on trace. Returns (phenotype, trace of the decisions made)."""
    p = Play(trace, rng, repair, namer)
    token = _current.set(p)
    try:
        pheno = generator(*args)
    finally:
        _current.reset(token)
    return pheno, p.output


def decide(dist, name=None):
    """Make the random decision dist (the rnd functions call this).

    During a play the decision is recorded; outside a play it is sampled
    from the random module, so a generator also runs without PTO.
    """
    p = _current.get()
    if p is None:
        return dist.sample(random)
    return p.choose(dist, name)
