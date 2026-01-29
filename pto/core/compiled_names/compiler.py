"""
Name-Compiling Generator Transformer for PTO.

Transforms a PTO generator that uses rnd.X() calls into one where
each rnd.X() call has a name= keyword argument filled in at compile
time with a structured name derived from the AST.

The compiled generator works with the existing PTO layers (fine
distributions, tracer, rnd proxy) — it just replaces the automatic
names layer (runtime stack + inspect) with static name injection.

Usage:
    from pto.core.compiler import compile_generator

    def generator():
        return [rnd.choice([0, 1]) for i in range(10)]

    compiled = compile_generator(generator)

    # Use with PTO as normal — rnd and tracer handle tracing/replay
    from pto import run
    result = run(compiled, sum, better=max)
"""

import ast
import inspect
import functools
import textwrap


# ---------------------------------------------------------------------------
# AST Transformer
# ---------------------------------------------------------------------------

class NameCompiler(ast.NodeTransformer):
    """
    Rewrites a PTO generator so that every rnd.X() call gets a
    name= keyword argument with a structured name computed from
    the source location.

    Transformation rules:

    1. rnd.X(args) → rnd.X(args, name=<name_expr>)

    2. for loops: inject enumerate + prefix save/restore so that
       loop iterations get distinct name prefixes.

    3. while loops: inject counter + prefix save/restore.

    4. comprehensions: inject enumerate, track counters for name
       expressions.

    5. nested functions: thread __prefix__ parameter through calls.

    6. top-level function: inject __prefix__ = "root/..." preamble.
    """

    def __init__(self):
        self.func_depth = 0
        self.nested_func_names = set()
        self.comp_segments = []

    # -- Name helpers -------------------------------------------------------

    def _counter_var(self, node):
        return f"__c_L{node.lineno}_{node.col_offset}__"

    def _save_var(self, node):
        return f"__ps_L{node.lineno}_{node.col_offset}__"

    def _make_name_expr(self, label, node):
        """
        Build AST expression: __prefix__ + <comp segments> + "/<label>@<line>.<col>"
        """
        expr = ast.Name(id="__prefix__", ctx=ast.Load())

        for slabel, sline, scol, svar in self.comp_segments:
            expr = ast.BinOp(
                left=expr,
                op=ast.Add(),
                right=ast.Constant(value=f"/{slabel}@{sline}.{scol}:"),
            )
            expr = ast.BinOp(
                left=expr,
                op=ast.Add(),
                right=ast.Call(
                    func=ast.Name(id="str", ctx=ast.Load()),
                    args=[ast.Name(id=svar, ctx=ast.Load())],
                    keywords=[],
                ),
            )

        expr = ast.BinOp(
            left=expr,
            op=ast.Add(),
            right=ast.Constant(value=f"/{label}@{node.lineno}.{node.col_offset}"),
        )
        return expr

    # -- Helpers for prefix save/restore ------------------------------------

    def _make_prefix_update(self, save_var, label, node, counter_var):
        return ast.Assign(
            targets=[ast.Name(id="__prefix__", ctx=ast.Store())],
            value=ast.BinOp(
                left=ast.BinOp(
                    left=ast.Name(id=save_var, ctx=ast.Load()),
                    op=ast.Add(),
                    right=ast.Constant(
                        value=f"/{label}@{node.lineno}.{node.col_offset}:"
                    ),
                ),
                op=ast.Add(),
                right=ast.Call(
                    func=ast.Name(id="str", ctx=ast.Load()),
                    args=[ast.Name(id=counter_var, ctx=ast.Load())],
                    keywords=[],
                ),
            ),
        )

    def _make_save(self, save_var):
        return ast.Assign(
            targets=[ast.Name(id=save_var, ctx=ast.Store())],
            value=ast.Name(id="__prefix__", ctx=ast.Load()),
        )

    def _make_restore(self, save_var):
        return ast.Assign(
            targets=[ast.Name(id="__prefix__", ctx=ast.Store())],
            value=ast.Name(id=save_var, ctx=ast.Load()),
        )

    # -- Collect nested function names --------------------------------------

    def _collect_nested_funcs(self, func_node):
        for stmt in func_node.body:
            if isinstance(stmt, ast.FunctionDef):
                self.nested_func_names.add(stmt.name)

    # -- Visitors -----------------------------------------------------------

    def visit_FunctionDef(self, node):
        self.func_depth += 1

        if self.func_depth == 1:
            # Top-level generator: inject __prefix__ preamble
            self._collect_nested_funcs(node)
            self.generic_visit(node)

            prefix_val = f"root/{node.name}@{node.lineno}.{node.col_offset}"
            preamble = [
                ast.Assign(
                    targets=[ast.Name(id="__prefix__", ctx=ast.Store())],
                    value=ast.Constant(value=prefix_val),
                ),
            ]
            node.body = preamble + node.body

        else:
            # Nested function: add __prefix__ as first parameter
            node.args.args = [
                ast.arg(arg="__prefix__"),
            ] + node.args.args

            saved = self.nested_func_names.copy()
            self._collect_nested_funcs(node)
            self.generic_visit(node)
            self.nested_func_names = saved

        self.func_depth -= 1
        return node

    def visit_For(self, node):
        counter = self._counter_var(node)
        save = self._save_var(node)

        node.target = ast.Tuple(
            elts=[ast.Name(id=counter, ctx=ast.Store()), node.target],
            ctx=ast.Store(),
        )
        node.iter = ast.Call(
            func=ast.Name(id="enumerate", ctx=ast.Load()),
            args=[node.iter],
            keywords=[],
        )

        self.generic_visit(node)

        prefix_update = self._make_prefix_update(save, "for", node, counter)
        node.body = [prefix_update] + node.body

        return [self._make_save(save), node, self._make_restore(save)]

    def visit_While(self, node):
        counter = self._counter_var(node)
        save = self._save_var(node)

        self.generic_visit(node)

        prefix_update = self._make_prefix_update(save, "while", node, counter)
        counter_inc = ast.AugAssign(
            target=ast.Name(id=counter, ctx=ast.Store()),
            op=ast.Add(),
            value=ast.Constant(value=1),
        )
        node.body = [prefix_update] + node.body + [counter_inc]

        counter_init = ast.Assign(
            targets=[ast.Name(id=counter, ctx=ast.Store())],
            value=ast.Constant(value=0),
        )
        return [
            self._make_save(save),
            counter_init,
            node,
            self._make_restore(save),
        ]

    def _visit_comp(self, node):
        for gen in node.generators:
            loc = gen.iter
            counter = self._counter_var(loc)

            self.comp_segments.append(
                ("comp", loc.lineno, loc.col_offset, counter)
            )

            gen.target = ast.Tuple(
                elts=[ast.Name(id=counter, ctx=ast.Store()), gen.target],
                ctx=ast.Store(),
            )
            gen.iter = ast.Call(
                func=ast.Name(id="enumerate", ctx=ast.Load()),
                args=[gen.iter],
                keywords=[],
            )

        self.generic_visit(node)

        for _ in node.generators:
            self.comp_segments.pop()

        return node

    visit_ListComp = _visit_comp
    visit_SetComp = _visit_comp
    visit_GeneratorExp = _visit_comp
    visit_DictComp = _visit_comp

    def visit_Call(self, node):
        self.generic_visit(node)

        # rnd.X(args) → rnd.X(args, name=<name_expr>)
        if (isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "rnd"):

            method = node.func.attr
            name_expr = self._make_name_expr(method, node)

            # Add name= keyword argument
            node.keywords.append(
                ast.keyword(arg="name", value=name_expr)
            )
            return node

        # nested_func(args) → nested_func(__prefix__ + "/func@line.col", args)
        if (isinstance(node.func, ast.Name)
                and node.func.id in self.nested_func_names):
            prefix_expr = self._make_name_expr(node.func.id, node)
            node.args = [prefix_expr] + node.args
            return node

        return node


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compile_generator(func):
    """
    Compile a PTO generator by injecting name= into every rnd.X() call.

    The compiled generator works with the existing PTO rnd proxy and
    tracer — it replaces the automatic names layer with static names
    derived from the AST.

    Returns a function with the same signature as the original generator.

    Diagnostic attributes on the returned function:
        _original_source: the original source code
        _compiled_source: the transformed source code (via ast.unparse)
    """
    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source)

    transformer = NameCompiler()
    tree = transformer.visit(tree)
    tree = ast.fix_missing_locations(tree)

    env = func.__globals__.copy()

    exec(compile(tree, "<compiled>", "exec"), env)
    new_func = env[func.__name__]
    functools.update_wrapper(new_func, func)
    new_func._original_source = source
    new_func._compiled_source = ast.unparse(tree)
    return new_func
