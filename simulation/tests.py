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

random.seed(5)
random_payments1 = random_payments(100, 10, 2000000000)
random_payments2 = random_payments(100, 10, 2000000000)

def test_random_payments_seed_inside():
    random.seed(5)
    random_payments_seed_inside1 = random_payments(100, 10, 2000000000)
    random_payments_seed_inside2 = random_payments(100, 10, 2000000000)
    assert random_payments1 == random_payments_seed_inside1
    assert random_payments2 == random_payments_seed_inside2

def test_random_payments_seed_outside():
    random_payments_seed_outside1 = random_payments(100, 10, 2000000000)
    random_payments_seed_outside2 = random_payments(100, 10, 2000000000)
    assert random_payments1 == random_payments_seed_outside1
    assert random_payments2 == random_payments_seed_outside2

def make_example_network(base_fee = 1000, ln_fee = 0.00002):
    lightning = LN(10, base_fee = base_fee, ln_fee = ln_fee)

    lightning.network.add_channel(0, 3000000000., 2, 7000000000.)
    lightning.network.add_channel(0, 6000000000., 1, 7000000000.)
    lightning.network.add_channel(1, 4000000000., 4, 8000000000.)
    lightning.network.add_channel(0, 5000000000., 2, 6000000000.)
    lightning.network.add_channel(3, 9000000000., 4, 8000000000.)
    lightning.network.add_channel(2, 9000000000., 3, 2000000000.)
    lightning.network.add_channel(1, 10000000000., 2, 8000000000.)
    lightning.network.add_channel(4, 10000000000., 7, 8000000000.)
    lightning.network.add_channel(3, 10000000000., 8, 8000000000.)
    return lightning

def make_example_network_and_future_payments(base_fee = 1000, ln_fee = 0.00002):
    lightning = make_example_network(base_fee, ln_fee)
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 3000000000.)]
    return base_fee, ln_fee, lightning, future_payments

def make_example_utility_function(factor_fee, factor_delay, factor_distance, factor_centrality):
    def utility_function(fee, delay, distance, centrality):
        weight_distance_array = np.array(distance)
        inverse_distance_array = 1/ weight_distance_array[:,1]
        weight_array = weight_distance_array[:,0]
        return (
            factor_fee/fee +
            factor_delay/delay +
            factor_distance * np.transpose(inverse_distance_array) @ weight_array +
            factor_centrality * sum(centrality.values())
            )
    return utility_function

def know_all(party, payments):
    return payments

example_utility_function_for_simulation = make_example_utility_function(10000, 5000, 10000, 1000)

def make_example_simulation_ln(seed = 0, coins_for_parties = 'max_value'):
    random.seed(seed)
    lightning = LN(10, coins_for_parties = coins_for_parties)
    knowledge = Knowledge(know_all)
    payments = random_payments(100, 10, 2000000000)
    utility_function = example_utility_function_for_simulation
    utility = Utility(utility_function)
    return Simulation(payments, lightning, knowledge, utility)

def test_cheapest_path():
    network = Network(5)
    network.add_channel(0, 6, 1, 7)
    network.add_channel(1, 4, 4, 8)
    network.add_channel(0, 5, 2, 6)
    network.add_channel(3, 9, 4, 8)
    network.add_channel(2, 9, 3, 2)
    network.add_channel(1, 10, 2, 8)

    fee_intermediary = 0
    cost1, cheapest_path1 = network.find_cheapest_path(0, 4, 3, fee_intermediary)
    assert cost1 == 2 and cheapest_path1 == [0,1,4]
    cost2, cheapest_path2 = network.find_cheapest_path(0, 4, 5, fee_intermediary)
    assert cost2 == 3 and cheapest_path2 == [0,2,3,4]
    cost_and_path3 = network.find_cheapest_path(0, 4, 12, fee_intermediary)
    assert cost_and_path3 is None
    cost4, cheapest_path4 = network.find_cheapest_path(0, 4, 6, fee_intermediary)
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
        fee_intermediary = base_fee + value * ln_fee
        path = lightning.network.find_cheapest_path(sender, receiver, value, fee_intermediary)
        num_hops = len(path) - 1
        assert (get_payment_fee_with_path(base_fee, ln_fee, payment, path) ==
            lightning.get_payment_fee(payment, num_hops)
        )

def test_get_payment_options_enough_money():
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1000, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1000000000., future_payments)
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    actual_onchain_option = payment_options[0]
    assert payment_options[1]['payment_information']['kind'] == 'ln-open'
    actual_ln_open_option = payment_options[1]
    assert payment_options[2]['payment_information']['kind'] == 'ln-pay'
    actual_ln_pay_option = payment_options[2]

    on_chain_centrality = lightning.network.get_harmonic_centrality()
    onchain_fee = lightning.plain_bitcoin.get_fee()
    expected_onchain_option = {
        'delay' : 3600,
        'fee': onchain_fee,
        'centrality': on_chain_centrality,
        'distance': [
            (100, 3), (100, 3), (100, 3), (100, 1), (1, 1), (1, 2),(1, 2),
            (1, math.inf), (1, math.inf), (1, math.inf)
        ],
        'payment_information': { 'kind': 'onchain', 'data': (0, 7, 1000000000.)}
    }
    ln_open_centrality = {
        0: 4.333333333333333, 1: 4.333333333333333, 2: 4.5, 3: 4.5, 4: 4.5,
        5: 0, 6: 0, 7: 3.8333333333333335, 8: 3.0, 9: 0
    }
    expected_ln_open_option = {
        'delay' : lightning.plain_bitcoin.bitcoin_delay + lightning.ln_delay,
        'fee' : lightning.plain_bitcoin.get_fee(lightning.opening_transaction_size),
        'centrality' : ln_open_centrality,
        'distance': [
            (100, 1), (100, 1), (100, 1), (100, 3), (1, 1), (1, 2), (1, 2),
            (1, math.inf), (1, math.inf), (1, math.inf)
        ],
        'payment_information' : {
            'kind' : 'ln-open',
            'data' : (0, 7, 1000000000., 7, 72000000000., None)
        }
    }
    expected_ln_pay_option = {
        'delay' : lightning.get_payment_time([0,1,4,7]),
        'fee' : lightning.get_payment_fee((0, 7, 1000000000.), 3),
        'centrality' : {
            0: 3.666666666666667, 1: 4.333333333333333, 2: 4.333333333333334, 3: 4.5,
            4: 4.5, 5: 0, 6: 0, 7: 3.0, 8: 3.0, 9: 0
        },
        'distance': [
            (100, 1), (100, 3), (100, 3), (100, 3), (1, 1), (1, 2), (1, 2),
            (1, math.inf), (1, math.inf), (1, math.inf)
        ],
        'payment_information' : {'kind' : 'ln-pay', 'data' : ([0,1,4,7], 1000000000.)}
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

def test_choose_payment_method_offchain_best():
    _, _, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    utility_function = make_example_utility_function(10000, 5000, 1, 1)
    utility = Utility(utility_function)
    # utilities for onchain and new channel are between 30 and 40
    # for offchain several orders of magnitude higher, just consider delay.
    payment_method = utility.choose_payment_method(payment_options)
    assert payment_method['kind'] == 'ln-pay'

def test_choose_payment_method_new_channel_best():
    _, _, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1000, ln_fee = 200)
    )
    payment_options = lightning.get_payment_options(0, 7, 1000000000., future_payments)
    # there's no offchain option
    # the first two terms in utility are both smaller than one for new_channel and onchain
    # the difference for the third term is over 100 in favor of new channel
    # the difference between the last two is about 2 in favor of new channel
    utility_function = make_example_utility_function(10000, 5000, 100, 1)
    utility = Utility(utility_function)
    payment_method = utility.choose_payment_method(payment_options)
    assert payment_method['kind'] == 'ln-open'

def test_choose_payment_method_onchain_best():
    _, _, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1000, ln_fee = 200)
    )
    payment_options = lightning.get_payment_options(0, 7, 1000000000., future_payments)
    # there's no offchain option
    # the fee in the utility favors the onchain option.
    utility_function = make_example_utility_function(1, 0, 0, 0)
    utility = Utility(utility_function)
    payment_method = utility.choose_payment_method(payment_options)
    assert payment_method['kind'] == 'onchain'

def test_choose_payment_method():
    test_choose_payment_method_offchain_best()
    test_choose_payment_method_new_channel_best()
    test_choose_payment_method_onchain_best()

def test_LN():
    nr_players = 10
    lightning = LN(nr_players)
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    result = lightning.sum_future_payments_to_counterparty(0, 7, future_payments)
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    assert result == 3.6

def make_example_values_for_do():
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_and_future_payments(base_fee = 1000, ln_fee = 0.00002)
    )
    value = 1000000000.
    payment_options = lightning.get_payment_options(0, 7, value, future_payments)
    MAX_COINS = lightning.plain_bitcoin.max_coins
    return base_fee, ln_fee, lightning, future_payments, value, payment_options, MAX_COINS


def test_do_onchain():
    base_fee, ln_fee, lightning, future_payments, value, payment_options, MAX_COINS = (
        make_example_values_for_do()
    )
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    payment_information_onchain = payment_options[0]['payment_information']
    lightning.do(payment_information_onchain)
    # sender should have MAX_COINS - 1 - fee many coins, receiver MAX_COINS + 1
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS - value - lightning.plain_bitcoin.get_fee() 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS + value

def test_do_onchain_exception():
    lightning = make_example_network(base_fee = 1000, ln_fee = 0.00002)
    payment_information_onchain = { 
        'kind': 'onchain', 'data': (0, 7, 999999999999999999999.)
    }
    try:
        lightning.do(payment_information_onchain)
        assert False, 'should raise exception as amount is too high'
    except ValueError:
        pass

def test_do_offchain():
    base_fee, ln_fee, lightning, future_payments, value, payment_options, MAX_COINS = (
        make_example_values_for_do()
    )
    fee_intermediary = base_fee + value*ln_fee
    for payment_option in payment_options:
        match payment_option['payment_information']['kind']:
            case 'ln-pay':
                payment_information_offchain = payment_option['payment_information']

    # path is [0,1,4,7]
    lightning = make_example_network(base_fee=1000, ln_fee = 0.00002)
    lightning.do(payment_information_offchain)
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS
    assert_eq(lightning.network.graph[0][1]['balance'], 6000000000-1000000000 - 2*fee_intermediary)
    assert_eq(lightning.network.graph[1][0]['balance'], 7000000000 + value + 2*fee_intermediary)
    # the first intermediary should have fee_intermediary less on his channel with 2nd intermediary.
    assert_eq(lightning.network.graph[1][4]['balance'], 4000000000 - value - fee_intermediary)
    assert_eq(lightning.network.graph[4][1]['balance'], 8000000000 + value + fee_intermediary)
    assert_eq(lightning.network.graph[4][7]['balance'], 10000000000 - value)
    assert_eq(lightning.network.graph[7][4]['balance'], 8000000000 + value)
    assert_eq(lightning.network.graph[1][2]['balance'], 10000000000)

def test_do_offchain_exception():
    base_fee = 1000
    ln_fee = 200
    lightning = make_example_network(base_fee, ln_fee)
    payment_information_offchain = {
        'kind': 'ln-pay', 'data': ([0,1,4,7], 1000000000)
    }
    try:
        lightning.do(payment_information_offchain)
        assert False, 'fee is too high, should raise Exception'
    except ValueError:
        pass

def test_do_new_channel():
    _, _, lightning, future_payments, value, payment_options, MAX_COINS = (
        make_example_values_for_do()
    )
    assert payment_options[1]['payment_information']['kind'] == 'ln-open'
    payment_information_new_channel = payment_options[1]['payment_information']

    lightning = make_example_network(base_fee=1000, ln_fee = 0.00002)
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
    lightning = make_example_network(base_fee = 1000, ln_fee = 0.00002)
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2000000000
    # 1 -> base_fee, 2 -> len(path) - 2
    fee_intermediary = base_fee + value*ln_fee
    lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
    # sender 0 has 6000000000. in the beginning on the channel to 1
    # after update he should have value less for the transaction to 7 and 2*fee_intermediary less for the fee,
    assert_eq(lightning.network.graph[0][1]['balance'],6000000000-value-2*fee_intermediary)
    # the first intermediary should have value + 2*fee_intermediary more on his channel with the sender
    assert_eq(lightning.network.graph[1][0]['balance'], 7000000000 + value + 2*fee_intermediary)
    # the first intermediary should have fee_intermediary less on his channel with 2nd intermediary.
    assert_eq(lightning.network.graph[1][4]['balance'], 4000000000 - value - fee_intermediary)
    assert_eq(lightning.network.graph[4][1]['balance'], 8000000000 + value + fee_intermediary)
    assert_eq(lightning.network.graph[4][7]['balance'], 10000000000 - value)
    assert_eq(lightning.network.graph[7][4]['balance'], 8000000000 + value)
    assert_eq(lightning.network.graph[1][2]['balance'], 10000000000)

def test_update_balances_pay_not_enough_money():
    lightning = make_example_network(base_fee=1000, ln_fee = 0.00002)
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2000000000000
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
    lightning = make_example_network(base_fee = 1000, ln_fee = 0.00002)
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2000000000
    lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
    # balances are updated, now we want to revert it
    lightning.update_balances(value, ln_fee, base_fee, path, pay=False)
    assert_eq(lightning.network.graph[0][1]['balance'],6000000000)
    # the first intermediary should have value + 2*fee_intermediary more on his channel with the sender
    assert_eq(lightning.network.graph[1][0]['balance'], 7000000000)
    # the first intermediary should have fee_intermediary less on his channel with 2nd intermediary.
    assert_eq(lightning.network.graph[1][4]['balance'], 4000000000)
    assert_eq(lightning.network.graph[4][1]['balance'], 8000000000)
    assert_eq(lightning.network.graph[4][7]['balance'], 10000000000)
    assert_eq(lightning.network.graph[7][4]['balance'], 8000000000)
    assert_eq(lightning.network.graph[1][2]['balance'], 10000000000)

def test_update_balances():
    test_update_balances_pay_enough_money()
    test_update_balances_pay_not_enough_money()
    test_update_balances_reverse()

def test_simulation_with_ln_different_coins(coins_for_parties):
    simulation1 = make_example_simulation_ln(seed = 0, coins_for_parties = coins_for_parties)
    results1 = simulation1.run()
    lightning1 = simulation1.payment_method
    plainbitcoin1 = lightning1.plain_bitcoin
    simulation2 = make_example_simulation_ln(seed = 0, coins_for_parties = coins_for_parties)
    lightning2 = simulation2.payment_method
    plainbitcoin2 = lightning2.plain_bitcoin
    results2 = simulation2.run()
    assert results1 == results2
    assert simulation1 == simulation2
    for party in plainbitcoin1.coins.keys():
        assert_eq(plainbitcoin1.coins[party], plainbitcoin2.coins[party])
    for sender in lightning1.network.graph.nodes():
        for receiver in lightning1.network.graph.nodes():
            if lightning1.network.graph.get_edge_data(sender, receiver) == None:
                assert lightning2.network.graph.get_edge_data(sender, receiver) == None
            else:
                assert_eq(
                    lightning1.network.graph[sender][receiver]['balance'],
                    lightning2.network.graph[sender][receiver]['balance']
                )
    print(results1)
    simulation3 = make_example_simulation_ln(seed = 1, coins_for_parties = coins_for_parties)
    assert simulation1 != simulation3

def test_simulation_with_ln():
    for coins_for_parties in ['max_value', 'small_value', 'random']:
        print(coins_for_parties)
        test_simulation_with_ln_different_coins(coins_for_parties)

if __name__ == "__main__":
    test_LN()
    test_cheapest_path()
    test_get_payment_fee()
    test_update_balances()
    test_get_payment_options()
    test_do()
    test_choose_payment_method()
    test_simulation_with_ln()
    test_random_payments_seed_inside()
    random.seed(5)
    test_random_payments_seed_outside()
    print("Success")


