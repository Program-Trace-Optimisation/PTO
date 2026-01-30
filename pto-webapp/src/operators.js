/**
 * operators.js — Op class providing search operators over traces.
 *
 * In PTO, search algorithms (solvers) never manipulate solutions directly.
 * Instead, they work through the Op class, which provides:
 *
 *   createInd()       — generate a random solution (empty trace → fresh sample)
 *   evaluateInd(sol)  — compute fitness of a solution's phenotype
 *   fixInd(geno)      — replay a (possibly modified) genotype through the
 *                        generator to produce a valid phenotype
 *   mutatePointInd(sol)          — mutate one random trace entry
 *   mutatePositionWiseInd(sol)   — mutate each entry with probability 1/len
 *   mutateRandomInd(sol)         — ignore input, create fresh random solution
 *   crossoverUniformInd(s1, s2)  — uniform crossover on aligned trace keys
 *   crossoverOnePointInd(s1, s2) — one-point crossover on aligned keys
 *   distanceInd(s1, s2)          — Manhattan distance over traces
 *
 * A Sol (solution) is a plain object { pheno, geno } where:
 *   - pheno: the observable solution (what the generator returns)
 *   - geno:  the trace — a dict mapping names to Dist objects
 *
 * The key insight: operators modify the trace, then fixInd() replays it
 * through the generator. This "repair" step ensures every offspring is a
 * valid solution regardless of how the trace was modified.
 */

/**
 * Compute the aligned keys between two solutions' genotypes.
 * Alignment = keys present in both, in sol1's order.
 *
 * @param {Object} geno1
 * @param {Object} geno2
 * @returns {Array<string|number>}
 */
function alignGenotypes(geno1, geno2) {
  const keys2 = new Set(Object.keys(geno2).map(k => String(k)));
  return Object.keys(geno1).filter(k => keys2.has(String(k)));
}

export class Op {
  /**
   * @param {Function} generator  Generator function (uses rnd internally)
   * @param {Function} fitness    Fitness function: phenotype → number
   * @param {Object}   opts
   * @param {Tracer}   opts.tracer  Tracer instance shared with rnd
   */
  constructor(generator, fitness, { tracer }) {
    this.generator = generator;
    this.fitness = fitness;
    this.tracer = tracer;
  }

  /**
   * Generate a fresh random solution.
   * @returns {{ pheno: *, geno: Object }}
   */
  createInd() {
    return this.tracer.play(this.generator, {});
  }

  /**
   * Evaluate a solution's fitness.
   * @param {{ pheno: * }} sol
   * @returns {number}
   */
  evaluateInd(sol) {
    return this.fitness(sol.pheno);
  }

  /**
   * Replay a (possibly modified) genotype through the generator to produce
   * a valid solution. This is the "repair" step — it ensures the phenotype
   * is consistent with the genotype after any operator modifies the trace.
   *
   * @param {Object} geno  Trace dict (name → Dist)
   * @returns {{ pheno: *, geno: Object }}
   */
  fixInd(geno) {
    return this.tracer.play(this.generator, geno);
  }

  /**
   * Point mutation: pick one random trace entry and re-sample it.
   * All other entries are preserved via replay.
   *
   * @param {{ pheno: *, geno: Object }} sol
   * @returns {{ pheno: *, geno: Object }}
   */
  mutatePointInd(sol) {
    const keys = Object.keys(sol.geno);
    if (keys.length === 0) return this.createInd();

    const newGeno = { ...sol.geno };
    const key = keys[Math.floor(Math.random() * keys.length)];
    newGeno[key] = newGeno[key].mutation();
    return this.fixInd(newGeno);
  }

  /**
   * Position-wise mutation: each trace entry mutates independently with
   * probability 1/len. Guarantees at least one mutation on average.
   *
   * @param {{ pheno: *, geno: Object }} sol
   * @returns {{ pheno: *, geno: Object }}
   */
  mutatePositionWiseInd(sol) {
    const keys = Object.keys(sol.geno);
    if (keys.length === 0) return this.createInd();

    const mutProb = 1 / keys.length;
    const newGeno = {};
    for (const key of keys) {
      newGeno[key] = Math.random() <= mutProb
        ? sol.geno[key].mutation()
        : sol.geno[key];
    }
    return this.fixInd(newGeno);
  }

  /**
   * Random mutation: ignore the input entirely, create a fresh solution.
   * Useful as a baseline or for restart strategies.
   *
   * @param {*} _sol  Ignored
   * @returns {{ pheno: *, geno: Object }}
   */
  mutateRandomInd(_sol) {
    return this.createInd();
  }

  /**
   * Uniform crossover: for each aligned trace key, call dist.crossover()
   * to pick one parent's value. Non-shared keys are inherited from their
   * respective parent.
   *
   * @param {{ geno: Object }} sol1
   * @param {{ geno: Object }} sol2
   * @returns {{ pheno: *, geno: Object }}
   */
  crossoverUniformInd(sol1, sol2) {
    const alignment = alignGenotypes(sol1.geno, sol2.geno);

    // Start with all keys from both parents
    const newGeno = { ...sol1.geno, ...sol2.geno };

    // Recombine aligned keys
    for (const key of alignment) {
      newGeno[key] = sol1.geno[key].crossover(sol2.geno[key]);
    }

    return this.fixInd(newGeno);
  }

  /**
   * One-point crossover: pick a random cut point along the aligned keys.
   * Take sol1's values before the cut, sol2's values after.
   *
   * @param {{ geno: Object }} sol1
   * @param {{ geno: Object }} sol2
   * @returns {{ pheno: *, geno: Object }}
   */
  crossoverOnePointInd(sol1, sol2) {
    const alignment = alignGenotypes(sol1.geno, sol2.geno);
    if (alignment.length === 0) {
      // No common keys — just merge
      return this.fixInd({ ...sol1.geno, ...sol2.geno });
    }

    const cutPoint = Math.floor(Math.random() * alignment.length);
    const newGeno = { ...sol1.geno, ...sol2.geno };

    // Before cut: sol1, after cut: sol2 (sol2 already in newGeno from spread)
    for (let i = 0; i < cutPoint; i++) {
      newGeno[alignment[i]] = sol1.geno[alignment[i]];
    }
    for (let i = cutPoint; i < alignment.length; i++) {
      newGeno[alignment[i]] = sol2.geno[alignment[i]];
    }

    return this.fixInd(newGeno);
  }

  /**
   * Manhattan distance between two solutions, computed over their traces.
   * For common keys: sum of per-entry distances.
   * For non-shared keys: count of symmetric difference.
   *
   * @param {{ geno: Object }} sol1
   * @param {{ geno: Object }} sol2
   * @returns {number}
   */
  distanceInd(sol1, sol2) {
    const keys1 = new Set(Object.keys(sol1.geno).map(String));
    const keys2 = new Set(Object.keys(sol2.geno).map(String));

    // Common keys: sum distances
    let dist = 0;
    for (const key of keys1) {
      if (keys2.has(key)) {
        dist += sol1.geno[key].distance(sol2.geno[key]);
      }
    }

    // Symmetric difference
    for (const key of keys1) {
      if (!keys2.has(key)) dist++;
    }
    for (const key of keys2) {
      if (!keys1.has(key)) dist++;
    }

    return dist;
  }
}
