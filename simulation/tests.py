# TODO: write __eq__ for simulation, comparing everything, and use it here to make test pass. Ensure that test fails if edges contain strings.

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin
from utility import Utility
from knowledge import Knowledge
from network import Network

import random
import sys



def test_find_paths():
    # TODO: use adjacency list
    network = Network(10)
    network.add_channel(2, 3.4, 6, 6.7)
    network.add_channel(2, 4., 5, 5.6)
    network.add_channel(5, 3.2, 6, 7.8)
    network.add_channel(8, 5.4, 6, 3.4)
    network.add_channel(3, 3., 4, 3.2)
    network.add_channel(2, 5.6, 3, 5.)
    network.add_channel(4, 7.8, 6, 3.9)
    all_paths = network.find_all_paths(2, 6, 0)
    paths = set()
    edge_ids = set()
    for i in range(3):
        path, edge_id = all_paths[i]
        paths.add(tuple(path))
        edge_ids.add(tuple(edge_id))
    right_paths = set()
    right_paths.add(tuple([2, 6]))
    right_paths.add(tuple([2,5,6]))
    right_paths.add(tuple([2,3,4,6]))
    right_edge_ids = set()
    right_edge_ids.add(tuple([0]))
    right_edge_ids.add(tuple([1,2]))
    right_edge_ids.add(tuple([5,4,6]))
    return right_paths == paths and right_edge_ids == edge_ids

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
    #assert(is_deterministic())
    #assert(test_adjacency_matrix())
    assert(test_find_paths())
    print("Success")


