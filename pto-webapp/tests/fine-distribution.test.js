/**
 * Tests for fine distribution operators.
 *
 * Each distribution type is tested in fine mode for:
 *   - mutation: produces small perturbation, not full re-sample
 *   - crossover: produces value influenced by both parents
 *   - repair: maps value from a different domain intelligently
 *   - distance: returns normalized continuous metric
 *   - mode propagation: clone preserves mode
 *
 * Also tests that coarse mode still works (backward compatibility).
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { RandomReal, RandomInt, RandomCat, RandomSeq } from '../src/distribution.js';

// ---------------------------------------------------------------------------
// Helper: set mode on a distribution
// ---------------------------------------------------------------------------
function fine(dist) {
  dist.mode = 'fine';
  return dist;
}

// ---------------------------------------------------------------------------
// RandomReal fine operators
// ---------------------------------------------------------------------------
describe('RandomReal fine', () => {
  it('fine mutation produces nearby value (Gaussian perturbation)', () => {
    const d = fine(new RandomReal(0, 100));
    d.val = 50;
    // Run many mutations — average distance should be small relative to range
    let totalDist = 0;
    const N = 200;
    for (let i = 0; i < N; i++) {
      const m = d.mutation();
      assert.ok(m.val >= 0 && m.val <= 100, `val ${m.val} out of bounds`);
      totalDist += Math.abs(m.val - 50);
    }
    const avgDist = totalDist / N;
    // Gaussian with sigma=10 (0.1*100): mean absolute deviation ~8
    assert.ok(avgDist < 30, `avg dist ${avgDist} too large for fine mutation`);
    assert.ok(avgDist > 1, `avg dist ${avgDist} suspiciously small`);
  });

  it('fine mutation clamps to bounds', () => {
    const d = fine(new RandomReal(0, 1));
    d.val = 0.01;
    for (let i = 0; i < 100; i++) {
      const m = d.mutation();
      assert.ok(m.val >= 0 && m.val <= 1);
    }
  });

  it('fine crossover interpolates between parents', () => {
    const a = fine(new RandomReal(0, 100, 20));
    const b = fine(new RandomReal(0, 100, 80));
    let minSeen = 100, maxSeen = 0;
    for (let i = 0; i < 100; i++) {
      const c = a.crossover(b);
      assert.ok(c.val >= 20 && c.val <= 80, `crossover val ${c.val} outside parent range`);
      minSeen = Math.min(minSeen, c.val);
      maxSeen = Math.max(maxSeen, c.val);
    }
    // Should explore the range, not just pick parents
    assert.ok(maxSeen - minSeen > 10, 'crossover should interpolate, not just pick parents');
  });

  it('fine distance is normalized', () => {
    const a = fine(new RandomReal(0, 100, 0));
    const b = fine(new RandomReal(0, 100, 100));
    const c = fine(new RandomReal(0, 100, 50));
    assert.equal(a.distance(b), 1);
    assert.equal(a.distance(c), 0.5);
    assert.equal(a.distance(a), 0);
  });

  it('fine repair maps proportionally', () => {
    const target = fine(new RandomReal(0, 10));
    const source = new RandomReal(0, 100);
    source.val = 50;
    target.repair(source);
    assert.ok(Math.abs(target.val - 5) < 0.01, `expected ~5, got ${target.val}`);
  });

  it('coarse mode still works', () => {
    const d = new RandomReal(0, 100);
    d.val = 50;
    assert.equal(d.mode, 'coarse');
    // Coarse mutation re-samples — value should often differ a lot
    const m = d.mutation();
    assert.ok(m.val >= 0 && m.val <= 100);
  });

  it('clone preserves mode', () => {
    const d = fine(new RandomReal(0, 1, 0.5));
    const c = d.clone();
    assert.equal(c.mode, 'fine');
  });
});

// ---------------------------------------------------------------------------
// RandomInt fine operators
// ---------------------------------------------------------------------------
describe('RandomInt fine', () => {
  it('fine mutation produces ±1 step', () => {
    const d = fine(new RandomInt(0, 100));
    d.val = 50;
    for (let i = 0; i < 50; i++) {
      const m = d.mutation();
      assert.ok(m.val === 49 || m.val === 50 || m.val === 51,
        `expected 49/50/51, got ${m.val}`);
    }
  });

  it('fine mutation at boundary stays in bounds', () => {
    const d = fine(new RandomInt(0, 5));
    d.val = 0;
    for (let i = 0; i < 50; i++) {
      const m = d.mutation();
      assert.ok(m.val >= 0 && m.val <= 5);
    }
  });

  it('fine mutation on single-value range returns same', () => {
    const d = fine(new RandomInt(3, 3));
    d.val = 3;
    const m = d.mutation();
    assert.equal(m.val, 3);
  });

  it('fine crossover produces integer between parents', () => {
    const a = fine(new RandomInt(0, 100, 20));
    const b = fine(new RandomInt(0, 100, 80));
    for (let i = 0; i < 50; i++) {
      const c = a.crossover(b);
      assert.ok(Number.isInteger(c.val));
      assert.ok(c.val >= 20 && c.val <= 80);
    }
  });

  it('fine distance is normalized', () => {
    const a = fine(new RandomInt(0, 10, 0));
    const b = fine(new RandomInt(0, 10, 10));
    const c = fine(new RandomInt(0, 10, 5));
    assert.equal(a.distance(b), 1);
    assert.equal(a.distance(c), 0.5);
  });

  it('fine repair maps proportionally', () => {
    const target = fine(new RandomInt(0, 10));
    const source = new RandomInt(0, 100);
    source.val = 50;
    target.repair(source);
    assert.equal(target.val, 5);
  });
});

// ---------------------------------------------------------------------------
// RandomCat fine operators
// ---------------------------------------------------------------------------
describe('RandomCat fine', () => {
  it('fine mutation always picks a different value', () => {
    const d = fine(new RandomCat(['a', 'b', 'c']));
    d.val = 'a';
    for (let i = 0; i < 50; i++) {
      const m = d.mutation();
      assert.notEqual(m.val, 'a', 'fine mutation should pick different value');
      assert.ok(['b', 'c'].includes(m.val));
    }
  });

  it('fine mutation with single-element seq keeps value', () => {
    const d = fine(new RandomCat([42]));
    d.val = 42;
    const m = d.mutation();
    assert.equal(m.val, 42);
  });

  it('fine repair keeps value if present in target seq', () => {
    const target = fine(new RandomCat(['a', 'b', 'c']));
    const source = new RandomCat(['x', 'b', 'y']);
    source.val = 'b';
    target.repair(source);
    assert.equal(target.val, 'b');
  });

  it('fine repair samples from target if value not present', () => {
    const target = fine(new RandomCat(['a', 'b', 'c']));
    const source = new RandomCat(['x', 'y', 'z']);
    source.val = 'x';
    target.repair(source);
    assert.ok(['a', 'b', 'c'].includes(target.val));
  });

  it('fine distance is binary', () => {
    const a = fine(new RandomCat(['a', 'b'], 'a'));
    const b = fine(new RandomCat(['a', 'b'], 'a'));
    const c = fine(new RandomCat(['a', 'b'], 'b'));
    assert.equal(a.distance(b), 0);
    assert.equal(a.distance(c), 1);
  });
});

// ---------------------------------------------------------------------------
// RandomSeq fine operators
// ---------------------------------------------------------------------------
describe('RandomSeq fine', () => {
  it('fine mutation swaps two positions (permutation case)', () => {
    const d = fine(new RandomSeq([1, 2, 3, 4, 5], 5));
    d.val = [1, 2, 3, 4, 5];
    let swapSeen = false;
    for (let i = 0; i < 50; i++) {
      const m = d.mutation();
      assert.equal(m.val.length, 5);
      assert.deepEqual([...m.val].sort(), [1, 2, 3, 4, 5], 'should be permutation');
      if (JSON.stringify(m.val) !== JSON.stringify([1, 2, 3, 4, 5])) {
        swapSeen = true;
      }
    }
    assert.ok(swapSeen, 'mutation should change order');
  });

  it('fine mutation can replace from pool (subset case)', () => {
    const d = fine(new RandomSeq([1, 2, 3, 4, 5], 3));
    d.val = [1, 2, 3];
    let replaceSeen = false;
    for (let i = 0; i < 100; i++) {
      const m = d.mutation();
      assert.equal(m.val.length, 3);
      // Check all elements are from seq
      for (const v of m.val) {
        assert.ok([1, 2, 3, 4, 5].includes(v));
      }
      if (m.val.includes(4) || m.val.includes(5)) {
        replaceSeen = true;
      }
    }
    assert.ok(replaceSeen, 'mutation should sometimes replace from pool');
  });

  it('fine crossover produces valid permutation', () => {
    const a = fine(new RandomSeq([1, 2, 3, 4, 5], 5, [1, 2, 3, 4, 5]));
    const b = fine(new RandomSeq([1, 2, 3, 4, 5], 5, [5, 4, 3, 2, 1]));
    for (let i = 0; i < 50; i++) {
      const c = a.crossover(b);
      assert.equal(c.val.length, 5);
      assert.deepEqual([...c.val].sort(), [1, 2, 3, 4, 5]);
    }
  });

  it('fine distance: identical sequences = 0', () => {
    const a = fine(new RandomSeq([1, 2, 3], 3, [1, 2, 3]));
    const b = fine(new RandomSeq([1, 2, 3], 3, [1, 2, 3]));
    assert.equal(a.distance(b), 0);
  });

  it('fine distance: swapped pair = 1', () => {
    const a = fine(new RandomSeq([1, 2, 3], 3, [1, 2, 3]));
    const b = fine(new RandomSeq([1, 2, 3], 3, [2, 1, 3]));
    assert.equal(a.distance(b), 1); // one swap
  });

  it('fine distance: fully reversed = multiple operations', () => {
    const a = fine(new RandomSeq([1, 2, 3, 4], 4, [1, 2, 3, 4]));
    const b = fine(new RandomSeq([1, 2, 3, 4], 4, [4, 3, 2, 1]));
    assert.ok(a.distance(b) > 0);
  });

  it('fine repair produces valid sequence', () => {
    const target = fine(new RandomSeq([1, 2, 3, 4, 5], 5));
    target.val = [1, 2, 3, 4, 5];
    const source = new RandomSeq([1, 2, 3, 4, 5], 5);
    source.val = [5, 4, 3, 2, 1];
    target.repair(source);
    assert.equal(target.val.length, 5);
    assert.deepEqual([...target.val].sort(), [1, 2, 3, 4, 5]);
  });

  it('pool computation is correct', () => {
    const d = fine(new RandomSeq([1, 2, 3, 4, 5], 3, [1, 2, 3]));
    const pool = d._pool();
    assert.deepEqual(pool.sort(), [4, 5]);
  });

  it('pool with full permutation is empty', () => {
    const d = fine(new RandomSeq([1, 2, 3], 3, [3, 1, 2]));
    const pool = d._pool();
    assert.deepEqual(pool, []);
  });
});

// ---------------------------------------------------------------------------
// Mode switching
// ---------------------------------------------------------------------------
describe('Mode switching', () => {
  it('switching mode changes operator behavior for RandomReal', () => {
    const d = new RandomReal(0, 100, 50);

    // Coarse: distance is absolute (not normalized)
    d.mode = 'coarse';
    assert.equal(d.distance(new RandomReal(0, 100, 100)), 50);

    // Fine: distance is normalized to [0,1]
    d.mode = 'fine';
    assert.equal(d.distance(fine(new RandomReal(0, 100, 100))), 0.5);
  });

  it('switching mode changes mutation behavior for RandomCat', () => {
    const d = new RandomCat(['a', 'b', 'c'], 'a');

    // Fine: always picks different value
    d.mode = 'fine';
    for (let i = 0; i < 20; i++) {
      assert.notEqual(d.mutation().val, 'a');
    }
  });
});
