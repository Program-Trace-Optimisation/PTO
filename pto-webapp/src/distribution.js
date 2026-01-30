/**
 * distribution.js — Base distribution class and 4 distribution subclasses
 * with both coarse and fine operators.
 *
 * In PTO, every random decision made during solution generation is modelled as
 * a "distribution" object. The distribution records:
 *   - funName: which random primitive was called (e.g. "uniform", "choice")
 *   - args: the arguments passed (e.g. [0, 10] for randint(0, 10))
 *   - val: the sampled value
 *
 * Two operator regimes:
 *
 *   COARSE (default):
 *     - mutation: re-sample from scratch
 *     - crossover: pick one parent's value at random
 *     - repair: re-sample
 *     - distance: binary (0 or 1)
 *
 *   FINE:
 *     - mutation: domain-aware incremental perturbation
 *     - crossover: domain-aware value blending
 *     - repair: intelligent value mapping preserving domain semantics
 *     - distance: normalized continuous metric
 *
 * The `mode` property ('coarse' or 'fine') controls which regime is used.
 * The mutation(), crossover(), repair(), and distance() methods dispatch
 * to the appropriate implementation, so callers (operators.js) need not
 * know which mode is active.
 *
 * Four distribution types correspond to PTO's four random primitives:
 *   - RandomReal:  continuous values via uniform(a, b)
 *   - RandomInt:   integer values via randint(a, b)
 *   - RandomCat:   categorical values via choice(seq)
 *   - RandomSeq:   ordered subsequences via sample(seq, k)
 */

// ---------------------------------------------------------------------------
// Gaussian random helper (Box-Muller transform)
// ---------------------------------------------------------------------------
function gaussRandom(mu = 0, sigma = 1) {
  let u, v;
  do { u = Math.random(); } while (u === 0);
  v = Math.random();
  return mu + sigma * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// ---------------------------------------------------------------------------
// Base class
// ---------------------------------------------------------------------------

export class Dist {
  /**
   * @param {string} funName  Name of the random primitive (e.g. "uniform")
   * @param {Array}  args     Arguments to the primitive (shallow-copied)
   * @param {*}      [val]    Optional pre-set value
   */
  constructor(funName, args, val) {
    this.funName = funName;
    this.args = Array.from(args);
    this.val = val !== undefined ? val : null;
    /** @type {'coarse'|'fine'} */
    this.mode = 'coarse';
  }

  /** Sample a new value. Subclasses override this. */
  sample() {
    throw new Error('Dist.sample() must be overridden by subclass');
  }

  /**
   * Repair: adapt a value from a previous trace entry whose distribution
   * parameters have changed.
   * @param {Dist} other  The old trace entry
   */
  repair(other) {
    if (this.mode === 'fine') {
      this._fineRepair(other);
    } else {
      this.sample();
    }
  }

  /**
   * Mutation: return a new Dist with a modified value.
   * @returns {Dist}
   */
  mutation() {
    if (this.mode === 'fine') {
      return this._fineMutation();
    }
    const offspring = this.clone();
    offspring.sample();
    return offspring;
  }

  /**
   * Crossover: combine this distribution's value with another's.
   * @param {Dist} other
   * @returns {Dist}
   */
  crossover(other) {
    if (this.mode === 'fine') {
      return this._fineCrossover(other);
    }
    const child = this.clone();
    child.val = Math.random() < 0.5 ? this.val : other.val;
    return child;
  }

  /**
   * Distance between two distribution values.
   * @param {Dist} other
   * @returns {number}
   */
  distance(other) {
    if (this.mode === 'fine') {
      return this._fineDistance(other);
    }
    return this.val === other.val ? 0 : 1;
  }

  /**
   * Search space size for this distribution dimension.
   * @returns {number}
   */
  size() {
    return 2;
  }

  /**
   * Check structural equality (same funName and args).
   * Used by the tracer to decide whether to reuse a cached value.
   * @param {Dist} other
   * @returns {boolean}
   */
  matches(other) {
    if (this.funName !== other.funName) return false;
    if (this.args.length !== other.args.length) return false;
    for (let i = 0; i < this.args.length; i++) {
      const a = this.args[i];
      const b = other.args[i];
      if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length || a.some((v, j) => v !== b[j])) return false;
      } else if (a !== b) {
        return false;
      }
    }
    return true;
  }

  /**
   * Return a deep copy of this distribution.
   * @returns {Dist}
   */
  clone() {
    const c = new this.constructor(...this.args, this.val);
    c.mode = this.mode;
    return c;
  }

  // Fine operator defaults (subclasses override)
  _fineMutation() { const o = this.clone(); o.sample(); return o; }
  _fineCrossover(other) { return this.crossover(other); }
  _fineRepair(_other) { this.sample(); }
  _fineDistance(other) { return this.val === other.val ? 0 : 1; }
}

// ---------------------------------------------------------------------------
// RandomReal — continuous values via uniform(a, b)
//
// Fine mutation:  Gaussian perturbation with sigma = 0.1 * range, clamped
// Fine crossover: Uniform interpolation between parent values
// Fine repair:    Proportional mapping from other's domain to this domain
// Fine distance:  Normalized absolute difference, capped at 1
// ---------------------------------------------------------------------------

export class RandomReal extends Dist {
  /**
   * @param {number} a    Lower bound (inclusive)
   * @param {number} b    Upper bound
   * @param {number} [val]
   */
  constructor(a, b, val) {
    super('uniform', [a, b], val);
  }

  get min() { return this.args[0]; }
  get max() { return this.args[1]; }
  get range() { return this.max - this.min; }

  sample() {
    this.val = this.min + Math.random() * this.range;
  }

  /** Clamp value to [min, max]. */
  _clamp() {
    this.val = Math.min(Math.max(this.min, this.val), this.max);
  }

  size() { return Infinity; }

  // -- Coarse distance (still absolute, not binary) -------------------------
  distance(other) {
    if (this.mode === 'fine') return this._fineDistance(other);
    return Math.abs(this.val - other.val);
  }

  // -- Fine operators -------------------------------------------------------

  _fineMutation() {
    const offspring = this.clone();
    offspring.val = this.val + gaussRandom(0, 0.1 * this.range);
    offspring._clamp();
    return offspring;
  }

  _fineCrossover(other) {
    const child = this.clone();
    if (this.funName === other.funName) {
      const lo = Math.min(this.val, other.val);
      const hi = Math.max(this.val, other.val);
      child.val = lo + Math.random() * (hi - lo);
    } else {
      child.val = Math.random() < 0.5 ? this.val : other.val;
    }
    return child;
  }

  _fineRepair(other) {
    if (this.funName !== other.funName || other.range === 0) {
      this.sample();
      return;
    }
    // Proportional mapping from other's domain to this domain
    this.val = ((other.val - other.min) / other.range) * this.range + this.min;
    this._clamp();
  }

  _fineDistance(other) {
    if (this.range === 0) return 0;
    return Math.min(1, Math.abs(this.val - other.val) / this.range);
  }
}

// ---------------------------------------------------------------------------
// RandomInt — integer values via randint(a, b), inclusive on both ends
//
// Fine mutation:  ±1 step with retry (up to 10 attempts to get a different value)
// Fine crossover: Uniform random integer between parent values
// Fine repair:    Proportional step mapping from other's domain
// Fine distance:  Normalized absolute difference, capped at 1
// ---------------------------------------------------------------------------

export class RandomInt extends Dist {
  /**
   * @param {number} a    Lower bound (inclusive)
   * @param {number} b    Upper bound (inclusive)
   * @param {number} [val]
   */
  constructor(a, b, val) {
    super('randint', [a, b], val);
  }

  get min() { return this.args[0]; }
  get max() { return this.args[1]; }
  get span() { return this.max - this.min; }

  sample() {
    this.val = this.min + Math.floor(Math.random() * (this.span + 1));
  }

  /** Round to nearest integer and clamp to bounds. */
  _repair() {
    this.val = Math.min(Math.max(this.min, Math.round(this.val)), this.max);
  }

  size() { return this.span + 1; }

  // Coarse distance is already absolute
  distance(other) {
    if (this.mode === 'fine') return this._fineDistance(other);
    return Math.abs(this.val - other.val);
  }

  // -- Fine operators -------------------------------------------------------

  _fineMutation() {
    const offspring = this.clone();
    for (let attempt = 0; attempt < 10; attempt++) {
      offspring.val = this.val + (Math.random() < 0.5 ? -1 : 1);
      offspring._repair();
      if (offspring.val !== this.val) break;
    }
    return offspring;
  }

  _fineCrossover(other) {
    const child = this.clone();
    if (this.funName === other.funName) {
      const lo = Math.min(this.val, other.val);
      const hi = Math.max(this.val, other.val);
      child.val = lo + Math.floor(Math.random() * (hi - lo + 1));
    } else {
      child.val = Math.random() < 0.5 ? this.val : other.val;
    }
    return child;
  }

  _fineRepair(other) {
    if (this.funName !== other.funName || other.span === 0) {
      this.sample();
      return;
    }
    // Proportional mapping: map step-relative position
    this.val = ((other.val - other.min) / other.span) * this.span + this.min;
    this._repair();
  }

  _fineDistance(other) {
    if (this.span === 0) return 0;
    return Math.min(1, Math.abs(this.val - other.val) / this.span);
  }
}

// ---------------------------------------------------------------------------
// RandomCat — categorical (symbol) values via choice(seq)
//
// Fine mutation:  Choose a *different* value from the sequence
// Fine crossover: Same as coarse (random parent selection — no interpolation
//                 makes sense for categorical values)
// Fine repair:    If other's value exists in this seq, keep it; otherwise
//                 prefer values not in other's seq, else random
// Fine distance:  Binary (0 or 1) — no continuous metric for categories
// ---------------------------------------------------------------------------

export class RandomCat extends Dist {
  /**
   * @param {Array} seq   Sequence to choose from
   * @param {*}     [val]
   */
  constructor(seq, val) {
    super('choice', [seq], val);
  }

  get seq() { return this.args[0]; }

  sample() {
    const s = this.seq;
    this.val = s[Math.floor(Math.random() * s.length)];
  }

  size() { return this.seq.length; }

  // -- Fine operators -------------------------------------------------------

  _fineMutation() {
    const offspring = this.clone();
    const s = this.seq;
    if (new Set(s).size >= 2) {
      const others = s.filter(v => v !== this.val);
      offspring.val = others[Math.floor(Math.random() * others.length)];
    }
    return offspring;
  }

  _fineCrossover(other) {
    // Categorical: no interpolation possible, random parent
    const child = this.clone();
    child.val = Math.random() < 0.5 ? this.val : other.val;
    return child;
  }

  _fineRepair(other) {
    const s = this.seq;
    if (s.includes(other.val)) {
      // Other's value is valid in our sequence — keep it
      this.val = other.val;
    } else {
      // Prefer values not in other's seq, else random
      const otherSeq = other.args && other.args[0] ? other.args[0] : [];
      const diff = s.filter(v => !otherSeq.includes(v));
      if (diff.length > 0) {
        this.val = diff[Math.floor(Math.random() * diff.length)];
      } else {
        this.sample();
      }
    }
  }

  // Fine distance is still binary for categories
  _fineDistance(other) {
    return this.val === other.val ? 0 : 1;
  }
}

// ---------------------------------------------------------------------------
// RandomSeq — ordered subsequence via sample(seq, k)
//
// Fine mutation:  50% swap two positions, 50% replace one element with an
//                 unused element from the pool
// Fine crossover: One-point crossover with intelligent swap/replace repair
// Fine repair:    Sample fresh then crossover with other (full-length)
// Fine distance:  Edit distance (swaps + replacements + length difference)
// ---------------------------------------------------------------------------

export class RandomSeq extends Dist {
  /**
   * @param {Array}  seq  Source sequence
   * @param {number} k    Number of elements to sample
   * @param {Array}  [val]
   */
  constructor(seq, k, val) {
    super('sample', [seq, k], val);
  }

  get seq() { return this.args[0]; }
  get k() { return this.args[1]; }

  /** Fisher-Yates on a copy, take first k elements. */
  sample() {
    const copy = Array.from(this.seq);
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    this.val = copy.slice(0, this.k);
  }

  size() {
    let result = 1;
    for (let i = 0; i < this.k; i++) {
      result *= this.seq.length - i;
    }
    return result;
  }

  /**
   * Compute the "pool" — elements in seq not currently in val.
   * Used by fine mutation, crossover, and repair.
   */
  _pool() {
    const used = [...this.val];
    const pool = [];
    for (const item of this.seq) {
      const idx = used.indexOf(item);
      if (idx >= 0) {
        used.splice(idx, 1); // consume one copy
      } else {
        pool.push(item);
      }
    }
    return pool;
  }

  // -- Fine operators -------------------------------------------------------

  _fineMutation() {
    const offspring = this.clone();
    const v = [...this.val];
    const pool = this._pool();

    if (v.length < 2) {
      // Can only replace if pool is non-empty
      if (pool.length > 0 && v.length > 0) {
        const idx = Math.floor(Math.random() * v.length);
        pool.push(v[idx]); // return old to pool
        v[idx] = pool[Math.floor(Math.random() * (pool.length - 1))]; // pick from pool (before push)
        // Simpler: just pick from pool directly
        v[idx] = pool[Math.floor(Math.random() * pool.length)];
      }
      offspring.val = v;
      return offspring;
    }

    if (pool.length === 0 || Math.random() < 0.5) {
      // Swap two positions
      const i = Math.floor(Math.random() * v.length);
      let j = Math.floor(Math.random() * (v.length - 1));
      if (j >= i) j++;
      [v[i], v[j]] = [v[j], v[i]];
    } else {
      // Replace one element with a pool element
      const idx = Math.floor(Math.random() * v.length);
      const poolIdx = Math.floor(Math.random() * pool.length);
      v[idx] = pool[poolIdx];
    }
    offspring.val = v;
    return offspring;
  }

  _fineCrossover(other) {
    const child = this.clone();
    const seq1 = [...this.val];
    const seq2 = other.val;
    const minLen = Math.min(seq1.length, seq2.length);

    if (minLen === 0) {
      child.val = seq1;
      return child;
    }

    const crossSeq = [...seq1];
    const pool = this._pool();
    const point = Math.floor(Math.random() * minLen);

    for (let i = 0; i < point; i++) {
      if (crossSeq[i] === seq2[i]) continue;

      // Try to find seq2[i] later in crossSeq and swap
      const laterIdx = crossSeq.indexOf(seq2[i], i + 1);
      if (laterIdx >= 0) {
        [crossSeq[i], crossSeq[laterIdx]] = [crossSeq[laterIdx], crossSeq[i]];
      } else {
        // Try to replace from pool
        const poolIdx = pool.indexOf(seq2[i]);
        if (poolIdx >= 0) {
          pool.splice(poolIdx, 1);
          pool.push(crossSeq[i]);
          crossSeq[i] = seq2[i];
        }
        // else: can't match, keep current
      }
    }

    child.val = crossSeq;
    return child;
  }

  _fineRepair(other) {
    // Sample fresh, then crossover with other using full length
    this.sample();
    if (!other.val || other.val.length === 0) return;

    const pool = this._pool();
    const seq2 = other.val;
    const crossSeq = [...this.val];
    const minLen = Math.min(crossSeq.length, seq2.length);

    for (let i = 0; i < minLen; i++) {
      if (crossSeq[i] === seq2[i]) continue;

      const laterIdx = crossSeq.indexOf(seq2[i], i + 1);
      if (laterIdx >= 0) {
        [crossSeq[i], crossSeq[laterIdx]] = [crossSeq[laterIdx], crossSeq[i]];
      } else {
        const poolIdx = pool.indexOf(seq2[i]);
        if (poolIdx >= 0) {
          pool.splice(poolIdx, 1);
          pool.push(crossSeq[i]);
          crossSeq[i] = seq2[i];
        }
      }
    }

    this.val = crossSeq;
  }

  _fineDistance(other) {
    const seq1 = [...this.val];
    const seq2 = other.val;
    const minLen = Math.min(seq1.length, seq2.length);
    const pool = this._pool();
    let swaps = 0;
    let replacements = 0;

    for (let i = 0; i < minLen; i++) {
      if (seq1[i] === seq2[i]) continue;

      const laterIdx = seq1.indexOf(seq2[i], i + 1);
      if (laterIdx >= 0) {
        swaps++;
        [seq1[i], seq1[laterIdx]] = [seq1[laterIdx], seq1[i]];
      } else {
        const poolIdx = pool.indexOf(seq2[i]);
        if (poolIdx >= 0) {
          pool.splice(poolIdx, 1);
          pool.push(seq1[i]);
          seq1[i] = seq2[i];
        }
        replacements++;
      }
    }

    return swaps + replacements + Math.abs(this.val.length - seq2.length);
  }

  // -- Coarse distance (positional diff) ------------------------------------
  distance(other) {
    if (this.mode === 'fine') return this._fineDistance(other);
    const a = this.val;
    const b = other.val;
    const len = Math.min(a.length, b.length);
    let diff = Math.abs(a.length - b.length);
    for (let i = 0; i < len; i++) {
      if (a[i] !== b[i]) diff++;
    }
    return diff;
  }

  // -- Coarse crossover (pick one parent) -----------------------------------
  crossover(other) {
    if (this.mode === 'fine') return this._fineCrossover(other);
    const child = this.clone();
    child.val = Math.random() < 0.5 ? [...this.val] : [...other.val];
    return child;
  }

  clone() {
    const c = new RandomSeq(this.seq, this.k, this.val ? [...this.val] : null);
    c.mode = this.mode;
    return c;
  }
}
