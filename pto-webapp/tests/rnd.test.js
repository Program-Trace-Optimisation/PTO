/**
 * Tests for rnd.js — Traced random wrapper.
 *
 * Covers:
 *   - Each method produces values in expected domain
 *   - Active tracer records entries in outputTrace
 *   - Linear naming: sequential integer keys
 *   - Explicit name override
 *   - Inactive tracer: values returned, no trace recorded
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { Tracer } from '../src/tracer.js';
import { createRnd } from '../src/rnd.js';

// ---------------------------------------------------------------------------
// Basic value domains
// ---------------------------------------------------------------------------
describe('rnd value domains', () => {
  it('uniform() returns float in [a, b)', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);
    for (let i = 0; i < 50; i++) {
      const v = rnd.uniform(2, 5);
      assert.ok(v >= 2 && v < 5, `${v} not in [2,5)`);
    }
  });

  it('randint() returns integer in [a, b]', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);
    for (let i = 0; i < 50; i++) {
      const v = rnd.randint(3, 7);
      assert.ok(Number.isInteger(v) && v >= 3 && v <= 7);
    }
  });

  it('choice() returns element from seq', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);
    const seq = ['x', 'y', 'z'];
    for (let i = 0; i < 50; i++) {
      assert.ok(seq.includes(rnd.choice(seq)));
    }
  });

  it('sample() returns k distinct elements', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);
    const seq = [1, 2, 3, 4, 5];
    const result = rnd.sample(seq, 3);
    assert.equal(result.length, 3);
    assert.equal(new Set(result).size, 3);
    for (const v of result) assert.ok(seq.includes(v));
  });
});

// ---------------------------------------------------------------------------
// Tracing with linear naming
// ---------------------------------------------------------------------------
describe('rnd tracing (linear naming)', () => {
  it('records entries with sequential integer keys when tracer active', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);

    const gen = () => [
      rnd.uniform(0, 1),
      rnd.randint(0, 10),
      rnd.choice(['a', 'b']),
    ];

    const { geno } = tracer.play(gen, {});
    assert.equal(Object.keys(geno).length, 3);
    assert.ok(0 in geno);
    assert.ok(1 in geno);
    assert.ok(2 in geno);
    assert.equal(geno[0].funName, 'uniform');
    assert.equal(geno[1].funName, 'randint');
    assert.equal(geno[2].funName, 'choice');
  });

  it('replay with recorded trace produces same phenotype', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);

    const gen = () => [
      rnd.randint(0, 100),
      rnd.randint(0, 100),
      rnd.choice([10, 20, 30]),
    ];

    const { pheno: p1, geno: g1 } = tracer.play(gen, {});
    const { pheno: p2 } = tracer.play(gen, g1);
    assert.deepEqual(p1, p2);
  });
});

// ---------------------------------------------------------------------------
// Explicit name override
// ---------------------------------------------------------------------------
describe('rnd explicit names', () => {
  it('uses provided name as trace key', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);

    const gen = () => [
      rnd.uniform(0, 1, { name: 'alpha' }),
      rnd.randint(0, 5, { name: 'beta' }),
    ];

    const { geno } = tracer.play(gen, {});
    assert.ok('alpha' in geno);
    assert.ok('beta' in geno);
    assert.ok(!(0 in geno), 'should not have integer keys when names given');
  });
});

// ---------------------------------------------------------------------------
// Inactive tracer
// ---------------------------------------------------------------------------
describe('rnd inactive tracer', () => {
  it('returns valid values without recording trace', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);

    // Not inside play() — tracer inactive
    const v = rnd.randint(0, 10);
    assert.ok(Number.isInteger(v) && v >= 0 && v <= 10);
    assert.deepEqual(tracer.outputTrace, {});
  });
});
