/**
 * browser.js — Browser entry point for PTO.
 * Bundles all PTO exports into a single global `PTO` object.
 */
export { run } from './run.js';
export { Tracer } from './tracer.js';
export { createRnd } from './rnd.js';
export { Op } from './operators.js';
export { compileGenerator } from './compiler.js';
export { hillClimber } from './solvers/hillClimber.js';
export { randomSearch } from './solvers/randomSearch.js';
export { geneticAlgorithm } from './solvers/geneticAlgorithm.js';
