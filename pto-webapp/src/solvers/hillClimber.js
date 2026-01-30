/**
 * hillClimber.js — Simple hill climbing local search.
 *
 * Starts from a random solution and iteratively mutates it.
 * Keeps the mutant only if it is at least as good as the current best.
 * This is the default solver in PTO — fast, simple, effective for
 * unimodal landscapes.
 *
 * Mirrors Python PTO's pto/solvers/hill_climber.py.
 *
 * @param {Op}      op                      Search operators instance
 * @param {Object}  [opts]
 * @param {number}  [opts.nIteration=1000]  Number of iterations
 * @param {string}  [opts.mutation='mutatePositionWiseInd']  Mutation operator name
 * @param {Function} [opts.better=Math.max] Comparison function
 * @param {Function} [opts.callback]        Called each iteration with { sol, fitness, iteration }
 * @param {boolean}  [opts.returnHistory=false]  If true, return history array
 * @returns {{ sol: { pheno, geno }, fitness: number, history?: Array }}
 */
export function hillClimber(op, {
  nIteration = 1000,
  mutation = 'mutatePositionWiseInd',
  better = Math.max,
  callback,
  returnHistory = false,
} = {}) {
  let current = op.createInd();
  let currentFx = op.evaluateInd(current);

  const history = returnHistory ? [{ sol: current, fitness: currentFx, iteration: 0 }] : null;

  for (let i = 1; i <= nIteration; i++) {
    const candidate = op[mutation](current);
    const candidateFx = op.evaluateInd(candidate);

    // Accept if candidate is at least as good (allows neutral drift)
    if (better(currentFx, candidateFx) === candidateFx) {
      current = candidate;
      currentFx = candidateFx;
    }

    if (callback) callback({ sol: current, fitness: currentFx, iteration: i });
    if (history) history.push({ sol: current, fitness: currentFx, iteration: i });
  }

  const result = { sol: current, fitness: currentFx };
  if (returnHistory) result.history = history;
  return result;
}
