/**
 * Tests for distribution.js — Base Dist class and 4 coarse distribution subclasses.
 *
 * Covers:
 *   - Sampling produces values within expected domains
 *   - Mutation returns a new instance without modifying the original
 *   - Crossover returns a value from one of the two parents
 *   - Distance is 0 for identical values, >0 otherwise
 *   - matches() correctly identifies structural equality
 *   - Edge cases: single-element sequences, equal bounds, k=0, k=seq.length
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { Dist, RandomReal, RandomInt, RandomCat, RandomSeq } from '../src/distribution.js';

// ---------------------------------------------------------------------------
// Helper: run a sampling function many times and collect results
// ---------------------------------------------------------------------------
function sampleMany(dist, n = 100) {
  const vals = [];
  for (let i = 0; i < n; i++) {
    const d = dist.clone();
    d.sample();
    vals.push(d.val);
  }
  return vals;
}

// ---------------------------------------------------------------------------
// RandomReal
// ---------------------------------------------------------------------------
describe('RandomReal', () => {
  it('sample() produces values in [a, b)', () => {
    const vals = sampleMany(new RandomReal(2, 5));
    for (const v of vals) {
      assert.ok(v >= 2 && v < 5, `${v} not in [2, 5)`);
    }
  });

  it('sample() with a == b produces exactly a', () => {
    const d = new RandomReal(3, 3);
    d.sample();
    assert.equal(d.val, 3);
  });

  it('size() is Infinity', () => {
    assert.equal(new RandomReal(0, 1).size(), Infinity);
  });

  it('distance() returns absolute difference', () => {
    const a = new RandomReal(0, 10, 2.5);
    const b = new RandomReal(0, 10, 7.5);
    assert.equal(a.distance(b), 5);
  });

  it('mutation() returns new instance, original unchanged', () => {
    const orig = new RandomReal(0, 1);
    orig.sample();
    const origVal = orig.val;
    const child = orig.mutation();
    assert.equal(orig.val, origVal);
    assert.notStrictEqual(child, orig);
  });

  it('crossover() returns value from one parent', () => {
    const a = new RandomReal(0, 10, 1.0);
    const b = new RandomReal(0, 10, 9.0);
    const results = new Set();
    for (let i = 0; i < 100; i++) {
      results.add(a.crossover(b).val);
    }
    // Should see both parent values
    assert.ok(results.has(1.0) || results.has(9.0));
    for (const v of results) {
      assert.ok(v === 1.0 || v === 9.0, `unexpected crossover value ${v}`);
    }
  });
});

// ---------------------------------------------------------------------------
// RandomInt
// ---------------------------------------------------------------------------
describe('RandomInt', () => {
  it('sample() produces integers in [a, b]', () => {
    const vals = sampleMany(new RandomInt(3, 7));
    for (const v of vals) {
      assert.ok(Number.isInteger(v), `${v} is not integer`);
      assert.ok(v >= 3 && v <= 7, `${v} not in [3, 7]`);
    }
  });

  it('sample() with a == b produces exactly a', () => {
    const d = new RandomInt(5, 5);
    d.sample();
    assert.equal(d.val, 5);
  });

  it('size() returns b - a + 1', () => {
    assert.equal(new RandomInt(0, 9).size(), 10);
    assert.equal(new RandomInt(5, 5).size(), 1);
  });

  it('distance() returns absolute difference', () => {
    const a = new RandomInt(0, 10, 2);
    const b = new RandomInt(0, 10, 8);
    assert.equal(a.distance(b), 6);
  });

  it('mutation() returns new instance, original unchanged', () => {
    const orig = new RandomInt(0, 100);
    orig.sample();
    const origVal = orig.val;
    const child = orig.mutation();
    assert.equal(orig.val, origVal);
    assert.notStrictEqual(child, orig);
  });
});

// ---------------------------------------------------------------------------
// RandomCat
// ---------------------------------------------------------------------------
describe('RandomCat', () => {
  it('sample() produces element from seq', () => {
    const seq = ['a', 'b', 'c'];
    const vals = sampleMany(new RandomCat(seq));
    for (const v of vals) {
      assert.ok(seq.includes(v), `${v} not in seq`);
    }
  });

  it('single-element seq always produces that element', () => {
    const d = new RandomCat([42]);
    d.sample();
    assert.equal(d.val, 42);
  });

  it('size() returns seq.length', () => {
    assert.equal(new RandomCat([1, 2, 3]).size(), 3);
  });

  it('distance() is binary (base Dist behavior)', () => {
    const a = new RandomCat(['x', 'y'], 'x');
    const b = new RandomCat(['x', 'y'], 'x');
    const c = new RandomCat(['x', 'y'], 'y');
    assert.equal(a.distance(b), 0);
    assert.equal(a.distance(c), 1);
  });

  it('mutation() returns new instance', () => {
    const orig = new RandomCat([1, 2, 3]);
    orig.sample();
    const child = orig.mutation();
    assert.notStrictEqual(child, orig);
  });
});

// ---------------------------------------------------------------------------
// RandomSeq
// ---------------------------------------------------------------------------
describe('RandomSeq', () => {
  it('sample() produces array of k distinct elements from seq', () => {
    const seq = [1, 2, 3, 4, 5];
    const d = new RandomSeq(seq, 3);
    d.sample();
    assert.equal(d.val.length, 3);
    const unique = new Set(d.val);
    assert.equal(unique.size, 3, 'elements should be distinct');
    for (const v of d.val) {
      assert.ok(seq.includes(v), `${v} not in seq`);
    }
  });

  it('k == 0 produces empty array', () => {
    const d = new RandomSeq([1, 2, 3], 0);
    d.sample();
    assert.deepEqual(d.val, []);
  });

  it('k == seq.length produces a permutation', () => {
    const seq = [1, 2, 3, 4];
    const d = new RandomSeq(seq, 4);
    d.sample();
    assert.equal(d.val.length, 4);
    assert.deepEqual([...d.val].sort(), [1, 2, 3, 4]);
  });

  it('single-element seq with k=1', () => {
    const d = new RandomSeq([99], 1);
    d.sample();
    assert.deepEqual(d.val, [99]);
  });

  it('size() returns k-permutation count', () => {
    // P(5,3) = 5*4*3 = 60
    assert.equal(new RandomSeq([1, 2, 3, 4, 5], 3).size(), 60);
    // P(4,4) = 4! = 24
    assert.equal(new RandomSeq([1, 2, 3, 4], 4).size(), 24);
    // P(n,0) = 1
    assert.equal(new RandomSeq([1, 2], 0).size(), 1);
  });

  it('distance() counts positional differences', () => {
    const a = new RandomSeq([1, 2, 3], 3, [1, 2, 3]);
    const b = new RandomSeq([1, 2, 3], 3, [1, 3, 2]);
    assert.equal(a.distance(b), 2);
    assert.equal(a.distance(a), 0);
  });

  it('crossover() returns copy of one parent value', () => {
    const a = new RandomSeq([1, 2, 3], 3, [1, 2, 3]);
    const b = new RandomSeq([1, 2, 3], 3, [3, 2, 1]);
    const child = a.crossover(b);
    const matches = (
      JSON.stringify(child.val) === JSON.stringify([1, 2, 3]) ||
      JSON.stringify(child.val) === JSON.stringify([3, 2, 1])
    );
    assert.ok(matches, 'child should have one parent\'s value');
  });

  it('clone() produces independent copy', () => {
    const orig = new RandomSeq([1, 2, 3], 2, [1, 2]);
    const copy = orig.clone();
    copy.val[0] = 99;
    assert.equal(orig.val[0], 1, 'original should not be affected');
  });

  it('mutation() does not modify original', () => {
    const orig = new RandomSeq([1, 2, 3, 4], 3);
    orig.sample();
    const origVal = [...orig.val];
    const child = orig.mutation();
    assert.deepEqual(orig.val, origVal);
    assert.notStrictEqual(child, orig);
  });
});

// ---------------------------------------------------------------------------
// Dist.matches()
// ---------------------------------------------------------------------------
describe('Dist.matches()', () => {
  it('same funName and args → true', () => {
    const a = new RandomInt(0, 10);
    const b = new RandomInt(0, 10);
    assert.ok(a.matches(b));
  });

  it('different funName → false', () => {
    const a = new RandomInt(0, 10);
    const b = new RandomReal(0, 10);
    assert.ok(!a.matches(b));
  });

  it('different args → false', () => {
    const a = new RandomInt(0, 10);
    const b = new RandomInt(0, 20);
    assert.ok(!a.matches(b));
  });

  it('array args compared deeply', () => {
    const a = new RandomCat([1, 2, 3]);
    const b = new RandomCat([1, 2, 3]);
    const c = new RandomCat([1, 2, 4]);
    assert.ok(a.matches(b));
    assert.ok(!a.matches(c));
  });
});
