/**
 * run.js — Top-level orchestrator for PTO.
 *
 * The run() function is the main entry point. It wires together the tracer,
 * rnd, and Op, then dispatches to a solver. This mirrors the Python PTO API:
 *
 *   const result = run(generator, fitness, { better: Math.max, solver: 'hillClimber' });
 *
 * Naming modes:
 *   - 'linear' (default): Trace keys are sequential integers (0, 1, 2, ...).
 *     Simple and works everywhere. No structural information.
 *
 *   - 'structural': Trace keys are hierarchical strings derived from the
 *     generator's source code via AST compilation:
 *       root/generator@1.0/for@3.4:0/choice@4.8
 *     Enables program-flow-aware crossover and meaningful trace inspection.
 *
 * The generator function receives `rnd` as its first argument so it can call
 * rnd.choice(), rnd.randint(), etc. This is the JS equivalent of Python PTO's
 * global `rnd` import.
 *
 * @example
 *   // Linear naming (default)
 *   const op = run(
 *     (rnd) => [rnd.choice([0, 1]), rnd.choice([0, 1])],
 *     (pheno) => pheno.reduce((a, b) => a + b, 0),
 *   );
 *
 * @example
 *   // Structural naming
 *   const op = run(
 *     (rnd) => [rnd.choice([0, 1]), rnd.choice([0, 1])],
 *     (pheno) => pheno.reduce((a, b) => a + b, 0),
 *     { naming: 'structural' }
 *   );
 */

import { Tracer } from './tracer.js';
import { createRnd } from './rnd.js';
import { Op } from './operators.js';
import { compileGenerator } from './compiler.js';
import { hillClimber } from './solvers/hillClimber.js';
import { randomSearch } from './solvers/randomSearch.js';
import { geneticAlgorithm } from './solvers/geneticAlgorithm.js';

/**
 * Create and run a PTO optimization.
 *
 * @param {Function} generator  Generator function: (rnd) => solution.
 *                              Must use rnd methods for all random decisions.
 * @param {Function} fitness    Fitness function: (phenotype) => number.
 * @param {Object}   [opts]
 * @param {Function} [opts.better=Math.max]  Comparison: Math.max or Math.min.
 * @param {string}   [opts.naming='linear']  Naming mode: 'linear' or 'structural'.
 * @param {string}   [opts.distType='coarse']  Distribution mode: 'coarse' or 'fine'.
 * @param {string}   [opts.solver='searchOperators']  Solver name.
 * @returns {Op}  (Currently always returns the Op instance.)
 */
export function run(generator, fitness, { better = Math.max, naming = 'linear', distType = 'coarse', solver = 'searchOperators', ...solverArgs } = {}) {
  if (distType !== 'coarse' && distType !== 'fine') {
    throw new Error(`Unknown distType: '${distType}'. Use 'coarse' or 'fine'.`);
  }

  const tracer = new Tracer();
  const rnd = createRnd(tracer, { distType });

  let gen;
  if (naming === 'structural') {
    // Compile the generator to inject structural name= arguments
    const compiled = compileGenerator(generator);
    gen = () => compiled(rnd);
  } else if (naming === 'linear') {
    // Linear naming: tracer auto-assigns integer keys
    gen = () => generator(rnd);
  } else {
    throw new Error(`Unknown naming mode: '${naming}'. Use 'linear' or 'structural'.`);
  }

  const op = new Op(gen, fitness, { tracer });

  if (solver === 'searchOperators') {
    return op;
  }

  const solverOpts = { better, ...solverArgs };

  const solvers = {
    hillClimber,
    randomSearch,
    geneticAlgorithm,
  };

  if (!(solver in solvers)) {
    throw new Error(`Unknown solver: '${solver}'. Available: ${Object.keys(solvers).join(', ')}, searchOperators`);
  }

  return solvers[solver](op, solverOpts);
}
