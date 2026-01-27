

# first all of our functions, and then put some of them in a macro_env




# booleans

# Identity function
IDENTITY = ('abs', 'x1', ('var', 'x1'))
IF = IDENTITY  # same as identity

TRUE = ('abs', 'x1', ('abs', 'x2', ('var', 'x1')))
FALSE = ('abs', 'x1', ('abs', 'x2', ('var', 'x2')))
AND = ('abs', 
       'x1',
       ('abs', 
        'x2',
        ('app',
          ('app', 
           ('var', 'x1'), 
           ('var', 'x2')
           ),
           'FALSE')))
OR = ('abs', 'x1',
    ('abs', 'x2',
    ('app',
    ('app', ('var', 'x1'), 'TRUE'),
    ('var', 'x2'))))
NOT = ('abs', 
       'x1',
       ('app',
        ('app', 
         ('var', 'x1'), 
         'FALSE'),
        'TRUE'))

XOR = ('abs', 'x1',
    ('abs', 'x2',
    ('app',
        ('app', ('var', 'x1'),
        ('app',
        ('app', ('var', 'x2'), 'FALSE'),
        'TRUE')),
        ('app',
        ('app', ('var', 'x2'), 'TRUE'),
        'FALSE'))))
XNOR = ('abs', 'x1',
    ('abs', 'x2',
        ('app', 'NOT',
        ('app',
        ('app', 'XOR', ('var', 'x1')),
        ('var', 'x2')))))




# ----- Church Numerals -----

# ZERO = λf.λx.x
ZERO = ('abs', 'g', ('abs', 'y', ('var', 'y')))

# ONE = λf.λx.f x
ONE = ('abs', 'g', ('abs', 'y', ('app', ('var', 'g'), ('var', 'y'))))

# TWO = λf.λx.f (f x)
TWO = ('abs', 'g', ('abs', 'y', ('app', ('var', 'g'), ('app', ('var', 'g'), ('var', 'y')))))

# THREE = λf.λx.f (f (f x))
THREE = ('abs', 'g', ('abs', 'y',  ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('var', 'y'))))))

FOUR = ('abs', 'g', ('abs', 'y',   ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('var', 'y')))))))

FIVE = ('abs', 'g', ('abs', 'y',   ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('var', 'y'))))))))

SIX  = ('abs', 'g', ('abs', 'y',   ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('var', 'y')))))))))

SEVEN  = ('abs', 'g', ('abs', 'y', ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('var', 'y'))))))))))

EIGHT  = ('abs', 'g', ('abs', 'y', ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('var', 'y')))))))))))

NINE  = ('abs', 'g', ('abs', 'y', ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('app', ('var', 'g'), ('var', 'y'))))))))))))


# ----- Arithmetic with Church Numerals -----

# SUCC = λn.λf.λx.f (n f x)
SUCC = ('abs', 'n', ('abs', 'f', ('abs', 'x', ('app', ('var', 'f'), ('app', ('app', ('var', 'n'), ('var', 'f')), ('var', 'x'))))))

# PLUS = λm.λn.λf.λx.m f (n f x)
PLUS = ('abs', 'm', ('abs', 'n', ('abs', 'f', ('abs', 'x', ('app', ('app', ('var', 'm'), ('var', 'f')), ('app', ('app', ('var', 'n'), ('var', 'f')), ('var', 'x')))))))

# MULT = λm.λn.λf.m (n f)
MULT = ('abs', 'm', ('abs', 'n', ('abs', 'f', ('app', ('var', 'm'), ('app', ('var', 'n'), ('var', 'f'))))))

# POW = λb.λe.e b
POW = ('abs', 'b', ('abs', 'e', ('app', ('var', 'e'), ('var', 'b'))))

# PRED (Predecessor - complex, often omitted in basic examples, corrected)
PRED = ('abs', 'n',
        ('abs', 'f',
         ('abs', 'x',
          ('app',
           ('app', ('app', ('var', 'n'),
                    ('abs', 'g',
                     ('abs', 'h',
                      ('app', ('var', 'h'),
                       ('app', ('var', 'g'), ('var', 'f')))))),
                    ('abs', 'u', ('var', 'x'))),
           ('abs', 'u', ('var', 'u'))))))

# IS_ZERO (Checks if a Church numeral is zero)
IS_ZERO = ('abs', 'n', ('app', ('app', ('var', 'n'), ('abs', 'x', 'FALSE')), 'TRUE'))

# ----- Combinators -----



I = ('abs', 'x', ('var', 'x'))
K = ('abs', 'x', ('abs', 'y', ('var', 'x')))
S = ('abs', 'x', ('abs', 'y', ('abs', 'z',
      ('app', ('app', ('var', 'x'), ('var', 'z')),
             ('app', ('var', 'y'), ('var', 'z'))))))
Y = ('abs', 'f',
      ('app',
       ('abs', 'x', ('app', ('var', 'f'), ('app', ('var', 'x'), ('var', 'x')))),
       ('abs', 'x', ('app', ('var', 'f'), ('app', ('var', 'x'), ('var', 'x'))))))




# lists

NIL = ('abs', 'f',
        ('abs', 'z',
        ('var', 'z')))
CONS = ('abs', 'h',
        ('abs', 't',
            ('abs', 'f',
            ('abs', 'z',
                ('app',
                ('app', ('var', 'f'), ('var', 'h')),
                ('app',
                    ('app', ('var', 't'), ('var', 'f')),
                    ('var', 'z')))))))


# recursive functions

FOLD = ('abs', 'f',
        ('abs', 'z',
            ('abs', 'l',
            ('app',
                ('app', ('var', 'l'), ('var', 'f')),
                ('var', 'z')))))
ALL = ('abs', 'l',
            ('app',
            ('app',
                ('app', 'FOLD', 'AND'),
                'TRUE'),
            ('var', 'l')))



# Factorial (Illustrative, requires PRED and IS_ZERO)
FACTORIAL_BASE = ('abs', 'f',
                   ('abs', 'n',
                    ('app',
                     ('app', 'IF',
                      ('app', 'IS_ZERO', ('var', 'n'))),
                     'ONE',
                     ('app', 'MULT',
                      ('var', 'n'),
                      ('app', ('var', 'f'),
                       ('app', 'PRED', ('var', 'n')))))))
FACTORIAL = ('app', Y, FACTORIAL_BASE)

# ----- Pairs and Projections -----
PAIR = ('abs', 'x', ('abs', 'y', ('abs', 'f', ('app', ('app', ('var', 'f'), ('var', 'x')), ('var', 'y')))))
FIRST = ('abs', 'p', ('app', ('var', 'p'), ('abs', 'x', ('abs', 'y', ('var', 'x')))))
SECOND = ('abs', 'p', ('app', ('var', 'p'), ('abs', 'x', ('abs', 'y', ('var', 'y')))))

# ----- List Operations -----

# LIST = CONS(TRUE)(TRUE)
# This creates an empty list where the first element (flag) is TRUE
LIST = ('app', 
        ('app', 'CONS', 'TRUE'), 
        'TRUE')

# PREPEND = lambda xs: lambda x: CONS(FALSE)(CONS(x)(xs))
PREPEND = ('abs', 'xs',
           ('abs', 'x',
            ('app',
             ('app', 'CONS', 'FALSE'),
             ('app',
              ('app', 'CONS', ('var', 'x')),
              ('var', 'xs')))))

# EMPTY = lambda xs: CAR(xs)
# CAR extracts the first element of a pair, which is FIRST in our implementation
EMPTY = ('abs', 'xs',
         ('app', 'FIRST', ('var', 'xs')))

# HEAD = lambda xs: CAR(CDR(xs))
HEAD = ('abs', 'xs',
        ('app', 'FIRST', 
         ('app', 'SECOND', ('var', 'xs'))))

# TAIL = lambda xs: CDR(CDR(xs))
TAIL = ('abs', 'xs',
        ('app', 'SECOND', 
         ('app', 'SECOND', ('var', 'xs'))))

# APPEND = Y(
#     lambda f: lambda xs: lambda x: EMPTY(xs)
#     (lambda _: PREPEND(xs)(x))
#     (lambda _: CONS(FALSE)(CONS(HEAD(xs))(f(TAIL(xs))(x))))
#     (TRUE)
# )
APPEND_BASE = ('abs', 'f',
              ('abs', 'xs',
               ('abs', 'x',
                ('app',
                 ('app',
                  ('app', ('var', 'xs'), ('var', 'xs')),
                  ('abs', '_',
                   ('app',
                    ('app', 'PREPEND', ('var', 'xs')),
                    ('var', 'x')))),
                 ('abs', '_',
                  ('app',
                   ('app', 'CONS', 'FALSE'),
                   ('app',
                    ('app', 'CONS', ('app', 'HEAD', ('var', 'xs'))),
                    ('app',
                     ('app', ('var', 'f'), ('app', 'TAIL', ('var', 'xs'))),
                     ('var', 'x')))))))))

APPEND = ('app', Y, APPEND_BASE)

# REVERSE = Y(
#     lambda f: lambda xs: EMPTY(xs)
#     (lambda _: LIST)
#     (lambda _: APPEND(f(TAIL(xs)))(HEAD(xs)))
#     (TRUE)
# )
REVERSE_BASE = ('abs', 'f',
               ('abs', 'xs',
                ('app',
                 ('app',
                  ('app', 'EMPTY', ('var', 'xs')),
                  ('abs', '_', 'LIST')),
                 ('abs', '_',
                  ('app',
                   ('app', 'APPEND', ('app', ('var', 'f'), ('app', 'TAIL', ('var', 'xs')))),
                   ('app', 'HEAD', ('var', 'xs')))))))

REVERSE = ('app', Y, REVERSE_BASE)

# MAP = Y(
#     lambda f: lambda a: lambda xs: EMPTY(xs)
#     (lambda _: LIST)
#     (lambda _: PREPEND(f(a)(TAIL(xs)))(a(HEAD(xs))))
#     (TRUE)
# )
MAP_BASE = ('abs', 'f',
           ('abs', 'a',
            ('abs', 'xs',
             ('app',
              ('app',
               ('app', 'EMPTY', ('var', 'xs')),
               ('abs', '_', 'LIST')),
              ('abs', '_',
               ('app',
                ('app', 'PREPEND', 
                 ('app',
                  ('app', ('var', 'f'), ('var', 'a')), 
                  ('app', 'TAIL', ('var', 'xs')))),
                ('app', ('var', 'a'), ('app', 'HEAD', ('var', 'xs')))))))))

MAP = ('app', Y, MAP_BASE)

# RANGE = Y(
#     lambda f: lambda a: lambda b: GTE(a)(b)
#     (lambda _: LIST)
#     (lambda _: PREPEND(f(INC(a))(b))(a))
#     (TRUE)
# )
RANGE_BASE = ('abs', 'f',
             ('abs', 'a',
              ('abs', 'b',
               ('app',
                ('app',
                 ('app', 
                  ('app', ('var', 'a'), ('var', 'b')),  # Note: replacing GTE with direct comparison
                  ('abs', '_', 'LIST')),
                 ('abs', '_',
                  ('app',
                   ('app', 'PREPEND',
                    ('app',
                     ('app', ('var', 'f'), ('app', 'SUCC', ('var', 'a'))),
                     ('var', 'b'))),
                   ('var', 'a')))),
                'TRUE'))))

RANGE = ('app', Y, RANGE_BASE)

# REDUCE = FOLD = Y(
#     lambda f: lambda r: lambda l: lambda v: EMPTY(l)
#     (lambda _: v)
#     (lambda _: f(r)(TAIL(l))(r(HEAD(l))(v)))
#     (TRUE)
# )
REDUCE_BASE = ('abs', 'f',
              ('abs', 'r',
               ('abs', 'l',
                ('abs', 'v',
                 ('app',
                  ('app',
                   ('app', 'EMPTY', ('var', 'l')),
                   ('abs', '_', ('var', 'v'))),
                  ('abs', '_',
                   ('app',
                    ('app',
                     ('app', ('var', 'f'), ('var', 'r')),
                     ('app', 'TAIL', ('var', 'l'))),
                    ('app',
                     ('app', ('var', 'r'), ('app', 'HEAD', ('var', 'l'))),
                     ('var', 'v')))))))))

REDUCE = ('app', Y, REDUCE_BASE)

# FILTER = lambda f: lambda l: (
#     REDUCE
#     (lambda x: lambda xs: f(x)(APPEND(xs)(x))(xs))
#     (l)
#     (LIST)
# )
FILTER = ('abs', 'f',
          ('abs', 'l',
           ('app',
            ('app',
             ('app', 'REDUCE',
              ('abs', 'x',
               ('abs', 'xs',
                ('app',
                 ('app',
                  ('app', ('var', 'f'), ('var', 'x')),
                  ('app', 
                   ('app', 'APPEND', ('var', 'xs')),
                   ('var', 'x'))),
                 ('var', 'xs'))))),
             ('var', 'l')),
            'LIST')))

# DROP = lambda n: lambda l: n(TAIL)(l)
DROP = ('abs', 'n',
        ('abs', 'l',
         ('app',
          ('app', ('var', 'n'), 'TAIL'),
          ('var', 'l'))))

# TAKE = Y(lambda f: lambda n: lambda l: (
#     OR(EMPTY(l))(ISZERO(n))
#     (lambda _: LIST)
#     (lambda _: (
#         PREPEND(f(DEC(n))(TAIL(l)))
#         (HEAD(l))
#     ))
#     (TRUE)
# ))
TAKE_BASE = ('abs', 'f',
            ('abs', 'n',
             ('abs', 'l',
              ('app',
               ('app',
                ('app',
                 ('app', 'OR',
                  ('app', 'EMPTY', ('var', 'l'))),
                 ('app', 'IS_ZERO', ('var', 'n'))),
                ('abs', '_', 'LIST')),
               ('abs', '_',
                ('app',
                 ('app', 'PREPEND',
                  ('app',
                   ('app', ('var', 'f'), ('app', 'PRED', ('var', 'n'))),
                   ('app', 'TAIL', ('var', 'l')))),
                 ('app', 'HEAD', ('var', 'l'))))))))

TAKE = ('app', Y, TAKE_BASE)

# LENGTH

# original version - recursion error
# LENGTH =    ('abs', 'l',
#               ('app',
#                 ('app',
#                   ('app', 'FOLD',
#                     ('abs', 'x',
#                       ('abs', 'n',
#                         ('app', 'SUCC', ('var', 'n'))))),
#                   'ZERO'),
#                 ('var', 'l')))


# # second version - Y combinator - recursion error
# LENGTH_BASE = ('abs', 'f',
#                ('abs', 'xs',
#                 ('app',
#                  ('app',
#                   ('app', 'EMPTY', ('var', 'xs')),
#                   ('abs', '_', 'ZERO')),
#                  ('abs', '_',
#                   ('app', 'SUCC',
#                    ('app', ('var', 'f'), ('app', 'TAIL', ('var', 'xs'))))))))
# LENGTH = ('app', Y, LENGTH_BASE)


# third version - no Y combinator - recursion error
# LENGTH = ('abs', 'l',
#           ('app',
#            ('app',
#             ('app', 'REDUCE',
#              ('abs', '_',
#               ('abs', 'acc',
#                ('app', 'SUCC', ('var', 'acc'))))),
#             ('var', 'l')),
#            'ZERO'))


# fourth version - no Y combinator - works
LENGTH =    ('app',
              ('app', 'FOLD',
                ('abs', '_',
                  ('abs', 'acc',
                    ('app', 'SUCC', ('var', 'acc'))))),
              'ZERO')



# INDEX = Y(lambda f: lambda n: lambda l: (
#     ISZERO(n)
#     (lambda _: HEAD(l))
#     (lambda _: f(DEC(n))(TAIL(l)))
#     (TRUE)
# ))
INDEX_BASE = ('abs', 'f',
             ('abs', 'n',
              ('abs', 'l',
               ('app',
                ('app',
                 ('app', 'IS_ZERO', ('var', 'n')),
                 ('abs', '_', ('app', 'HEAD', ('var', 'l')))),
                ('abs', '_',
                 ('app',
                  ('app', ('var', 'f'), ('app', 'PRED', ('var', 'n'))),
                  ('app', 'TAIL', ('var', 'l'))))))))

INDEX = ('app', Y, INDEX_BASE)

# ANY = Y(lambda f: lambda l: (
#     EMPTY(l)
#     (lambda _: FALSE)
#     (lambda _: HEAD(l)(TRUE)(f(TAIL(l))))
#     (TRUE)
# ))
ANY_BASE = ('abs', 'f',
           ('abs', 'l',
            ('app',
             ('app',
              ('app', 'EMPTY', ('var', 'l')),
              ('abs', '_', 'FALSE')),
             ('abs', '_',
              ('app',
               ('app',
                ('app', ('app', 'HEAD', ('var', 'l')), 'TRUE'),
                ('app', ('var', 'f'), ('app', 'TAIL', ('var', 'l')))),
               'TRUE')))))

ANY = ('app', Y, ANY_BASE)


LAST_BASE = ('abs', 'f',
             ('abs', 'xs',
              ('app',
               ('app',
                ('app', 'EMPTY', ('var', 'xs')),
                ('abs', '_', 'NIL')),
               ('abs', '_',
                ('app',
                 ('app',
                  ('app', 'EMPTY', ('app', 'TAIL', ('var', 'xs'))),
                  ('abs', '_', ('app', 'HEAD', ('var', 'xs')))),
                 ('abs', '_',
                  ('app', ('var', 'f'), ('app', 'TAIL', ('var', 'xs')))))))))
LAST = ('app', Y, LAST_BASE)

# ALL = Y(lambda f: lambda l: (
#     EMPTY(l)
#     (lambda _: TRUE)
#     (lambda _: NOT(HEAD(l))(FALSE)(f(TAIL(l))))
#     (TRUE)
# ))
ALL_Y_BASE = ('abs', 'f',
           ('abs', 'l',
            ('app',
             ('app',
              ('app', 'EMPTY', ('var', 'l')),
              ('abs', '_', 'TRUE')),
             ('abs', '_',
              ('app',
               ('app',
                ('app', ('app', 'NOT', ('app', 'HEAD', ('var', 'l'))), 'FALSE'),
                ('app', ('var', 'f'), ('app', 'TAIL', ('var', 'l')))),
               'TRUE')))))

ALL_Y = ('app', Y, ALL_Y_BASE)

macro_env = {

    'IDENTITY': IDENTITY,
    'IF': IF,
    'NOT': NOT,
    'AND': AND,
    'OR': OR,
    'XOR': XOR,
    'XNOR': XNOR,
    'TRUE': TRUE,
    'FALSE': FALSE,

    'SUCC': SUCC,
    'ZERO': ZERO,
    'ONE': ONE,
    'TWO': TWO,
    'THREE': THREE,
    'FOUR': FOUR,
    'FIVE': FIVE,
    'SIX': SIX,
    'SEVEN': SEVEN,
    'EIGHT': EIGHT,
    'NINE': NINE,
    'PLUS': PLUS,
    'MULT': MULT,
    'IS_ZERO': IS_ZERO,

    'NIL': NIL,
    'CONS': CONS,
    # 'LIST': LIST,
    'FOLD': FOLD,
    'ALL': ALL,

    'I': I,
    'K': K,
    'S': S,
    'Y': Y

}

def make_macro_env(macro_env, macros):
    return {macro: macro_env[macro] for macro in macros}


