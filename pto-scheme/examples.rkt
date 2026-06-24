#lang racket
(require "pto.rkt"
         plot
         racket/gui/base)

;; ===========================================================================
;; SYSTEM CONFIGURATION SELECTOR
;; Change this symbol to switch the target optimization environment:
;;   'onemax -> Binary bitstring maximization (Length: 40)
;;   'tsp    -> Traveling Salesperson Problem via Random-Key Permutation
;;   'gp     -> Symbolic Regression (Evolving y = x^2 + x + 2 Expression Tree)
;; ===========================================================================
(define PROBLEM-TO-RUN 'onemax)

;; ===========================================================================
;; PROBLEM DEPLOYMENT 1: ONEMAX
;; ===========================================================================

;; Generator builds a flat list of 0s and 1s. The framework's code walker
;; intercepts the `for/list` form to create clean, unique iteration trace names.
(define-generator (onemax-gen size)
  (for/list ([i (in-range size)])
    (rnd-choice '(0 1))))

;; Fitness is the total sum of elements. Global maximum score is equal to size.
(define (onemax-fitness pheno)
  (apply + pheno))

;; ===========================================================================
;; PROBLEM DEPLOYMENT 2: TRAVELING SALESPERSON (TSP)
;; ===========================================================================
(define cities '(A B C D E F G))

;; Generate an immutable, shared random cost matrix between cities
(define dist-matrix
  (let ([d (make-hash)])
    (for* ([a cities] [b cities])
      (unless (eq? a b)
        (hash-set! d (list a b) (+ 1 (random 9)))))
    d))

;; Evaluates total trip length, looping back to the starting city at the end
(define (tour-cost tour)
  (for/sum ([a tour] [b (append (rest tour) (list (first tour)))])
    (hash-ref dist-matrix (list a b) 1)))

;; Random-Key encoding avoids name collisions by avoiding manual recursive loops.
;; It builds 7 traceable float values which sort into a clean permutation.
(define-generator (tsp-gen)
  (define keys (for/list ([i (in-range (length cities))]) (rnd-real 0.0 1.0)))
  (map cdr (sort (map cons keys cities) < #:key car)))

;; Framework optimizes via maximization, so we invert the positive tour cost
(define (tsp-fitness pheno)
  (- (tour-cost pheno)))

;; ===========================================================================
;; PROBLEM DEPLOYMENT 3: GENETIC PROGRAMMING (SYMBOLIC REGRESSION)
;; ===========================================================================

;; The mathematical relationship we want the system to autonomously discover
(define (target-math-fn x) 
  (+ (* x x) x 2))

;; Tree interpreter to evaluate nested mathematical S-expressions
(define (eval-tree tree x-val)
  (cond
    [(eq? tree 'x) x-val]
    [(number? tree) tree]
    [(list? tree)
     (define op (first tree))
     (define left  (eval-tree (second tree) x-val))
     (define right (eval-tree (third tree) x-val))
     (case op
       [(+) (+ left right)]
       [(-) (- left right)]
       [(*) (* left right)]
       [else 0])]
    [else 0]))

;; Recursive structure generator. Unique code-column offsets inside the
;; branches automatically build hierarchical paths mapped directly to tree nodes.
(define-generator (gp-gen max-depth)
  (define (build d)
    (cond
      [(<= d 0)
       (case (rnd-choice '(var const))
         [(var) 'x]
         [(const) (rnd-int 1 5)])]
      [else
       (case (rnd-choice '(add sub mul leaf))
         [(leaf)
          (case (rnd-choice '(var const))
            [(var) 'x]
            [(const) (rnd-int 1 5)])]
         [(add) (list '+ (build (- d 1)) (build (- d 1)))]
         [(sub) (list '- (build (- d 1)) (build (- d 1)))]
         [(mul) (list '* (build (- d 1)) (build (- d 1)))])]))
  (build max-depth))

;; Measures error across multiple points. Returns negative total discrepancy.
(define (gp-fitness tree)
  (define sample-inputs '(-3 -2 -1 0 1 2 3))
  (define total-error
    (for/sum ([x sample-inputs])
      (abs (- (eval-tree tree x) (target-math-fn x)))))
  (- total-error))

;; ===========================================================================
;; RUNTIME DISPATCHER & GRAPHICAL INTERFACE
;; ===========================================================================

;; Extract execution constraints based on the top-level selector setting
(define-values (target-gen target-fit total-iters gen-args chart-title result-formatter)
  (case PROBLEM-TO-RUN
    [(onemax)
     (values onemax-gen onemax-fitness 400 '(40) "OneMax Convergence"
             (λ (sol) (format "Bits: ~a" (sol-pheno sol))))]
    [(tsp)
     (values tsp-gen tsp-fitness 800 '() "TSP Cost Minimization"
             (λ (sol) (format "Tour Order: ~a | Real Cost: ~a" (sol-pheno sol) (- (tsp-fitness (sol-pheno sol))))))]
    [(gp)
     (values gp-gen gp-fitness 1500 '(3) "GP Equation Discovery"
             (λ (sol) (format "Discovered Formula Tree: ~a" (sol-pheno sol))))]
    [else (error 'workbench "Unknown selection assignment: ~a" PROBLEM-TO-RUN)]))

;; Mutable repository holding our coordinate vectors: #(iteration best-fitness)
(define evolution-history '())

;; Construct standard window frame
(define display-frame 
  (new frame% 
       [label (format "PTO Engine: ~a" chart-title)] 
       [width 650] 
       [height 450]))

;; Canvas containing the official OS-isolated paint-callback loop
(define plot-canvas
  (new canvas%
       [parent display-frame]
       [paint-callback
        (λ (canvas dc)
          (define-values (width height) (send canvas get-client-size))
          (unless (null? evolution-history)
            ;; plot/dc handles Y-axis range scaling automatically when boundaries are omitted
            (plot/dc (lines evolution-history #:color "darkgreen" #:width 2.5 #:label "Fitness Over Time")
                     dc 0 0 width height
                     #:x-label "Generation Iterations"
                     #:y-label "Current Peak Fitness"
                     #:title chart-title
                     #:x-min 0 #:x-max total-iters)))]))

;; Framework engine callback hook fired on every loop alteration step
(define (iteration-tracker iter cand-fit best-fit)
  (set! evolution-history (append evolution-history (list (vector iter best-fit))))
  
  ;; Redraw the canvas graph surface every 5 steps to keep memory footprints lean
  (when (zero? (modulo iter 5))
    (queue-callback (λ () (send plot-canvas refresh)))))

;; Render GUI display window
(send display-frame show #t)

;; Kick off core system calculation pipeline
(printf "Executing system profile: [ ~a ]...\n" PROBLEM-TO-RUN)
(define-values (best-individual final-score)
  (run target-gen target-fit
       #:better >
       #:naming 'structured
       #:dist-mode 'coarse
       #:n-iterations total-iters
       #:gen-args gen-args
       #:on-iteration iteration-tracker))

;; Print operational log analytics to the console window
(printf "\n================ PROGRESSION COMPLETE ================\n")
(printf "Target Objective:   ~a\n" chart-title)
(printf "Final Score Target: ~a\n" final-score)
(printf "Decoded Phenotype:  ~a\n" (result-formatter best-individual))
(printf "------------------------------------------------------\n")
(printf "Execution Snapshot Samples (Trace Address -> Gene value):\n")
(for ([key (take (sol-key-order best-individual) (min 3 (length (sol-key-order best-individual))))])
  (printf "  ~a -> ~a\n" key (entry-val (hash-ref (sol-geno best-individual) key))))