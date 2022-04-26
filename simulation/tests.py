# TODO: Check __eq__ method for simulation. Ensure that test fails if edges contain strings.

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin, LN
from utility import Utility
from knowledge import Knowledge
from network import Network

import random
import sys

def test_cheapest_path():
    network = Network(5)
    network.add_channel(0, 6, 1, 7)
    network.add_channel(1, 4, 4, 8)
    network.add_channel(0, 5, 2, 6)
    network.add_channel(3, 9, 4, 8)
    network.add_channel(2, 9, 3, 2)
    network.add_channel(1, 10, 2, 8)

    # doesn't work yet, as amount flow can take several paths at once, if one doesn't have enough capacity on one path, but enough if several paths are taken at the same time.
    cost1, cheapest_path1 = network.find_cheapest_path(0, 4, 3)
    cost2, cheapest_path2 = network.find_cheapest_path(0, 4, 5)
    cost_and_path3 = network.find_cheapest_path(0, 4, 12)
    cost4, cheapest_path4 = network.find_cheapest_path(0, 4, 6)
    return cost1 == 2 and cheapest_path1 == [0,1,4] and cost2 == 3 and cheapest_path2 == [0,2,3,4] and cost_and_path3 == None and cost4 == 4 and cheapest_path4 == [0,1,2,3,4]

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

def test_LN():
    network = Network(10)
    network.add_channel(0, 6.5, 1, 7.3)
    network.add_channel(1, 4.8, 4, 8.9)
    network.add_channel(0, 5., 2, 6.7)
    network.add_channel(3, 2.3, 4, 8.2)
    network.add_channel(2, 3.4, 3, 5.5)

    plain_bitcoin = PlainBitcoin()
    lightning = LN(10, plain_bitcoin)
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    result = lightning.sum_future_payments_to_receiver(7, future_payments)
    payment_options = lightning.get_payment_from(0, 7, 1., future_payments)
    return result == 3.6

if __name__ == "__main__":
    #assert(is_deterministic())
    assert(test_LN())
    assert(test_cheapest_path())
    print("Success")


