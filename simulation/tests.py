# TODO: write __eq__ for simulation, comparing everything, and use it here to make test pass. Ensure that test fails if edges contain strings.

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin
from utility import Utility
from knowledge import Knowledge

import random
import sys

def get_adjacency_matrix(network):
    # edge is just a set of vertices
    nr_vertices = len(network.vertices)
    adjacency_matrix = np.zeros((nr_vertices, nr_vertices))
    for vertex1 in network.vertices:
        for vertex2 in network.vertices:
            if set(vertex1, vertex2) in network.edges:
                adjacency_matrix[vertex1, vertex2] = 1
    return adjacency_matrix

def is_deterministic():

    bitcoin = PlainBitcoin()

    # Player knows everything
    def knowledge_function(party, payments):
        return payments

    # very simple utility function
    def utility_add(cost, time, knowledge):
        return cost + time
    utility = Utility(utility_add)

    nr_players = 20

    seed = random.randrange(sys.maxsize)

    random.seed(seed)
    payments = random_payments(1000, 100, 100000)
    knowledge = Knowledge(0, payments, knowledge_function)
    simulation1 = Simulation(nr_players, payments, bitcoin, knowledge, utility)
    simulation1.run()

    random.seed(seed)
    payments = random_payments(1000, 100, 100000)
    knowledge = Knowledge(0, payments, knowledge_function)
    simulation2 = Simulation(nr_players, payments, bitcoin, knowledge, utility)
    simulation2.run()

    print(list(simulation1.network.edges)[:6])
    print(list(simulation2.network.edges)[:6])
    return simulation1 == simulation2

if __name__ == "__main__":
    assert(is_deterministic())
    print("Success")
