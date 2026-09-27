"""Example problems for PTO, one module per problem, eg

    from pto.problems.onemax import generator, fitness

Run one as a script with `python -m pto.problems.onemax`. as_classes wraps
the problems as classes for experiments (it needs numpy).

The modules are not imported here: importing them eagerly made every
`python -m pto.problems.<name>` warn that the module was already imported,
and made every problem require numpy (via as_classes).
"""
