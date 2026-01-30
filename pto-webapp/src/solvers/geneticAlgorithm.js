/**
 * geneticAlgorithm.js — Generational GA with truncation selection and elitism.
 *
 * Each generation:
 *   1. Sort population by fitness
 *   2. Keep top fraction (truncation selection)
 *   3. Fill remaining slots by crossover of randomly chosen parents
 *   4. Apply mutation with probability mutationRate
 *   5. Elitism: always keep the best individual
 *
 * Mirrors Python PTO's pto/solvers/genetic_algorithm.py.
 *
 * @param {Op}      op                            Search operators instance
 * @param {Object}  [opts]
 * @param {number}  [opts.populationSize=50]      Population size
 * @param {number}  [opts.nGeneration=100]        Number of generations
 * @param {number}  [opts.truncationRate=0.5]     Fraction selected as parents
 * @param {number}  [opts.mutationRate=0.05]      Per-individual mutation probability
 * @param {string}  [opts.mutation='mutatePositionWiseInd']  Mutation operator
 * @param {string}  [opts.crossover='crossoverUniformInd']   Crossover operator
 * @param {Function} [opts.better=Math.max]       Comparison function
 * @param {Function} [opts.callback]              Called each generation
 * @param {boolean}  [opts.returnHistory=false]
 * @returns {{ sol: { pheno, geno }, fitness: number, history?: Array }}
 */
export function geneticAlgorithm(op, {
  populationSize = 50,
  nGeneration = 100,
  truncationRate = 0.5,
  mutationRate = 0.05,
  mutation = 'mutatePositionWiseInd',
  crossover = 'crossoverUniformInd',
  better = Math.max,
  callback,
  returnHistory = false,
} = {}) {
  const isMax = better === Math.max;

  // Helper: sort population by fitness (best first)
  function sortPop(pop) {
    pop.sort((a, b) => isMax ? b.fx - a.fx : a.fx - b.fx);
  }

  // Initialize population
  let pop = [];
  for (let i = 0; i < populationSize; i++) {
    const sol = op.createInd();
    pop.push({ sol, fx: op.evaluateInd(sol) });
  }
  sortPop(pop);

  const history = returnHistory ? [{ sol: pop[0].sol, fitness: pop[0].fx, generation: 0 }] : null;

  for (let gen = 1; gen <= nGeneration; gen++) {
    // Truncation selection: keep top fraction as parents
    const nParents = Math.max(2, Math.floor(populationSize * truncationRate));
    const parents = pop.slice(0, nParents);

    // Elite: best individual always survives
    const elite = pop[0];

    // Generate offspring
    const nextPop = [elite]; // elitism
    while (nextPop.length < populationSize) {
      // Pick two random parents
      const p1 = parents[Math.floor(Math.random() * nParents)];
      const p2 = parents[Math.floor(Math.random() * nParents)];

      // Crossover
      let child = op[crossover](p1.sol, p2.sol);

      // Mutation with probability
      if (Math.random() < mutationRate) {
        child = op[mutation](child);
      }

      const fx = op.evaluateInd(child);
      nextPop.push({ sol: child, fx });
    }

    pop = nextPop;
    sortPop(pop);

    if (callback) callback({ sol: pop[0].sol, fitness: pop[0].fx, generation: gen });
    if (history) history.push({ sol: pop[0].sol, fitness: pop[0].fx, generation: gen });
  }

  const result = { sol: pop[0].sol, fitness: pop[0].fx };
  if (returnHistory) result.history = history;
  return result;
}
