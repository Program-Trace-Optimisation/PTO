/**
 * Tests for compiler.js — AST compiler for structured trace naming.
 *
 * Mirrors the Python test_compiler.py test cases. Each test:
 *   1. Compiles a generator
 *   2. Runs it via the tracer to produce a solution + trace
 *   3. Replays the trace to verify identical solution
 *   4. Checks trace key structure (structural names, not integers)
 *
 * Covers:
 *   - For loops with rnd calls
 *   - While loops
 *   - Nested functions
 *   - Multiple rnd calls per iteration
 *   - Nested loops
 *   - Conditional branches
 *   - Multiple call sites for same function
 *   - Functions with arguments
 *   - Single rnd call (no loop)
 *   - No rnd calls
 *   - Arrow function generators
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { compileGenerator } from '../src/compiler.js';
import { Tracer } from '../src/tracer.js';
import { createRnd } from '../src/rnd.js';

// ---------------------------------------------------------------------------
// Helper: compile, play, replay, verify
// ---------------------------------------------------------------------------
function compileAndTest(generator, { expectedEntries, keyMustContain, keyMustNotContain } = {}) {
  const compiled = compileGenerator(generator);

  // Verify compiled source is available
  assert.ok(compiled._originalSource);
  assert.ok(compiled._compiledSource);

  const tracer = new Tracer();
  const rnd = createRnd(tracer);

  // Play: generate fresh solution
  const { pheno: sol1, geno: trace1 } = tracer.play(() => compiled(rnd), {});

  // Replay: reproduce from trace
  const { pheno: sol2, geno: trace2 } = tracer.play(() => compiled(rnd), trace1);

  // Solutions must match
  assert.deepEqual(sol1, sol2, 'Replay should produce identical solution');

  // Trace keys must match
  assert.deepEqual(
    Object.keys(trace1).sort(),
    Object.keys(trace2).sort(),
    'Trace keys should match after replay',
  );

  // Check trace entry count
  if (expectedEntries !== undefined) {
    assert.equal(
      Object.keys(trace1).length,
      expectedEntries,
      `Expected ${expectedEntries} trace entries, got ${Object.keys(trace1).length}`,
    );
  }

  // Check key patterns
  if (keyMustContain) {
    for (const key of Object.keys(trace1)) {
      for (const pattern of keyMustContain) {
        assert.ok(key.includes(pattern), `Key "${key}" should contain "${pattern}"`);
      }
    }
  }

  if (keyMustNotContain) {
    for (const key of Object.keys(trace1)) {
      for (const pattern of keyMustNotContain) {
        assert.ok(!key.includes(pattern), `Key "${key}" should NOT contain "${pattern}"`);
      }
    }
  }

  // All keys should be strings (structured), not integers
  for (const key of Object.keys(trace1)) {
    assert.ok(typeof key === 'string', `Key should be string, got ${typeof key}`);
    assert.ok(key.startsWith('root/'), `Key "${key}" should start with "root/"`);
  }

  return { compiled, trace: trace1, pheno: sol1 };
}

// ---------------------------------------------------------------------------
// 1. For loop with rnd.choice (OneMax)
// ---------------------------------------------------------------------------
describe('Compiler: for loop', () => {
  it('for loop with rnd.choice produces structural names', () => {
    compileAndTest(
      function generator(rnd) {
        const bits = [];
        for (let i = 0; i < 10; i++) {
          bits.push(rnd.choice([0, 1]));
        }
        return bits;
      },
      { expectedEntries: 10, keyMustContain: ['for', 'choice'] },
    );
  });
});

// ---------------------------------------------------------------------------
// 2. While loop
// ---------------------------------------------------------------------------
describe('Compiler: while loop', () => {
  it('while loop produces structural names', () => {
    compileAndTest(
      function whileGen(rnd) {
        const result = [];
        let i = 0;
        while (i < 5) {
          result.push(rnd.uniform(0, 1));
          i++;
        }
        return result;
      },
      { expectedEntries: 5, keyMustContain: ['while', 'uniform'] },
    );
  });
});

// ---------------------------------------------------------------------------
// 3. Nested function
// ---------------------------------------------------------------------------
describe('Compiler: nested function', () => {
  it('nested function gets __prefix__ threaded', () => {
    compileAndTest(
      function nestedGen(rnd) {
        function pickFloat() {
          return rnd.uniform(-1, 1);
        }
        const result = [];
        for (let i = 0; i < 4; i++) {
          result.push(pickFloat());
        }
        return result;
      },
      { expectedEntries: 4, keyMustContain: ['uniform'] },
    );
  });
});

// ---------------------------------------------------------------------------
// 4. Multiple rnd calls per iteration
// ---------------------------------------------------------------------------
describe('Compiler: multiple rnd calls', () => {
  it('multiple rnd calls per loop iteration', () => {
    compileAndTest(
      function multiCall(rnd) {
        const pairs = [];
        for (let i = 0; i < 3; i++) {
          const x = rnd.uniform(0, 1);
          const y = rnd.uniform(0, 1);
          pairs.push([x, y]);
        }
        return pairs;
      },
      { expectedEntries: 6 },
    );
  });
});

// ---------------------------------------------------------------------------
// 5. Nested loops
// ---------------------------------------------------------------------------
describe('Compiler: nested loops', () => {
  it('nested for loops produce distinct names per cell', () => {
    compileAndTest(
      function nestedLoops(rnd) {
        const matrix = [];
        for (let i = 0; i < 3; i++) {
          const row = [];
          for (let j = 0; j < 4; j++) {
            row.push(rnd.randint(0, 9));
          }
          matrix.push(row);
        }
        return matrix;
      },
      { expectedEntries: 12, keyMustContain: ['for', 'randint'] },
    );
  });
});

// ---------------------------------------------------------------------------
// 6. Conditional branches
// ---------------------------------------------------------------------------
describe('Compiler: conditional', () => {
  it('conditional branches produce correct trace entries', () => {
    const { trace } = compileAndTest(
      function conditional(rnd) {
        const result = [];
        for (let i = 0; i < 6; i++) {
          const coin = rnd.choice([0, 1]);
          if (coin) {
            result.push(rnd.uniform(0, 1));
          } else {
            result.push(rnd.randint(0, 100));
          }
        }
        return result;
      },
    );
    // 6 coin flips + 6 branch values = 12 entries
    assert.equal(Object.keys(trace).length, 12);
  });
});

// ---------------------------------------------------------------------------
// 7. Multiple call sites for same nested function
// ---------------------------------------------------------------------------
describe('Compiler: multiple call sites', () => {
  it('different call sites produce different trace keys', () => {
    const { trace } = compileAndTest(
      function multiSite(rnd) {
        function makeBit() {
          return rnd.choice([0, 1]);
        }
        const a = makeBit();
        const b = makeBit();
        const c = makeBit();
        return [a, b, c];
      },
      { expectedEntries: 3 },
    );
    // Each call site should have a unique key
    const keys = Object.keys(trace);
    assert.equal(new Set(keys).size, 3, 'All 3 trace keys should be unique');
  });
});

// ---------------------------------------------------------------------------
// 8. Nested function with arguments
// ---------------------------------------------------------------------------
describe('Compiler: nested func with args', () => {
  it('nested function with arguments preserves args after __prefix__', () => {
    compileAndTest(
      function funcWithArgs(rnd) {
        function pick(lo, hi) {
          return rnd.randint(lo, hi);
        }
        const result = [];
        for (let i = 0; i < 5; i++) {
          result.push(pick(0, i + 1));
        }
        return result;
      },
      { expectedEntries: 5 },
    );
  });
});

// ---------------------------------------------------------------------------
// 9. Single rnd call (no loop)
// ---------------------------------------------------------------------------
describe('Compiler: single call', () => {
  it('single rnd call produces one trace entry', () => {
    compileAndTest(
      function singleCall(rnd) {
        return rnd.choice(['red', 'green', 'blue']);
      },
      { expectedEntries: 1, keyMustContain: ['choice'] },
    );
  });
});

// ---------------------------------------------------------------------------
// 10. No rnd calls
// ---------------------------------------------------------------------------
describe('Compiler: no rnd calls', () => {
  it('generator with no rnd calls produces empty trace', () => {
    compileAndTest(
      function noRnd(rnd) {
        return 42;
      },
      { expectedEntries: 0 },
    );
  });
});

// ---------------------------------------------------------------------------
// 11. Arrow function generator
// ---------------------------------------------------------------------------
describe('Compiler: arrow function', () => {
  it('arrow function with block body', () => {
    compileAndTest(
      (rnd) => {
        const bits = [];
        for (let i = 0; i < 5; i++) {
          bits.push(rnd.choice([0, 1]));
        }
        return bits;
      },
      { expectedEntries: 5, keyMustContain: ['choice'] },
    );
  });
});

// ---------------------------------------------------------------------------
// 12. Distinct keys per loop iteration
// ---------------------------------------------------------------------------
describe('Compiler: key uniqueness', () => {
  it('each loop iteration produces a distinct trace key', () => {
    const { trace } = compileAndTest(
      function uniqueKeys(rnd) {
        const result = [];
        for (let i = 0; i < 5; i++) {
          result.push(rnd.randint(0, 10));
        }
        return result;
      },
      { expectedEntries: 5 },
    );
    const keys = Object.keys(trace);
    assert.equal(new Set(keys).size, 5, 'All keys should be distinct');

    // Keys should contain iteration indices 0..4
    for (let i = 0; i < 5; i++) {
      assert.ok(
        keys.some(k => k.includes(`:${i}/`)),
        `Should find key with iteration index ${i}`,
      );
    }
  });
});

// ---------------------------------------------------------------------------
// 13. Compiled source inspection
// ---------------------------------------------------------------------------
describe('Compiler: source inspection', () => {
  it('_compiledSource contains __prefix__ and name:', () => {
    const compiled = compileGenerator(
      function inspect(rnd) {
        return rnd.choice([0, 1]);
      },
    );
    assert.ok(compiled._compiledSource.includes('__prefix__'));
    assert.ok(compiled._compiledSource.includes('name'));
  });
});
