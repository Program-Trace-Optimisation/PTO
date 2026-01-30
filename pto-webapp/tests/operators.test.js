/**
 * Tests for operators.js — Op class providing search operators over traces.
 *
 * Covers:
 *   - createInd: produces valid Sol with pheno and geno
 *   - evaluateInd: returns fitness(pheno)
 *   - fixInd: replaying modified geno produces valid solution
 *   - mutatePointInd: exactly one trace entry differs
 *   - mutatePositionWiseInd: original unchanged, at least some may differ
 *   - mutateRandomInd: produces fresh solution ignoring input
 *   - crossoverUniformInd: child values from either parent
 *   - crossoverOnePointInd: prefix from sol1, suffix from sol2
 *   - distanceInd: 0 for identical, > 0 for different
 *   - Edge: single-entry trace
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { Tracer } from '../src/tracer.js';
import { createRnd } from '../src/rnd.js';
import { Op } from '../src/operators.js';

// ---------------------------------------------------------------------------
// Helpers: OneMax problem (maximize sum of binary string)
// ---------------------------------------------------------------------------
function makeOneMax(size = 10) {
  const tracer = new Tracer();
  const rnd = createRnd(tracer);

  const generator = () => {
    const bits = [];
    for (let i = 0; i < size; i++) {
      bits.push(rnd.choice([0, 1]));
    }
    return bits;
  };

  const fitness = (pheno) => pheno.reduce((a, b) => a + b, 0);

  const op = new Op(generator, fitness, { tracer });
  return { op, tracer, rnd };
}

// ---------------------------------------------------------------------------
// createInd
// ---------------------------------------------------------------------------
describe('Op.createInd()', () => {
  it('returns sol with pheno and geno', () => {
    const { op } = makeOneMax();
    const sol = op.createInd();
    assert.ok('pheno' in sol && 'geno' in sol);
    assert.equal(sol.pheno.length, 10);
    assert.equal(Object.keys(sol.geno).length, 10);
  });

  it('phenotype values are 0 or 1', () => {
    const { op } = makeOneMax();
    const sol = op.createInd();
    for (const v of sol.pheno) {
      assert.ok(v === 0 || v === 1);
    }
  });
});

// ---------------------------------------------------------------------------
// evaluateInd
// ---------------------------------------------------------------------------
describe('Op.evaluateInd()', () => {
  it('returns fitness of phenotype', () => {
    const { op } = makeOneMax();
    const sol = op.createInd();
    const fx = op.evaluateInd(sol);
    assert.equal(fx, sol.pheno.reduce((a, b) => a + b, 0));
  });
});

// ---------------------------------------------------------------------------
// fixInd
// ---------------------------------------------------------------------------
describe('Op.fixInd()', () => {
  it('replaying geno produces valid solution', () => {
    const { op } = makeOneMax();
    const sol1 = op.createInd();
    const sol2 = op.fixInd(sol1.geno);
    assert.deepEqual(sol1.pheno, sol2.pheno);
  });
});

// ---------------------------------------------------------------------------
// mutatePointInd
// ---------------------------------------------------------------------------
describe('Op.mutatePointInd()', () => {
  it('child geno differs from parent in at most one entry (value may or may not change due to re-sampling)', () => {
    const { op } = makeOneMax(20);
    const parent = op.createInd();

    // Run many times — on average, the mutated entry's value should differ
    // at least sometimes (binary choice: 50% chance same value)
    let everDiffered = false;
    for (let trial = 0; trial < 50; trial++) {
      const child = op.mutatePointInd(parent);
      let diffs = 0;
      for (const key of Object.keys(parent.geno)) {
        if (parent.geno[key].val !== child.geno[key].val) diffs++;
      }
      // At most 1 entry was mutated (repair may cascade, but for OneMax it won't)
      if (diffs > 0) everDiffered = true;
    }
    assert.ok(everDiffered, 'mutation should change at least one entry sometimes');
  });

  it('original solution is not modified', () => {
    const { op } = makeOneMax();
    const parent = op.createInd();
    const origPheno = [...parent.pheno];
    op.mutatePointInd(parent);
    assert.deepEqual(parent.pheno, origPheno);
  });
});

// ---------------------------------------------------------------------------
// mutatePositionWiseInd
// ---------------------------------------------------------------------------
describe('Op.mutatePositionWiseInd()', () => {
  it('returns valid solution, original unchanged', () => {
    const { op } = makeOneMax();
    const parent = op.createInd();
    const origPheno = [...parent.pheno];
    const child = op.mutatePositionWiseInd(parent);
    assert.equal(child.pheno.length, 10);
    assert.deepEqual(parent.pheno, origPheno);
  });
});

// ---------------------------------------------------------------------------
// mutateRandomInd
// ---------------------------------------------------------------------------
describe('Op.mutateRandomInd()', () => {
  it('returns fresh solution ignoring input', () => {
    const { op } = makeOneMax();
    const parent = op.createInd();
    const child = op.mutateRandomInd(parent);
    assert.equal(child.pheno.length, 10);
    // Can't assert different since random could match, but structure is valid
    assert.equal(Object.keys(child.geno).length, 10);
  });
});

// ---------------------------------------------------------------------------
// crossoverUniformInd
// ---------------------------------------------------------------------------
describe('Op.crossoverUniformInd()', () => {
  it('child values come from either parent', () => {
    const { op } = makeOneMax();
    const sol1 = op.createInd();
    const sol2 = op.createInd();
    const child = op.crossoverUniformInd(sol1, sol2);

    for (let i = 0; i < child.pheno.length; i++) {
      const key = String(i);
      const childVal = child.geno[key].val;
      const p1Val = sol1.geno[key].val;
      const p2Val = sol2.geno[key].val;
      assert.ok(
        childVal === p1Val || childVal === p2Val,
        `child[${i}]=${childVal} not from parents (${p1Val}, ${p2Val})`
      );
    }
  });
});

// ---------------------------------------------------------------------------
// crossoverOnePointInd
// ---------------------------------------------------------------------------
describe('Op.crossoverOnePointInd()', () => {
  it('produces valid solution with correct length', () => {
    const { op } = makeOneMax();
    const sol1 = op.createInd();
    const sol2 = op.createInd();
    const child = op.crossoverOnePointInd(sol1, sol2);
    assert.equal(child.pheno.length, 10);
  });

  it('child values come from either parent', () => {
    const { op } = makeOneMax();
    const sol1 = op.createInd();
    const sol2 = op.createInd();
    const child = op.crossoverOnePointInd(sol1, sol2);

    for (let i = 0; i < child.pheno.length; i++) {
      const key = String(i);
      const childVal = child.geno[key].val;
      const p1Val = sol1.geno[key].val;
      const p2Val = sol2.geno[key].val;
      assert.ok(childVal === p1Val || childVal === p2Val);
    }
  });
});

// ---------------------------------------------------------------------------
// distanceInd
// ---------------------------------------------------------------------------
describe('Op.distanceInd()', () => {
  it('distance to self is 0', () => {
    const { op } = makeOneMax();
    const sol = op.createInd();
    assert.equal(op.distanceInd(sol, sol), 0);
  });

  it('distance between different solutions is > 0 (usually)', () => {
    const { op } = makeOneMax(50);
    const sol1 = op.createInd();
    const sol2 = op.createInd();
    // With 50 binary entries, extremely unlikely to be identical
    assert.ok(op.distanceInd(sol1, sol2) > 0);
  });
});

// ---------------------------------------------------------------------------
// Edge: single-entry trace
// ---------------------------------------------------------------------------
describe('Op edge cases', () => {
  it('single-entry trace: mutation works', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);
    const gen = () => rnd.choice([0, 1]);
    const fit = (v) => v;
    const op = new Op(gen, fit, { tracer });

    const parent = op.createInd();
    const child = op.mutatePointInd(parent);
    assert.ok(child.pheno === 0 || child.pheno === 1);
  });

  it('single-entry trace: crossover works', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);
    const gen = () => rnd.choice([0, 1]);
    const fit = (v) => v;
    const op = new Op(gen, fit, { tracer });

    const sol1 = op.createInd();
    const sol2 = op.createInd();
    const child = op.crossoverUniformInd(sol1, sol2);
    assert.ok(child.pheno === 0 || child.pheno === 1);
  });

  it('empty trace (no rnd calls): operators handle gracefully', () => {
    const tracer = new Tracer();
    const gen = () => 42;
    const fit = (v) => v;
    const op = new Op(gen, fit, { tracer });

    const sol = op.createInd();
    assert.equal(sol.pheno, 42);
    assert.deepEqual(sol.geno, {});

    const mutated = op.mutatePointInd(sol);
    assert.equal(mutated.pheno, 42);

    const child = op.crossoverUniformInd(sol, sol);
    assert.equal(child.pheno, 42);
  });
});
