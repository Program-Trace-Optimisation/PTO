/**
 * Tests for compiler.js on language constructs beyond plain for/while loops.
 *
 * Every rnd call executed by the generator must get its own structured trace
 * key (starting with "root/"). If two calls get the same key, the second
 * overwrites the first in the trace, so replay no longer reproduces the
 * solution; the tracer now rejects that with an error.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { compileGenerator } from '../src/compiler.js';
import { Tracer } from '../src/tracer.js';
import { createRnd } from '../src/rnd.js';

function play(generator) {
  const compiled = compileGenerator(generator);
  const tracer = new Tracer();
  const rnd = createRnd(tracer);
  const first = tracer.play(() => compiled(rnd), {});
  const replay = tracer.play(() => compiled(rnd), first.geno);
  assert.deepEqual(replay.pheno, first.pheno, 'replay should reproduce the solution');
  const keys = Object.keys(first.geno);
  for (const key of keys) {
    assert.ok(key.startsWith('root/'), `key "${key}" should be structured`);
  }
  return { keys, pheno: first.pheno, compiled };
}

function assertEntries(generator, expected) {
  const { keys } = play(generator);
  assert.equal(keys.length, expected, `expected ${expected} distinct keys, got ${keys.length}: ${keys.join(', ')}`);
  return keys;
}

describe('Compiler: array callbacks', () => {
  it('map callback without index parameter', () => {
    assertEntries((rnd) => {
      return Array(5).fill(0).map(() => rnd.choice([0, 1]));
    }, 5);
  });

  it('map callback with its own index parameter', () => {
    assertEntries((rnd) => {
      return [10, 20, 30].map((x, i) => x + i + rnd.random());
    }, 3);
  });

  it('Array.from with a length and a callback', () => {
    assertEntries((rnd) => {
      return Array.from({ length: 4 }, () => rnd.random());
    }, 4);
  });

  it('forEach with a block-body callback', () => {
    assertEntries((rnd) => {
      const out = [];
      [1, 2, 3].forEach((x) => { out.push(x * rnd.random()); });
      return out;
    }, 3);
  });

  it('nested maps', () => {
    assertEntries((rnd) => {
      return [0, 1, 2].map(() => [0, 1, 2].map(() => rnd.choice([0, 1])));
    }, 9);
  });

  it('map over the result of an rnd call', () => {
    assertEntries((rnd) => {
      return rnd.sample([1, 2, 3, 4], 2).map((x) => x * rnd.random());
    }, 3);
  });

  it('nested function passed as the callback', () => {
    assertEntries((rnd) => {
      function bit() {
        return rnd.choice([0, 1]);
      }
      return Array.from({ length: 4 }, bit).concat([0, 1].map(bit));
    }, 6);
  });
});

describe('Compiler: loops with continue', () => {
  it('for loop with continue after the rnd call', () => {
    assertEntries((rnd) => {
      const out = [];
      for (let i = 0; i < 5; i++) {
        out.push(rnd.random());
        continue;
      }
      return out;
    }, 5);
  });

  it('while loop with continue', () => {
    assertEntries((rnd) => {
      const out = [];
      let i = 0;
      while (i < 4) {
        i++;
        out.push(rnd.random());
        if (i > 0) continue;
      }
      return out;
    }, 4);
  });

  it('for-of loop with continue', () => {
    assertEntries((rnd) => {
      const out = [];
      for (const x of [1, 2, 3]) {
        out.push(x * rnd.random());
        continue;
      }
      return out;
    }, 3);
  });

  it('labelled continue to an outer loop', () => {
    assertEntries((rnd) => {
      const out = [];
      outer: for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
          out.push(rnd.random());
          continue outer;
        }
      }
      return out;
    }, 3);
  });
});

describe('Compiler: other statements', () => {
  it('do-while loop', () => {
    assertEntries((rnd) => {
      const out = [];
      let i = 0;
      do {
        out.push(rnd.random());
        i++;
      } while (i < 4);
      return out;
    }, 4);
  });

  it('try / catch / finally', () => {
    assertEntries((rnd) => {
      const out = [];
      for (let i = 0; i < 3; i++) {
        try {
          out.push(rnd.random());
        } catch (e) {
          out.push(rnd.random());
        } finally {
          out.push(rnd.random());
        }
      }
      return out;
    }, 6);
  });

  it('switch statement', () => {
    assertEntries((rnd) => {
      const out = [];
      for (let i = 0; i < 3; i++) {
        switch (rnd.choice(['a', 'b'])) {
          case 'a':
            out.push(rnd.random());
            break;
          default:
            out.push(rnd.random());
        }
      }
      return out;
    }, 6);
  });

  it('rnd calls in new expressions and method chains', () => {
    assertEntries((rnd) => {
      const a = new Array(rnd.randint(1, 3)).fill(0);
      const b = rnd.random().toFixed(2);
      return [a, b];
    }, 2);
  });
});

describe('Compiler: generator forms', () => {
  it('arrow function with an expression body', () => {
    assertEntries((rnd) => [rnd.random(), rnd.random()], 2);
  });

  it('columns on the first line are not shifted', () => {
    const { keys } = play((rnd) => { return rnd.random(); });
    assert.deepEqual(keys, ['root/generator@1.0/random@1.18']);
  });
});

describe('Tracer: duplicate names', () => {
  it('rejects two samples with the same name in one play', () => {
    const tracer = new Tracer();
    const rnd = createRnd(tracer);
    assert.throws(
      () => tracer.play(() => [rnd.random({ name: 'x' }), rnd.random({ name: 'x' })], {}),
      /not unique/,
    );
    assert.equal(tracer.active, false);
  });
});
