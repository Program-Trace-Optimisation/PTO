/**
 * randomSearch.js — Pure random sampling baseline.
 *
 * Generates nIteration random solutions, keeps the best.
 * Implemented as hill climber with mutateRandomInd — each "mutation"
 * ignores the parent and creates a fresh random solution.
 *
 * Mirrors Python PTO's pto/solvers/random_search.py.
 *
 * @param {Op}      op                      Search operators instance
 * @param {Object}  [opts]
 * @param {number}  [opts.nIteration=1000]  Number of random samples
 * @param {Function} [opts.better=Math.max] Comparison function
 * @param {Function} [opts.callback]        Called each iteration
 * @param {boolean}  [opts.returnHistory=false]
 * @returns {{ sol: { pheno, geno }, fitness: number, history?: Array }}
 */
import { hillClimber } from './hillClimber.js';

export function randomSearch(op, {
  nIteration = 1000,
  better = Math.max,
  callback,
  returnHistory = false,
} = {}) {
  return hillClimber(op, {
    nIteration,
    mutation: 'mutateRandomInd',
    better,
    callback,
    returnHistory,
  });
}
