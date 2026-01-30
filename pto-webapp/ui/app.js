/**
 * app.js — PTO Playground UI controller.
 *
 * Wires Monaco editors, Chart.js, and the PTO engine bundle together.
 * Runs optimization synchronously (generator functions are fast enough),
 * using requestAnimationFrame to keep the UI responsive during long runs.
 */

// ── Built-in Examples ──────────────────────────────────────────

const EXAMPLES = [
  {
    name: 'OneMax (20 bits)',
    generator: `(rnd) => {
  const bits = [];
  for (let i = 0; i < 20; i++) {
    bits.push(rnd.choice([0, 1]));
  }
  return bits;
}`,
    fitness: `(solution) => {
  return solution.reduce((sum, bit) => sum + bit, 0);
}`,
    better: 'max',
    solver: 'hillClimber',
    iterations: 200,
  },
  {
    name: 'Sphere (10D, minimize)',
    generator: `(rnd) => {
  const x = [];
  for (let i = 0; i < 10; i++) {
    x.push(rnd.uniform(-5.12, 5.12));
  }
  return x;
}`,
    fitness: `(x) => {
  return x.reduce((sum, xi) => sum + xi * xi, 0);
}`,
    better: 'min',
    solver: 'hillClimber',
    iterations: 500,
  },
  {
    name: 'Hello World',
    generator: `(rnd) => {
  const target = "Hello World";
  const chars = [];
  for (let i = 0; i < target.length; i++) {
    chars.push(rnd.randint(32, 126));
  }
  return String.fromCharCode(...chars);
}`,
    fitness: `(s) => {
  const target = "Hello World";
  let score = 0;
  for (let i = 0; i < target.length; i++) {
    score -= Math.abs(s.charCodeAt(i) - target.charCodeAt(i));
  }
  return score;
}`,
    better: 'max',
    solver: 'hillClimber',
    iterations: 1000,
  },
  {
    name: 'OneMax (GA, 50 bits)',
    generator: `(rnd) => {
  const bits = [];
  for (let i = 0; i < 50; i++) {
    bits.push(rnd.choice([0, 1]));
  }
  return bits;
}`,
    fitness: `(solution) => {
  return solution.reduce((sum, bit) => sum + bit, 0);
}`,
    better: 'max',
    solver: 'geneticAlgorithm',
    iterations: 100,
  },
  {
    name: 'TSP (8 cities)',
    generator: `(rnd) => {
  // 8 cities: return a permutation via rnd.sample
  const cities = [0, 1, 2, 3, 4, 5, 6, 7];
  return rnd.sample(cities, cities.length);
}`,
    fitness: `(tour) => {
  // Random city coordinates (fixed seed for reproducibility)
  const coords = [
    [0, 0], [1, 5], [5, 2], [6, 6],
    [8, 3], [2, 8], [7, 9], [3, 1]
  ];
  let dist = 0;
  for (let i = 0; i < tour.length; i++) {
    const a = coords[tour[i]];
    const b = coords[tour[(i + 1) % tour.length]];
    dist += Math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2);
  }
  return -dist; // Negate: PTO maximizes, we want shortest tour
}`,
    better: 'max',
    solver: 'geneticAlgorithm',
    iterations: 100,
  },
  {
    name: 'Neural Network (nested loops)',
    generator: `(rnd) => {
  // 2-layer NN: 4 inputs → up to 6 hidden → 4 outputs
  // Nested loops: layers × neurons × weights
  var nInputs = 4;
  var nOutputs = 4;
  var nHidden = rnd.randint(1, 6);
  var network = [];
  // Hidden layer
  var hidden = [];
  for (var i = 0; i < nHidden; i++) {
    var neuron = [];
    for (var j = 0; j < nInputs + 1; j++) {
      neuron.push(rnd.uniform(-2, 2)); // +1 for bias
    }
    hidden.push(neuron);
  }
  network.push(hidden);
  // Output layer
  var output = [];
  for (var i = 0; i < nOutputs; i++) {
    var neuron = [];
    for (var j = 0; j < nHidden + 1; j++) {
      neuron.push(rnd.uniform(-2, 2)); // +1 for bias
    }
    output.push(neuron);
  }
  network.push(output);
  return network;
}`,
    fitness: `(network) => {
  // Target: f(x) = [0.5 + x[i]*x[i+1]*x[i+2]]
  // Fixed training data (4 inputs, 4 outputs)
  var data = [
    { x: [0.1, 0.2, 0.3, 0.4], y: [0.506, 0.524, 0.504, 0.508] },
    { x: [0.5, 0.6, 0.7, 0.8], y: [0.710, 0.836, 0.780, 0.700] },
    { x: [0.9, 0.3, 0.1, 0.7], y: [0.527, 0.521, 0.570, 0.563] },
    { x: [0.2, 0.8, 0.5, 0.6], y: [0.580, 0.740, 0.560, 0.524] },
  ];
  function sigmoid(x) { return 1 / (1 + Math.exp(-x)); }
  function forward(net, inputs) {
    for (var l = 0; l < net.length; l++) {
      var layer = net[l];
      var outputs = [];
      for (var n = 0; n < layer.length; n++) {
        var act = layer[n][layer[n].length - 1]; // bias
        for (var w = 0; w < inputs.length; w++) {
          act += layer[n][w] * inputs[w];
        }
        outputs.push(sigmoid(act));
      }
      inputs = outputs;
    }
    return inputs;
  }
  var mse = 0;
  for (var d = 0; d < data.length; d++) {
    var yhat = forward(network, data[d].x);
    for (var i = 0; i < yhat.length; i++) {
      mse += (yhat[i] - data[d].y[i]) ** 2;
    }
  }
  return -mse; // Negate: maximize negative MSE
}`,
    better: 'max',
    solver: 'hillClimber',
    iterations: 2000,
  },
  {
    name: 'Symbolic Regression (GP, recursive)',
    generator: `(rnd) => {
  // Evolve a math expression tree via recursive generation.
  // Uses rnd.choice at each node to pick function or terminal.
  var terms = ["x[0]", "x[1]", "x[2]", "1"];
  var funcs = ["+", "-", "*"];
  function rndExpr(depth) {
    // Probabilistic termination: deeper = more likely to stop
    if (depth <= 0 || rnd.random() < 0.3) {
      return rnd.choice(terms);
    }
    var op = rnd.choice(funcs);
    var left = rndExpr(depth - 1);
    var right = rndExpr(depth - 1);
    return "(" + left + " " + op + " " + right + ")";
  }
  return rndExpr(5);
}`,
    fitness: `(expr) => {
  // Target: x[0]*x[1] + x[2]
  // Training data
  var data = [
    { x: [1, 2, 3], y: 5 },
    { x: [2, 3, 1], y: 7 },
    { x: [0, 5, 2], y: 2 },
    { x: [3, 1, 4], y: 7 },
    { x: [4, 0, 1], y: 1 },
    { x: [1, 1, 1], y: 2 },
    { x: [2, 2, 0], y: 4 },
    { x: [5, 3, 2], y: 17 },
  ];
  try {
    var f = new Function("x", "return " + expr);
    var err = 0;
    for (var i = 0; i < data.length; i++) {
      var yhat = f(data[i].x);
      if (!isFinite(yhat)) return -1e9;
      err += Math.abs(yhat - data[i].y);
    }
    return -err; // Negate: maximize negative error
  } catch (e) {
    return -1e9;
  }
}`,
    better: 'max',
    solver: 'hillClimber',
    iterations: 5000,
  },
];

// ── State ──────────────────────────────────────────────────────

let generatorEditor = null;
let fitnessEditor = null;
let chart = null;
let isRunning = false;

// ── Monaco Setup ───────────────────────────────────────────────

require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });

require(['vs/editor/editor.main'], function () {
  const editorOpts = {
    language: 'javascript',
    theme: 'vs-dark',
    minimap: { enabled: false },
    fontSize: 14,
    lineNumbers: 'on',
    scrollBeyondLastLine: false,
    automaticLayout: true,
    tabSize: 2,
  };

  generatorEditor = monaco.editor.create(
    document.getElementById('generator-editor'),
    { ...editorOpts, value: EXAMPLES[0].generator }
  );

  fitnessEditor = monaco.editor.create(
    document.getElementById('fitness-editor'),
    { ...editorOpts, value: EXAMPLES[0].fitness }
  );

  // Enable run button once editors are ready
  document.getElementById('btn-run').disabled = false;
});

// ── Tab Switching ──────────────────────────────────────────────

function setupTabs(containerSelector) {
  const tabs = document.querySelectorAll(containerSelector);
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.target;
      // Deactivate siblings
      tab.parentElement.querySelectorAll('.editor-tab, .output-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      // Show target pane
      const container = tab.closest('.left-panel, .right-panel');
      container.querySelectorAll('.editor-box, .output-pane').forEach(p => p.classList.remove('active'));
      document.getElementById(target).classList.add('active');
      // Trigger Monaco layout refresh
      if (generatorEditor) generatorEditor.layout();
      if (fitnessEditor) fitnessEditor.layout();
    });
  });
}
setupTabs('.editor-tab');
setupTabs('.output-tab');

// ── Example Loading ────────────────────────────────────────────

const exampleSelect = document.getElementById('example-select');
EXAMPLES.forEach((ex, i) => {
  const opt = document.createElement('option');
  opt.value = i;
  opt.textContent = ex.name;
  exampleSelect.appendChild(opt);
});

exampleSelect.addEventListener('change', () => {
  const idx = exampleSelect.value;
  if (idx === '') return;
  const ex = EXAMPLES[idx];
  if (generatorEditor) generatorEditor.setValue(ex.generator);
  if (fitnessEditor) fitnessEditor.setValue(ex.fitness);
  document.getElementById('solver-select').value = ex.solver;
  document.getElementById('iterations-input').value = ex.iterations;
  // Infer better from example
  exampleSelect._better = ex.better;
});

// ── Chart Setup ────────────────────────────────────────────────

function initChart() {
  if (chart) chart.destroy();
  const ctx = document.getElementById('fitness-chart').getContext('2d');
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Best Fitness',
        data: [],
        borderColor: '#569cd6',
        backgroundColor: 'rgba(86, 156, 214, 0.1)',
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { title: { display: true, text: 'Iteration', color: '#888' }, ticks: { color: '#888' }, grid: { color: '#333' } },
        y: { title: { display: true, text: 'Fitness', color: '#888' }, ticks: { color: '#888' }, grid: { color: '#333' } },
      },
      plugins: { legend: { labels: { color: '#ccc' } } },
    }
  });
}

// ── Logging ────────────────────────────────────────────────────

const logPane = document.getElementById('log-pane');

function log(msg, cls = 'log-info') {
  const span = document.createElement('span');
  span.className = cls;
  span.textContent = msg + '\n';
  logPane.appendChild(span);
  logPane.scrollTop = logPane.scrollHeight;
}

function clearLog() { logPane.innerHTML = ''; }

// ── Solution & Trace Display ───────────────────────────────────

function showSolution(sol, fx) {
  const pane = document.getElementById('solution-pane');
  let phenoStr;
  try { phenoStr = JSON.stringify(sol.pheno, null, 2); }
  catch { phenoStr = String(sol.pheno); }

  pane.innerHTML = `
    <div class="label">Fitness</div>
    <div class="value">${fx}</div>
    <div class="label">Phenotype</div>
    <div class="value">${escapeHtml(phenoStr)}</div>
  `;
}

function showTrace(sol) {
  const pane = document.getElementById('trace-pane');
  const keys = Object.keys(sol.geno);
  if (keys.length === 0) {
    pane.innerHTML = '<p>Empty trace</p>';
    return;
  }
  let html = '<table><tr><th>Key</th><th>Type</th><th>Value</th><th>Args</th></tr>';
  for (const k of keys) {
    const d = sol.geno[k];
    html += `<tr>
      <td class="key">${escapeHtml(String(k))}</td>
      <td>${escapeHtml(String(d.funName ?? ''))}</td>
      <td class="val">${escapeHtml(JSON.stringify(d.val) ?? '')}</td>
      <td>${escapeHtml(JSON.stringify(d.args) ?? '')}</td>
    </tr>`;
  }
  html += '</table>';
  pane.innerHTML = html;
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── Run Optimization ───────────────────────────────────────────

const btnRun = document.getElementById('btn-run');
const statusBar = document.getElementById('status-bar');

btnRun.addEventListener('click', () => {
  if (isRunning) return;
  runOptimization();
});

function runOptimization() {
  isRunning = true;
  btnRun.textContent = 'Running...';
  btnRun.classList.add('running');
  statusBar.className = '';
  statusBar.textContent = 'Running...';
  clearLog();

  // Read settings
  const solverName = document.getElementById('solver-select').value;
  const naming = document.getElementById('naming-select').value;
  const distType = document.getElementById('dist-select').value;
  const iterations = parseInt(document.getElementById('iterations-input').value, 10) || 200;

  // Determine better function from last loaded example, default to max
  const betterStr = exampleSelect._better || 'max';
  const better = betterStr === 'min' ? Math.min : Math.max;

  // Parse generator and fitness from editors
  let generatorFn, fitnessFn;
  try {
    generatorFn = eval(`(${generatorEditor.getValue()})`);
    if (typeof generatorFn !== 'function') throw new Error('Generator must be a function');
  } catch (e) {
    log(`Generator error: ${e.message}`, 'log-error');
    finish(); return;
  }
  try {
    fitnessFn = eval(`(${fitnessEditor.getValue()})`);
    if (typeof fitnessFn !== 'function') throw new Error('Fitness must be a function');
  } catch (e) {
    log(`Fitness error: ${e.message}`, 'log-error');
    finish(); return;
  }

  log(`Solver: ${solverName} | Naming: ${naming} | Dist: ${distType} | Iterations: ${iterations}`);
  log(`Better: ${betterStr}`);

  // Initialize chart
  initChart();

  // Build solver args
  const iterKey = solverName === 'geneticAlgorithm' ? 'nGeneration' : 'nIteration';
  const solverArgs = {
    [iterKey]: iterations,
    returnHistory: true,
  };

  // For GA, add populationSize
  if (solverName === 'geneticAlgorithm') {
    solverArgs.populationSize = 50;
    solverArgs.mutationRate = 0.1;
  }

  // Run
  try {
    const result = PTO.run(generatorFn, fitnessFn, {
      better,
      naming,
      distType,
      solver: solverName,
      ...solverArgs,
    });

    // Update chart with history
    if (result.history) {
      const labels = result.history.map(h => h.iteration ?? h.generation ?? 0);
      const data = result.history.map(h => h.fitness);
      chart.data.labels = labels;
      chart.data.datasets[0].data = data;
      chart.update();
    }

    // Show results
    showSolution(result.sol, result.fitness);
    showTrace(result.sol);
    log(`Done! Best fitness: ${result.fitness}`, 'log-best');

    // Log phenotype summary
    let phenoSummary;
    try { phenoSummary = JSON.stringify(result.sol.pheno); }
    catch { phenoSummary = String(result.sol.pheno); }
    if (phenoSummary.length > 100) phenoSummary = phenoSummary.slice(0, 100) + '...';
    log(`Best solution: ${phenoSummary}`, 'log-best');

  } catch (e) {
    log(`Error: ${e.message}`, 'log-error');
    if (e.stack) log(e.stack, 'log-error');
  }

  finish();
}

function finish() {
  isRunning = false;
  btnRun.textContent = 'Run';
  btnRun.classList.remove('running');
  statusBar.className = 'idle';
  statusBar.textContent = 'Ready';
}
