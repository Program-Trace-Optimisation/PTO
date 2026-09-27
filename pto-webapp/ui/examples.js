/**
 * examples.js — built-in example problems for the PTO Playground.
 *
 * Loaded as a classic script before app.js, which reads EXAMPLES. Each
 * generator and fitness is source text, shown in the editors.
 * tests/examples.test.js runs every example.
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
