"""Rewriting a generator so that each rnd call gets its structured address.

The machinery behind dynamic and static naming (see naming.py for what the
addresses are). ScopeTransformer marks the scopes of the generator's source:
function calls, loop iterations and comprehension iterations, and gives each
rnd call a name. With mode='dynamic', the scopes are entered and left at run
time by the helpers at the end of this module, which keep the current scope
in the namer of the current play (namer.prefix). With mode='static', each
function computes the addresses itself, in a local variable _pto_prefix.
"""

import ast
import functools
import inspect
import itertools
import linecache
import sys
import textwrap

from ._compat import is_old_rnd
from .distributions import Rnd, rnd
from .trace import current_play

FILENAME_PREFIX = "<pto_next "  # filename of rewritten generators


def is_rewritten(frame):
    return frame.f_code.co_filename.startswith(FILENAME_PREFIX)


# ---------------------------------------------------------------------------
# The generator's environment, with rnd
# ---------------------------------------------------------------------------


def _closure_vars(func):
    out = {}
    for name, cell in zip(func.__code__.co_freevars, func.__closure__ or ()):
        try:
            out[name] = cell.cell_contents
        except ValueError:
            pass
    return out


def environment(func):
    """func's globals and closure variables, with every rnd (also the old
    core's) replaced by this core's rnd, and the names under which func sees rnd."""
    env = func.__globals__ | _closure_vars(func)
    names = {"rnd"} | {k for k, v in env.items() if isinstance(v, Rnd) or is_old_rnd(v)}
    env.update(dict.fromkeys(names, rnd))
    return env, names


# ---------------------------------------------------------------------------
# The scope transformer
# ---------------------------------------------------------------------------


def _site(node):
    return (node.lineno, node.col_offset)


def _name(id, store=False):
    return ast.Name(id=id, ctx=ast.Store() if store else ast.Load())


def _call(func, *args):
    return ast.Call(func=_name(func) if isinstance(func, str) else func, args=list(args), keywords=[])


class StaticNamingError(ValueError):
    pass


def _local_defs(fn):
    """Names of the functions defined in fn's body (at any statement depth),
    not counting those inside other functions or classes."""
    names, todo = set(), list(fn.body)
    while todo:
        node = todo.pop()
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif not isinstance(node, (ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            todo.extend(ast.iter_child_nodes(node))
    return names


class ScopeTransformer(ast.NodeTransformer):
    """Rewrites a generator so that each rnd call is given its address.

    mode='dynamic': scopes are entered and left at run time (_pto_fn,
    _pto_loop, _pto_iter), and each rnd call gets name=_pto_addr(segment).
    mode='static': each function has a local _pto_prefix, the address of its
    scope, updated by loops and passed to nested functions as an extra first
    argument; each rnd call gets name=_pto_prefix + (..., segment).
    """

    def __init__(self, mode, rnd_names):
        assert mode in ("dynamic", "static")
        self.mode = mode
        self.rnd_names = rnd_names
        self.depth = 0
        self.nested = set()  # static: nested functions visible here
        self.comp = []  # static: comprehension segments (site, counter var) we are in
        self.counter = itertools.count()

    def _var(self, what):
        return f"_pto_{what}_{next(self.counter)}"

    # -- addresses ----------------------------------------------------------------

    def _address(self, segment):
        """Expression for the address of a call with this (constant) segment."""
        if self.mode == "dynamic":
            return _call("_pto_addr", ast.Constant(segment))
        elts = [
            ast.Tuple(elts=[ast.Constant("comp"), ast.Constant(site), _name(var)], ctx=ast.Load())
            for site, var in self.comp
        ]
        elts.append(ast.Constant(segment))
        return ast.BinOp(left=_name("_pto_prefix"), op=ast.Add(), right=ast.Tuple(elts=elts, ctx=ast.Load()))

    # -- functions ----------------------------------------------------------------

    def visit_FunctionDef(self, node):
        top = self.depth == 0
        if top:
            node.decorator_list = []  # the generator is rewritten, not re-decorated
        saved = self.nested
        if self.mode == "static":
            self.nested = saved | _local_defs(node)
            if not top:
                node.args.posonlyargs.insert(0, ast.arg(arg="_pto_prefix"))
        elif not top:
            node.decorator_list.insert(0, _name("_pto_fn"))
        self.depth += 1
        comp, self.comp = self.comp, []
        self.generic_visit(node)
        self.comp = comp
        self.depth -= 1
        self.nested = saved
        if top and self.mode == "static":
            node.body.insert(0, ast.Assign(targets=[_name("_pto_prefix", True)], value=ast.Constant(())))
        return node

    def visit_AsyncFunctionDef(self, node):
        raise StaticNamingError("async functions are not supported in a generator")

    def visit_ClassDef(self, node):
        if self.mode == "static":
            return node  # methods are left alone: their rnd calls need dynamic naming
        return self.generic_visit(node)

    def _statements(self, stmts):
        out = []
        for s in stmts:
            s = self.visit(s)
            if isinstance(s, list):
                out.extend(s)
            elif s is not None:
                out.append(s)
        return out

    def visit_Lambda(self, node):
        # a lambda has no scope of its own: its rnd calls get the address
        # of the scope where it is called (dynamic) or defined (static)
        return self.generic_visit(node)

    # -- calls ----------------------------------------------------------------------

    def visit_Call(self, node):
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in self.rnd_names
        ):
            node.args = [self.visit(a) for a in node.args]
            node.keywords = [self.visit(k) for k in node.keywords]
            if not any(k.arg == "name" for k in node.keywords):
                node.keywords.append(ast.keyword(arg="name", value=self._address((func.attr, _site(node)))))
            return node
        if self.mode == "static" and isinstance(func, ast.Name) and func.id in self.nested:
            node.args = [self.visit(a) for a in node.args]
            node.keywords = [self.visit(k) for k in node.keywords]
            node.args.insert(0, self._address((func.id, _site(node))))
            return node
        return self.generic_visit(node)

    def visit_Name(self, node):
        if self.mode == "static" and isinstance(node.ctx, ast.Load) and node.id in self.nested:
            raise StaticNamingError(
                f"line {node.lineno}: the nested function {node.id!r} is used other than by "
                "calling it directly, which static naming cannot follow; use naming='dynamic'"
            )
        return node

    # -- loops ----------------------------------------------------------------------

    def visit_For(self, node):
        return self._loop(node, "for")

    def visit_While(self, node):
        return self._loop(node, "while")

    def visit_AsyncFor(self, node):
        raise StaticNamingError("async for is not supported in a generator")

    def _loop(self, node, kind):
        segment = (kind, _site(node))
        if isinstance(node, ast.For):
            node.iter = self.visit(node.iter)  # evaluated once, outside the loop's scope
            node.target = self.visit(node.target)
        else:
            node.test = self.visit(node.test)
        node.body = self._statements(node.body)
        node.orelse = self._statements(node.orelse)

        if self.mode == "dynamic":
            var = self._var("loop")
            node.body.insert(0, ast.Expr(_call(ast.Attribute(value=_name(var), attr="next", ctx=ast.Load()))))
            return ast.With(
                items=[ast.withitem(context_expr=_call("_pto_loop", ast.Constant(segment)),
                                    optional_vars=_name(var, True))],
                body=[node],
            )

        save, count = self._var("save"), self._var("i")
        if isinstance(node, ast.For):
            node.target = ast.Tuple(elts=[_name(count, True), node.target], ctx=ast.Store())
            node.iter = _call("enumerate", node.iter)
            start = []
        else:
            start = [ast.Assign(targets=[_name(count, True)], value=ast.Constant(-1))]
            node.body.insert(0, ast.AugAssign(target=_name(count, True), op=ast.Add(), value=ast.Constant(1)))
        # _pto_prefix = save + ((kind, site, i),) at the start of each iteration
        where = 1 if isinstance(node, ast.While) else 0
        node.body.insert(where, ast.Assign(
            targets=[_name("_pto_prefix", True)],
            value=ast.BinOp(left=_name(save), op=ast.Add(), right=ast.Tuple(elts=[ast.Tuple(
                elts=[ast.Constant(kind), ast.Constant(segment[1]), _name(count)], ctx=ast.Load())],
                ctx=ast.Load())),
        ))
        return [
            ast.Assign(targets=[_name(save, True)], value=_name("_pto_prefix")),
            *start,
            ast.Try(body=[node], handlers=[], orelse=[],
                    finalbody=[ast.Assign(targets=[_name("_pto_prefix", True)], value=_name(save))]),
        ]

    # -- comprehensions ----------------------------------------------------------

    def _comprehension(self, node, parts):
        pushed = 0
        for gen in node.generators:
            gen.iter = self.visit(gen.iter)  # before this generator's own scope
            segment = ("comp", _site(gen.iter))
            if self.mode == "dynamic":
                gen.iter = _call("_pto_iter", ast.Constant(segment), gen.iter)
                gen.target = self.visit(gen.target)
            else:
                var = self._var("c")
                gen.target = ast.Tuple(elts=[_name(var, True), self.visit(gen.target)], ctx=ast.Store())
                gen.iter = _call("enumerate", gen.iter)
                self.comp.append((segment[1], var))
                pushed += 1
            gen.ifs = [self.visit(i) for i in gen.ifs]
        for part in parts:
            setattr(node, part, self.visit(getattr(node, part)))
        del self.comp[len(self.comp) - pushed:]
        return node

    def visit_ListComp(self, node):
        return self._comprehension(node, ["elt"])

    visit_SetComp = visit_GeneratorExp = visit_ListComp

    def visit_DictComp(self, node):
        return self._comprehension(node, ["key", "value"])


# ---------------------------------------------------------------------------
# Rewriting a generator
# ---------------------------------------------------------------------------


def rewrite(generator, mode):
    """generator rewritten by ScopeTransformer ('dynamic' or 'static'), in its
    own environment."""
    try:
        source = textwrap.dedent(inspect.getsource(generator))
    except (OSError, TypeError) as e:
        raise ValueError(
            f"structured naming needs the source of {generator!r} (a def in a .py file or "
            "notebook cell); use naming='linear' otherwise"
        ) from e
    tree = ast.parse(source)
    if inspect.ismethod(generator) or not (len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef)):
        raise ValueError(f"the generator must be a function defined with def, not {generator!r}")
    env, names = environment(generator)
    tree = ast.fix_missing_locations(ScopeTransformer(mode, names).visit(tree))

    filename = f"{FILENAME_PREFIX}{mode} {generator.__qualname__}>"
    lines = source.splitlines(keepends=True)
    linecache.cache[filename] = (len(source), None, lines, filename)  # for tracebacks
    if mode == "dynamic":
        env.update(_pto_addr=_pto_addr, _pto_fn=_pto_fn, _pto_loop=_pto_loop, _pto_iter=_pto_iter)
    exec(compile(tree, filename, "exec"), env)
    new = env[tree.body[0].name]
    functools.update_wrapper(new, generator)
    new._pto_source = ast.unparse(tree)
    return new


# ---------------------------------------------------------------------------
# Dynamic naming at run time: the current scope is the namer's prefix
# ---------------------------------------------------------------------------


if sys.version_info >= (3, 11):
    _positions = {}

    def call_site(frame):
        """(line, column) of the call being made in frame."""
        key = (frame.f_code, frame.f_lasti)
        site = _positions.get(key)
        if site is None:
            pos = next(itertools.islice(frame.f_code.co_positions(), frame.f_lasti // 2, None))
            site = _positions[key] = (pos[0], pos[2])
        return site

else:  # no column information: use the bytecode offset

    def call_site(frame):
        return (frame.f_lineno, frame.f_lasti)


def _pto_addr(segment):
    p = current_play()
    return None if p is None else p.namer.prefix + (segment,)


def _pto_fn(func):
    """Decorator of the generator's nested functions: a call is a scope."""
    name = func.__name__

    @functools.wraps(func)
    def scoped(*args, **kwargs):
        p = current_play()
        if p is None:
            return func(*args, **kwargs)
        namer = p.namer
        saved = namer.prefix
        namer.prefix = saved + ((name, call_site(sys._getframe(1))),)
        try:
            return func(*args, **kwargs)
        finally:
            namer.prefix = saved

    return scoped


class _pto_loop:
    """Context of a for or while loop: each iteration is a scope."""

    __slots__ = ("segment", "namer", "saved", "i")

    def __init__(self, segment):
        p = current_play()
        self.segment = segment
        self.namer = None if p is None else p.namer
        self.i = 0

    def __enter__(self):
        if self.namer is not None:
            self.saved = self.namer.prefix
        return self

    def next(self):
        if self.namer is not None:
            self.namer.prefix = self.saved + (self.segment + (self.i,),)
            self.i += 1

    def __exit__(self, *exc):
        if self.namer is not None:
            self.namer.prefix = self.saved
        return False


def _pto_iter(segment, iterable):
    """The iterable of a comprehension: each item is a scope."""
    p = current_play()
    if p is None:
        yield from iterable
        return
    namer = p.namer
    saved = namer.prefix
    try:
        for i, x in enumerate(iterable):
            namer.prefix = saved + (segment + (i,),)
            yield x
    finally:
        namer.prefix = saved
