/**
 * Tests for run.js — Top-level PTO orchestrator.
 *
 * Covers:
 *   - searchOperators mode returns Op instance
 *   - Op from run works: createInd, evaluateInd, mutateInd, crossoverInd
 *   - OneMax end-to-end smoke test: repeated mutation improves fitness
 *   - Unknown solver throws
 *   - Multiple problem types (binary, integer, sequence)
 *   - Structural naming mode: keys are hierarchical strings
 *   - Both naming modes produce same-quality optimization
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { run } from '../src/run.js';
import { Op } from '../src/operators.js';

// ---------------------------------------------------------------------------
// searchOperators mode
// ---------------------------------------------------------------------------
describe('run() searchOperators mode', () => {
  it('returns an Op instance', () => {
    const op = run(
      (rnd) => [rnd.choice([0, 1]), rnd.choice([0, 1])],
      (pheno) => pheno.reduce((a, b) => a + b, 0),
    );
    assert.ok(op instanceof Op);
  });

  it('Op can createInd and evaluateInd', () => {
    const op = run(
      (rnd) => [rnd.choice([0, 1]), rnd.choice([0, 1]), rnd.choice([0, 1])],
      (pheno) => pheno.reduce((a, b) => a + b, 0),
    );
    const sol = op.createInd();
    assert.equal(sol.pheno.length, 3);
    const fx = op.evaluateInd(sol);
    assert.equal(fx, sol.pheno.reduce((a, b) => a + b, 0));
  });

  it('Op can mutate and crossover', () => {
    const op = run(
      (rnd) => [rnd.choice([0, 1]), rnd.choice([0, 1])],
      (pheno) => pheno.reduce((a, b) => a + b, 0),
    );
    const sol1 = op.createInd();
    const sol2 = op.createInd();
    const mutated = op.mutatePointInd(sol1);
    const crossed = op.crossoverUniformInd(sol1, sol2);
    assert.equal(mutated.pheno.length, 2);
    assert.equal(crossed.pheno.length, 2);
  });
});

// ---------------------------------------------------------------------------
// OneMax end-to-end smoke test
// ---------------------------------------------------------------------------
describe('OneMax smoke test', () => {
  it('repeated point mutation can improve fitness', () => {
    const SIZE = 20;
    const op = run(
      (rnd) => {
        const bits = [];
        for (let i = 0; i < SIZE; i++) bits.push(rnd.choice([0, 1]));
        return bits;
      },
      (pheno) => pheno.reduce((a, b) => a + b, 0),
    );

    let best = op.createInd();
    let bestFx = op.evaluateInd(best);

    for (let iter = 0; iter < 200; iter++) {
      const child = op.mutatePointInd(best);
      const childFx = op.evaluateInd(child);
      if (childFx >= bestFx) {
        best = child;
        bestFx = childFx;
      }
    }

    // After 200 iterations of hill climbing on a 20-bit OneMax,
    // we should reach at least 15 (very likely optimal 20)
    assert.ok(bestFx >= 15, `expected fitness >= 15, got ${bestFx}`);
  });
});

// ---------------------------------------------------------------------------
// Multiple problem types
// ---------------------------------------------------------------------------
describe('run() with different problem types', () => {
  it('integer-valued problem (Sphere)', () => {
    const op = run(
      (rnd) => {
        const vec = [];
        for (let i = 0; i < 5; i++) vec.push(rnd.randint(-10, 10));
        return vec;
      },
      (pheno) => pheno.reduce((s, x) => s + x * x, 0),
    );
    const sol = op.createInd();
    assert.equal(sol.pheno.length, 5);
    const fx = op.evaluateInd(sol);
    assert.ok(fx >= 0);
  });

  it('real-valued problem', () => {
    const op = run(
      (rnd) => [rnd.uniform(-5, 5), rnd.uniform(-5, 5)],
      (pheno) => pheno.reduce((s, x) => s + x * x, 0),
    );
    const sol = op.createInd();
    assert.equal(sol.pheno.length, 2);
  });

  it('sequence-valued problem (permutation)', () => {
    const cities = [0, 1, 2, 3, 4];
    const op = run(
      (rnd) => rnd.sample(cities, cities.length),
      (pheno) => {
        // Dummy fitness: sum of indices
        return pheno.reduce((s, c, i) => s + Math.abs(c - i), 0);
      },
    );
    const sol = op.createInd();
    assert.equal(sol.pheno.length, 5);
    assert.deepEqual([...sol.pheno].sort(), [0, 1, 2, 3, 4]);
  });
});

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Structural naming mode
// ---------------------------------------------------------------------------
describe('run() with structural naming', () => {
  it('produces structural trace keys (strings starting with root/)', () => {
    const op = run(
      function gen(rnd) {
        const bits = [];
        for (let i = 0; i < 5; i++) bits.push(rnd.choice([0, 1]));
        return bits;
      },
      (pheno) => pheno.reduce((a, b) => a + b, 0),
      { naming: 'structural' },
    );
    const sol = op.createInd();
    const keys = Object.keys(sol.geno);
    assert.equal(keys.length, 5);
    for (const key of keys) {
      assert.ok(typeof key === 'string', `key should be string, got ${typeof key}`);
      assert.ok(key.startsWith('root/'), `key "${key}" should start with root/`);
      assert.ok(key.includes('choice'), `key "${key}" should contain method name`);
    }
  });

  it('structural naming supports mutation and crossover', () => {
    const op = run(
      function gen(rnd) {
        const bits = [];
        for (let i = 0; i < 10; i++) bits.push(rnd.choice([0, 1]));
        return bits;
      },
      (pheno) => pheno.reduce((a, b) => a + b, 0),
      { naming: 'structural' },
    );
    const sol1 = op.createInd();
    const sol2 = op.createInd();
    const mutated = op.mutatePointInd(sol1);
    const crossed = op.crossoverUniformInd(sol1, sol2);
    assert.equal(mutated.pheno.length, 10);
    assert.equal(crossed.pheno.length, 10);
  });

  it('structural naming hill climber improves OneMax', () => {
    const op = run(
      function gen(rnd) {
        const bits = [];
        for (let i = 0; i < 20; i++) bits.push(rnd.choice([0, 1]));
        return bits;
      },
      (pheno) => pheno.reduce((a, b) => a + b, 0),
      { naming: 'structural' },
    );

    let best = op.createInd();
    let bestFx = op.evaluateInd(best);
    for (let iter = 0; iter < 200; iter++) {
      const child = op.mutatePointInd(best);
      const childFx = op.evaluateInd(child);
      if (childFx >= bestFx) { best = child; bestFx = childFx; }
    }
    assert.ok(bestFx >= 15, `expected >= 15, got ${bestFx}`);
  });

  it('linear naming produces integer keys', () => {
    const op = run(
      (rnd) => [rnd.choice([0, 1]), rnd.choice([0, 1])],
      (pheno) => pheno.reduce((a, b) => a + b, 0),
      { naming: 'linear' },
    );
    const sol = op.createInd();
    const keys = Object.keys(sol.geno);
    for (const key of keys) {
      assert.ok(!key.startsWith('root/'), `linear key "${key}" should not start with root/`);
    }
  });

  it('unknown naming mode throws', () => {
    assert.throws(
      () => run(
        (rnd) => rnd.choice([0, 1]),
        (v) => v,
        { naming: 'bogus' },
      ),
      { message: /Unknown naming mode/ },
    );
  });
});

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------
describe('run() error handling', () => {
  it('unknown solver throws', () => {
    assert.throws(
      () => run(
        (rnd) => rnd.choice([0, 1]),
        (v) => v,
        { solver: 'nonexistent' },
      ),
      { message: /Unknown solver/ },
    );
  });
});
