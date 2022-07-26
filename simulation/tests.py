
import random
import numpy as np
import math
from numpy.testing import assert_almost_equal as assert_eq
import networkx as nx
import collections

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin, sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE_LN, MULTIPLIER_CHANNEL_BALANCE_ELMO
from ln import LN
from elmo import Elmo
from lvpc import LVPC
from utility import Utility
from knowledge import Knowledge
from network import Network


def make_example_utility_function(factor_fee, factor_delay, factor_distance, factor_centrality):
    def utility_function(fee, delay, distance, centrality):
        weight_distance_array = np.array(distance)
        inverse_distance_array = 1/ weight_distance_array[:,1]
        weight_array = weight_distance_array[:,0]
        return (
            # review: I'm not sure this is correct, let's discuss
            factor_fee/(1+fee) +
            factor_delay/delay +
            factor_distance * np.transpose(inverse_distance_array) @ weight_array +
            factor_centrality * sum(centrality.values())
            )
    return utility_function

example_utility_function_for_simulation = make_example_utility_function(10000, 5000, 10000, 1000)

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


def make_example_network_ln(base_fee = 1000, ln_fee = 0.00002):
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

def make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 0.00002):
    lightning = make_example_network_ln(base_fee, ln_fee)
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 3000000000.)]
    return base_fee, ln_fee, lightning, future_payments

def make_example_simulation_ln(seed = 12345, coins_for_parties = 'max_value'):
    random.seed(seed)
    lightning = LN(10, coins_for_parties = coins_for_parties)
    knowledge = Knowledge('know-all')
    payments = random_payments(100, 10, 2000000000)
    utility_function = example_utility_function_for_simulation
    utility = Utility(utility_function)
    return Simulation(payments, lightning, knowledge, utility)

def test_get_payment_fee_ln():
    def get_payment_fee_with_path(base_fee, ln_fee, payment, path):
        sender, receiver, value = payment
        return (base_fee +  value * ln_fee) * (len(path) - 1)
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    for payment in future_payments:
        sender, receiver, value = payment
        fee_intermediary = base_fee + value * ln_fee
        path = lightning.network.find_cheapest_path(sender, receiver, value, fee_intermediary)
        num_hops = len(path) - 1
        assert (get_payment_fee_with_path(base_fee, ln_fee, payment, path) ==
            lightning.get_payment_fee(payment, num_hops)
        )

def test_get_payment_options_ln_enough_money():
    _, _, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 0.00002)
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
            'data' : (0, 7, 1000000000., 7, 18000000000., None)
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

def test_get_payment_options_ln():
    test_get_payment_options_ln_enough_money()

def test_choose_payment_method_offchain_best_ln():
    _, _, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1, ln_fee = 0.00002)
    )
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    utility_function = make_example_utility_function(10000, 5000, 1, 1)
    utility = Utility(utility_function)
    # utilities for onchain and new channel are between 30 and 40
    # for offchain several orders of magnitude higher, just consider delay.
    payment_method = utility.choose_payment_method(payment_options)
    assert payment_method['kind'] == 'ln-pay'

def test_choose_payment_method_new_channel_best_ln():
    _, _, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 200)
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

def test_choose_payment_method_onchain_best_ln():
    _, _, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 200)
    )
    payment_options = lightning.get_payment_options(0, 7, 1000000000., future_payments)
    # there's no offchain option
    # the fee in the utility favors the onchain option.
    utility_function = make_example_utility_function(1, 0, 0, 0)
    utility = Utility(utility_function)
    payment_method = utility.choose_payment_method(payment_options)
    assert payment_method['kind'] == 'onchain'

def test_choose_payment_method_ln():
    test_choose_payment_method_offchain_best_ln()
    test_choose_payment_method_new_channel_best_ln()
    test_choose_payment_method_onchain_best_ln()

def test_LN():
    nr_players = 10
    lightning = LN(nr_players)
    future_payments = [(0,1,2.), (0, 7, 1.5), (0,7,2.1), (0, 8, 3.)]
    result = sum_future_payments_to_counterparty(0, 7, future_payments)
    payment_options = lightning.get_payment_options(0, 7, 1., future_payments)
    assert result == 3.6

def make_example_values_for_do_ln():
    base_fee, ln_fee, lightning, future_payments = (
        make_example_network_ln_and_future_payments(base_fee = 1000, ln_fee = 0.00002)
    )
    value = 1000000000.
    payment_options = lightning.get_payment_options(0, 7, value, future_payments)
    MAX_COINS = lightning.plain_bitcoin.max_coins
    return base_fee, ln_fee, lightning, future_payments, value, payment_options, MAX_COINS


def test_do_ln_onchain():
    base_fee, ln_fee, lightning, future_payments, value, payment_options, MAX_COINS = (
        make_example_values_for_do_ln()
    )
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    payment_information_onchain = payment_options[0]['payment_information']
    lightning.do(payment_information_onchain)
    # sender should have MAX_COINS - 1 - fee many coins, receiver MAX_COINS + 1
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS - value - lightning.plain_bitcoin.get_fee() 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS + value

def test_do_ln_onchain_exception():
    lightning = make_example_network_ln(base_fee = 1000, ln_fee = 0.00002)
    payment_information_onchain = { 
        'kind': 'onchain', 'data': (0, 7, 999999999999999999999.)
    }
    try:
        lightning.do(payment_information_onchain)
        assert False, 'should raise exception as amount is too high'
    except ValueError:
        pass

def test_do_ln_offchain():
    base_fee, ln_fee, lightning, future_payments, value, payment_options, MAX_COINS = (
        make_example_values_for_do_ln()
    )
    fee_intermediary = base_fee + value*ln_fee
    for payment_option in payment_options:
        match payment_option['payment_information']['kind']:
            case 'ln-pay':
                payment_information_offchain = payment_option['payment_information']

    # path is [0,1,4,7]
    lightning = make_example_network_ln(base_fee=1000, ln_fee = 0.00002)
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

def test_do_ln_offchain_exception():
    base_fee = 1000
    ln_fee = 200
    lightning = make_example_network_ln(base_fee, ln_fee)
    payment_information_offchain = {
        'kind': 'ln-pay', 'data': ([0,1,4,7], 1000000000)
    }
    try:
        lightning.do(payment_information_offchain)
        assert False, 'fee is too high, should raise Exception'
    except ValueError:
        pass

def test_do_ln_new_channel():
    _, _, lightning, future_payments, value, payment_options, MAX_COINS = (
        make_example_values_for_do_ln()
    )
    assert payment_options[1]['payment_information']['kind'] == 'ln-open'
    payment_information_new_channel = payment_options[1]['payment_information']

    lightning.do(payment_information_new_channel)
    # check first the coins of the parties
    sum_future_payments = sum_future_payments_to_counterparty(0, 7, future_payments)
    sender_coins = MULTIPLIER_CHANNEL_BALANCE_LN * sum_future_payments
    receiver_coins = value
    tx_size = lightning.opening_transaction_size
    assert lightning.plain_bitcoin.coins[0] == MAX_COINS - lightning.plain_bitcoin.get_fee(tx_size) - sender_coins - receiver_coins 
    assert lightning.plain_bitcoin.coins[7] == MAX_COINS
    # test the balances on ln (-2 for base fee and payment, +1 for payment).
    assert lightning.network.graph[0][7]['balance'] == sender_coins 
    assert lightning.network.graph[7][0]['balance'] == receiver_coins

def test_do_ln_new_channel_exception():
    lightning = make_example_network_ln(base_fee = 1, ln_fee = 0.00002)
    payment_information_new_channel = {
        'kind': 'ln-open',
        'data': (0, 7, 1, 7, 99999999999999999999999, None)
    }
    try:
        lightning.do(payment_information_new_channel)
        assert False, "sender can't put more on channel than he has"
    except ValueError:
        pass

def test_do_ln():
    test_do_ln_onchain()
    test_do_ln_onchain_exception()
    test_do_ln_offchain()
    test_do_ln_offchain_exception()
    test_do_ln_new_channel()
    test_do_ln_new_channel_exception()

def test_update_balances_pay_enough_money_ln():
    lightning = make_example_network_ln(base_fee = 1000, ln_fee = 0.00002)
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

def test_update_balances_pay_not_enough_money_ln():
    lightning = make_example_network_ln(base_fee=1000, ln_fee = 0.00002)
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2000000000000
    balances = nx.get_edge_attributes(lightning.network.graph, "balance")
    try:
        lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
        assert False, 'update_balances() should raise a ValueError'
    except ValueError:
        balances_after_failure = nx.get_edge_attributes(lightning.network.graph, "balance")
        for key in balances.keys():
            assert_eq(balances[key], balances_after_failure[key])
        

def test_update_balances_reverse_ln():
    lightning = make_example_network_ln(base_fee = 1000, ln_fee = 0.00002)
    channels_before = [channel for channel in lightning.network.graph.edges.data("balance")]
    base_fee = lightning.base_fee
    ln_fee = lightning.ln_fee
    path = [0, 1, 4, 7]
    value = 2000000000
    lightning.update_balances(value, ln_fee, base_fee, path, pay=True)
    # balances are updated, now we want to revert it
    lightning.update_balances(value, ln_fee, base_fee, path, pay=False)
    channels_after = [channel for channel in lightning.network.graph.edges.data("balance")]
    for i in range(len(channels_before)):
        assert_eq(channels_before[i][2], channels_after[i][2])
    assert_eq(lightning.network.graph[0][1]['balance'],6000000000)
    assert_eq(lightning.network.graph[1][0]['balance'], 7000000000)
    assert_eq(lightning.network.graph[1][4]['balance'], 4000000000)
    assert_eq(lightning.network.graph[4][1]['balance'], 8000000000)
    assert_eq(lightning.network.graph[4][7]['balance'], 10000000000)
    assert_eq(lightning.network.graph[7][4]['balance'], 8000000000)
    assert_eq(lightning.network.graph[1][2]['balance'], 10000000000)

def test_update_balances_ln():
    test_update_balances_pay_enough_money_ln()
    test_update_balances_pay_not_enough_money_ln()
    test_update_balances_reverse_ln()

def test_simulation_with_ln_different_coins(coins_for_parties):
    simulation1 = make_example_simulation_ln(seed = 12345, coins_for_parties = coins_for_parties)
    results1 = simulation1.run()
    lightning1 = simulation1.payment_method
    plainbitcoin1 = lightning1.plain_bitcoin
    simulation2 = make_example_simulation_ln(seed = 12345, coins_for_parties = coins_for_parties)
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
    simulation3 = make_example_simulation_ln(seed = 123, coins_for_parties = coins_for_parties)
    assert simulation1 != simulation3

def test_simulation_with_ln():
    for coins_for_parties in ['max_value', 'small_value', 'random']:
        test_simulation_with_ln_different_coins(coins_for_parties)


def make_example_network_elmo(fee_intermediary = 1000000):
    elmo = Elmo(10, fee_intermediary = fee_intermediary)

    elmo.network.add_channel(0, 3000000000., 2, 7000000000., None)
    elmo.network.add_channel(0, 6000000000., 1, 7000000000., None)
    elmo.network.add_channel(1, 4000000000., 4, 8000000000., None)
    elmo.network.add_channel(3, 9000000000., 4, 8000000000., None)
    elmo.network.add_channel(2, 9000000000., 3, 2000000000., None)
    elmo.network.add_channel(1, 10000000000., 2, 8000000000., None)
    elmo.network.add_channel(4, 10000000000., 7, 8000000000., None)
    elmo.network.add_channel(3, 10000000000., 8, 8000000000., None)
    return elmo

def make_example_network_elmo_and_future_payments(fee_intermediary = 1000000):
    elmo = make_example_network_elmo(fee_intermediary)
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 3000000000.)]
    return fee_intermediary, elmo, future_payments

def make_example_simulation_elmo(seed = 12345, coins_for_parties = 'max_value'):
    random.seed(seed)
    elmo = Elmo(10, coins_for_parties=coins_for_parties)
    knowledge = Knowledge('know-all')
    payments = random_payments(100, 10, 2000000000)
    utility_function = example_utility_function_for_simulation
    utility = Utility(utility_function)
    return Simulation(payments, elmo, knowledge, utility)

def test_get_payment_options_elmo_channel_exists():
    fee_intermediary, elmo, future_payments = make_example_network_elmo_and_future_payments()
    payment_options = elmo.get_payment_options(0, 2, 1000000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-pay'

# adjusted from tests_ln
def make_example_values_for_do_elmo():
    fee_intermediary, elmo, future_payments = (
        make_example_network_elmo_and_future_payments(fee_intermediary = 1000000)
    )
    value = 100000000.
    payment_options = elmo.get_payment_options(0, 7, value, future_payments)
    # review: ALL_CAPS case is customarily reserved for user-adjustable global constants
    MAX_COINS = elmo.plain_bitcoin.max_coins
    return fee_intermediary, elmo, future_payments, value, MAX_COINS

def test_get_payment_options_elmo_no_channel_exists_no_virtual_channel_possible():
    # virtual channel not possible because too much future payments, would need too much balance
    fee_intermediary, elmo, future_payments = make_example_network_elmo_and_future_payments()
    payment_options = elmo.get_payment_options(0, 7, 10000000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-open-channel'

def test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible1():
    fee_intermediary, elmo, future_payments = make_example_network_elmo_and_future_payments()
    payment_options = elmo.get_payment_options(0, 4, 100000000., future_payments)
    assert len(payment_options) == 3
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-open-channel'
    assert payment_options[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'

def test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible2():
    fee_intermediary, elmo, future_payments = make_example_network_elmo_and_future_payments()
    payment_options = elmo.get_payment_options(0, 7, 100000000., future_payments)
    assert len(payment_options) == 3
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-open-channel'
    assert payment_options[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'

def test_get_payment_options_elmo():
    test_get_payment_options_elmo_channel_exists()
    test_get_payment_options_elmo_no_channel_exists_no_virtual_channel_possible()
    test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible1()
    test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible2()

# adjusted from tests_ln
def test_do_onchain_elmo():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo()
    )
    payment_options = elmo.get_payment_options(0, 7, value, future_payments)
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    payment_information_onchain = payment_options[0]['payment_information']
    elmo.do(payment_information_onchain)
    # sender should have MAX_COINS - 1 - fee many coins, receiver MAX_COINS + 1
    assert elmo.plain_bitcoin.coins[0] == MAX_COINS - value - elmo.plain_bitcoin.get_fee() 
    assert elmo.plain_bitcoin.coins[7] == MAX_COINS + value

def test_do_new_channel_elmo():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo()
    )
    payment_options = elmo.get_payment_options(0, 8, value, future_payments)
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-open-channel'
    payment_information_new_channel = payment_options[1]['payment_information']

    elmo.do(payment_information_new_channel)
    # check first the coins of the parties
    sum_future_payments = sum_future_payments_to_counterparty(0, 8, future_payments)
    sender_coins = MULTIPLIER_CHANNEL_BALANCE_ELMO * sum_future_payments
    receiver_coins = value
    tx_size = elmo.opening_transaction_size
    assert elmo.plain_bitcoin.coins[0] == MAX_COINS - elmo.plain_bitcoin.get_fee(tx_size) - sender_coins - receiver_coins 
    assert elmo.plain_bitcoin.coins[8] == MAX_COINS
    # test the balances on ln (-2 for base fee and payment, +1 for payment).
    assert elmo.network.graph[0][8]['balance'] == sender_coins
    assert elmo.network.graph[8][0]['balance'] == receiver_coins

def test_do_new_virtual_channel_elmo():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo()
    )
    payment_options = elmo.get_payment_options(0, 4, value, future_payments)
    assert payment_options[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']

    previous_balance01 = elmo.network.graph[0][1]['balance']
    previous_balance10 = elmo.network.graph[1][0]['balance']
    previous_balance14 = elmo.network.graph[1][4]['balance']
    previous_balance41 = elmo.network.graph[4][1]['balance']
    previous_balance12 = elmo.network.graph[1][2]['balance']

    elmo.do(payment_information_new_virtual_channel)
    # check first the coins of the parties
    sum_future_payments = sum_future_payments_to_counterparty(0, 4, future_payments)
    wanted_sender_coins = MULTIPLIER_CHANNEL_BALANCE_ELMO * sum_future_payments
    new_virtual_channel_fee = elmo.get_new_virtual_channel_fee([0,1,4])
    sender_coins = min(
        elmo.network.graph[0][1]['balance'] - value - new_virtual_channel_fee,
        elmo.network.graph[1][4]['balance'] - value - new_virtual_channel_fee,
        wanted_sender_coins
    )
    locked_coins = sender_coins + value
    # review: consider testing all channels in two for loops: one for the on-path channels, of which the balances & locked coins have changed, and one for all untouched coins
    assert elmo.network.graph[1][4]['locked_coins'] == locked_coins
    assert elmo.network.graph[0][1]['balance'] == previous_balance01 - new_virtual_channel_fee - value - sender_coins
    assert elmo.network.graph[1][0]['locked_coins'] == 0
    assert elmo.network.graph[1][0]['balance'] == previous_balance10 + new_virtual_channel_fee
    assert elmo.network.graph[1][4]['balance'] == previous_balance14 - locked_coins
    assert elmo.network.graph[4][1]['balance'] == previous_balance41
    assert elmo.network.graph[4][1]['locked_coins'] == 0
    assert elmo.network.graph[1][2]['locked_coins'] == 0
    assert elmo.network.graph[1][2]['balance'] == previous_balance12
    assert elmo.network.graph.get_edge_data(5, 0) is None

def test_do_elmo_pay():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo()
    )
    payment_options = elmo.get_payment_options(0, 2, value, future_payments)
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-pay'
    payment_information_pay = payment_options[1]['payment_information']

    previous_balance02 = elmo.network.graph[0][2]['balance']
    previous_balance20 = elmo.network.graph[2][0]['balance']
    previous_balance01 = elmo.network.graph[0][1]['balance']

    elmo.do(payment_information_pay)
    assert elmo.network.graph[0][2]['balance'] == previous_balance02 - value
    assert elmo.network.graph[2][0]['balance'] == previous_balance20 + value
    assert elmo.network.graph[0][2]['locked_coins'] == 0
    assert elmo.network.graph[0][1]['balance'] == previous_balance01

def test_do_elmo():
    # TODO: test exceptions
    test_do_onchain_elmo()
    test_do_new_channel_elmo()
    test_do_new_virtual_channel_elmo()
    test_do_elmo_pay()

def test_update_balances_new_virtual_channel_true_elmo():
    # Here locking isn't done yet.
    elmo = make_example_network_elmo()
    path = [0, 1, 4, 7]
    value = 2000000000
    fee_intermediary = elmo.fee_intermediary
    sender_coins = 100000000
    elmo.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = True)
    # review: it's unclear where the numbers come from
    # review: better extract them from elmo
    # review: do this in all similar spots
    assert_eq(elmo.network.graph[0][1]['balance'],6000000000 - 2*fee_intermediary)
    assert_eq(elmo.network.graph[1][0]['balance'], 7000000000 + 2*fee_intermediary)
    assert_eq(elmo.network.graph[1][4]['balance'], 4000000000 - fee_intermediary)
    assert_eq(elmo.network.graph[4][1]['balance'], 8000000000 + fee_intermediary)
    assert_eq(elmo.network.graph[4][7]['balance'], 10000000000)
    assert_eq(elmo.network.graph[7][4]['balance'], 8000000000)
    assert_eq(elmo.network.graph[1][2]['balance'], 10000000000)

def test_update_balances_new_virtual_channel_reverse_elmo():
    elmo = make_example_network_elmo()
    channels_before = [channel for channel in elmo.network.graph.edges.data("balance")]
    path = [0, 1, 4, 7]
    value = 2000000000
    sender_coins = 100000000
    elmo.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = True)
    # balances are updated, now we want to revert it
    elmo.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = False)
    channels_after = [channel for channel in elmo.network.graph.edges.data("balance")]
    for i in range(len(channels_before)):
        assert_eq(channels_before[i][2], channels_after[i][2])
    assert_eq(elmo.network.graph[0][1]['balance'],6000000000)
    assert_eq(elmo.network.graph[1][0]['balance'], 7000000000)
    assert_eq(elmo.network.graph[1][4]['balance'], 4000000000)
    assert_eq(elmo.network.graph[4][1]['balance'], 8000000000)
    assert_eq(elmo.network.graph[4][7]['balance'], 10000000000)
    assert_eq(elmo.network.graph[7][4]['balance'], 8000000000)
    assert_eq(elmo.network.graph[1][2]['balance'], 10000000000)

def test_update_balances_new_virtual_channel_not_enough_money_elmo():
    elmo = make_example_network_elmo()
    elmo.fee_intermediary = 9999999999999999
    path = [0, 1, 4, 7]
    value = 2000000000000
    balances = nx.get_edge_attributes(elmo.network.graph, "balance")
    sender_coins = 100000000
    try:
        elmo.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = True)
        assert False, 'update_balances() should raise a ValueError'
    except ValueError:
        balances_after_failure = nx.get_edge_attributes(elmo.network.graph, "balance")
        for key in balances.keys():
            assert_eq(balances[key], balances_after_failure[key])

def test_update_balances_new_virtual_channel_elmo():
    test_update_balances_new_virtual_channel_true_elmo()
    test_update_balances_new_virtual_channel_reverse_elmo()
    test_update_balances_new_virtual_channel_not_enough_money_elmo()

def test_locking_and_unlocking_enough_balance_elmo():
    elmo = make_example_network_elmo()
    path = [0, 1, 4, 7]
    value = 2000000000
    sender_coins = 100000000
    lock_value = value + sender_coins
    elmo.network.lock_coins(path, lock_value)
    assert_eq(elmo.network.graph[0][1]['balance'],6000000000 - lock_value)
    assert_eq(elmo.network.graph[1][0]['balance'], 7000000000)
    assert_eq(elmo.network.graph[1][4]['balance'], 4000000000 - lock_value)
    assert_eq(elmo.network.graph[4][1]['balance'], 8000000000)
    assert_eq(elmo.network.graph[4][7]['balance'], 10000000000 - lock_value)
    assert_eq(elmo.network.graph[7][4]['balance'], 8000000000)
    assert_eq(elmo.network.graph[1][2]['balance'], 10000000000)
    assert_eq(elmo.network.graph[0][1]['locked_coins'], lock_value)
    assert_eq(elmo.network.graph[1][0]['locked_coins'], 0)
    assert_eq(elmo.network.graph[1][4]['locked_coins'], lock_value)
    assert_eq(elmo.network.graph[4][1]['locked_coins'], 0)
    assert_eq(elmo.network.graph[4][7]['locked_coins'], lock_value)
    assert_eq(elmo.network.graph[7][4]['locked_coins'], 0)
    assert_eq(elmo.network.graph[1][2]['locked_coins'], 0)

    elmo.network.undo_locking(path, lock_value)
    assert_eq(elmo.network.graph[0][1]['balance'], 6000000000)
    assert_eq(elmo.network.graph[1][0]['balance'], 7000000000)
    assert_eq(elmo.network.graph[1][4]['balance'], 4000000000)
    assert_eq(elmo.network.graph[4][1]['balance'], 8000000000)
    assert_eq(elmo.network.graph[4][7]['balance'], 10000000000)
    assert_eq(elmo.network.graph[7][4]['balance'], 8000000000)
    assert_eq(elmo.network.graph[1][2]['balance'], 10000000000)
    assert_eq(elmo.network.graph[0][1]['locked_coins'], 0)
    assert_eq(elmo.network.graph[1][0]['locked_coins'], 0)
    assert_eq(elmo.network.graph[1][4]['locked_coins'], 0)
    assert_eq(elmo.network.graph[4][1]['locked_coins'], 0)
    assert_eq(elmo.network.graph[4][7]['locked_coins'], 0)
    assert_eq(elmo.network.graph[7][4]['locked_coins'], 0)
    assert_eq(elmo.network.graph[1][2]['locked_coins'], 0)

def test_locking_not_enough_balance_elmo():
    elmo = make_example_network_elmo()
    path = [0, 1, 4, 7]
    value = 2000000000000
    sender_coins = 100000000
    lock_value = value + sender_coins
    balances_before = nx.get_edge_attributes(elmo.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(elmo.network.graph, "locked_coins")
    try:
        elmo.network.lock_coins(path, lock_value)
        assert False, "should raise ValueError"
    except ValueError:
        balances_after_failure = nx.get_edge_attributes(elmo.network.graph, "balance")
        locked_coins_after_failure = nx.get_edge_attributes(elmo.network.graph, "locked_coins")
        for key in balances_before.keys():
            assert_eq(balances_before[key], balances_after_failure[key])
        for key in locked_coins_before.keys():
            assert_eq(locked_coins_before[key], locked_coins_after_failure[key])

def test_lock_and_unlock_elmo():
    test_locking_and_unlocking_enough_balance_elmo()
    test_locking_not_enough_balance_elmo()

def test_pay_enough_balance_elmo():
    elmo = make_example_network_elmo()
    sender = 0
    receiver = 2
    value = 20000000
    elmo.pay(sender, receiver, value)
    assert_eq(elmo.network.graph[sender][receiver]['balance'], 3000000000 - value)
    assert_eq(elmo.network.graph[receiver][sender]['balance'], 7000000000 + value)
    assert_eq(elmo.network.graph[0][1]['balance'], 6000000000)
    assert_eq(elmo.network.graph[sender][receiver]['locked_coins'], 0)

def test_pay_not_enough_balance_elmo():
    elmo = make_example_network_elmo()
    sender = 0
    receiver = 2
    value = 20000000000000
    try:
        elmo.pay(sender, receiver, value)
        assert False, "should raise ValueError"
    except ValueError:
        assert_eq(elmo.network.graph[sender][receiver]['balance'], 3000000000)
        assert_eq(elmo.network.graph[receiver][sender]['balance'], 7000000000)
        assert_eq(elmo.network.graph[0][1]['balance'], 6000000000)
        assert_eq(elmo.network.graph[sender][receiver]['locked_coins'], 0)

def test_pay_elmo():
    test_pay_enough_balance_elmo()
    test_pay_not_enough_balance_elmo()

def test_undo_new_virtual_channel_elmo():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo()
    )
    payment_options = elmo.get_payment_options(0, 4, value, future_payments)
    sender_coins = elmo.plain_bitcoin.coins[0]
    receiver_coins = elmo.plain_bitcoin.coins[4]
    assert payment_options[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']
    balances_before = nx.get_edge_attributes(elmo.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(elmo.network.graph, "locked_coins")

    elmo.do(payment_information_new_virtual_channel)
    elmo.undo(payment_information_new_virtual_channel)
    balances_after_failure = nx.get_edge_attributes(elmo.network.graph, "balance")
    locked_coins_after_failure = nx.get_edge_attributes(elmo.network.graph, "locked_coins")
    for key in balances_before.keys():
        assert_eq(balances_before[key], balances_after_failure[key])
    for key in locked_coins_before.keys():
        assert_eq(locked_coins_before[key], locked_coins_after_failure[key])
    assert sender_coins == elmo.plain_bitcoin.coins[0]
    assert receiver_coins == elmo.plain_bitcoin.coins[4]

def test_undo_elmo_pay():
    #TODO: tests are very similar. Check how to unify them.
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo()
    )
    payment_options = elmo.get_payment_options(0, 2, value, future_payments)
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-pay'
    payment_information_pay = payment_options[1]['payment_information']
    balances_before = nx.get_edge_attributes(elmo.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(elmo.network.graph, "locked_coins")
    elmo.do(payment_information_pay)
    elmo.undo(payment_information_pay)
    balances_after_failure = nx.get_edge_attributes(elmo.network.graph, "balance")
    locked_coins_after_failure = nx.get_edge_attributes(elmo.network.graph, "locked_coins")
    for key in balances_before.keys():
        assert_eq(balances_before[key], balances_after_failure[key])
    for key in locked_coins_before.keys():
        assert_eq(locked_coins_before[key], locked_coins_after_failure[key])

def test_undo_elmo():
    test_undo_new_virtual_channel_elmo()
    test_undo_elmo_pay()

def test_coop_close_channel_first_virtual_layer_no_layer_above_elmo():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo()
    )
    payment_options = elmo.get_payment_options(0, 4, value, future_payments)
    assert payment_options[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']

    elmo.do(payment_information_new_virtual_channel)
    assert elmo.network.graph[0][4]['channels_below'] == [0,1,4]
    assert elmo.network.graph[4][0]['channels_below'] == [4,1,0]
    assert elmo.network.graph[0][1]['channels_above'] == [{0,4}]
    assert elmo.network.graph[1][0]['channels_above'] == [{0,4}]
    assert elmo.network.graph[4][1]['channels_above'] == [{0,4}]
    assert elmo.network.graph[1][4]['channels_above'] == [{0,4}]
    assert elmo.network.graph[0][2]['channels_above'] == []
    assert elmo.network.graph[2][0]['channels_above'] == []
    elmo.network.cooperative_close_channel(0, 4)
    assert elmo.network.graph[0][1]['channels_above'] == []
    assert elmo.network.graph[0][1]['channels_below'] is None
    assert elmo.network.graph[1][0]['channels_above'] == []
    assert elmo.network.graph[4][1]['channels_above'] == []
    assert elmo.network.graph[1][4]['channels_above'] == []

def test_coop_close_channel_first_virtual_layer_one_layer_above_elmo(forward = True):
    elmo = make_example_network_elmo()
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 300000000.), (0, 3, 2500000000.)]
    value1 = 100000000
    payment_options1 = elmo.get_payment_options(0, 3, value1, future_payments)
    assert payment_options1[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'
    payment_information_new_virtual_channel1 = payment_options1[2]['payment_information']

    elmo.do(payment_information_new_virtual_channel1)

    value2 = 1000000
    payment_options2 = elmo.get_payment_options(0, 8, value2, future_payments)
    assert payment_options2[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'
    assert payment_options2[2]['payment_information']['data'][0] == [0, 3, 8]
    payment_information_new_virtual_channel2 = payment_options2[2]['payment_information']

    elmo.do(payment_information_new_virtual_channel2)
    assert elmo.network.graph[0][3]['channels_below'] == [0, 2, 3]
    assert elmo.network.graph[3][0]['channels_below'] == [3, 2, 0]
    assert elmo.network.graph[0][8]['channels_below'] == [0, 3, 8]
    assert elmo.network.graph[8][0]['channels_below'] == [8, 3, 0]
    assert elmo.network.graph[0][2]['channels_above'] == [{0, 3}]
    assert elmo.network.graph[2][0]['channels_above'] == [{0, 3}]
    assert elmo.network.graph[3][2]['channels_above'] == [{0, 3}]
    assert elmo.network.graph[2][3]['channels_above'] == [{0, 3}]
    assert elmo.network.graph[0][3]['channels_above'] == [{0, 8}]
    assert elmo.network.graph[3][0]['channels_above'] == [{0, 8}]
    assert elmo.network.graph[3][8]['channels_above'] == [{0, 8}]
    assert elmo.network.graph[8][3]['channels_above'] == [{0, 8}]
    if forward == True:
        elmo.network.cooperative_close_channel(0, 3)
    else:
        elmo.network.cooperative_close_channel(3, 0)
    assert elmo.network.graph[0][8]['channels_below'] == [0, 2, 3, 8]
    assert elmo.network.graph[8][0]['channels_below'] == [8, 3, 2, 0]
    assert elmo.network.graph[0][2]['channels_above'] == [{0, 8}]
    assert elmo.network.graph[2][0]['channels_above'] == [{0, 8}]
    assert elmo.network.graph[3][2]['channels_above'] == [{0, 8}]
    assert elmo.network.graph[2][3]['channels_above'] == [{0, 8}]
    assert elmo.network.graph[3][8]['channels_above'] == [{0, 8}]
    assert elmo.network.graph[8][3]['channels_above'] == [{0, 8}]
    assert elmo.network.graph.get_edge_data(0, 3) is None
    assert elmo.network.graph.get_edge_data(3, 0) is None

def test_force_close_channel_onchain_layer_one_layer_above_elmo():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo()
    )
    payment_options = elmo.get_payment_options(0, 4, value, future_payments)
    assert payment_options[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']

    elmo.do(payment_information_new_virtual_channel)
    assert elmo.network.graph[0][4]['channels_below'] == [0,1,4]
    assert elmo.network.graph[4][0]['channels_below'] == [4,1,0]
    elmo.network.force_close_channel(0, 1)
    assert elmo.network.graph[0][4]['channels_below'] is None
    assert elmo.network.graph[4][0]['channels_below'] is None
    assert elmo.network.graph.get_edge_data(1, 4) is None

def test_close_channel_elmo():
    test_coop_close_channel_first_virtual_layer_no_layer_above_elmo()
    test_coop_close_channel_first_virtual_layer_one_layer_above_elmo(forward = True)
    test_coop_close_channel_first_virtual_layer_one_layer_above_elmo(forward = False)
    test_force_close_channel_onchain_layer_one_layer_above_elmo()

def test_force_close1_elmo():
    elmo = Elmo(6, fee_intermediary = 1000000)

    elmo.network.add_channel(0, 3000000000., 1, 7000000000., None)
    elmo.network.add_channel(1, 6000000000., 2, 7000000000., None)
    elmo.network.add_channel(2, 4000000000., 3, 8000000000., None)
    elmo.network.add_channel(4, 9000000000., 5, 8000000000., None)
    elmo.network.add_channel(1, 9000000000., 4, 2000000000., None)
    elmo.network.add_channel(0, 1000000000., 2, 800000000., [0,1,2])
    elmo.network.lock_coins([0,1,2], 1000000000. + 800000000.)
    elmo.network.add_channel(3, 1000000000., 4, 800000000., [3,2,1,4])
    elmo.network.lock_coins([3,2,1,4], 1000000000. + 800000000.)
    elmo.network.add_channel(2, 100000000., 4, 80000000., [2,3,4])
    elmo.network.lock_coins([2,3,4], 100000000. + 80000000.)
    elmo.network.add_channel(0, 90000000., 5, 20000000., [0,2,4,5])
    elmo.network.lock_coins([0,2,4,5], 9000000. + 2000000.)
    previous_balances = nx.get_edge_attributes(elmo.network.graph, 'balance')
    previous_locked_coins = nx.get_edge_attributes(elmo.network.graph, 'locked_coins')
    coins_for_chain = elmo.network.force_close_channel(0, 1)
    assert set(elmo.network.graph.edges()) == set([(0, 2), (2, 0), (5, 0), (0, 5), (2, 4), (4, 2), (4, 5), (5, 4)])
    assert elmo.network.graph[0][2]['channels_below'] is None
    assert elmo.network.graph[2][0]['channels_below'] is None
    assert elmo.network.graph[4][2]['channels_below'] is None
    assert elmo.network.graph[2][4]['channels_below'] is None
    assert elmo.network.graph[4][5]['channels_below'] is None
    assert elmo.network.graph[5][4]['channels_below'] is None
    assert elmo.network.graph[0][2]['channels_above'] == [{5, 0}]
    assert elmo.network.graph[2][0]['channels_above'] == [{0, 5}]
    assert elmo.network.graph[4][2]['channels_above'] == [{0, 5}]
    assert elmo.network.graph[2][4]['channels_above'] == [{0, 5}]
    assert elmo.network.graph[4][5]['channels_above'] == [{0, 5}]
    assert elmo.network.graph[5][4]['channels_above'] == [{0, 5}]
    assert coins_for_chain[(0, 1)] == 3000000000.
    assert coins_for_chain[(1, 0)] == 7000000000.
    assert set(coins_for_chain) == set([(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3), (1, 4), (4, 1)])
    for parties, value in coins_for_chain.items():
        assert value == previous_balances[parties] + previous_locked_coins[parties]

def test_force_close2_elmo():
    elmo = Elmo(4, fee_intermediary = 1000000)

    elmo.network.add_channel(0, 3000000000., 1, 7000000000., None)
    elmo.network.add_channel(1, 6000000000., 2, 7000000000., None)
    elmo.network.add_channel(2, 4000000000., 3, 8000000000., None)
    elmo.network.add_channel(1, 1000000000., 3, 800000000., [1,2,3])
    elmo.network.add_channel(0, 100000000., 3, 80000000., [0,1,3])
    elmo.network.force_close_channel(0, 1)
    assert set(elmo.network.graph.edges()) == set([(0, 3), (3, 0)])
    assert elmo.network.graph[0][3]['channels_below'] is None
    assert elmo.network.graph[0][3]['channels_above'] == []
    assert elmo.network.graph[3][0]['channels_below'] is None
    assert elmo.network.graph[3][0]['channels_above'] == []

def test_force_close_elmo():
    test_force_close1_elmo()
    test_force_close2_elmo()

def test_simulation_with_elmo_ignore_centrality():
    elmo = Elmo(
        nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
        fee_intermediary = 1000000, opening_transaction_size = 200, elmo_pay_delay = 0.05,
        elmo_new_virtual_channel_delay = 1
    )
    knowledge = Knowledge('know-all')
    payments = collections.deque([(0, 1, 100000000000), (0, 1, 10000000000)])
    utility_function = make_example_utility_function(10000, 5000, 10000, 0)
    utility = Utility(utility_function)
    simulation = Simulation(payments, elmo, knowledge, utility)
    results = simulation.run()
    done_payment0, payment0_info = results[0]
    assert done_payment0 == True
    assert payment0_info['kind'] == 'Elmo-open-channel'
    done_payment1, payment1_info = results[1]
    assert done_payment1 == True
    assert payment1_info['kind'] == 'Elmo-pay'
    assert len(results) == 2

def test_simulation_with_elmo_ignore_centrality_and_distance():
    elmo = Elmo(
        nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
        fee_intermediary = 1000000, opening_transaction_size = 200, elmo_pay_delay = 0.05,
        elmo_new_virtual_channel_delay = 1
    )
    knowledge = Knowledge('know-all')
    payments = collections.deque([(0, 1, 100000000000), (0, 1, 10000000000)])
    utility_function = make_example_utility_function(10000, 5000, 0, 0)
    utility = Utility(utility_function)
    simulation = Simulation(payments, elmo, knowledge, utility)
    results = simulation.run()
    done_payment0, payment0_info = results[0]
    assert done_payment0 == True
    assert payment0_info['kind'] == 'onchain'
    done_payment1, payment1_info = results[1]
    assert done_payment1 == True
    assert payment1_info['kind'] == 'onchain'
    assert len(results) == 2

def test_simulation_with_previous_channels_elmo_ignore_centrality():
    elmo = Elmo(4, fee_intermediary = 1000000)

    elmo.network.add_channel(0, 3000000000000., 1, 7000000000000., None)
    elmo.network.add_channel(1, 6000000000000., 2, 7000000000000., None)
    elmo.network.add_channel(2, 4000000000000., 3, 8000000000000., None)
    elmo.network.add_channel(1, 1000000000000., 3, 800000000000., [1,2,3])
    elmo.network.add_channel(0, 100000000000., 3, 80000000000., [0,1,3])
    knowledge = Knowledge('know-all')
    payments = collections.deque([(0, 2, 1000000000), (0, 1, 20000000000)])
    utility_function = make_example_utility_function(10000, 5000, 1, 0)
    utility = Utility(utility_function)
    simulation = Simulation(payments, elmo, knowledge, utility)
    results = simulation.run()
    done_payment0, payment0_info = results[0]
    done_payment1, payment1_info = results[1]
    assert done_payment0 == True
    assert payment0_info['kind'] == 'Elmo-open-virtual-channel'
    assert done_payment1 == True
    assert payment1_info['kind'] == 'Elmo-pay'
    assert len(results) == 2
    assert set(elmo.network.graph.edges()) == set(
        [(0, 1), (1, 0), (0, 2), (2, 0), (0, 3), (3, 0), (1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2)]
    )
    assert elmo.network.graph[0][1]['locked_coins'] == 1000000000
    assert elmo.network.graph[1][2]['locked_coins'] == 1000000000
    assert elmo.network.graph[1][0]['locked_coins'] == 0

def test_simulation_with_elmo():
    simulation = make_example_simulation_elmo()
    results = simulation.run()
    print(results)
    test_simulation_with_elmo_ignore_centrality()
    test_simulation_with_elmo_ignore_centrality_and_distance()
    test_simulation_with_previous_channels_elmo_ignore_centrality()


def make_example_network_lvpc(lvpc_fee_intermediary = 1000000):
    lvpc = LVPC(10, lvpc_fee_intermediary = lvpc_fee_intermediary)

    lvpc.network.add_channel(0, 3000000000., 2, 7000000000., None)
    lvpc.network.add_channel(0, 6000000000., 1, 7000000000., None)
    lvpc.network.add_channel(1, 4000000000., 4, 8000000000., None)
    lvpc.network.add_channel(3, 9000000000., 4, 8000000000., None)
    lvpc.network.add_channel(2, 9000000000., 3, 2000000000., None)
    lvpc.network.add_channel(1, 10000000000., 2, 8000000000., None)
    lvpc.network.add_channel(4, 10000000000., 7, 8000000000., None)
    lvpc.network.add_channel(3, 10000000000., 8, 8000000000., None)
    return lvpc

# copied from elmo
def make_example_network_lvpc_and_future_payments(fee_intermediary = 1000000):
    lvpc = make_example_network_lvpc(fee_intermediary)
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 3000000000.)]
    return fee_intermediary, lvpc, future_payments

# copied from elmo
def make_example_simulation_lvpc(seed = 12345, coins_for_parties = 'max_value'):
    random.seed(seed)
    lvpc = LVPC(10, coins_for_parties=coins_for_parties)
    knowledge = Knowledge('know-all')
    payments = random_payments(100, 10, 2000000000)
    utility_function = example_utility_function_for_simulation
    utility = Utility(utility_function)
    return Simulation(payments, lvpc, knowledge, utility)

def test_get_payment_options_lvpc_no_channel_exists_virtual_channel_possible():
    fee_intermediary, lvpc, future_payments = make_example_network_lvpc_and_future_payments()
    payment_options = lvpc.get_payment_options(0, 4, 100000000., future_payments)
    assert len(payment_options) == 3
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'LVPC-open-channel'
    assert payment_options[2]['payment_information']['kind'] == 'LVPC-open-virtual-channel'

def test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible1():
    fee_intermediary, lvpc, future_payments = make_example_network_lvpc_and_future_payments()
    payment_options = lvpc.get_payment_options(0, 7, 100000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'LVPC-open-channel'

def test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible2():
    # virtual channel not possible because too much future payments, would need too much balance
    fee_intermediary, lvpc, future_payments = make_example_network_lvpc_and_future_payments()
    payment_options = lvpc.get_payment_options(0, 7, 10000000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'LVPC-open-channel'

def test_get_payment_options_lvpc():
    test_get_payment_options_lvpc_no_channel_exists_virtual_channel_possible()
    test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible1()
    test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible2()

def test_simulation_with_lvpc():
    simulation = make_example_simulation_lvpc()
    results = simulation.run()
    print(results)



if __name__ == "__main__":
    test_cheapest_path()
    test_LN()
    test_get_payment_fee_ln()
    test_update_balances_ln()
    test_get_payment_options_ln()
    test_do_ln()
    test_choose_payment_method_ln()
    test_simulation_with_ln()
    test_get_payment_options_elmo()
    test_do_elmo()
    test_update_balances_new_virtual_channel_elmo()
    test_lock_and_unlock_elmo()
    test_pay_elmo()
    test_undo_elmo()
    test_simulation_with_elmo()
    test_close_channel_elmo()
    test_force_close_elmo()
    test_get_payment_options_lvpc()
    test_simulation_with_lvpc()
    print("Success")
