##### Generalised Assignment Problem

from pto import run, rnd

import numpy as np

import random  # for generating random problem instances


#################
# INSTANCE DATA #
#################


# Random instance generator
def generate_gap_instance(num_agents, num_tasks, seed=None):
    """
    Generate a random GAP instance.

    Args:
        num_agents: Number of agents
        num_tasks: Number of tasks
        seed: Random seed for reproducibility

    Returns:
        tuple: (cost_matrix, resource_matrix, agent_capacities)
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate random cost matrix (uniform distribution between 10 and 50)
    cost_matrix = np.random.randint(10, 51, size=(num_agents, num_tasks))

    # Generate random resource requirements (uniform distribution between 1 and 10)
    resource_matrix = np.random.randint(1, 11, size=(num_agents, num_tasks))

    # Generate agent capacities
    # Make them somewhat reasonable: each agent can handle about (num_tasks/num_agents) tasks
    avg_tasks_per_agent = num_tasks / num_agents
    avg_resource_per_task = np.mean(resource_matrix)
    base_capacity = int(avg_tasks_per_agent * avg_resource_per_task)

    # Add some random variation to capacities
    agent_capacities = np.random.randint(
        base_capacity - base_capacity//4,
        base_capacity + base_capacity//4,
        size=num_agents
    )

    return cost_matrix, resource_matrix, agent_capacities

# generate instance
num_agents=10
num_tasks=20
cost_matrix, resource_matrix, agent_capacities = generate_gap_instance(num_agents, num_tasks)

better = min



def fitness(solution, cost_matrix, resource_matrix, agent_capacities):
    """
    Calculate fitness for a GAP solution.

    Args:
        solution: List or array where index is task and value is assigned agent
        cost_matrix: Matrix of costs for each agent-task pair
        resource_matrix: Matrix of resource requirements for each agent-task pair
        agent_capacities: Array of agent capacities

    Returns:
        float: Fitness value (lower is better)
    """
    solution = np.array(solution)
    num_agents = len(agent_capacities)

    # Initialize tracking variables
    total_cost = 0
    agent_loads = np.zeros(num_agents)

    # Calculate costs and resource usage
    for task, agent in enumerate(solution):
        total_cost += cost_matrix[agent][task]
        agent_loads[agent] += resource_matrix[agent][task]

    # Calculate capacity violation penalties
    penalties = np.sum(np.maximum(0, agent_loads - agent_capacities) * 1000)

    # Final fitness
    fitness = total_cost + penalties

    return fitness



##########################
# ALTERNATIVE GENERATORS #
##########################

# Several alternative generators for experiments re the new distributions for shuffle, choices, and sample.

# Generator (native 'choices')
def generator_native(num_agents, num_tasks):
    return rnd.choices(range(num_agents), k=num_tasks)

# Generator (simulated 'choices')
def generator_simulated(num_agents, num_tasks):
    def _choices(x,k):
        return [rnd.choice(x) for i in range(k)]

    return _choices(range(num_agents), k=num_tasks)



#####################
# DEFAULT GENERATOR #
#####################

# the "obvious" generator, suitable for PTO with custom
# distributions for shuffle, choices, and sample.
generator = generator_native 