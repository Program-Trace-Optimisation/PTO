/**
 * tracer.js — Trace recording and replay engine.
 *
 * The tracer is the heart of PTO. It sits between the generator function and
 * the random primitives (rnd), intercepting every random decision and recording
 * it in a "trace" — a dictionary mapping location keys to Dist objects.
 *
 * How it works:
 *   1. When the tracer is INACTIVE, rnd calls just sample normally.
 *   2. When the tracer is ACTIVE (during play()), each rnd call goes through
 *      tracer.sample(name, dist), which either:
 *        a) Reuses a value from a previous trace (if the name exists and the
 *           distribution parameters match),
 *        b) Repairs the value (if the name exists but parameters changed), or
 *        c) Samples a fresh value (if the name is new).
 *
 * Linear naming: When no explicit name is given, the tracer assigns sequential
 * integer keys (0, 1, 2, ...). This is the simplest scheme and works for any
 * generator. Structural naming (Slice 2) will inject explicit name strings
 * via AST transformation.
 *
 * The trace (genotype) fully determines the solution (phenotype) when replayed
 * through the same generator. This is what makes PTO's operators work: mutate
 * or crossover the trace, replay it, and get a new valid solution.
 */

export class Tracer {
  constructor() {
    /** Whether trace recording is currently active. */
    this.active = false;

    /** Trace from a previous solution, used to guide replay. */
    this.inputTrace = {};

    /** Trace being built during the current play() call. */
    this.outputTrace = {};

    /** Counter for linear (auto-increment) naming. */
    this.counter = 0;
  }

  /**
   * Record or replay a single random decision.
   *
   * Called by rnd methods. When active, this either reuses a value from the
   * input trace (if the name matches and distribution parameters agree),
   * repairs the value (if parameters changed), or samples fresh.
   *
   * @param {string|number|null} name  Trace key. null → auto-assign integer.
   * @param {Dist} dist  Distribution object (not yet sampled).
   * @returns {*}  The sampled/replayed value.
   */
  sample(name, dist) {
    if (!this.active) {
      dist.sample();
      return dist.val;
    }

    // Auto-assign linear name if none provided
    if (name == null) {
      name = this.counter++;
    }

    // Look up in input trace
    if (name in this.inputTrace) {
      const traceDist = this.inputTrace[name];
      if (dist.matches(traceDist)) {
        // Same distribution parameters → reuse cached value
        dist.val = traceDist.val;
      } else {
        // Parameters changed → repair (coarse: re-sample)
        dist.repair(traceDist);
      }
    } else {
      // New entry → sample fresh
      dist.sample();
    }

    this.outputTrace[name] = dist;
    return dist.val;
  }

  /**
   * Run a generator function under tracing, producing a solution and its trace.
   *
   * @param {Function} generator  Generator function that calls rnd methods.
   * @param {Object}   trace      Input trace to replay from (empty {} for fresh).
   * @returns {{ pheno: *, geno: Object }}  The phenotype and its genotype trace.
   */
  play(generator, trace) {
    this.active = true;
    this.inputTrace = trace;
    this.outputTrace = {};
    this.counter = 0;

    let pheno;
    try {
      pheno = generator();
    } finally {
      this.active = false;
    }

    return { pheno, geno: this.outputTrace };
  }
}
