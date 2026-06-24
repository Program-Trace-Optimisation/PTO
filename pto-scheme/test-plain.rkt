#lang racket
(require "plain.rkt")
(require rackunit)

(define-generator (onemax n)
  (for/list ([i (in-range n)])
    (rnd-choice '(0 1))))

(module+ test
  (test-case "plain onemax runs with no PTO infrastructure"
    (define result (onemax 10))
    (check-equal? (length result) 10)
    (check-true (andmap (λ (x) (and (member x '(0 1)) #t)) result)))

  (define-generator (mixed n)
    (for/list ([i (in-range n)])
      (list (rnd-choice '(a b c))
            (rnd-real 0.0 1.0)
            (rnd-int 1 6))))

  (test-case "plain mixed types"
    (define r (mixed 5))
    (check-equal? (length r) 5)
    (for ([elem r])
      (check-not-false (member (first elem) '(a b c)))
      (check-true (<= 0.0 (second elem) 1.0))
      (check-true (<= 1 (third elem) 6))))

  (define-generator (tsp-plain)
    (define cities '(A B C D E))
    (define (pick rem)
      (list-ref rem (rnd-int 0 (sub1 (length rem)))))
    (let loop ([rem cities] [tour '()])
      (if (null? rem) (reverse tour)
          (let ([c (pick rem)])
            (loop (remove c rem) (cons c tour))))))

  (test-case "plain nested helper + named let compiles and runs"
    (define tour (tsp-plain))
    (check-equal? (length tour) 5)
    (check-equal? (list->set tour) (list->set '(A B C D E)))))
