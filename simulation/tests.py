# TODO: Check __eq__ method for simulation. Ensure that test fails if edges contain strings.

import random
import sys
import numpy as np
import math
from numpy.testing import assert_almost_equal as assert_eq
import networkx as nx
import unittest

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin, LN
from utility import Utility
from knowledge import Knowledge
from network import Network


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

def make_example_network_and_future_payments(base_fee = 1000, ln_fee = 0.00002):
    lightning = make_example_network(base_fee, ln_fee)
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    return base_fee, ln_fee, lightning, future_payments

def test_cheapest_path():
    network = Network(5)
    network.add_channel(0, 6, 1, 7)
    network.add_channel(1, 4, 4, 8)
    network.add_channel(0, 5, 2, 6)
    network.add_channel(3, 9, 4, 8)
    network.add_channel(2, 9, 3, 2)
    network.add_channel(1, 10, 2, 8)

    cost1, cheapest_path1 = network.find_cheapest_path(0, 4, 3)
    assert cost1 == 2 and cheapest_path1 == [0,1,4]
    cost2, cheapest_path2 = network.find_cheapest_path(0, 4, 5)
    assert cost2 == 3 and cheapest_path2 == [0,2,3,4]
    cost_and_path3 = network.find_cheapest_path(0, 4, 12)
    assert cost_and_path3 is None
    cost4, cheapest_path4 = network.find_cheapest_path(0, 4, 6)
    assert cost4 == 4 and cheapest_path4 == [0,1,2,3,4]

def test_get_payment_fee():
    def get_payment_fee_with_path(base_fee, ln_fee, payment, path):
        sender, receiver, value = payment
        return (base_fee +  value * ln_fee) * (len(path) - 1)
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    for payment in future_payments:
        sender, receiver, value = payment
        path = lightning.network.find_cheapest_path(sender, receiver, value)
        num_hops = len(path) - 1
        assert (get_payment_fee_with_path(base_fee, ln_fee, payment, path) ==
            lightning.get_payment_fee(payment, num_hops)
        )

def test_get_payment_options_enough_money():
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    # review: this `for` overwrites `_option` if there are more than one similar options. This should be guarded against and fail the test otherwise. If we expect exactly one of each kind, better not do it in a `for`.
    for payment_option in payment_options:
        match payment_option['payment_information']['kind']:
            case 'onchain':
                actual_onchain_option = payment_option
            case 'ln-open':
                actual_ln_open_option = payment_option
            case 'ln-pay':
                actual_ln_pay_option = payment_option
    on_chain_centrality = lightning.network.get_harmonic_centrality()
    onchain_fee = lightning.plain_bitcoin.get_fee()
    expected_onchain_option = {
        'delay' : 3600, 'fee': onchain_fee, 'centrality': on_chain_centrality,
    # review: I don't like identations that depend on the length of variable names
        'distance': [(100, 3), (100, 3), (100, 3), (100, 1), (1, 1), (1, 2), (1, 2), (1, math.inf), (1, math.inf), (1, math.inf)],
        'payment_information': { 'kind': 'onchain', 'data': (0, 7, 1.0)}
    }
    ln_open_centrality = {
        0: 4.333333333333333, 1: 4.333333333333333, 2: 4.5, 3: 4.5, 4: 4.5,
        5: 0, 6: 0, 7: 3.8333333333333335, 8: 3.0, 9: 0
    }
    expected_ln_open_option = {
        'delay' : lightning.plain_bitcoin.bitcoin_delay + lightning.ln_delay,
        'fee' : lightning.plain_bitcoin.get_fee(lightning.opening_transaction_size),
        'centrality' : ln_open_centrality,
        'distance': [(100, 1), (100, 1), (100, 1), (100, 3), (1, 1), (1, 2), (1, 2), (1, math.inf), (1, math.inf), (1, math.inf)],
        'payment_information' : {
            'kind' : 'ln-open',
            'data' : (0, 7, 1.0, 7, 72.0, None)
        }
    }
    expected_ln_pay_option = {
        'delay' : lightning.get_payment_time([0,1,4,7]),
        'fee' : lightning.get_payment_fee((0, 7, 1.0), 3),
        'centrality' : {
            0: 3.666666666666667, 1: 4.333333333333333, 2: 4.333333333333334, 3: 4.5,
            4: 4.5, 5: 0, 6: 0, 7: 3.0, 8: 3.0, 9: 0
        },
        # 1 can pay 1.5 to 4 as he still has a little less than 2, but he can't pay 2.1.
        # So we get the distance as described (by 0->2->3->4->7)
        'distance': [(100, 1), (100, 3), (100, 4), (100, 3), (1, 1), (1, 2), (1, 3), (1, math.inf), (1, math.inf), (1, math.inf)],
        'payment_information' : {'kind' : 'ln-pay', 'data' : ([0,1,4,7], 1.0)}
    }
    assert expected_onchain_option['delay'] == actual_onchain_option['delay']
    assert expected_onchain_option['fee'] == actual_onchain_option['fee']
    assert expected_onchain_option['centrality'] == actual_onchain_option['centrality']
    expected_onchain_option['distance'].sort()
    actual_onchain_option['distance'].sort()
    assert expected_onchain_option['distance'] == actual_onchain_option['distance']
    assert expected_onchain_option['payment_information'] == actual_onchain_option['payment_information']

    assert_eq(expected_ln_open_option['fee'], actual_ln_open_option['fee'])
    assert_eq(expected_ln_open_option['delay'], actual_ln_open_option['delay'])
    for key in expected_ln_open_option['centrality'].keys():
        assert_eq(expected_ln_open_option['centrality'][key], actual_ln_open_option['centrality'][key])
    expected_ln_open_option['distance'].sort()
    actual_ln_open_option['distance'].sort()
    assert expected_ln_open_option['distance'] == actual_ln_open_option['distance']
    assert expected_ln_open_option['payment_information']['data'] == actual_ln_open_option['payment_information']['data']

    assert_eq(expected_ln_pay_option['delay'], actual_ln_pay_option['delay'])
    assert_eq(expected_ln_pay_option['fee'], actual_ln_pay_option['fee'])
    for key in expected_ln_pay_option['centrality'].keys():
        assert_eq(expected_ln_pay_option['centrality'][key], actual_ln_pay_option['centrality'][key])
    expected_ln_pay_option['distance'].sort()
    actual_ln_pay_option['distance'].sort()
    assert expected_ln_pay_option['distance'] == actual_ln_pay_option['distance']
    assert expected_ln_pay_option['payment_information'] == actual_ln_pay_option['payment_information']

def test_get_payment_options():
    test_get_payment_options_enough_money()

# TODO: debug for warnings.

def test_choose_payment_method_offchain_best():
    _, _, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    # TODO: define utility function outside.
    # TODO: make constants for numbers
    def utility_function(fee, delay, distance, centrality):
        weight_distance_array = np.array(distance)
        inverse_distance_array = 1/ weight_distance_array[:,1]
        weight_array = weight_distance_array[:,0]
        # TODO: matrix multiplication.
        combined_weight_inverse_distance = inverse_distance_array * weight_array
        # TODO: sum centrality.values()
        return 10000/fee + 5000/delay + sum(combined_weight_inverse_distance) + sum(centrality.values())
    utility = Utility(utility_function)
    # utilities for onchain and new channel are between 30 and 40
    # for offchain several orders of magnitude higher, just consider delay.
    payment_method = utility.choose_payment_method(payment_options)
    assert payment_method['kind'] == 'ln-pay'

def test_choose_payment_method_new_channel_best():
    _, _, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1000, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    def utility_function(fee, delay, distance, centrality):
        weight_distance_array = np.array(distance)
        inverse_distance_array = 1/ weight_distance_array[:,1]
        weight_array = weight_distance_array[:,0]
        combined_weight_inverse_distance = inverse_distance_array * weight_array
        # there's no offchain option
        # the first two terms are both smaller than one for new_channel and onchain
        # the difference for the third term is over 100 in favor of new channel
        # the difference between the last two is about 2 in favor of new channel
        return 10000/fee + 50000/delay + 100 * sum(combined_weight_inverse_distance) + sum(centrality)
    utility = Utility(utility_function)
    payment_method = utility.choose_payment_method(payment_options)
    assert payment_method['kind'] == 'ln-open'

def test_choose_payment_method_onchain_best():
    _, _, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1000, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    def utility_function(fee, delay, distance, centrality):
        weight_distance_array = np.array(distance)
        inverse_distance_array = 1/ weight_distance_array[:,1]
        weight_array = weight_distance_array[:,0]
        combined_weight_inverse_distance = inverse_distance_array * weight_array
        # there's no offchain option
        # the first two terms are both smaller than one for new_channel and onchain
        # the difference for the third term is over 100 in favor of new channel
        # the difference between the last two is about 2 in favor of new channel
        return 1/fee
    utility = Utility(utility_function)
    payment_method = utility.choose_payment_method(payment_options)
    assert payment_method['kind'] == 'onchain'

def test_choose_payment_method():
    test_choose_payment_method_offchain_best()
    test_choose_payment_method_new_channel_best()
    test_choose_payment_method_onchain_best()

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
    result = lightning.sum_future_payments_to_counterparty(0, 7, future_payments)
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    assert result == 3.6

def test_do_onchain():
    # review: the next few lines are duplicated many times. The first few are also used in _exception()s, a few more only in the 2 other `do` tests
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    fee_intermediary = base_fee + 1*ln_fee
    MAX_COINS = lightning.plain_bitcoin.max_coins
    # review: this `for` overwrites `payment_information_onchain` if there are more than one 'onchain' options. This should be guarded against and fail the test otherwise
    for payment_option in payment_options:
        match payment_option['payment_information']['kind']:
            case 'onchain':
                payment_information_onchain = payment_option['payment_information']
    lightning.do(payment_information_onchain)
    # sender should have MAX_COINS - 1 - fee many coins, receiver MAX_COINS + 1
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS - 1. - lightning.plain_bitcoin.get_fee() 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS + 1.
    # TODO: test for exceptions

def test_do_onchain_exception():
    lightning = make_example_network(base_fee = 1, ln_fee = 0.00002)
    payment_information_onchain = { 
        'kind': 'onchain', 'data': (0, 7, 999999999999999999999.)
    }
    try:
        lightning.do(payment_information_onchain)
        assert False, 'should raise exception as amount is too high'
    except ValueError:
        pass

def test_do_offchain():
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    fee_intermediary = base_fee + 1*ln_fee
    MAX_COINS = lightning.plain_bitcoin.max_coins
    for payment_option in payment_options:
        match payment_option['payment_information']['kind']:
            case 'ln-pay':
                payment_information_offchain = payment_option['payment_information']

    # path is [0,1,4,7]
    lightning = make_example_network(base_fee=1, ln_fee = 0.00002)
    lightning.do(payment_information_offchain)
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS
    value = 1
    assert_eq(lightning.network.graph[0][1]['balance'], 6-1 - 2*fee_intermediary)
    assert_eq(lightning.network.graph[1][0]['balance'], 7 + value + 2*fee_intermediary)
    # the first intermediary should have fee_intermediary less on his channel with 2nd intermediary.
    assert_eq(lightning.network.graph[1][4]['balance'], 4 - value - fee_intermediary)
    assert_eq(lightning.network.graph[4][1]['balance'], 8 + value + fee_intermediary)
    assert_eq(lightning.network.graph[4][7]['balance'], 10 - value)
    assert_eq(lightning.network.graph[7][4]['balance'], 8 + value)
    assert_eq(lightning.network.graph[1][2]['balance'], 10)

def test_do_offchain_exception():
    base_fee = 10
    ln_fee = 0.00002
    lightning = make_example_network(base_fee, ln_fee)
    payment_information_offchain = {
        'kind': 'ln-pay', 'data': ([0,1,4,7], 1.)
    }
    try:
        lightning.do(payment_information_offchain)
        assert False, 'fee is too high, should raise Exception'
    except ValueError:
        pass

def test_do_new_channel():
    _, _, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    value = 1
    MAX_COINS = lightning.plain_bitcoin.max_coins
    # first test on-chain option
    # review: this `for` overwrites `payment_information_new_channel` if there are more than one 'ln-open' options. This should be guarded against and fail the test otherwise
    for payment_option in payment_options:
        match payment_option['payment_information']['kind']:
            case 'ln-open':
                payment_information_new_channel = payment_option['payment_information']

    lightning = make_example_network(base_fee=1, ln_fee = 0.00002)
    lightning.do(payment_information_new_channel)
    # check first the coins of the parties
    sum_future_payments = lightning.sum_future_payments_to_counterparty(0, 7, future_payments)
    sender_coins = 20 * sum_future_payments
    receiver_coins = value
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS - lightning.plain_bitcoin.get_fee(200) - sender_coins - receiver_coins 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS
    # test the balances on ln (-2 for base fee and payment, +1 for payment).
    assert lightning.network.graph[0][7]['balance'] == sender_coins 
    assert lightning.network.graph[7][0]['balance'] == receiver_coins

def test_do_new_channel_exception():
    lightning = make_example_network(base_fee = 1, ln_fee = 0.00002)
    payment_information_new_channel = {
        'kind': 'ln-open',
        'data': (0, 7, 1, 7, 99999999999999999999999, None)
    }
    try:
        lightning.do(payment_information_new_channel)
        assert False, "sender can't put more on channel than he has"
    except ValueError:
        pass

def test_do():
    test_do_onchain()
    test_do_onchain_exception()
    test_do_offchain()
    test_do_offchain_exception()
    test_do_new_channel()
    test_do_new_channel_exception()

def test_update_balances_pay_enough_money():
    lightning = make_example_network(base_fee = 1, ln_fee = 0.00002)
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2
    # 1 -> base_fee, 2 -> len(path) - 2
    fee_intermediary = 1 + 2*ln_fee
    lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
    # sender 0 has 6. in the beginning on the channel to 1
    # after update he should have 2 less for the transaction to 7 and 2*fee_intermediary less for the fee,
    assert_eq(lightning.network.graph[0][1]['balance'],6-value-2*fee_intermediary)
    # the first intermediary should have value + 2*fee_intermediary more on his channel with the sender
    assert_eq(lightning.network.graph[1][0]['balance'], 7 + value + 2*fee_intermediary)
    # the first intermediary should have fee_intermediary less on his channel with 2nd intermediary.
    assert_eq(lightning.network.graph[1][4]['balance'], 4 - value - fee_intermediary)
    assert_eq(lightning.network.graph[4][1]['balance'], 8 + value + fee_intermediary)
    assert_eq(lightning.network.graph[4][7]['balance'], 10 - value)
    assert_eq(lightning.network.graph[7][4]['balance'], 8 + 2)
    assert_eq(lightning.network.graph[1][2]['balance'], 10)

def test_update_balances_pay_not_enough_money():
    lightning = make_example_network(base_fee=1000, ln_fee = 0.00002)
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2
    balances = nx.get_edge_attributes(lightning.network.graph, "balance")
    try:
        lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
        balances_after_failure = nx.get_edge_attributes(lightning.network.graph, "balance")
        for key in balances.keys():
            assert_eq(balances[key], balances_after_failure[key])
        assert False, 'update_balances() should raise a ValueError'
    except ValueError:
        pass

def test_update_balances_reverse():
    # review: store initial balances of parties before the forward payment and compare parties' balances against the stored ones after reversing. This way the balances in the assertions are "obviously" the expected ones.
    lightning = make_example_network(base_fee = 1, ln_fee = 0.00002)
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2
    lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
    # balances are updated, now we want to revert it
    lightning.update_balances(value, ln_fee, base_fee, path, pay=False)
    assert_eq(lightning.network.graph[0][1]['balance'],6)
    # the first intermediary should have value + 2*fee_intermediary more on his channel with the sender
    assert_eq(lightning.network.graph[1][0]['balance'], 7)
    # the first intermediary should have fee_intermediary less on his channel with 2nd intermediary.
    assert_eq(lightning.network.graph[1][4]['balance'], 4)
    assert_eq(lightning.network.graph[4][1]['balance'], 8)
    assert_eq(lightning.network.graph[4][7]['balance'], 10)
    assert_eq(lightning.network.graph[7][4]['balance'], 8)
    assert_eq(lightning.network.graph[1][2]['balance'], 10)

def test_update_balances():
    test_update_balances_pay_enough_money()
    test_update_balances_pay_not_enough_money()
    test_update_balances_reverse()

def test_simulation_with_ln():
    lightning = LN(10)
    seed = 0
    random.seed(seed)
    def know_all(party, payments):
        return payments
    knowledge = Knowledge(know_all)
    payments = random_payments(100, 10, 2000000000)
    def utility_function(fee, delay, distance, centrality):
        weight_distance_array = np.array(distance)
        inverse_distance_array = 1/ weight_distance_array[:,1]
        weight_array = weight_distance_array[:,0]
        combined_weight_inverse_distance = inverse_distance_array * weight_array
        utility = 10000/fee + 5000/delay + 10000*sum(combined_weight_inverse_distance) + 1000*sum(centrality)
        return utility
    utility = Utility(utility_function)
    simulation = Simulation(payments, lightning, knowledge, utility)
    output = simulation.run()
    print(output)


if __name__ == "__main__":
    #assert(is_deterministic())
    test_LN()
    test_cheapest_path()
    test_get_payment_fee()
    test_update_balances()
    test_get_payment_options()
    test_do()
    test_choose_payment_method()
    test_simulation_with_ln()
    print("Success")


