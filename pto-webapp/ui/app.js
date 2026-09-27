/**
 * app.js — PTO Playground UI controller.
 *
 * Wires Monaco editors, Chart.js, and the PTO engine bundle together.
 * Runs optimization synchronously on the main thread, so the page does not
 * respond until a run finishes; keep iteration counts moderate.
 */

// Built-in examples: EXAMPLES is defined in examples.js

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
  document.getElementById('better-select').value = ex.better;
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

  const betterStr = document.getElementById('better-select').value;
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
  // Other solver parameters (eg GA population size, mutation rate) use the solver defaults
  const solverArgs = {
    [iterKey]: iterations,
    returnHistory: true,
  };

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
