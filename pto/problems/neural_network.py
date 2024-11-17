from pto import run, rnd

import random # for generating problem data
import numpy as np # only for data processing, not used in the generator


def target_function(x):
    n = len(x) # will produce same number of outputs
    return [0.5 + x[i] * x[(i+1) % n] * x[(i+2) % n] for i in range(n)]

def make_training_data(n_samples, n_inputs):
    X_train = [[random.random() for _ in range(n_inputs)] for _ in range(n_samples)]
    y_train = [target_function(xi) for xi in X_train]
    return X_train, y_train

better = min

def generator(n_inputs, max_hidden, n_outputs):
    # max_hidden is the max size of hidden layer. n_hidden is sampled.
    n_hidden = rnd.randint(1, max_hidden)
    network = []
    hidden_layer = [[rnd.normalvariate(0, 1) for _ in range(n_inputs + 1)] for _ in range(n_hidden)] # +1 for bias term
    network.append(hidden_layer)
    output_layer = [[rnd.normalvariate(0, 1) for _ in range(n_hidden + 1)] for _ in range(n_outputs)] # +1 for bias term
    network.append(output_layer)
    return network

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def forward_propagate_base_python(network, inputs):
    for layer in network:
        outputs = []
        for neuron in layer:
            activation = neuron[-1]  # Bias term
            activation += sum(weight * input for weight, input in zip(neuron[:-1], inputs))
            outputs.append(sigmoid(activation))
        inputs = outputs
    return inputs

def forward_propagate(network, inputs):
    for layer in network:
        layer = np.array(layer)
        weights, biases = layer[:, :-1], layer[:, -1]
        outputs = inputs @ weights.T + biases
        outputs = sigmoid(outputs)
        inputs = outputs
    return outputs

def fitness_base_python(network, X_train, y_train):
    predictions = [forward_propagate_base_python(network, row) for row in X_train]
    mse = np.mean([sum((pred_i - target_i)**2 for pred_i, target_i in zip(pred, target))
                   for pred, target in zip(predictions, y_train)])
    return mse

def fitness(network, X_train, y_train):
    y_train = np.array(y_train)
    yhat = forward_propagate(network, X_train)
    return np.linalg.norm(y_train - yhat)

if __name__ == '__main__':
    max_hidden = 8
    n_inputs = 4
    n_outputs = n_inputs
    n_samples = n_inputs * 10
    X_train, y_train = make_training_data(n_samples, n_inputs)
    (pheno, geno), fx = run(generator, fitness, 
                            gen_args=(n_inputs, max_hidden, n_outputs), 
                            fit_args=(X_train, y_train), better=better)
    print(f'Solution {pheno}')
    print(f'Fitness {fx}')