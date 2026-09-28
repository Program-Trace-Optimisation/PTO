"""Naming: how each random decision gets its address.

Three strategies:

    Linear()   addresses 0, 1, 2, ... in the order of the decisions.
    Dynamic()  structured addresses, computed as the generator runs.
    Static()   the same structured addresses, compiled into the generator.

A structured address is a tuple of segments, one per scope the decision is
in, ending with the rnd call itself. For

    def generator():
        def helper():
            return rnd.choice([0, 1])
        return [helper() for i in range(3)]

the first decision is (('comp', (4, 30), 0), ('helper', (4, 12)), ('choice', (3, 15))):
iteration 0 of the comprehension whose iterable is at line 4, column 30, then
the call to helper at (4, 12), then the choice call at (3, 15). Positions are
(line, column) in the generator's source, line 1 being its def line. The
scopes are function calls (kind, site), and iterations of for and while
loops and comprehensions (kind, site, i). format_address shows an address
as a string.

A strategy prepares the generator once (Dynamic and Static rewrite its
source, see _rewrite.py), and gives each play a namer, which holds the
naming's state during that play and names the decisions made without a name.
Dynamic also names the rnd calls in helpers defined outside the generator,
from the call stack. Static computes every address in the generator's own
code, so it is faster, but it only sees rnd calls written in the generator
and its nested functions, which must be called directly by name.
"""

import functools
import sys
import types

from ._rewrite import StaticNamingError, call_site, environment, is_rewritten, rewrite
from .distributions import rnd

__all__ = ["Linear", "Dynamic", "Static", "NAMINGS", "format_address", "StaticNamingError"]


def format_address(address):
    """An address as a string, eg 'comp@4.30:0/helper@4.12/choice@3.15'."""
    if not isinstance(address, tuple):
        return str(address)
    parts = []
    for seg in address:
        kind, (line, col), *count = seg
        parts.append(f"{kind}@{line}.{col}" + (f":{count[0]}" if count else ""))
    return "/".join(parts)


def _in_core(frame):
    return frame.f_globals.get("__name__", "").startswith("pto_next.") and not is_rewritten(frame)


def _outside_core(frame):
    """The first frame outside this package, and the name of the rnd
    function called from it (the last frame inside)."""
    kind = None
    while frame is not None and _in_core(frame):
        kind = frame.f_code.co_name
        frame = frame.f_back
    return frame, kind


# ---------------------------------------------------------------------------
# Linear
# ---------------------------------------------------------------------------


class _LinearNamer:
    __slots__ = ("count",)

    def __init__(self):
        self.count = 0

    def unnamed(self):
        address = self.count
        self.count += 1
        return address


class Linear:
    """Addresses 0, 1, 2, ... The generator's source is not needed."""

    def prepare(self, generator):
        env, names = environment(generator)  # for the old core's rnd
        if all(generator.__globals__.get(k) is rnd for k in names if k in generator.__globals__):
            return generator
        new = types.FunctionType(
            generator.__code__, env, generator.__name__,
            generator.__defaults__, generator.__closure__,
        )
        new.__kwdefaults__ = generator.__kwdefaults__
        return functools.update_wrapper(new, generator)

    def start(self):
        return _LinearNamer()


# ---------------------------------------------------------------------------
# Dynamic
# ---------------------------------------------------------------------------


class _DynamicNamer:
    __slots__ = ("prefix",)

    def __init__(self):
        self.prefix = ()  # the address of the current scope

    def unnamed(self):
        """A decision the rewriting did not reach (in a helper defined outside
        the generator): its address continues from the call stack, up to the
        rewritten code."""
        frame, kind = _outside_core(sys._getframe(1))
        segments = []
        while frame is not None and not is_rewritten(frame):
            segments.append((kind, call_site(frame)))
            kind = frame.f_code.co_name
            frame = frame.f_back
        if frame is not None:
            segments.append((kind, call_site(frame)))
        return self.prefix + tuple(reversed(segments))


class Dynamic:
    """Structured addresses, computed as the generator runs."""

    def prepare(self, generator):
        return rewrite(generator, "dynamic")

    def start(self):
        return _DynamicNamer()


# ---------------------------------------------------------------------------
# Static
# ---------------------------------------------------------------------------


class _StaticNamer:
    __slots__ = ()

    def unnamed(self):
        _, kind = _outside_core(sys._getframe(1))
        raise ValueError(
            f"rnd.{kind}() was called without a name under naming='static'. Static naming "
            "only sees rnd calls written in the generator and its nested functions; for "
            "helpers defined elsewhere use naming='dynamic' (the default)."
        )


class Static:
    """Structured addresses compiled into the generator."""

    def prepare(self, generator):
        return rewrite(generator, "static")

    def start(self):
        return _StaticNamer()


NAMINGS = {"linear": Linear, "dynamic": Dynamic, "static": Static}
