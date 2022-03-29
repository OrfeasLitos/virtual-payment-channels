# TODO: write __eq__ for simulation, comparing everything, and use it here to make test pass. Ensure that test fails if edges contain strings.

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin
from utility import Utility
from knowledge import Knowledge
from network import Network

import random
import sys

def get_weighted_adjacency_matrix(network):
    # edge is just a set of vertices
    nr_vertices = len(network.vertices)
    weighted_adjacency_matrix = np.zeros((nr_vertices, nr_vertices))
    money_on_network = 0
    for vertex1 in network.vertices:
        for vertex2 in network.vertices:
            for edge in network.edges:
                parties, balance_a, balance_b = edge
                a , b = parties
                if (a == vertex1 and b == vertex2) or (a == vertex2 and b == vertex1):
                    weighted_adjacency_matrix[vertex1, vertex2] = balance_a + balance_b
                    money_on_network += balance_a + balance_b
    for vertex1 in network.vertices:
        for vertex2 in network.vertices:
            weighted_adjacency_matrix[vertex1, vertex2] /= money_on_network
    return weighted_adjacency_matrix

def test_adjacency_matrix():
    # TODO: use adjacency list
    network = Network(5)
    network.add_channel(0, 1, 2, 0)
    network.add_channel(1, 1.2, 2, 5.6)
    network.add_channel(3, 0.1, 4, 3.2)
    network.add_channel(1, 1, 0, 2)
    adjacency_matrix_edges = network.get_weighted_adjacency_matrix()
    adjacency_matrix_vertices = get_weighted_adjacency_matrix(network)
    return (np.linalg.norm(adjacency_matrix_edges - adjacency_matrix_vertices) < 10**(-10))

def test_find_paths():
    # TODO: use adjacency list
    network = Network(5)
    edge1 = (set({0,2}, 1, 0))
    edge2 = (set({1,2}, 1.2, 5.6))
    edge3 = (set({3,4}, 0.1, 3.2))
    edge4 = (set({1,0}, 1, 2))
    network.add_edge(edge1)
    network.add_edge(edge2)
    network.add_edge(edge3)
    network.add_edge(edge4)
    paths_calculated = network.find_all_paths(0, 2)
    paths = set({[0,2], [0,1,2]})
    return paths_calculated == paths

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
    #assert(test_adjacency_matrix())
    #assert(test_find_paths())
    print("Success")
