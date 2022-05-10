# TODO: Check __eq__ method for simulation. Ensure that test fails if edges contain strings.

from turtle import distance
from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin, LN
from utility import Utility
from knowledge import Knowledge
from network import Network

import random
import sys
import numpy as np

def test_cheapest_path():
    network = Network(5)
    network.add_channel(0, 6, 1, 7)
    network.add_channel(1, 4, 4, 8)
    network.add_channel(0, 5, 2, 6)
    network.add_channel(3, 9, 4, 8)
    network.add_channel(2, 9, 3, 2)
    network.add_channel(1, 10, 2, 8)

    cost1, cheapest_path1 = network.find_cheapest_path(0, 4, 3)
    cost2, cheapest_path2 = network.find_cheapest_path(0, 4, 5)
    cost_and_path3 = network.find_cheapest_path(0, 4, 12)
    cost4, cheapest_path4 = network.find_cheapest_path(0, 4, 6)
    return cost1 == 2 and cheapest_path1 == [0,1,4] and cost2 == 3 and cheapest_path2 == [0,2,3,4] and cost_and_path3 == None and cost4 == 4 and cheapest_path4 == [0,1,2,3,4]

def test_get_payment_fee():
    def get_payment_fee_with_path(base_fee, ln_fee, payment, path):
        sender, receiver, value = payment
        return (base_fee +  value * ln_fee) * (len(path) - 1)
    base_fee = 1000
    ln_fee = 0.00002
    lightning = LN(10, base_fee = base_fee, ln_fee = ln_fee)

    lightning.network.add_channel(0, 3., 2, 7.)
    lightning.network.add_channel(0, 6., 1, 7.)
    lightning.network.add_channel(1, 4., 4, 8.)
    lightning.network.add_channel(0, 5., 2, 6.)
    lightning.network.add_channel(3, 9., 4, 8.)
    lightning.network.add_channel(2, 9., 3, 2.)
    lightning.network.add_channel(1, 10., 2, 8.)
    lightning.network.add_channel(4, 10., 7, 8.)
    lightning.network.add_channel(3, 10., 8, 8.)
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    output = True
    for payment in future_payments:
        sender, receiver, value = payment
        path = lightning.network.find_cheapest_path(sender, receiver, value)
        num_hops = len(path) - 1
        if get_payment_fee_with_path(base_fee, ln_fee, payment, path) != lightning.get_payment_fee(payment, num_hops):
            output = False
    return output

def test_get_payment_options():
    lightning = LN(10)

    # Probably LN should have an add_channel method
    lightning.network.add_channel(0, 3., 2, 7.)
    lightning.network.add_channel(0, 6., 1, 7.)
    lightning.network.add_channel(1, 4., 4, 8.)
    lightning.network.add_channel(0, 5., 2, 6.)
    lightning.network.add_channel(3, 9., 4, 8.)
    lightning.network.add_channel(2, 9., 3, 2.)
    lightning.network.add_channel(1, 10., 2, 8.)
    lightning.network.add_channel(4, 10., 7, 8.)
    lightning.network.add_channel(3, 10., 8, 8.)
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    on_chain_centrality = lightning.network.get_harmonic_centrality()
    on_chain_option = {'delay' : 3600, 'fee': 1000000, 'centrality': on_chain_centrality, 'distance': [1, 3, 3, 3], 'payment_information': {'kind': 'onchain', 'data': (0, 7, 1.0)}}
    ln_open_centrality = {0: 4.333333333333333, 1: 4.333333333333333, 2: 4.5, 3: 4.5, 4: 4.5, 5: 0, 6: 0, 7: 3.8333333333333335, 8: 3.0, 9: 0}
    ln_open_option = {'delay' : lightning.plain_bitcoin.bitcoin_delay + lightning.ln_delay, 'fee' : lightning.plain_bitcoin.get_fee() * lightning.opening_transaction_size,
    'centrality' : ln_open_centrality, 'distance': [1,1,1,3], 'payment_information' : {'kind' : 'ln-open', 'data' : (0, 7, 1.0, 7, 5.2, 5.2)}}
    ln_pay_option = {'delay' : lightning.get_payment_time([0,1,4,7]), 'fee' : lightning.get_payment_fee((0, 7, 1.0), 3),
    'centrality' : {0: 3.666666666666667, 1: 4.333333333333333, 2: 4.333333333333334, 3: 4.5, 4: 4.5, 5: 0, 6: 0, 7: 3.0, 8: 3.0, 9: 0},
    'distance': [1,3,3,3], 'payment_information' : {'kind' : 'ln-pay', 'data' : (0, 7, 1.0, 3, [0,1,4,7])}}
    return [on_chain_option, ln_open_option, ln_pay_option] == payment_options


def test_choose_payment_method():
    lightning = LN(10)

    # Probably LN should have an add_channel method
    lightning.network.add_channel(0, 3., 2, 7.)
    lightning.network.add_channel(0, 6., 1, 7.)
    lightning.network.add_channel(1, 4., 4, 8.)
    lightning.network.add_channel(0, 5., 2, 6.)
    lightning.network.add_channel(3, 9., 4, 8.)
    lightning.network.add_channel(2, 9., 3, 2.)
    lightning.network.add_channel(1, 10., 2, 8.)
    lightning.network.add_channel(4, 10., 7, 8.)
    lightning.network.add_channel(3, 10., 8, 8.)
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    on_chain_centrality = lightning.network.get_harmonic_centrality()
    on_chain_option = {'delay' : 3600, 'fee': 1000000, 'centrality': on_chain_centrality, 'distance': [1, 3, 3, 3], 'payment_information': {'kind': 'onchain', 'data': (0, 7, 1.0)}}
    def utility_function(fee, delay, distance, centrality):
        distance_array = np.array(distance)
        distance_array = 1 / distance_array
        return 10000/fee + 5000/delay + sum(distance_array) + sum(centrality)
    utility = Utility(utility_function)
    payment_method = utility.choose_payment_method(payment_options)
    print(payment_method)
    return

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
    nr_players = 10
    lightning = LN(nr_players)
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    result = lightning.sum_future_payments_to_receiver(7, future_payments)
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    return result == 3.6

def test_do():
    pass

if __name__ == "__main__":
    #assert(is_deterministic())
    assert(test_LN())
    assert(test_cheapest_path())
    assert(test_get_payment_fee())
    assert(test_get_payment_options())
    test_choose_payment_method()
    print("Success")


