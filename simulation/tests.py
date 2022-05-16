# TODO: Check __eq__ method for simulation. Ensure that test fails if edges contain strings.

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin, LN
from utility import Utility
from knowledge import Knowledge
from network import Network

import random
import sys
import numpy as np

def make_example_network(base_fee = 1000, ln_fee = 0.00002):
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
    return lightning

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
    lightning = make_example_network()
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
    lightning = make_example_network()
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    on_chain_centrality = lightning.network.get_harmonic_centrality()
    on_chain_option = {'delay' : 3600, 'fee': 1000000, 'centrality': on_chain_centrality, 'distance': [1, 3, 3, 3], 'payment_information': {'kind': 'onchain', 'data': (0, 7, 1.0)}}
    ln_open_centrality = {0: 4.333333333333333, 1: 4.333333333333333, 2: 4.5, 3: 4.5, 4: 4.5, 5: 0, 6: 0, 7: 3.8333333333333335, 8: 3.0, 9: 0}
    ln_open_option = {'delay' : lightning.plain_bitcoin.bitcoin_delay + lightning.ln_delay, 'fee' : lightning.plain_bitcoin.get_fee() * lightning.opening_transaction_size,
    'centrality' : ln_open_centrality, 'distance': [1,1,1,3], 'payment_information' : {'kind' : 'ln-open', 'data' : (0, 7, 1.0, 7, 5.2, 5.2,
    {'delay': 0.1, 'fee': 1000.00002, 'centrality': {0: 4.333333333333333, 1: 4.333333333333333, 2: 4.5, 3: 4.5, 4: 4.5, 5: 0, 6: 0, 7: 3.8333333333333335, 8: 3.0, 9: 0},
    'distance': [1, 1, 3], 'payment_information': {'kind': 'ln-pay', 'data': ([0, 7], 1.0)}})}}
    ln_pay_option = {'delay' : lightning.get_payment_time([0,1,4,7]), 'fee' : lightning.get_payment_fee((0, 7, 1.0), 3),
    'centrality' : {0: 3.666666666666667, 1: 4.333333333333333, 2: 4.333333333333334, 3: 4.5, 4: 4.5, 5: 0, 6: 0, 7: 3.0, 8: 3.0, 9: 0},
    'distance': [1,3,3,3], 'payment_information' : {'kind' : 'ln-pay', 'data' : ([0,1,4,7], 1.0)}}
    return [on_chain_option, ln_open_option, ln_pay_option] == payment_options


def test_choose_payment_method():
    lightning = make_example_network()
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
    lightning = make_example_network()
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    # first test on-chain option
    payment_information = payment_options[0]['payment_information']
    lightning.do(payment_information)
    MAX_COINS = lightning.plain_bitcoin.max_coins
    # sender should have MAX_COINS - 1 - fee many coins, receiver MAX_COINS + 1
    test_onchain = lightning.plain_bitcoin.coins[0] == MAX_COINS - 1. - lightning.plain_bitcoin.get_fee() and lightning.plain_bitcoin.coins[7] == MAX_COINS + 1.
    # TODO: test for exceptions
    return test_onchain

def test_update_balances():
    lightning1 = make_example_network(base_fee = 1, ln_fee = 0.00002)
    base_fee1 = lightning1.base_fee
    fee_intermediary = lightning1.ln_fee
    path = [0, 1, 4, 7]
    value = 2
    lightning1.update_balances(value, fee_intermediary, base_fee1, path)
    # sender 0 has 6. in the beginning on the channel to 1
    # after update he should have 2 less for the transaction to 7, 1 less for the base fee and 0.00004 less for the intermediaries
    # the intermediaries should have 0.00002 more each on the channel with the previous party
    test1 =  (lightning1.network.graph[0][1]['balance'] == 6-3-0.00004 and lightning1.network.graph[1][0]['balance'] == 7.00002
            and lightning1.network.graph[4][1]['balance'] == 8.00002 and lightning1.network.graph[7][4]['balance'] == 10.)
    lightning2 = make_example_network()
    base_fee2 = lightning2.base_fee
    test2 = False
    try:
        lightning2.update_balances(value, fee_intermediary, base_fee2, path)
    except ValueError:
        test2 = True
    return test1 and test2

if __name__ == "__main__":
    #assert(is_deterministic())
    assert(test_LN())
    assert(test_cheapest_path())
    assert(test_get_payment_fee())
    assert(test_update_balances())
    assert(test_get_payment_options())
    assert(test_do())
    test_choose_payment_method()
    print("Success")


