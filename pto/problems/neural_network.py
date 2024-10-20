from pto import run, rnd

import random # for generating problem data
import numpy as np # only for data processing, not used in the generator


def target_function(x1, x2): return [x1 + x2, x1 * x2]

def make_training_data(n_samples, n_inputs, target_function):
    X_train = [[random.random() for _ in range(n_inputs)] for _ in range(n_samples)]
    y_train = [target_function(*xi) for xi in X_train]
    return X_train, y_train

better = min

def generator(n_inputs, max_hidden, n_outputs):
    # max_hidden is the max size of hidden layer. n_hidden is sampled.
    n_hidden = rnd.randint(1, max_hidden)
    network = []
    hidden_layer = [[rnd.random() for _ in range(n_inputs + 1)] for _ in range(n_hidden)]
    network.append(hidden_layer)
    output_layer = [[rnd.random() for _ in range(n_hidden + 1)] for _ in range(n_outputs)]
    network.append(output_layer)
    return network

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def forward_propagate(network, inputs):
    for layer in network:
        outputs = []
        for neuron in layer:
            activation = neuron[-1]  # Bias term
            activation += sum(weight * input for weight, input in zip(neuron[:-1], inputs))
            outputs.append(sigmoid(activation))
        inputs = outputs
    return inputs

def fitness(network, X_train, y_train):
    predictions = [forward_propagate(network, row) for row in X_train]
    mse = np.mean([(pred[0] - target[0])**2 + (pred[1] - target[1])**2 
                   for pred, target in zip(predictions, y_train)])
    return mse


if __name__ == '__main__':
    max_hidden = 3
    n_inputs = 2
    n_outputs = 2
    n_samples = 20
    X_train, y_train = make_training_data(n_samples, n_inputs, target_function)
    (pheno, geno), fx = run(generator, fitness, 
                            gen_args=(n_inputs, max_hidden, n_outputs), 
                            fit_args=(X_train, y_train), better=better)
    print(f'Solution {pheno}')
    print(f'Fitness {fx}')