#lang racket
;; ===========================================================================
;; PTO — Program Trace Optimisation (Racket)
;;
;; Design notes (deviations from the spec, agreed up front):
;;   * `entry` is IMMUTABLE. The spec's `entry-sample!` / `entry-replay!` that
;;     mutated `val` in place are replaced by `entry-sample` / `entry-replay`
;;     that RETURN a fresh entry. `entry-mutate` / `entry-crossover` were
;;     already specified to return new entries; now all four are consistent.
;;     This removes the aliasing footgun: crossover copies entry references
;;     into a merged hash, which is correct only because entries can't be
;;     mutated underneath you.
;;   * Per-play accumulation state lives in ONE mutable cell (`trace-ctx`),
;;     held in a single parameter `_ctx`. `_ctx` is #f when no play is in
;;     progress, which also subsumes the spec's `_tracing` flag.
;;   * `_name-frames` stays a separate parameter: it is a stack that is
;;     pushed/popped around sub-expressions, and `parameterize` gives exactly
;;     the dynamic-extent restore-on-exit (incl. exceptions) that a stack
;;     wants. A box would need dynamic-wind to be correct.
;;   * The linear name counter is KEPT as explicit state (in `trace-ctx`),
;;     even though derivable from key-order length. Keeping it means
;;     `pto-sample!` does identical work for linear and structured naming, so
;;     the same operators apply uniformly regardless of label kind.
;; ===========================================================================

(require racket/hash      ; hash-union
         racket/set       ; set ops used by distance / align
         racket/math)     ; pi (Box-Muller)

(require (for-syntax racket/base
                     racket/set
                     syntax/parse))

(provide ;; structs
         (struct-out entry)
         (struct-out sol)
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
         run)

;; ---------------------------------------------------------------------------
;; Data structures
;; ---------------------------------------------------------------------------

;; entry: one recorded random decision (IMMUTABLE).
(struct entry (type params val) #:transparent)

;; sol: a solution.
(struct sol (pheno geno key-order) #:transparent)

;; ---------------------------------------------------------------------------
;; Parameters
;; ---------------------------------------------------------------------------

;; Public
(define current-naming    (make-parameter 'linear))   ; 'linear | 'structured
(define current-dist-mode (make-parameter 'coarse))   ; 'coarse | 'fine

;; Internal accumulator cell. #f outside a play; a `trace-ctx` during a play.
;;   in        : immutable input trace (hash name -> entry)
;;   out       : output trace being built (immutable hash, replaced as it grows)
;;   key-order : names in insertion order, REVERSED (head = most recent)
;;   name-seq  : linear-naming counter
(struct trace-ctx (in [out #:mutable] [key-order #:mutable] [name-seq #:mutable]))

(define _ctx (make-parameter #f))

;; Structured-naming frame stack (innermost frame at head). Parameter so that
;; pushes via `parameterize` unwind automatically.
(define _name-frames (make-parameter '()))

;; ---------------------------------------------------------------------------
;; Entry sampling / replay / mutation / crossover (all return fresh entries)
;; ---------------------------------------------------------------------------

;; Box-Muller standard normal; gauss scales it.
(define (box-muller)
  (define u1 (+ 1e-10 (random)))   ; avoid log(0)
  (define u2 (random))
  (* (sqrt (* -2.0 (log u1)))
     (cos (* 2.0 pi u2))))
(define (gauss mu sigma) (+ mu (* sigma (box-muller))))

(define (clamp lo hi v) (max lo (min hi v)))

;; entry-sample : entry -> entry
;; Return a copy of `e` (type+params) with a freshly sampled val.
(define (entry-sample e)
  (define params (entry-params e))
  (entry
   (entry-type e)
   params
   (case (entry-type e)
     [(cat)  (let ([cs (first params)]) (list-ref cs (random (length cs))))]
     [(cont) (let ([lo (first params)] [hi (second params)])
               (+ lo (* (random) (- hi lo))))]
     [(int)  (let ([lo (first params)] [hi (second params)])
               (+ lo (random (add1 (- hi lo)))))])))

;; entry-replay : new-template old-e mode -> entry
;; Fill a fresh entry by reusing/repairing old-e's value where appropriate.
(define (entry-replay e old-e mode)
  (define same-type?   (eq? (entry-type e) (entry-type old-e)))
  (define same-params? (equal? (entry-params e) (entry-params old-e)))
  (cond
    ;; ---- coarse: reuse only on exact distribution match, else resample ----
    [(eq? mode 'coarse)
     (if (and same-type? same-params?)
         (entry (entry-type e) (entry-params e) (entry-val old-e))
         (entry-sample e))]
    ;; ---- fine: type mismatch resamples; same params reuse; else repair ----
    [(eq? mode 'fine)
     (cond
       [(not same-type?) (entry-sample e)]
       [same-params?     (entry (entry-type e) (entry-params e) (entry-val old-e))]
       [else             (entry-repair e old-e)])]
    [else (error 'entry-replay "unknown dist-mode: ~a" mode)]))

;; entry-repair : new-template old-e -> entry   (fine mode, same type, params changed)
(define (entry-repair e old-e)
  (define params (entry-params e))
  (define old-val (entry-val old-e))
  (case (entry-type e)
    [(cat)
     (define choices (first params))
     (entry 'cat params
            (if (member old-val choices) old-val (entry-val (entry-sample e))))]
    [(cont)
     (define lo (first params)) (define hi (second params))
     (entry 'cont params (clamp lo hi old-val))]
    [(int)
     (define lo (first params)) (define hi (second params))
     (entry 'int params (clamp lo hi (inexact->exact (round old-val))))]))

;; entry-mutate : entry mode -> entry
(define (entry-mutate e mode)
  (cond
    [(eq? mode 'coarse) (entry-sample e)]          ; resample regardless of type
    [(eq? mode 'fine)
     (case (entry-type e)
       [(cat) (entry-sample e)]                    ; no better local move
       [(cont)
        (define lo (first (entry-params e))) (define hi (second (entry-params e)))
        (define sigma (* (- hi lo) 0.1))
        (entry 'cont (entry-params e)
               (clamp lo hi (+ (entry-val e) (gauss 0.0 sigma))))]
       [(int)
        (define lo (first (entry-params e))) (define hi (second (entry-params e)))
        (define step (if (< (random) 0.5) -1 1))
        (entry 'int (entry-params e) (clamp lo hi (+ (entry-val e) step)))])]
    [else (error 'entry-mutate "unknown dist-mode: ~a" mode)]))

;; entry-crossover : e1 e2 mode -> entry   (assumes aligned: same type)
(define (entry-crossover e1 e2 mode)
  (cond
    [(eq? mode 'coarse) (if (< (random) 0.5) e1 e2)]
    [(eq? mode 'fine)
     (case (entry-type e1)
       [(cat) (if (< (random) 0.5) e1 e2)]
       [(cont)
        (define a (random))
        (define lo (first (entry-params e1))) (define hi (second (entry-params e1)))
        (entry 'cont (entry-params e1)
               (clamp lo hi (+ (* a (entry-val e1)) (* (- 1.0 a) (entry-val e2)))))]
       [(int) (if (< (random) 0.5) e1 e2)])]
    [else (error 'entry-crossover "unknown dist-mode: ~a" mode)]))

;; ---------------------------------------------------------------------------
;; Naming
;; ---------------------------------------------------------------------------

;; next-name! : site-sym ctx -> name
(define (next-name! site ctx)
  (case (current-naming)
    [(linear)
     (define n (trace-ctx-name-seq ctx))
     (set-trace-ctx-name-seq! ctx (add1 n))
     n]
    [(structured)
     (string-append
      "root"
      (apply string-append
             (for/list ([f (in-list (reverse (_name-frames)))])
               (format "/~a:~a" (car f) (cdr f))))
      (format "/~a" site))]
    [else (error 'next-name! "unknown naming: ~a" (current-naming))]))

;; ---------------------------------------------------------------------------
;; Core sampling entry point (called by every rnd-* macro)
;; ---------------------------------------------------------------------------

;; pto-sample! : site-sym (-> entry) -> any
;; make-entry builds a *template* entry (val = #f) carrying type+params.
(define (pto-sample! site make-entry)
  (define ctx (_ctx))
  (define tmpl (make-entry))
  (cond
    [(not ctx)                                    ; Not tracing: just sample directly
     (entry-val (entry-sample tmpl))]
    [else
     (define name (next-name! site ctx))
     
     ;; ---- NEW CRASH-EARLY GUARD ----
     (when (hash-has-key? (trace-ctx-out ctx) name)
       (error 'pto-sample! 
              "Trace name collision detected: ~s\n  This usually means an unsupported loop form (like a named let) or un-tracked recursion was used inside a generator." 
              name))
     ;; --------------------------------
     
     (define in (trace-ctx-in ctx))
     (define e
       (if (hash-has-key? in name)
           (entry-replay tmpl (hash-ref in name) (current-dist-mode))
           (entry-sample tmpl)))
     
     ;; Since the guard guarantees 'name' is fresh to 'out', we can simplify this setup
     (set-trace-ctx-key-order! ctx (cons name (trace-ctx-key-order ctx)))
     (set-trace-ctx-out! ctx (hash-set (trace-ctx-out ctx) name e))
     (entry-val e)]))

;; ---------------------------------------------------------------------------
;; play
;; ---------------------------------------------------------------------------

(define (play gen trace)
  (parameterize ([_ctx (trace-ctx trace #hash() '() 0)]
                 [_name-frames '()])
    (define pheno (gen))
    (define ctx (_ctx))
    (sol pheno (trace-ctx-out ctx) (reverse (trace-ctx-key-order ctx)))))

;; ---------------------------------------------------------------------------
;; rnd-* macros — capture use-site source location as the structural id
;; ---------------------------------------------------------------------------

(begin-for-syntax
  ;; Disambiguating counter for sites that lack source location (e.g. some
  ;; REPL inputs). Assigned once at expansion time, so it is stable across
  ;; runs of the compiled code.
  (define no-loc-counter 0)
  (define (site-sym label stx)
    (define l (syntax-line stx))
    (define c (syntax-column stx))
    (if (and l c)
        (string->symbol (format "~a@~a:~a" label l c))
        (let ([n no-loc-counter])
          (set! no-loc-counter (add1 n))
          (string->symbol (format "~a@nl~a" label n))))))

(define-syntax (rnd-choice stx)
  (syntax-parse stx
    [(_ seq)
     (define site (site-sym 'cat stx))
     #`(pto-sample! '#,site (λ () (entry 'cat (list seq) #f)))]))

(define-syntax (rnd-real stx)
  (syntax-parse stx
    [(_ lo hi)
     (define site (site-sym 'cont stx))
     #`(pto-sample! '#,site (λ () (entry 'cont (list lo hi) #f)))]))

(define-syntax (rnd-int stx)
  (syntax-parse stx
    [(_ lo hi)
     (define site (site-sym 'int stx))
     #`(pto-sample! '#,site (λ () (entry 'int (list lo hi) #f)))]))

;; ---------------------------------------------------------------------------
;; define-generator : structured-naming code walker
;; ---------------------------------------------------------------------------

(begin-for-syntax
  ;; Pass 1: collect top-level (define (f ...) ...) helper names.
  (define (collect-locals forms)
    (for/fold ([s (set)]) ([f (in-list forms)])
      (syntax-parse f
        #:literals (define)
        [(define (fname:id . _) . _) (set-add s (syntax-e #'fname))]
        [_ s])))

  ;; transform : syntax set -> syntax   (Pass 2)
  (define (transform stx locals)
    (define (t s) (transform s locals))
    (define (t* ss) (map t (syntax->list ss)))
    (syntax-parse stx
      #:literals (for/list for let let* letrec if cond begin and or when unless define
                  rnd-choice rnd-real rnd-int)
      ;; T9 — rnd-* are self-naming leaves; do not recurse.
      [(rnd-choice . _) stx]
      [(rnd-real   . _) stx]
      [(rnd-int    . _) stx]
      ;; T1 — for/list (any number of clauses)
      [(for/list (clause ...) body ...)
       (define ls (site-sym 'loop stx))
       (with-syntax ([(i) (generate-temporaries '(__pto-loop-i__))]
                     [(nb ...) (t* #'(body ...))])
         #`(for/list ([i (in-naturals)] clause ...)
             (parameterize ([_name-frames (cons (cons '#,ls i) (_name-frames))])
               nb ...)))]
      ;; T2 — for (void)
      [(for (clause ...) body ...)
       (define ls (site-sym 'loop stx))
       (with-syntax ([(i) (generate-temporaries '(__pto-loop-i__))]
                     [(nb ...) (t* #'(body ...))])
         #`(for ([i (in-naturals)] clause ...)
             (parameterize ([_name-frames (cons (cons '#,ls i) (_name-frames))])
               nb ...)))]
      ;; T3 — nested helper definition (no frame here; frames pushed at calls)
      [(define (fname:id fa ...) fb ...)
       #:when (set-member? locals (syntax-e #'fname))
       (with-syntax ([(nb ...) (t* #'(fb ...))])
         #`(define (fname fa ...) nb ...))]
      ;; T5 — let / let* / letrec
      [(let ([x e] ...) body ...)
       (with-syntax ([(ne ...) (t* #'(e ...))] [(nb ...) (t* #'(body ...))])
         #`(let ([x ne] ...) nb ...))]
      [(let* ([x e] ...) body ...)
       (with-syntax ([(ne ...) (t* #'(e ...))] [(nb ...) (t* #'(body ...))])
         #`(let* ([x ne] ...) nb ...))]
      [(letrec ([x e] ...) body ...)
       (with-syntax ([(ne ...) (t* #'(e ...))] [(nb ...) (t* #'(body ...))])
         #`(letrec ([x ne] ...) nb ...))]
      ;; T6 — if
      [(if c then else) #`(if #,(t #'c) #,(t #'then) #,(t #'else))]
      [(if c then)      #`(if #,(t #'c) #,(t #'then))]
      ;; T7 — cond
      [(cond clause ...)
       #`(cond #,@(map (λ (c)
                         (syntax-parse c
                           #:literals (else)
                           [(else e ...)
                            (with-syntax ([(ne ...) (t* #'(e ...))]) #'(else ne ...))]
                           [(test e ...)
                            (with-syntax ([nt (t #'test)] [(ne ...) (t* #'(e ...))])
                              #'(nt ne ...))]))
                       (syntax->list #'(clause ...))))]
      ;; T8 — begin
      [(begin e ...) (with-syntax ([(ne ...) (t* #'(e ...))]) #`(begin ne ...))]
      ;; T10 — and / or / when / unless
      [(and e ...)        (with-syntax ([(ne ...) (t* #'(e ...))]) #`(and ne ...))]
      [(or e ...)         (with-syntax ([(ne ...) (t* #'(e ...))]) #`(or ne ...))]
      [(when c e ...)     (with-syntax ([(ne ...) (t* #'(e ...))]) #`(when #,(t #'c) ne ...))]
      [(unless c e ...)   (with-syntax ([(ne ...) (t* #'(e ...))]) #`(unless #,(t #'c) ne ...))]
      ;; T4 — call to a local helper: push a call-site frame
      [(f:id arg ...)
       #:when (set-member? locals (syntax-e #'f))
       (define cs (site-sym (syntax-e #'f) stx))
       (with-syntax ([(na ...) (t* #'(arg ...))])
         #`(parameterize ([_name-frames (cons (cons '#,cs 0) (_name-frames))])
             (f na ...)))]
      ;; T11 — any other list form: recurse into args only
      [(head arg ...)
       (with-syntax ([(na ...) (t* #'(arg ...))])
         #`(head na ...))]
      ;; T12 — atom
      [_ stx])))

(define-syntax (define-generator stx)
  (syntax-parse stx
    [(_ (name args ...) body ...)
     (define fn-site (site-sym (syntax-e #'name) #'name))
     (define locals  (collect-locals (syntax->list #'(body ...))))
     (with-syntax ([(nb ...) (map (λ (b) (transform b locals))
                                  (syntax->list #'(body ...)))]
                   [fns fn-site])
       #`(define (name args ...)
           (parameterize ([_name-frames (list (cons 'fns 0))])
             nb ...)))]))

;; ---------------------------------------------------------------------------
;; Operators
;; ---------------------------------------------------------------------------

(define (create-ind gen) (play gen #hash()))

;; align-traces : common names in s1's key-order
(define (align-traces s1 s2)
  (define g2 (sol-geno s2))
  (for/list ([k (in-list (sol-key-order s1))] #:when (hash-has-key? g2 k)) k))

(define (mutate-point gen s)
  (define geno (sol-geno s))
  (define keys (hash-keys geno))
  (define key (list-ref keys (random (length keys))))
  (define new-e (entry-mutate (hash-ref geno key) (current-dist-mode)))
  (play gen (hash-set geno key new-e)))

(define (mutate-random gen _s) (play gen #hash()))

(define (crossover-uniform gen s1 s2)
  (define g1 (sol-geno s1))
  (define g2 (sol-geno s2))
  (define merged0 (hash-union g1 g2 #:combine (λ (v1 v2) v2)))  ; s2 wins on overlap
  (define alignment (align-traces s1 s2))
  (define merged
    (for/fold ([m merged0]) ([k (in-list alignment)])
      (hash-set m k (entry-crossover (hash-ref g1 k) (hash-ref g2 k)
                                     (current-dist-mode)))))
  (play gen merged))

(define (crossover-one-point gen s1 s2)
  (define g1 (sol-geno s1))
  (define g2 (sol-geno s2))
  (define merged0 (hash-union g1 g2 #:combine (λ (v1 v2) v2)))
  (define alignment (align-traces s1 s2))
  (define n (length alignment))
  (define point (random (add1 n)))                ; 0..n inclusive
  (define merged
    (for/fold ([m merged0]) ([k (in-list alignment)] [i (in-naturals)])
      (hash-set m k (if (< i point) (hash-ref g1 k) (hash-ref g2 k)))))
  (play gen merged))

(define (entry-distance e1 e2)
  (if (and (eq? (entry-type e1) (entry-type e2))
           (equal? (entry-val e1) (entry-val e2)))
      0.0
      1.0))

(define (distance-ind s1 s2)
  (define g1 (sol-geno s1))
  (define g2 (sol-geno s2))
  (define k1 (list->set (hash-keys g1)))
  (define k2 (list->set (hash-keys g2)))
  (define common (set-intersect k1 k2))
  (define sym-diff-count (set-count (set-symmetric-difference k1 k2)))
  (define aligned
    (for/sum ([k (in-set common)])
      (entry-distance (hash-ref g1 k) (hash-ref g2 k))))
  (+ 0.0 aligned sym-diff-count))                 ; force inexact

;; ---------------------------------------------------------------------------
;; Solvers and run
;; ---------------------------------------------------------------------------

(define (hill-climber gen fit better n-iterations #:on-iteration [on-iter #f])
  (define best     (create-ind gen))
  (define best-fit (fit (sol-pheno best)))
  (for ([i (in-range n-iterations)])
    (define cand     (mutate-point gen best))
    (define cand-fit (fit (sol-pheno cand)))
    (when (better cand-fit best-fit)
      (set! best cand)
      (set! best-fit cand-fit))
    ;; ---- NEW: Fire the callback if one was provided ----
    (when on-iter
      (on-iter i cand-fit best-fit)))
  (values best best-fit))

(define (run gen fit
             #:better       [better >]
             #:naming       [naming 'structured]
             #:dist-mode    [dist-mode 'coarse]
             #:solver       [solver hill-climber]
             #:n-iterations [n 1000]
             #:gen-args     [gen-args '()]
             #:fit-args     [fit-args '()]
             #:on-iteration [on-iter #f]) ; <-- Added keyword here
  (define wrapped-gen (λ () (apply gen gen-args)))
  (define wrapped-fit (λ (pheno) (apply fit pheno fit-args)))
  (parameterize ([current-naming    naming]
                 [current-dist-mode dist-mode])
    ;; Pass the callback straight down to the solver
    (solver wrapped-gen wrapped-fit better n #:on-iteration on-iter)))

;; ===========================================================================
;; Tests (run with: raco test pto.rkt). These live inside the module so they
;; can reach internal, non-exported functions (entry-sample, entry-mutate, …).
;; ===========================================================================
(module+ test
  (require rackunit)

  ;; ---------------- Stage 1: core tracing ----------------
  (test-case "entry struct"
    (let ([e (entry 'cat '((a b c)) #f)])
      (check-equal? (entry-type e) 'cat)
      (check-equal? (entry-params e) '((a b c)))
      (check-false  (entry-val e))))

  (test-case "entry-sample fills val (cont/int/cat)"
    (let ([e (entry-sample (entry 'cont '(0.0 1.0) #f))])
      (check-true (real? (entry-val e)))
      (check-true (<= 0.0 (entry-val e) 1.0)))
    (let ([e (entry-sample (entry 'int '(3 7) #f))])
      (check-true (exact-integer? (entry-val e)))
      (check-true (<= 3 (entry-val e) 7)))
    (let ([e (entry-sample (entry 'cat '((x y)) #f))])
      (check-not-false (member (entry-val e) '(x y)))))

  (test-case "play produces a sol; linear key is 0"
    (parameterize ([current-naming 'linear])
      (define gen (λ () (rnd-choice '(a b c))))
      (define s (play gen #hash()))
      (check-true (sol? s))
      (check-not-false (member (sol-pheno s) '(a b c)))
      (check-equal? (length (sol-key-order s)) 1)
      (check-equal? (sol-key-order s) '(0))))

  (test-case "replay is deterministic"
    (parameterize ([current-naming 'linear])
      (define gen (λ () (rnd-choice '(a b c))))
      (define s1 (play gen #hash()))
      (define s2 (play gen (sol-geno s1)))
      (check-equal? (sol-pheno s1) (sol-pheno s2))))

  (test-case "multiple rnd calls: keys 0 1 2 in order"
    (parameterize ([current-naming 'linear])
      (define gen (λ () (list (rnd-choice '(a b)) (rnd-int 1 3) (rnd-real 0.0 1.0))))
      (define s (play gen #hash()))
      (check-equal? (sol-key-order s) '(0 1 2))
      (check-equal? (length (sol-pheno s)) 3)))

  (test-case "coarse replay reuses value when params match"
    (parameterize ([current-naming 'linear])
      (define gen (λ () (rnd-int 0 100)))
      (define s1 (play gen #hash()))
      (define s2 (play gen (sol-geno s1)))
      (check-equal? (sol-pheno s1) (sol-pheno s2))))

  (test-case "coarse replay resamples when params differ"
    (parameterize ([current-naming 'linear])
      (define gen (λ () (rnd-int 0 10)))
      (define fake (hash 0 (entry 'cont '(0.0 1.0) 0.5)))
      (define s (play gen fake))
      (check-true (exact-integer? (sol-pheno s)))
      (check-true (<= 0 (sol-pheno s) 10))))

  ;; ---------------- Stage 2: coarse operators ----------------
  (test-case "stage 2 coarse operators"
    (parameterize ([current-naming 'linear])
      (define (gen) (for/list ([i (in-range 10)]) (rnd-choice '(0 1))))

      (define s (create-ind gen))
      (check-true (sol? s))
      (check-equal? (length (sol-pheno s)) 10)

      (define s1 (create-ind gen))
      (define sm (mutate-point gen s1))
      (check-equal? (list->set (hash-keys (sol-geno s1)))
                    (list->set (hash-keys (sol-geno sm))))

      (define s2 (create-ind gen))
      (define sx (crossover-uniform gen s1 s2))
      (check-equal? (list->set (hash-keys (sol-geno sx)))
                    (list->set (hash-keys (sol-geno s1))))

      (define alignment (align-traces s1 s2))
      (for ([k alignment])
        (define v  (entry-val (hash-ref (sol-geno sx) k)))
        (define v1 (entry-val (hash-ref (sol-geno s1) k)))
        (define v2 (entry-val (hash-ref (sol-geno s2) k)))
        (check-true (or (equal? v v1) (equal? v v2))
                    (format "key ~a: ~a not in {~a, ~a}" k v v1 v2)))

      (define s3 (play gen (sol-geno s1)))
      (check-equal? (distance-ind s1 s3) 0.0)

      (define s4 (create-ind gen))
      (check-true (>= (distance-ind s1 s4) 0.0))))

  (test-case "crossover-one-point keeps parent key set"
    (parameterize ([current-naming 'linear])
      (define (gen) (for/list ([i (in-range 8)]) (rnd-int 0 9)))
      (define s1 (create-ind gen))
      (define s2 (create-ind gen))
      (define sx (crossover-one-point gen s1 s2))
      (check-equal? (list->set (hash-keys (sol-geno sx)))
                    (list->set (hash-keys (sol-geno s1))))))

  ;; ---------------- Stage 3: structured naming ----------------
  (test-case "structured names are strings starting with root/"
    (parameterize ([current-naming 'structured])
      (define-generator (check-format-gen)
        (list (rnd-choice '(a b)) (rnd-real 0.0 1.0) (rnd-int 1 10)))
      (define s (play check-format-gen #hash()))
      (check-equal? (length (hash-keys (sol-geno s))) 3)
      (for ([k (hash-keys (sol-geno s))])
        (check-true (string? k) "name must be a string")
        (check-true (string-prefix? k "root/") "name must start with root/"))))

  (test-case "same generator -> same names across runs"
    (parameterize ([current-naming 'structured])
      (define-generator (stable-gen)
        (list (rnd-choice '(a b)) (rnd-int 0 9)))
      (define s1 (play stable-gen #hash()))
      (define s2 (play stable-gen #hash()))
      (check-equal? (sol-key-order s1) (sol-key-order s2))))

  (test-case "loop: each iteration distinct name"
    (parameterize ([current-naming 'structured])
      (define-generator (loop-gen n)
        (for/list ([i (in-range n)]) (rnd-choice '(0 1))))
      (define s (play (λ () (loop-gen 5)) #hash()))
      (check-equal? (length (hash-keys (sol-geno s))) 5)
      (check-equal? (length (sol-key-order s))
                    (set-count (list->set (sol-key-order s)))
                    "all structured names must be distinct")))

  (test-case "nested loops: n*m distinct names"
    (parameterize ([current-naming 'structured])
      (define-generator (nested-gen n m)
        (for/list ([i (in-range n)])
          (for/list ([j (in-range m)])
            (rnd-choice '(0 1)))))
      (define s (play (λ () (nested-gen 3 4)) #hash()))
      (check-equal? (length (hash-keys (sol-geno s))) 12)))

  (test-case "nested helper: two call sites -> two names"
    (parameterize ([current-naming 'structured])
      (define-generator (helper-gen)
        (define (flip) (rnd-choice '(0 1)))
        (list (flip) (flip)))
      (define s (play helper-gen #hash()))
      (check-equal? (length (hash-keys (sol-geno s))) 2)
      (check-equal? (length (sol-key-order s))
                    (set-count (list->set (sol-key-order s))))))

  (test-case "structured naming + replay deterministic"
    (parameterize ([current-naming 'structured])
      (define-generator (s-onemax n)
        (for/list ([i (in-range n)]) (rnd-choice '(0 1))))
      (define s1 (play (λ () (s-onemax 10)) #hash()))
      (define s2 (play (λ () (s-onemax 10)) (sol-geno s1)))
      (check-equal? (sol-pheno s1) (sol-pheno s2))))

  (test-case "loop name carries iteration index"
    (parameterize ([current-naming 'structured])
      (define-generator (idx-gen n)
        (for/list ([i (in-range n)]) (rnd-choice '(0 1))))
      (define s (play (λ () (idx-gen 10)) #hash()))
      (define names (sol-key-order s))
      (check-false (equal? (list-ref names 3) (list-ref names 7)))))

  ;; ---------------- Stage 4: fine distributions ----------------
  (test-case "fine mutation cont: in bounds, type preserved"
    (for ([_ (in-range 50)])
      (define e2 (entry-mutate (entry 'cont '(0.0 10.0) 5.0) 'fine))
      (check-true (<= 0.0 (entry-val e2) 10.0))
      (check-equal? (entry-type e2) 'cont)))

  (test-case "fine mutation int: +/-1 away from boundary"
    (let ([e2 (entry-mutate (entry 'int '(0 10) 5) 'fine)])
      (check-true (<= 0 (entry-val e2) 10))
      (check-not-false (member (- (entry-val e2) 5) '(-1 1)))))

  (test-case "fine mutation int at boundaries stays in range"
    (for ([_ (in-range 20)])
      (check-true (<= 0 (entry-val (entry-mutate (entry 'int '(0 10) 0) 'fine)) 10)))
    (for ([_ (in-range 20)])
      (check-true (<= 0 (entry-val (entry-mutate (entry 'int '(0 10) 10) 'fine)) 10))))

  (test-case "fine crossover cont: result between parents"
    (for ([_ (in-range 50)])
      (define ex (entry-crossover (entry 'cont '(0.0 10.0) 2.0)
                                  (entry 'cont '(0.0 10.0) 8.0) 'fine))
      (check-true (<= 2.0 (entry-val ex) 8.0))
      (check-equal? (entry-type ex) 'cont)))

  (test-case "fine repair: cont clamp"
    (define r (entry-replay (entry 'cont '(0.0 50.0) #f)
                            (entry 'cont '(0.0 100.0) 75.0) 'fine))
    (check-equal? (entry-val r) 50.0))

  (test-case "fine repair: int round+clamp"
    (define r (entry-replay (entry 'int '(0 50) #f)
                            (entry 'int '(0 100) 73) 'fine))
    (check-equal? (entry-val r) 50))

  (test-case "fine repair: cat reuse if valid"
    (define r (entry-replay (entry 'cat '((b c d)) #f)
                            (entry 'cat '((a b c)) 'b) 'fine))
    (check-equal? (entry-val r) 'b))

  (test-case "fine repair: cat resample if invalid"
    (define r (entry-replay (entry 'cat '((x y z)) #f)
                            (entry 'cat '((a b c)) 'a) 'fine))
    (check-not-false (member (entry-val r) '(x y z))))

  (test-case "coarse repair: resamples (ignores old) on param change"
    (define r (entry-replay (entry 'cont '(0.0 50.0) #f)
                            (entry 'cont '(0.0 100.0) 75.0) 'coarse))
    (check-true (<= 0.0 (entry-val r) 50.0)))

  ;; ---------------- Stage 5: hill-climber + run ----------------
  (define-generator (om-gen n)
    (for/list ([i (in-range n)]) (rnd-choice '(0 1))))

  (test-case "hill-climber improves ONEMAX"
    (parameterize ([current-naming 'linear])
      (define-values (best fit)
        (hill-climber (λ () (om-gen 20)) (λ (pheno) (apply + pheno)) > 300))
      (check-true (> fit 14) "hill-climber should beat random on ONEMAX-20")))

  (test-case "run API basic (linear, coarse)"
    (define-values (rb rf)
      (run om-gen (λ (pheno) (apply + pheno))
           #:better > #:naming 'linear #:dist-mode 'coarse
           #:n-iterations 300 #:gen-args '(20)))
    (check-true (sol? rb))
    (check-true (real? rf)))

  (test-case "run with structured naming"
    (define-values (sb sf)
      (run om-gen (λ (pheno) (apply + pheno))
           #:better > #:naming 'structured #:dist-mode 'coarse
           #:n-iterations 300 #:gen-args '(20)))
    (check-true (sol? sb)))

  (define-generator (sp-gen n)
    (for/list ([i (in-range n)]) (rnd-real -5.0 5.0)))

  (test-case "run fine on sphere (maximise -sum sq)"
    (define-values (spb spf)
      (run sp-gen (λ (pheno) (- (apply + (map (λ (x) (* x x)) pheno))))
           #:better > #:naming 'linear #:dist-mode 'fine
           #:n-iterations 500 #:gen-args '(5)))
    (check-true (> spf -1.0) "fine hill-climber should get sphere close to 0"))

  (test-case "run minimisation (better = <)"
    (define-values (mb mf)
      (run sp-gen (λ (pheno) (apply + (map (λ (x) (* x x)) pheno)))
           #:better < #:naming 'linear #:dist-mode 'fine
           #:n-iterations 500 #:gen-args '(5)))
    (check-true (< mf 1.0))))
