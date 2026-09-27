/**
 * Runs every built-in example of the playground (ui/examples.js) with both
 * naming modes, as the UI would, for a few iterations.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { run } from '../src/run.js';

const source = readFileSync(new URL('../ui/examples.js', import.meta.url), 'utf-8');
const EXAMPLES = new Function(`${source}\nreturn EXAMPLES;`)();

describe('Playground examples', () => {
  it('there are examples', () => {
    assert.ok(EXAMPLES.length > 0);
  });

  for (const ex of EXAMPLES) {
    for (const naming of ['linear', 'structural']) {
      for (const distType of ['coarse', 'fine']) {
        it(`${ex.name} (${naming}, ${distType})`, () => {
          const generator = eval(`(${ex.generator})`);
          const fitness = eval(`(${ex.fitness})`);
          const iterKey = ex.solver === 'geneticAlgorithm' ? 'nGeneration' : 'nIteration';
          const result = run(generator, fitness, {
            better: ex.better === 'min' ? Math.min : Math.max,
            naming,
            distType,
            solver: ex.solver,
            [iterKey]: 5,
            returnHistory: true,
          });
          assert.ok(Number.isFinite(result.fitness), `fitness ${result.fitness}`);
          assert.equal(result.fitness, fitness(result.sol.pheno));
          assert.ok(result.history.length > 0);
        });
      }
    }
  }
});
