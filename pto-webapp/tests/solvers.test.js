/**
 * Tests for PTO solvers: hill climber, random search, genetic algorithm.
 * Uses the OneMax problem (maximize sum of binary string) as a simple
 * test case where we can verify optimization is happening.
 */
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

import { run } from '../src/run.js';
import { hillClimber } from '../src/solvers/hillClimber.js';
import { randomSearch } from '../src/solvers/randomSearch.js';
import { geneticAlgorithm } from '../src/solvers/geneticAlgorithm.js';

// OneMax: maximize sum of 20-bit binary string
const SIZE = 20;
const generator = (rnd) => {
  const bits = [];
  for (let i = 0; i < SIZE; i++) bits.push(rnd.choice([0, 1]));
  return bits;
};
const fitness = (pheno) => pheno.reduce((a, b) => a + b, 0);

// Helper: get an Op instance
function makeOp(opts = {}) {
  return run(generator, fitness, { better: Math.max, solver: 'searchOperators', ...opts });
}

// ── Hill Climber ──────────────────────────────────────────────

describe('hillClimber', () => {
  it('returns a solution with fitness', () => {
    const op = makeOp();
    const result = hillClimber(op, { nIteration: 10, better: Math.max });
    assert.ok(result.sol);
    assert.ok(result.sol.pheno);
    assert.ok(result.sol.geno);
    assert.equal(typeof result.fitness, 'number');
  });

  it('improves over random initial solution', () => {
    const op = makeOp();
    // With 200 iterations on 20 bits, should beat random (expected ~10)
    const result = hillClimber(op, { nIteration: 200, better: Math.max });
    assert.ok(result.fitness > 10, `Expected fitness > 10, got ${result.fitness}`);
  });

  it('works with minimization', () => {
    const op = makeOp();
    const result = hillClimber(op, { nIteration: 200, better: Math.min });
    assert.ok(result.fitness < 10, `Expected fitness < 10, got ${result.fitness}`);
  });

  it('supports returnHistory', () => {
    const op = makeOp();
    const result = hillClimber(op, { nIteration: 10, better: Math.max, returnHistory: true });
    assert.ok(Array.isArray(result.history));
    assert.equal(result.history.length, 11); // initial + 10 iterations
    assert.equal(result.history[0].iteration, 0);
    assert.equal(result.history[10].iteration, 10);
  });

  it('calls callback each iteration', () => {
    const op = makeOp();
    let count = 0;
    hillClimber(op, { nIteration: 5, better: Math.max, callback: () => count++ });
    assert.equal(count, 5);
  });

  it('history fitness is monotonically non-decreasing (max)', () => {
    const op = makeOp();
    const result = hillClimber(op, { nIteration: 50, better: Math.max, returnHistory: true });
    for (let i = 1; i < result.history.length; i++) {
      assert.ok(result.history[i].fitness >= result.history[i - 1].fitness);
    }
  });

  it('accepts custom mutation operator', () => {
    const op = makeOp();
    const result = hillClimber(op, { nIteration: 10, mutation: 'mutatePointInd', better: Math.max });
    assert.equal(typeof result.fitness, 'number');
  });

  it('works with fine distributions', () => {
    const op = makeOp({ distType: 'fine' });
    const result = hillClimber(op, { nIteration: 100, better: Math.max });
    assert.ok(result.fitness > 10, `Expected fitness > 10 with fine, got ${result.fitness}`);
  });
});

// ── Random Search ─────────────────────────────────────────────

describe('randomSearch', () => {
  it('returns a solution with fitness', () => {
    const op = makeOp();
    const result = randomSearch(op, { nIteration: 10, better: Math.max });
    assert.ok(result.sol);
    assert.equal(typeof result.fitness, 'number');
  });

  it('best fitness equals best of many random samples', () => {
    const op = makeOp();
    const result = randomSearch(op, { nIteration: 100, better: Math.max, returnHistory: true });
    const maxInHistory = Math.max(...result.history.map(h => h.fitness));
    assert.equal(result.fitness, maxInHistory);
  });

  it('supports returnHistory', () => {
    const op = makeOp();
    const result = randomSearch(op, { nIteration: 20, better: Math.max, returnHistory: true });
    assert.equal(result.history.length, 21);
  });
});

// ── Genetic Algorithm ─────────────────────────────────────────

describe('geneticAlgorithm', () => {
  it('returns a solution with fitness', () => {
    const op = makeOp();
    const result = geneticAlgorithm(op, {
      populationSize: 10, nGeneration: 5, better: Math.max,
    });
    assert.ok(result.sol);
    assert.equal(typeof result.fitness, 'number');
  });

  it('improves over random initial population', () => {
    const op = makeOp();
    const result = geneticAlgorithm(op, {
      populationSize: 20, nGeneration: 30, better: Math.max,
    });
    assert.ok(result.fitness > 10, `Expected GA fitness > 10, got ${result.fitness}`);
  });

  it('works with minimization', () => {
    const op = makeOp();
    const result = geneticAlgorithm(op, {
      populationSize: 20, nGeneration: 30, better: Math.min,
    });
    assert.ok(result.fitness < 10, `Expected GA min fitness < 10, got ${result.fitness}`);
  });

  it('supports returnHistory', () => {
    const op = makeOp();
    const result = geneticAlgorithm(op, {
      populationSize: 10, nGeneration: 5, better: Math.max, returnHistory: true,
    });
    assert.ok(Array.isArray(result.history));
    assert.equal(result.history.length, 6); // initial + 5 generations
  });

  it('history fitness is monotonically non-decreasing (elitism)', () => {
    const op = makeOp();
    const result = geneticAlgorithm(op, {
      populationSize: 10, nGeneration: 20, better: Math.max, returnHistory: true,
    });
    for (let i = 1; i < result.history.length; i++) {
      assert.ok(result.history[i].fitness >= result.history[i - 1].fitness,
        `Gen ${i}: ${result.history[i].fitness} < ${result.history[i - 1].fitness}`);
    }
  });

  it('calls callback each generation', () => {
    const op = makeOp();
    let count = 0;
    geneticAlgorithm(op, {
      populationSize: 10, nGeneration: 5, better: Math.max, callback: () => count++,
    });
    assert.equal(count, 5);
  });

  it('works with fine distributions', () => {
    const op = makeOp({ distType: 'fine' });
    const result = geneticAlgorithm(op, {
      populationSize: 20, nGeneration: 20, better: Math.max,
    });
    assert.ok(result.fitness > 10, `Expected GA fine fitness > 10, got ${result.fitness}`);
  });

  it('works with structural naming', () => {
    // Structural naming compiles the generator, so it can't capture closures.
    // Use a self-contained generator with literal values.
    const structGen = (rnd) => {
      const bits = [];
      for (let i = 0; i < 10; i++) bits.push(rnd.choice([0, 1]));
      return bits;
    };
    const op = run(structGen, (p) => p.reduce((a, b) => a + b, 0), {
      better: Math.max, naming: 'structural', solver: 'searchOperators',
    });
    const result = geneticAlgorithm(op, {
      populationSize: 10, nGeneration: 10, better: Math.max,
    });
    assert.equal(typeof result.fitness, 'number');
  });
});

// ── Integration via run() ─────────────────────────────────────

describe('run() solver dispatch', () => {
  it('dispatches to hillClimber', () => {
    const result = run(generator, fitness, {
      better: Math.max, solver: 'hillClimber', nIteration: 10,
    });
    assert.ok(result.sol);
    assert.equal(typeof result.fitness, 'number');
  });

  it('dispatches to randomSearch', () => {
    const result = run(generator, fitness, {
      better: Math.max, solver: 'randomSearch', nIteration: 10,
    });
    assert.ok(result.sol);
  });

  it('dispatches to geneticAlgorithm', () => {
    const result = run(generator, fitness, {
      better: Math.max, solver: 'geneticAlgorithm', populationSize: 10, nGeneration: 5,
    });
    assert.ok(result.sol);
  });

  it('throws on unknown solver', () => {
    assert.throws(() => run(generator, fitness, { solver: 'bogus' }), /Unknown solver/);
  });

  it('passes solver args through', () => {
    const result = run(generator, fitness, {
      better: Math.max, solver: 'hillClimber', nIteration: 5, returnHistory: true,
    });
    assert.ok(Array.isArray(result.history));
    assert.equal(result.history.length, 6);
  });
});
