# TODO: Check __eq__ method for simulation. Ensure that test fails if edges contain strings.

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin
from utility import Utility
from knowledge import Knowledge
from network import Network

import random
import sys

def test_cheapest_path():
    network = Network(5)
    network.add_channel(0, 6.5, 1, 7.3)
    network.add_channel(1, 4.8, 4, 8.9)
    network.add_channel(0, 5., 2, 6.7)
    network.add_channel(3, 2.3, 4, 8.2)
    network.add_channel(2, 3.4, 3, 5.5)

    cost, cheapest_path = network.find_cheapest_path(0, 4, 1)
    print(cheapest_path)
    # TODO: Complete the Test

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
    test_cheapest_path()
    print("Success")


