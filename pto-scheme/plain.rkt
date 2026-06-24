#lang racket
;; pto/plain — drop-in stubs. Swap (require "pto.rkt") for (require "pto/plain.rkt")
;; to run any generator as ordinary Racket: no trace, no operators, just rng.
(provide define-generator rnd-choice rnd-real rnd-int)

(define-syntax-rule (define-generator (name args ...) body ...)
  (define (name args ...) body ...))

(define (rnd-choice seq)
  (list-ref seq (random (length seq))))

(define (rnd-real lo hi)
  (+ lo (* (random) (- hi lo))))

(define (rnd-int lo hi)
  (+ lo (random (add1 (- hi lo)))))
