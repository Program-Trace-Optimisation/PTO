/**
 * Tests for tracer.js — Trace recording and replay engine.
 *
 * Covers:
 *   - Recording traces with linear (integer) keys
 *   - Exact replay from a recorded trace
 *   - Replay with modified trace entries
 *   - Empty generators (no rnd calls)
 *   - Single rnd call
 *   - Counter reset between plays
 *   - Matching logic: reuse vs repair vs fresh sample
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { Tracer } from '../src/tracer.js';
import { RandomInt, RandomCat, RandomReal } from '../src/distribution.js';

// ---------------------------------------------------------------------------
// Helper: create a simple generator that uses the tracer directly
// ---------------------------------------------------------------------------
function makeGenerator(tracer, specs) {
  // specs: array of () => dist objects
  return () => specs.map(mkDist => {
    const dist = mkDist();
    return tracer.sample(null, dist);
  });
}

// ---------------------------------------------------------------------------
// Recording
// ---------------------------------------------------------------------------
describe('Tracer recording', () => {
  it('records trace with sequential integer keys', () => {
    const tracer = new Tracer();
    const gen = makeGenerator(tracer, [
      () => new RandomInt(0, 10),
      () => new RandomCat(['a', 'b', 'c']),
      () => new RandomInt(1, 5),
    ]);

    const { pheno, geno } = tracer.play(gen, {});
    assert.equal(Object.keys(geno).length, 3);
    assert.ok(0 in geno);
    assert.ok(1 in geno);
    assert.ok(2 in geno);
    assert.equal(pheno.length, 3);
  });

  it('empty generator produces empty trace', () => {
    const tracer = new Tracer();
    const gen = () => 'hello';
    const { pheno, geno } = tracer.play(gen, {});
    assert.equal(pheno, 'hello');
    assert.deepEqual(geno, {});
  });

  it('single rnd call produces trace with one entry', () => {
    const tracer = new Tracer();
    const gen = makeGenerator(tracer, [() => new RandomInt(0, 1)]);
    const { geno } = tracer.play(gen, {});
    assert.equal(Object.keys(geno).length, 1);
    assert.ok(0 in geno);
  });
});

// ---------------------------------------------------------------------------
// Replay
// ---------------------------------------------------------------------------
describe('Tracer replay', () => {
  it('replays exact trace to produce identical phenotype', () => {
    const tracer = new Tracer();
    const gen = makeGenerator(tracer, [
      () => new RandomInt(0, 100),
      () => new RandomInt(0, 100),
      () => new RandomInt(0, 100),
    ]);

    // Generate first solution
    const { pheno: pheno1, geno: geno1 } = tracer.play(gen, {});

    // Replay with same trace
    const { pheno: pheno2 } = tracer.play(gen, geno1);

    assert.deepEqual(pheno1, pheno2);
  });

  it('modified trace entry changes corresponding phenotype position', () => {
    const tracer = new Tracer();
    const gen = makeGenerator(tracer, [
      () => new RandomCat([0, 1]),
      () => new RandomCat([0, 1]),
      () => new RandomCat([0, 1]),
    ]);

    // Generate and capture trace
    const { pheno: pheno1, geno: geno1 } = tracer.play(gen, {});

    // Modify one entry: flip position 1
    const modifiedGeno = { ...geno1 };
    const flipped = new RandomCat([0, 1], pheno1[1] === 0 ? 1 : 0);
    modifiedGeno[1] = flipped;

    const { pheno: pheno2 } = tracer.play(gen, modifiedGeno);

    // Position 0 and 2 should be the same, position 1 should differ
    assert.equal(pheno2[0], pheno1[0]);
    assert.notEqual(pheno2[1], pheno1[1]);
    assert.equal(pheno2[2], pheno1[2]);
  });
});

// ---------------------------------------------------------------------------
// Counter reset
// ---------------------------------------------------------------------------
describe('Tracer counter', () => {
  it('resets counter between successive plays', () => {
    const tracer = new Tracer();
    const gen = makeGenerator(tracer, [() => new RandomInt(0, 10)]);

    const { geno: geno1 } = tracer.play(gen, {});
    const { geno: geno2 } = tracer.play(gen, {});

    // Both should have key 0
    assert.ok(0 in geno1);
    assert.ok(0 in geno2);
  });
});

// ---------------------------------------------------------------------------
// Matching logic
// ---------------------------------------------------------------------------
describe('Tracer matching', () => {
  it('reuses value when funName and args match', () => {
    const tracer = new Tracer();
    const gen = makeGenerator(tracer, [() => new RandomInt(0, 100)]);

    const { geno: geno1 } = tracer.play(gen, {});
    const val1 = geno1[0].val;

    // Replay — should get same value
    const { pheno: pheno2 } = tracer.play(gen, geno1);
    assert.equal(pheno2[0], val1);
  });

  it('repairs (re-samples) when args differ', () => {
    const tracer = new Tracer();

    // First play: randint(0, 100)
    const gen1 = makeGenerator(tracer, [() => new RandomInt(0, 100)]);
    const { geno: geno1 } = tracer.play(gen1, {});

    // Second play: randint(0, 1) — different args, so repair (re-sample)
    const gen2 = makeGenerator(tracer, [() => new RandomInt(0, 1)]);
    const { pheno: pheno2 } = tracer.play(gen2, geno1);

    // Value should be in new range [0, 1]
    assert.ok(pheno2[0] >= 0 && pheno2[0] <= 1);
  });

  it('samples fresh when name not in input trace', () => {
    const tracer = new Tracer();

    // Input trace has key 0 only
    const inputTrace = {};
    const d = new RandomInt(0, 10);
    d.val = 5;
    inputTrace[0] = d;

    // Generator makes 2 calls — key 1 is new
    const gen = makeGenerator(tracer, [
      () => new RandomInt(0, 10),
      () => new RandomInt(0, 10),
    ]);

    const { pheno, geno } = tracer.play(gen, inputTrace);

    // Key 0 reused, key 1 fresh
    assert.equal(pheno[0], 5);
    assert.equal(Object.keys(geno).length, 2);
  });
});

// ---------------------------------------------------------------------------
// Inactive tracer
// ---------------------------------------------------------------------------
describe('Tracer inactive', () => {
  it('sample() works when tracer is inactive (just samples)', () => {
    const tracer = new Tracer();
    assert.equal(tracer.active, false);

    const dist = new RandomInt(0, 10);
    const val = tracer.sample(null, dist);
    assert.ok(Number.isInteger(val));
    assert.ok(val >= 0 && val <= 10);

    // No output trace recorded
    assert.deepEqual(tracer.outputTrace, {});
  });
});

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------
describe('Tracer error handling', () => {
  it('deactivates tracer even if generator throws', () => {
    const tracer = new Tracer();
    const gen = () => { throw new Error('boom'); };

    assert.throws(() => tracer.play(gen, {}), { message: 'boom' });
    assert.equal(tracer.active, false);
  });
});
