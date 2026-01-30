/**
 * rnd.js — Traced random wrapper.
 *
 * In PTO, all randomness in a generator function must go through `rnd` rather
 * than calling Math.random() directly. This allows the tracer to intercept
 * and record every random decision, building the trace (genotype).
 *
 * The rnd object exposes exactly 4 pure primitives (none mutate their arguments):
 *
 *   rnd.uniform(a, b)     → float in [a, b)        → RandomReal distribution
 *   rnd.randint(a, b)     → integer in [a, b]       → RandomInt distribution
 *   rnd.choice(seq)       → element from seq         → RandomCat distribution
 *   rnd.sample(seq, k)    → k distinct elements      → RandomSeq distribution
 *
 * Each call creates a Dist object and delegates to tracer.sample(), which
 * handles recording/replaying. An optional `{ name }` parameter allows
 * explicit trace keys (used by the structural naming compiler in Slice 2);
 * when omitted, the tracer assigns sequential integer keys.
 *
 * Factory pattern: createRnd(tracer) returns a new rnd object bound to the
 * given tracer. This allows multiple independent tracing contexts.
 */

import { RandomReal, RandomInt, RandomCat, RandomSeq } from './distribution.js';

/**
 * Create a traced random object bound to the given tracer.
 *
 * @param {Tracer} tracer  The tracer instance to record decisions in.
 * @param {Object} [opts]
 * @param {'coarse'|'fine'} [opts.distType='coarse']  Distribution operator mode.
 * @returns {Object}  rnd object with uniform, randint, choice, sample methods.
 */
export function createRnd(tracer, { distType = 'coarse' } = {}) {
  function withMode(dist) {
    dist.mode = distType;
    return dist;
  }

  return {
    /**
     * Sample a uniform real value in [a, b).
     * @param {number} a  Lower bound (inclusive)
     * @param {number} b  Upper bound (exclusive)
     * @param {Object} [opts]
     * @param {string|number} [opts.name]  Explicit trace key
     * @returns {number}
     */
    uniform(a, b, { name } = {}) {
      return tracer.sample(name ?? null, withMode(new RandomReal(a, b)));
    },

    /**
     * Sample a random integer in [a, b] (inclusive both ends).
     * @param {number} a  Lower bound (inclusive)
     * @param {number} b  Upper bound (inclusive)
     * @param {Object} [opts]
     * @param {string|number} [opts.name]  Explicit trace key
     * @returns {number}
     */
    randint(a, b, { name } = {}) {
      return tracer.sample(name ?? null, withMode(new RandomInt(a, b)));
    },

    /**
     * Choose a random element from a sequence.
     * @param {Array} seq  Non-empty array to choose from
     * @param {Object} [opts]
     * @param {string|number} [opts.name]  Explicit trace key
     * @returns {*}
     */
    choice(seq, { name } = {}) {
      return tracer.sample(name ?? null, withMode(new RandomCat(seq)));
    },

    /**
     * Sample k distinct elements from seq without replacement.
     * Returns a new array; does not mutate the input.
     * @param {Array}  seq  Source sequence
     * @param {number} k    Number of elements to draw
     * @param {Object} [opts]
     * @param {string|number} [opts.name]  Explicit trace key
     * @returns {Array}
     */
    sample(seq, k, { name } = {}) {
      return tracer.sample(name ?? null, withMode(new RandomSeq(seq, k)));
    },

    /**
     * Sample a uniform real value in [0, 1). Shorthand for uniform(0, 1).
     * @param {Object} [opts]
     * @param {string|number} [opts.name]  Explicit trace key
     * @returns {number}
     */
    random({ name } = {}) {
      return tracer.sample(name ?? null, withMode(new RandomReal(0, 1)));
    },
  };
}
