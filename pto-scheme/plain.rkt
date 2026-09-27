#lang racket
;; pto/plain — drop-in stubs. Swap (require "pto.rkt") for (require "pto/plain.rkt")
;; to run any generator as ordinary Racket: no trace, no operators, just rng.
(provide define-generator rnd-choice rnd-real rnd-int)

;; `formals` as in `define`, like pto.rkt's define-generator
(define-syntax-rule (define-generator (name . formals) body ...)
  (define (name . formals) body ...))

(define (rnd-choice seq)
  (when (null? seq) (error 'rnd-choice "empty sequence"))
  (list-ref seq (random (length seq))))

(define (rnd-real lo hi)
  (+ lo (* (random) (- hi lo))))

(define (rnd-int lo hi)
  (when (> lo hi) (error 'rnd-int "lo > hi: ~a > ~a" lo hi))
  (+ lo (random (add1 (- hi lo)))))
