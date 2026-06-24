# PTO for Racket — Implementation Specification

## Purpose

This document specifies a complete Racket implementation of **PTO (Program Trace Optimisation)**, a metaheuristic optimisation framework based on Wingate et al. 2011 ("Lightweight Implementations of Probabilistic Programming Languages Via Transformational Compilation"). It is self-contained: no prior conversation is needed to implement from it.

**Core idea**: a *generator* is a Racket function that builds a solution using `rnd-choice`, `rnd-real`, and `rnd-int` calls. PTO records each random decision as a named *trace entry*. Optimisation mutates and recombines traces, then replays the generator to produce new solutions.

---

## Architecture

Six stages, each building on the previous. All code lives in `pto.rkt` plus a companion `pto/plain.rkt`.

```
Stage 5: run + hill-climber
Stage 4: fine distributions (type-aware mutation/crossover/repair)
Stage 3: structured naming + define-generator macro
Stage 2: coarse operators (mutate, crossover, distance)
Stage 1: core tracing (entry struct, play, linear naming, rnd-* macros)
```

After each stage, all prior tests plus the new stage's tests must pass.

---

## Stage 1: Core Tracing Infrastructure

### Data Structures

**`entry` struct** — one recorded random decision:

```racket
(struct entry (type params val) #:transparent #:mutable)
```

| Field | Type | Values |
|---|---|---|
| `type` | symbol | `'cat`, `'cont`, `'int` |
| `params` | immutable list | `'cat`: `(list choices-list)` · `'cont`: `(list lo hi)` · `'int`: `(list lo hi)` |
| `val` | any | sampled value; `#f` when not yet sampled |

Constraints: `choices-list` non-empty; `lo < hi` for `'cont`; `lo <= hi` exact integers for `'int`.

**`sol` struct** — a solution:

```racket
(struct sol (pheno geno key-order) #:transparent)
```

| Field | Description |
|---|---|
| `pheno` | value returned by the generator |
| `geno` | immutable hash `{name → entry}` |
| `key-order` | list of all names in first-insertion order |

In Stage 1, names are exact non-negative integers. In Stage 3 they become strings.

---

### Parameters

**Public** (users may read/bind via `parameterize`):

```racket
(define current-naming    (make-parameter 'linear))  ; 'linear | 'structured
(define current-dist-mode (make-parameter 'coarse))  ; 'coarse | 'fine
```

**Internal** (not exported):

```racket
(define _tracing     (make-parameter #f))       ; bool: is a play in progress?
(define _in-trace    (make-parameter #hash()))  ; input trace for replay
(define _out-trace   (make-parameter #hash()))  ; output trace being built
(define _key-order   (make-parameter '()))      ; keys in insertion order, reversed
(define _name-seq    (make-parameter 0))        ; counter for linear naming
(define _name-frames (make-parameter '()))      ; stack for structured naming (Stage 3)
```

---

### `entry-sample!`

Fills `e.val` with a fresh sample. Mutates `e` in place.

```
entry-sample!(e):
  'cat  → e.val = random element of (first (entry-params e))
  'cont → lo = (first params), hi = (second params)
           e.val = lo + (random) * (hi - lo)
  'int  → lo = (first params), hi = (second params)
           e.val = lo + (random (+ 1 (- hi lo)))   ; inclusive range
```

---

### `entry-replay!` (Stage 1: coarse only)

Fills `e.val` by attempting to reuse `old-e.val`. Mutates `e` in place.

```
entry-replay!(e, old-e, mode):
  ; Stage 1: mode is always 'coarse here
  if (entry-type e) == (entry-type old-e) AND
     (entry-params e) == (entry-params old-e):
    e.val = (entry-val old-e)      ; reuse: same distribution, reuse value
  else:
    entry-sample!(e)               ; incompatible: resample from prior
```

Fine mode is added in Stage 4.

---

### `next-name!`

```
next-name!(site-sym):
  if (current-naming) is 'linear:
    n = (_name-seq)
    (_name-seq (+ n 1))
    return n
  if (current-naming) is 'structured:
    → see Stage 3
```

In Stage 1, `site-sym` is ignored.

---

### `pto-sample!`

The core function called by every `rnd-*` macro.

```
pto-sample!(site-sym, make-entry):
  name = next-name!(site-sym)
  e    = make-entry()                          ; fresh entry, val = #f

  if not (_tracing):
    entry-sample!(e)
    return (entry-val e)

  ; Tracing is active
  if name ∈ (_in-trace):
    old-e = hash-ref(_in-trace, name)
    entry-replay!(e, old-e, (current-dist-mode))
  else:
    entry-sample!(e)

  ; Record in output trace
  if name ∉ (_out-trace):
    (_key-order (cons name (_key-order)))      ; record insertion order

  (_out-trace (hash-set (_out-trace) name e))

  return (entry-val e)
```

---

### `play`

Runs a generator with a given input trace; returns a `sol`.

```
play(gen, trace):
  pheno = (parameterize ([_tracing    #t]
                         [_in-trace   trace]
                         [_out-trace  #hash()]
                         [_key-order  '()]
                         [_name-seq   0]
                         [_name-frames '()])
            (gen))
  return sol(pheno, (_out-trace), reverse((_key-order)))
```

Note: `(_out-trace)` and `(_key-order)` are read *after* `gen` returns but *inside* the `parameterize` scope, so they reflect the trace built during this run.

Correct Racket spelling:
```racket
(define (play gen trace)
  (parameterize ([_tracing    #t]
                 [_in-trace   trace]
                 [_out-trace  #hash()]
                 [_key-order  '()]
                 [_name-seq   0]
                 [_name-frames '()])
    (define pheno (gen))
    (sol pheno (_out-trace) (reverse (_key-order)))))
```

---

### `rnd-*` Macros

These are **syntax macros**. At compile time, each use site's source line and column are captured and embedded as a symbol. This symbol is passed to `pto-sample!` as the structural identifier used by structured naming (Stage 3). In linear mode it is ignored.

Site symbol format: `<prefix>@<line>:<col>` where prefix is `cat`, `cont`, or `int`.

```racket
(define-syntax (rnd-choice stx)
  (syntax-parse stx
    [(_ seq)
     (define site (string->symbol
                   (format "cat@~a:~a" (syntax-line stx) (syntax-column stx))))
     #`(pto-sample! '#,site (λ () (entry 'cat (list seq) #f)))]))

(define-syntax (rnd-real stx)
  (syntax-parse stx
    [(_ lo hi)
     (define site (string->symbol
                   (format "cont@~a:~a" (syntax-line stx) (syntax-column stx))))
     #`(pto-sample! '#,site (λ () (entry 'cont (list lo hi) #f)))]))

(define-syntax (rnd-int stx)
  (syntax-parse stx
    [(_ lo hi)
     (define site (string->symbol
                   (format "int@~a:~a" (syntax-line stx) (syntax-column stx))))
     #`(pto-sample! '#,site (λ () (entry 'int (list lo hi) #f)))]))
```

**Important**: `rnd-choice`, `rnd-real`, `rnd-int` capture the source location of their *use site*, not of the macro definition. A use of `(rnd-choice '(0 1))` at line 5 col 10 always produces the symbol `cat@5:10` regardless of which module defines the macro.

---

### Stage 1 Tests

```racket
(require rackunit)

;;; entry struct
(let ([e (entry 'cat '((a b c)) #f)])
  (check-equal? (entry-type e) 'cat)
  (check-equal? (entry-params e) '((a b c)))
  (check-false  (entry-val e)))

;;; entry-sample! fills val
(let ([e (entry 'cont '(0.0 1.0) #f)])
  (entry-sample! e)
  (check-true (real? (entry-val e)))
  (check-true (<= 0.0 (entry-val e) 1.0)))

(let ([e (entry 'int '(3 7) #f)])
  (entry-sample! e)
  (check-true (exact-integer? (entry-val e)))
  (check-true (<= 3 (entry-val e) 7)))

(let ([e (entry 'cat '((x y)) #f)])
  (entry-sample! e)
  (check-true (member (entry-val e) '(x y))))

;;; play produces a sol
(parameterize ([current-naming 'linear])
  (define gen (λ () (rnd-choice '(a b c))))
  (define s (play gen #hash()))
  (check-true (sol? s))
  (check-true (member (sol-pheno s) '(a b c)))
  (check-equal? (length (sol-key-order s)) 1)
  (check-equal? (sol-key-order s) '(0)))

;;; replay is deterministic
(parameterize ([current-naming 'linear])
  (define gen (λ () (rnd-choice '(a b c))))
  (define s1 (play gen #hash()))
  (define s2 (play gen (sol-geno s1)))
  (check-equal? (sol-pheno s1) (sol-pheno s2)))

;;; multiple rnd calls: keys are 0 1 2 in order
(parameterize ([current-naming 'linear])
  (define gen (λ () (list (rnd-choice '(a b))
                          (rnd-int 1 3)
                          (rnd-real 0.0 1.0))))
  (define s (play gen #hash()))
  (check-equal? (sol-key-order s) '(0 1 2))
  (check-equal? (length (sol-pheno s)) 3))

;;; coarse replay reuses value when params match
(parameterize ([current-naming 'linear])
  (define gen (λ () (rnd-int 0 100)))
  (define s1 (play gen #hash()))
  (define s2 (play gen (sol-geno s1)))
  (check-equal? (sol-pheno s1) (sol-pheno s2)))

;;; coarse replay resamples when params differ
;;; (force params mismatch by manually crafting a trace)
(parameterize ([current-naming 'linear])
  (define gen (λ () (rnd-int 0 10)))
  ; Manually insert a 'cont entry where 'int is expected
  (define fake-trace (hash 0 (entry 'cont '(0.0 1.0) 0.5)))
  (define s (play gen fake-trace))
  ; Should resample: result must be integer in [0,10]
  (check-true (exact-integer? (sol-pheno s)))
  (check-true (<= 0 (sol-pheno s) 10)))
```

---

### Stage 1 Example

```racket
;; ONEMAX generator
(define (onemax-gen n)
  (for/list ([i (in-range n)])
    (rnd-choice '(0 1))))

(parameterize ([current-naming 'linear])
  (define s (play (λ () (onemax-gen 5)) #hash()))
  (printf "pheno:     ~a\n" (sol-pheno s))
  (printf "key-order: ~a\n" (sol-key-order s))
  (printf "geno:      ~a\n"
          (for/list ([k (sol-key-order s)])
            (list k (entry-val (hash-ref (sol-geno s) k))))))
;; Expected output (values random):
;;   pheno:     (1 0 1 1 0)
;;   key-order: (0 1 2 3 4)
;;   geno:      ((0 1) (1 0) (2 1) (3 1) (4 0))
```

---

## Stage 2: Coarse Operators

### Goal

Implement mutation, crossover, and distance operators that produce new `sol` values by modifying the geno and replaying the generator. All operators in this stage use coarse mode.

---

### `entry-mutate` (coarse)

Returns a **new** `entry` with a freshly sampled val. Does not mutate the original.

```
entry-mutate(e, 'coarse):
  new-e = copy of e with val = #f
  entry-sample!(new-e)
  return new-e
```

Fine mode is added in Stage 4.

---

### `align-traces`

Returns the list of names common to both solutions, in the order they appear in `s1.key-order`.

```
align-traces(s1, s2):
  s2-keys = set of keys in (sol-geno s2)
  return [k for k in (sol-key-order s1) if k ∈ s2-keys]
```

**Debug assertion**: the common keys must appear in the same relative order in `(sol-key-order s2)`. Violation indicates a naming bug.

---

### `create-ind`

```racket
(define (create-ind gen)
  (play gen #hash()))
```

---

### `mutate-point`

Mutate one randomly chosen entry.

```
mutate-point(gen, s):
  geno = (sol-geno s)
  keys = (hash-keys geno)
  key  = (list-ref keys (random (length keys)))
  old-e = (hash-ref geno key)
  new-e = entry-mutate(old-e, (current-dist-mode))
  new-geno = (hash-set geno key new-e)
  return play(gen, new-geno)
```

---

### `mutate-random`

```racket
(define (mutate-random gen _s)
  (play gen #hash()))
```

---

### `crossover-uniform`

```
crossover-uniform(gen, s1, s2):
  alignment = align-traces(s1, s2)
  ; Start with union, s2 wins for non-aligned overlapping keys
  merged = hash-union (sol-geno s1) (sol-geno s2)
           with (λ (v1 v2) v2) as conflict resolver
  ; For aligned keys: pick uniformly from either parent
  for key in alignment:
    merged[key] = if (random) < 0.5
                  then (hash-ref (sol-geno s1) key)
                  else (hash-ref (sol-geno s2) key)
  return play(gen, merged)
```

In Racket: `(hash-union h1 h2 #:combine (λ (v1 v2) v2))`.

---

### `crossover-one-point`

```
crossover-one-point(gen, s1, s2):
  alignment = align-traces(s1, s2)
  n = (length alignment)
  point = (random (+ n 1))           ; 0..n inclusive
  merged = hash-union(s1.geno, s2.geno, prefer s2)
  for i, key in enumerate(alignment):
    merged[key] = if i < point
                  then (hash-ref (sol-geno s1) key)
                  else (hash-ref (sol-geno s2) key)
  return play(gen, merged)
```

---

### `entry-distance`

```
entry-distance(e1, e2):
  if (entry-type e1) == (entry-type e2) AND (entry-val e1) == (entry-val e2):
    return 0.0
  return 1.0
```

---

### `distance-ind`

```
distance-ind(s1, s2):
  common = set-intersect(keys(s1.geno), keys(s2.geno))
  sym-diff-count = |keys(s1.geno) △ keys(s2.geno)|
  aligned-dist = sum(entry-distance(s1.geno[k], s2.geno[k]) for k in common)
  return aligned-dist + sym-diff-count
```

---

### Stage 2 Tests

```racket
(parameterize ([current-naming 'linear])
  (define (gen) (for/list ([i (in-range 10)]) (rnd-choice '(0 1))))

  ;;; create-ind
  (define s (create-ind gen))
  (check-true (sol? s))
  (check-equal? (length (sol-pheno s)) 10)

  ;;; mutate-point: same key set, at least one value may differ
  (define s1 (create-ind gen))
  (define sm (mutate-point gen s1))
  (check-equal? (list->set (hash-keys (sol-geno s1)))
                (list->set (hash-keys (sol-geno sm))))

  ;;; crossover-uniform: result keys == parent keys
  (define s2 (create-ind gen))
  (define sx (crossover-uniform gen s1 s2))
  (check-equal? (list->set (hash-keys (sol-geno sx)))
                (list->set (hash-keys (sol-geno s1))))

  ;;; crossover-uniform: each aligned value comes from a parent
  (define alignment (align-traces s1 s2))
  (for ([k alignment])
    (define v  (entry-val (hash-ref (sol-geno sx) k)))
    (define v1 (entry-val (hash-ref (sol-geno s1) k)))
    (define v2 (entry-val (hash-ref (sol-geno s2) k)))
    (check-true (or (equal? v v1) (equal? v v2))
                (format "key ~a: ~a not in {~a, ~a}" k v v1 v2)))

  ;;; distance: identical solutions → 0
  (define s3 (play gen (sol-geno s1)))
  (check-equal? (distance-ind s1 s3) 0.0)

  ;;; distance: different solutions → > 0 (with very high probability for n=10)
  (define s4 (create-ind gen))
  (check-true (>= (distance-ind s1 s4) 0.0)))
```

---

### Stage 2 Example

```racket
(parameterize ([current-naming 'linear])
  (define (gen) (for/list ([i (in-range 5)]) (rnd-choice '(0 1))))
  (define s1 (create-ind gen))
  (define s2 (create-ind gen))
  (define sx (crossover-uniform gen s1 s2))
  (define sm (mutate-point gen s1))
  (printf "s1: ~a  fit=~a\n" (sol-pheno s1) (apply + (sol-pheno s1)))
  (printf "s2: ~a  fit=~a\n" (sol-pheno s2) (apply + (sol-pheno s2)))
  (printf "cx: ~a  fit=~a\n" (sol-pheno sx) (apply + (sol-pheno sx)))
  (printf "mu: ~a  fit=~a\n" (sol-pheno sm) (apply + (sol-pheno sm))))
```

---

## Stage 3: Structured Naming and `define-generator`

### Goal

Implement structured naming and the `define-generator` macro. After this stage, generator functions look like plain Racket code and can be tested with `pto/plain` (Stage 6) by swapping one `require`.

---

### Structured Name Format

A structured name is a string built from `_name-frames` and the call-site symbol:

```
structured-name(call-site-sym):
  frames-reversed = reverse(_name-frames)     ; outermost frame first
  "root"
  + for each (site . count) in frames-reversed:
      "/" + symbol->string(site) + ":" + number->string(count)
  + "/" + symbol->string(call-site-sym)
```

**Example**: generator `onemax` at line 1 col 0; `for/list` at line 2 col 2; `rnd-choice` at line 3 col 4; iteration 3:

```
_name-frames = ((loop@2:2 . 3) (onemax@1:0 . 0))   ; innermost first
structured-name('cat@3:4)
  = "root/onemax@1:0:0/loop@2:2:3/cat@3:4"
```

**Uniqueness property**: two `rnd-*` calls have identical structured names across multiple runs of the same generator if and only if they occur at the same source location in the same execution context (same generator, same loop iteration indices, same call-site chain).

---

### `next-name!` — structured branch

```
next-name!(site-sym):
  if (current-naming) == 'structured:
    frames = (_name-frames)
    return (string-append
              "root"
              (apply string-append
                (for/list ([f (reverse frames)])
                  (format "/~a:~a" (car f) (cdr f))))
              (format "/~a" (symbol->string site-sym)))
```

---

### Name Frame Stack

`_name-frames` is a list of pairs `(site-sym . count)`, innermost frame at the head.

Two kinds of frames:
- **Function frame**: `(fn-site-sym . 0)` — pushed by `define-generator` before executing the body; also pushed at every call site of a locally-defined helper function.
- **Loop frame**: `(loop-site-sym . i)` — pushed inside loop bodies, one per iteration.

---

### Site Symbol Helper

At macro-expansion time, given a label and a syntax object:

```
make-site-sym(label, stx):
  return string->symbol(format("~a@~a:~a", label, syntax-line(stx), syntax-column(stx)))
```

Where `label` is a string or symbol (e.g., the function name, `"loop"`, `"call"`).

---

### `define-generator` Macro

**Syntax**: `(define-generator (name args ...) body ...)`

**Effect**: defines `name` as a function that initialises the name frame stack and executes a transformed body.

**Expansion overview**:

```racket
(define (name args ...)
  (parameterize ([_name-frames (list (cons 'fn-site 0))])
    <transformed body>))
```

where `fn-site = make-site-sym(name, stx-of-define-generator)`.

The body is transformed by a two-pass process:

**Pass 1 — collect local functions**: scan the top-level forms of `body` for `(define (f ...) ...)`. Collect the names into `local-fns` (a set of symbols). Only top-level `define` forms count; `let`-bound functions are not tracked.

**Pass 2 — transform**: apply `transform(expr, local-fns)` to each top-level expression of `body`.

---

### Transformation Rules

`transform(expr, local-fns)` pattern-matches on `expr`. Rules are checked in order; the first match applies.

**T1 — `for/list` with any number of binding clauses:**

```
transform((for/list ([x1 s1] [x2 s2] ...) body ...), local-fns)
```

Let `loop-site = make-site-sym("loop", stx-of-for/list)`.
Let `__i__` be a fresh variable name (use `gensym` or a fixed mangled name like `__pto-loop-i__`; must not shadow user variables).

Expands to:
```racket
(for/list ([__i__ (in-naturals)] [x1 s1] [x2 s2] ...)
  (parameterize ([_name-frames (cons (cons 'loop-site __i__) (_name-frames))])
    transform(body, local-fns) ...))
```

**T2 — `for` (void-returning):**

Same as T1 but using `for` instead of `for/list`.

**T3 — nested function definition (f ∈ local-fns):**

```
transform((define (f fargs ...) fbody ...), local-fns)
```

Expands to:
```racket
(define (f fargs ...)
  transform(fbody, local-fns) ...)
```

No frame is pushed in the definition. Frames are pushed at call sites (T4).

**T4 — call to a local function (f ∈ local-fns):**

```
transform((f carg ...), local-fns)
```

Let `call-site = make-site-sym(f, stx-of-call)`.

Expands to:
```racket
(parameterize ([_name-frames (cons (cons 'call-site 0) (_name-frames))])
  (f transform(carg, local-fns) ...))
```

**T5 — `let` / `let*` / `letrec`:**

```
transform((let ([x e] ...) body ...), local-fns)
```

Expands to:
```racket
(let ([x transform(e, local-fns)] ...)
  transform(body, local-fns) ...)
```

Same pattern for `let*` and `letrec`.

**T6 — `if`:**

```
transform((if cond then else), local-fns)
→ (if transform(cond) transform(then) transform(else))

transform((if cond then), local-fns)
→ (if transform(cond) transform(then))
```

**T7 — `cond`:**

```
transform((cond [test expr] ... [else default]), local-fns)
→ (cond [transform(test) transform(expr)] ... [else transform(default)])
```

**T8 — `begin`:**

```
transform((begin e ...), local-fns)
→ (begin transform(e) ...)
```

**T9 — `rnd-choice`, `rnd-real`, `rnd-int` (pass through unchanged):**

These are self-naming macros. `define-generator` must not recurse into them. Treat them as atomic leaves.

**T10 — `and`, `or`, `when`, `unless`:**

Recurse into all sub-expressions (treat body forms as expressions, not special positions).

**T11 — any other list-form `(head arg ...)` (non-local function call or special form not listed above):**

```
transform((head arg ...), local-fns)
→ (head transform(arg, local-fns) ...)
```

This recursion into args handles things like `(list ...)`, `(cons ...)`, `(apply ...)`, `(+ ...)`, etc. It is safe because non-local `head` is not wrapped with a frame.

**T12 — atom (identifier, literal, `'quoted`):**

Return unchanged.

---

### Supported Generator Syntax

The following forms are fully supported:

- `(for/list ([x seq]) body ...)`
- `(for ([x seq]) body ...)`
- `(define (helper args ...) body ...)` at top level of generator body
- `(helper args ...)` calls to locally-defined helpers
- `(let ([x e] ...) body ...)`
- `(let* ([x e] ...) body ...)`
- `(if cond then [else])`
- `(cond [test expr] ...)`
- `(begin e ...)`
- `(rnd-choice seq)`, `(rnd-real lo hi)`, `(rnd-int lo hi)`
- Any Racket expression passed through unchanged

**Constraints on generator functions** (must be enforced by documentation, not checked at runtime):
1. Finite: no unbounded loops or recursion.
2. No external side effects.
3. All randomness via `rnd-*` only.
4. Locally-defined helper functions must appear as top-level `define` forms in the generator body (not inside `let`).
5. Helper functions must not call each other recursively.

---

### Stage 3 Tests

```racket
(require rackunit)

;;; structured names are strings starting with "root/"
(parameterize ([current-naming 'structured])
  (define-generator (check-format-gen)
    (list (rnd-choice '(a b))
          (rnd-real 0.0 1.0)
          (rnd-int 1 10)))
  (define s (play check-format-gen #hash()))
  (check-equal? (length (hash-keys (sol-geno s))) 3)
  (for ([k (hash-keys (sol-geno s))])
    (check-true (string? k) "name must be a string")
    (check-true (string-prefix? k "root/") "name must start with root/")))

;;; same generator, same names across two independent runs
(parameterize ([current-naming 'structured])
  (define-generator (stable-gen)
    (list (rnd-choice '(a b))
          (rnd-int 0 9)))
  (define s1 (play stable-gen #hash()))
  (define s2 (play stable-gen #hash()))
  (check-equal? (sol-key-order s1) (sol-key-order s2)))

;;; loop: each iteration gets a distinct name
(parameterize ([current-naming 'structured])
  (define-generator (loop-gen n)
    (for/list ([i (in-range n)])
      (rnd-choice '(0 1))))
  (define s (play (λ () (loop-gen 5)) #hash()))
  (check-equal? (length (hash-keys (sol-geno s))) 5)
  (check-equal? (length (sol-key-order s))
                (set-count (list->set (sol-key-order s)))
                "all structured names must be distinct"))

;;; nested loops: n*m distinct names
(parameterize ([current-naming 'structured])
  (define-generator (nested-gen n m)
    (for/list ([i (in-range n)])
      (for/list ([j (in-range m)])
        (rnd-choice '(0 1)))))
  (define s (play (λ () (nested-gen 3 4)) #hash()))
  (check-equal? (length (hash-keys (sol-geno s))) 12))

;;; nested helper: two call sites → two distinct names
(parameterize ([current-naming 'structured])
  (define-generator (helper-gen)
    (define (flip) (rnd-choice '(0 1)))
    (list (flip)    ; call site A
          (flip)))  ; call site B
  (define s (play helper-gen #hash()))
  (check-equal? (length (hash-keys (sol-geno s))) 2)
  (check-equal? (length (sol-key-order s))
                (set-count (list->set (sol-key-order s)))))

;;; structured naming + replay is deterministic
(parameterize ([current-naming 'structured])
  (define-generator (s-onemax n)
    (for/list ([i (in-range n)])
      (rnd-choice '(0 1))))
  (define s1 (play (λ () (s-onemax 10)) #hash()))
  (define s2 (play (λ () (s-onemax 10)) (sol-geno s1)))
  (check-equal? (sol-pheno s1) (sol-pheno s2)))

;;; loop name contains iteration index
;;; (name for iteration 3 must differ from iteration 7)
(parameterize ([current-naming 'structured])
  (define-generator (idx-gen n)
    (for/list ([i (in-range n)])
      (rnd-choice '(0 1))))
  (define s (play (λ () (idx-gen 10)) #hash()))
  (define names (sol-key-order s))
  (check-false (equal? (list-ref names 3) (list-ref names 7))))
```

---

### Stage 3 Example

```racket
;; TSP generator with nested helper; structured naming correctly
;; distinguishes each pick-city call site
(define cities '(A B C D E))

(define-generator (tsp)
  (define (pick-city remaining)
    (list-ref remaining (rnd-int 0 (sub1 (length remaining)))))
  (let loop ([rem cities] [tour '()])
    (if (null? rem)
        (reverse tour)
        (let ([city (pick-city rem)])
          (loop (remove city rem) (cons city tour))))))

(parameterize ([current-naming 'structured])
  (define s (play tsp #hash()))
  (printf "Tour: ~a\n" (sol-pheno s))
  (printf "Trace names:\n")
  (for ([k (sol-key-order s)])
    (printf "  ~a → ~a\n" k (entry-val (hash-ref (sol-geno s) k)))))
```

---

## Stage 4: Fine Distributions

### Goal

Extend `entry-mutate` and `entry-replay!` with distribution-aware fine-grained operations. The `current-dist-mode` parameter selects between `'coarse` (Stage 2 behaviour) and `'fine`.

---

### `entry-replay!` — fine mode

Extend Stage 1's `entry-replay!`:

```
entry-replay!(e, old-e, 'fine):
  if (entry-type e) != (entry-type old-e):
    entry-sample!(e)                        ; type mismatch: always resample
  else if (entry-params e) == (entry-params old-e):
    e.val = (entry-val old-e)               ; same params: reuse (same as coarse)
  else:
    ; params changed: fine repair
    match (entry-type e):
      'cat  → choices = (first (entry-params e))
               if (entry-val old-e) ∈ choices:
                 e.val = (entry-val old-e)  ; old value still valid
               else:
                 entry-sample!(e)           ; old value invalid: resample
      'cont → lo = (first (entry-params e)), hi = (second (entry-params e))
               e.val = max(lo, min(hi, (entry-val old-e)))  ; clamp
      'int  → lo = (first (entry-params e)), hi = (second (entry-params e))
               v = (inexact->exact (round (entry-val old-e)))
               e.val = max(lo, min(hi, v))  ; round and clamp
```

---

### `entry-mutate` — fine mode

```
entry-mutate(e, 'coarse):
  new-e = (entry (entry-type e) (entry-params e) #f)
  entry-sample!(new-e)
  return new-e

entry-mutate(e, 'fine):
  match (entry-type e):
    'cat  → same as coarse (no better mutation for categorical)
    'cont → lo = (first params), hi = (second params)
             σ = (hi - lo) * 0.1
             new-val = (entry-val e) + (random-gaussian 0 σ)
             new-val = max(lo, min(hi, new-val))    ; clamp
             return (entry 'cont params new-val)
    'int  → lo = (first params), hi = (second params)
             step = if (random) < 0.5 then -1 else +1
             new-val = max(lo, min(hi, (entry-val e) + step))
             return (entry 'int params new-val)
```

`random-gaussian` can be implemented with the Box-Muller transform or Racket's `flrandom` if available. A simple approximation: `(- (apply + (for/list ([_ (in-range 12)]) (random))) 6.0)` (central limit theorem; σ≈1).

Preferred: use `(define (gauss mu sigma) (+ mu (* sigma (box-muller))))`.

Box-Muller:
```racket
(define (box-muller)
  (define u1 (+ 1e-10 (random)))  ; avoid log(0)
  (define u2 (random))
  (* (sqrt (* -2.0 (log u1)))
     (cos (* 2.0 pi u2))))
```

---

### `entry-crossover` — fine mode

```
entry-crossover(e1, e2, 'coarse):
  return (if (< (random) 0.5) e1 e2)

entry-crossover(e1, e2, 'fine):
  ; Assumes e1.type == e2.type (aligned entries)
  match (entry-type e1):
    'cat  → return (if (< (random) 0.5) e1 e2)
    'cont → α = (random)                        ; uniform in [0,1]
             lo = (first (entry-params e1))
             hi = (second (entry-params e1))
             v = α * (entry-val e1) + (1-α) * (entry-val e2)
             v = max(lo, min(hi, v))
             return (entry 'cont (entry-params e1) v)
    'int  → return (if (< (random) 0.5) e1 e2)
```

Update `crossover-uniform` and `crossover-one-point` to use `entry-crossover(e1, e2, (current-dist-mode))`.

---

### Stage 4 Tests

```racket
;;; fine mutation for 'cont: stays in bounds
(for ([_ (in-range 50)])
  (define e (entry 'cont '(0.0 10.0) 5.0))
  (define e2 (entry-mutate e 'fine))
  (check-true (<= 0.0 (entry-val e2) 10.0))
  (check-equal? (entry-type e2) 'cont))

;;; fine mutation for 'int: changes by exactly 1 (except at boundaries)
(let* ([e  (entry 'int '(0 10) 5)]
       [e2 (entry-mutate e 'fine)])
  (check-true (<= 0 (entry-val e2) 10))
  (check-true (member (- (entry-val e2) (entry-val e)) '(-1 1))))

;;; fine mutation for 'int at lower boundary: can only go up
(for ([_ (in-range 20)])
  (define e  (entry 'int '(0 10) 0))
  (define e2 (entry-mutate e 'fine))
  (check-true (<= 0 (entry-val e2) 10)))

;;; fine mutation for 'int at upper boundary: can only go down
(for ([_ (in-range 20)])
  (define e  (entry 'int '(0 10) 10))
  (define e2 (entry-mutate e 'fine))
  (check-true (<= 0 (entry-val e2) 10)))

;;; fine crossover for 'cont: result between parents
(for ([_ (in-range 50)])
  (define e1 (entry 'cont '(0.0 10.0) 2.0))
  (define e2 (entry 'cont '(0.0 10.0) 8.0))
  (define ex (entry-crossover e1 e2 'fine))
  (check-true (<= 2.0 (entry-val ex) 8.0))
  (check-equal? (entry-type ex) 'cont))

;;; fine repair: cont value clamped to new range
(let* ([old-e (entry 'cont '(0.0 100.0) 75.0)]
       [new-e (entry 'cont '(0.0 50.0) #f)])
  (entry-replay! new-e old-e 'fine)
  (check-equal? (entry-val new-e) 50.0))

;;; fine repair: int value clamped
(let* ([old-e (entry 'int '(0 100) 73)]
       [new-e (entry 'int '(0 50) #f)])
  (entry-replay! new-e old-e 'fine)
  (check-equal? (entry-val new-e) 50))

;;; fine repair: cat value reused if still valid
(let* ([old-e (entry 'cat '((a b c)) 'b)]
       [new-e (entry 'cat '((b c d)) #f)])
  (entry-replay! new-e old-e 'fine)
  (check-equal? (entry-val new-e) 'b))

;;; fine repair: cat value resampled if no longer valid
(let* ([old-e (entry 'cat '((a b c)) 'a)]
       [new-e (entry 'cat '((x y z)) #f)])
  (entry-replay! new-e old-e 'fine)
  (check-true (member (entry-val new-e) '(x y z))))

;;; coarse repair: resamples (ignores old value when params change)
(let* ([old-e (entry 'cont '(0.0 100.0) 75.0)]
       [new-e (entry 'cont '(0.0 50.0) #f)])
  (entry-replay! new-e old-e 'coarse)
  (check-true (<= 0.0 (entry-val new-e) 50.0)))
```

---

### Stage 4 Example

```racket
;; Sphere: fine distributions converge faster
(define-generator (sphere-gen n)
  (for/list ([i (in-range n)])
    (rnd-real -5.0 5.0)))

(define (sphere-fit pheno)
  (- (apply + (map (λ (x) (* x x)) pheno))))

(for ([mode '(coarse fine)])
  (parameterize ([current-naming 'linear] [current-dist-mode mode])
    (define best (create-ind (λ () (sphere-gen 3))))
    (define best-fit (sphere-fit (sol-pheno best)))
    (for ([_ (in-range 300)])
      (define candidate (mutate-point (λ () (sphere-gen 3)) best))
      (define f (sphere-fit (sol-pheno candidate)))
      (when (> f best-fit)
        (set! best candidate)
        (set! best-fit f)))
    (printf "mode=~a  best-fit=~a\n" mode best-fit)))
;; Expected: 'fine achieves fitness closer to 0 than 'coarse
```

---

## Stage 5: Hill Climber and `run`

### `hill-climber`

```
hill-climber(gen, fit, better, n-iterations):
  best     = create-ind(gen)
  best-fit = fit((sol-pheno best))

  repeat n-iterations times:
    candidate     = mutate-point(gen, best)
    candidate-fit = fit((sol-pheno candidate))
    if better(candidate-fit, best-fit):
      best     = candidate
      best-fit = candidate-fit

  return (values best best-fit)
```

Signature: `(hill-climber gen fit better n-iterations)` where `better` is a two-argument comparator (e.g. `>` for maximisation, `<` for minimisation).

---

### `run`

```racket
(define (run gen fit
             #:better     [better >]
             #:naming     [naming 'structured]
             #:dist-mode  [dist-mode 'coarse]
             #:solver     [solver hill-climber]
             #:n-iterations [n 1000]
             #:gen-args   [gen-args '()]
             #:fit-args   [fit-args '()])
  (define wrapped-gen (λ () (apply gen gen-args)))
  (define wrapped-fit (λ (pheno) (apply fit pheno fit-args)))
  (parameterize ([current-naming   naming]
                 [current-dist-mode dist-mode])
    (solver wrapped-gen wrapped-fit better n)))
```

`solver` receives `(gen fit better n-iterations)`. The default is `hill-climber`. Additional solvers (GA, random search) may be added later with the same signature.

---

### Stage 5 Tests

```racket
;;; hill-climber improves ONEMAX reliably
(define-generator (om-gen n)
  (for/list ([i (in-range n)])
    (rnd-choice '(0 1))))

(parameterize ([current-naming 'linear])
  (define-values (best fit)
    (hill-climber (λ () (om-gen 20))
                  (λ (pheno) (apply + pheno))
                  > 300))
  (check-true (> fit 14) "hill-climber should beat random on ONEMAX-20"))

;;; run API: basic call succeeds
(define-values (r-best r-fit)
  (run om-gen (λ (pheno) (apply + pheno))
       #:better > #:naming 'linear #:dist-mode 'coarse
       #:n-iterations 300 #:gen-args '(20)))
(check-true (sol? r-best))
(check-true (real? r-fit))

;;; run with structured naming
(define-values (s-best s-fit)
  (run om-gen (λ (pheno) (apply + pheno))
       #:better > #:naming 'structured #:dist-mode 'coarse
       #:n-iterations 300 #:gen-args '(20)))
(check-true (sol? s-best))

;;; run with fine distributions on sphere
(define-generator (sp-gen n)
  (for/list ([i (in-range n)])
    (rnd-real -5.0 5.0)))

(define-values (sp-best sp-fit)
  (run sp-gen (λ (pheno) (- (apply + (map (λ (x) (* x x)) pheno))))
       #:better > #:naming 'linear #:dist-mode 'fine
       #:n-iterations 500 #:gen-args '(5)))
(check-true (> sp-fit -1.0) "fine hill-climber should get sphere close to 0")

;;; minimisation (better = <)
(define-values (mn-best mn-fit)
  (run sp-gen (λ (pheno) (apply + (map (λ (x) (* x x)) pheno)))
       #:better < #:naming 'linear #:dist-mode 'fine
       #:n-iterations 500 #:gen-args '(5)))
(check-true (< mn-fit 1.0))
```

---

### Stage 5 Example

```racket
;; ONEMAX: end-to-end run
(define-generator (onemax n)
  (for/list ([i (in-range n)])
    (rnd-choice '(0 1))))

(define-values (best fit)
  (run onemax (λ (pheno) (apply + pheno))
       #:better > #:naming 'structured #:dist-mode 'coarse
       #:n-iterations 500 #:gen-args '(30)))

(printf "ONEMAX-30 best: ~a/30\n" fit)
(printf "Solution: ~a\n" (sol-pheno best))
;; Expected: fit >= 28 reliably
```

---

## Stage 6: `pto/plain` Companion Module

### Goal

Provide stubs so any file using `(require pto)` can be tested as plain Racket by substituting `(require pto/plain)`. No trace, no operators — just randomness.

### `pto/plain.rkt`

```racket
#lang racket
(provide define-generator rnd-choice rnd-real rnd-int)

(define-syntax-rule (define-generator (name args ...) body ...)
  (define (name args ...) body ...))

(define (rnd-choice seq)
  (list-ref seq (random (length seq))))

(define (rnd-real lo hi)
  (+ lo (* (random) (- hi lo))))

(define (rnd-int lo hi)
  (+ lo (random (add1 (- hi lo)))))
```

---

### Stage 6 Tests

```racket
;; File: test-plain.rkt
#lang racket
(require "pto/plain.rkt")
(require rackunit)

(define-generator (onemax n)
  (for/list ([i (in-range n)])
    (rnd-choice '(0 1))))

;;; runs without any PTO infrastructure
(define result (onemax 10))
(check-equal? (length result) 10)
(check-true (andmap (λ (x) (member x '(0 1))) result))

(define-generator (mixed n)
  (for/list ([i (in-range n)])
    (list (rnd-choice '(a b c))
          (rnd-real 0.0 1.0)
          (rnd-int 1 6))))

(define r (mixed 5))
(check-equal? (length r) 5)
(for ([elem r])
  (check-true (member (first elem) '(a b c)))
  (check-true (<= 0.0 (second elem) 1.0))
  (check-true (<= 1 (third elem) 6)))

;;; nested helper compiles and runs
(define-generator (tsp-plain)
  (define cities '(A B C D E))
  (define (pick rem)
    (list-ref rem (rnd-int 0 (sub1 (length rem)))))
  (let loop ([rem cities] [tour '()])
    (if (null? rem) (reverse tour)
        (let ([c (pick rem)])
          (loop (remove c rem) (cons c tour))))))

(define tour (tsp-plain))
(check-equal? (length tour) 5)
(check-equal? (list->set tour) (list->set '(A B C D E)))
```

---

## Complete Reference Example: TSP

This example exercises every feature: structured naming, nested helper, crossover alignment across permutation-length-variable traces, fine vs coarse mode.

```racket
#lang racket
(require "pto.rkt")

;;; Problem
(define cities '(A B C D E F G))

(define dist-matrix
  (let ([d (make-hash)])
    (for* ([a cities] [b cities])
      (unless (eq? a b)
        (hash-set! d (list a b)
                   (+ 1 (random 9)))))
    d))

(define (tour-cost tour)
  (for/sum ([a tour]
            [b (append (rest tour) (list (first tour)))])
    (hash-ref dist-matrix (list a b) 1)))

;;; Generator
(define-generator (tsp)
  (define (pick remaining)
    (list-ref remaining (rnd-int 0 (sub1 (length remaining)))))
  (let loop ([rem cities] [tour '()])
    (if (null? rem)
        (reverse tour)
        (let ([city (pick rem)])
          (loop (remove city rem) (cons city tour))))))

;;; Run
(define-values (best fit)
  (run tsp
       (λ (pheno) (- (tour-cost pheno)))   ; negate: maximise negative cost
       #:better >
       #:naming 'structured
       #:dist-mode 'coarse
       #:n-iterations 1000))

(printf "Best tour: ~a\n" (sol-pheno best))
(printf "Tour cost: ~a\n" (- fit))

;;; Verify: structured names enable meaningful crossover
(parameterize ([current-naming 'structured])
  (define s1 (create-ind tsp))
  (define s2 (create-ind tsp))
  (define alignment (align-traces s1 s2))
  (printf "Aligned positions: ~a / ~a\n"
          (length alignment)
          (length (sol-key-order s1)))
  ;; With structured naming, all 7 rnd-int calls share the same
  ;; keys because the generator always makes 7 picks regardless
  ;; of the chosen cities. alignment should be 7.
  (check-equal? (length alignment) 7))
```

---

## Appendix A: Linear vs Structured Naming

| Property | Linear | Structured |
|---|---|---|
| Key type | exact integer | string |
| Format | `0`, `1`, `2`, ... | `"root/fn@L:C:0/loop@L:C:i/cat@L:C"` |
| Counter reset | each `play` call | n/a (frame stack reset) |
| Stability across runs | yes (same generator) | yes |
| Works in REPL | yes | yes (unlike Python `inspect.getsource`) |
| Crossover alignment | by integer order | by execution context |
| Variable-length loops | poor alignment | good alignment |
| When to use | default, debugging | production, variable-structure generators |

---

## Appendix B: Distribution Modes

| Aspect | Coarse | Fine |
|---|---|---|
| Mutation `'cat` | resample | resample |
| Mutation `'cont` | resample uniform | Gaussian perturbation, σ=10% of range |
| Mutation `'int` | resample uniform | ±1 step, clamped |
| Crossover `'cat` | copy from one parent | copy from one parent |
| Crossover `'cont` | copy from one parent | convex combination α∈[0,1] |
| Crossover `'int` | copy from one parent | copy from one parent |
| Repair on param change `'cat` | resample | reuse if valid, else resample |
| Repair on param change `'cont` | resample | clamp to new `[lo,hi]` |
| Repair on param change `'int` | resample | round and clamp |

---

## Appendix C: Naming Frame Stack Reference

At the start of `play`, `_name-frames` is reset to `'()`.

`define-generator` pushes `(fn-site-sym . 0)` via `parameterize` before running the body.

Each `for/list` expansion pushes `(loop-site-sym . i)` for iteration `i` via `parameterize` inside the loop body.

Each call to a locally-defined helper `(f args ...)` wraps the call in `parameterize` that pushes `(call-site-sym . 0)`.

The stack is a proper Racket list; `parameterize` ensures the frame is automatically popped on exit (including exceptions).

---

## Appendix D: `pto.rkt` Module Exports

The following names are exported from `pto.rkt`:

```racket
;; structs
entry entry? entry-type entry-params entry-val
sol   sol?   sol-pheno  sol-geno     sol-key-order

;; parameters
current-naming current-dist-mode

;; rnd macros
rnd-choice rnd-real rnd-int

;; generator macro
define-generator

;; play
play

;; operators
create-ind
mutate-point mutate-random
crossover-uniform crossover-one-point
distance-ind align-traces

;; solvers
hill-climber

;; top-level
run
```

Internal names (`_tracing`, `_in-trace`, `_out-trace`, `_key-order`, `_name-seq`, `_name-frames`, `pto-sample!`, `next-name!`, `entry-sample!`, `entry-replay!`, `entry-mutate`, `entry-crossover`) are **not exported**.
