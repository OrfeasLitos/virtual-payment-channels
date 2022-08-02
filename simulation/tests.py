
import random
import numpy as np
import math
from numpy.testing import assert_almost_equal as assert_eq
import networkx as nx
import collections

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin, sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE
from ln import LN
from elmo import Elmo
from lvpc import LVPC
from donner import Donner
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

def make_example_simulation_for_all(method_name, seed = 12345, coins_for_parties = 'max_value'):
    random.seed(seed)
    match method_name:
        case "LN":
            method = LN(10, coins_for_parties = coins_for_parties)
        case "Elmo":
            method = Elmo(10, coins_for_parties = coins_for_parties)
        case "LVPC":
            method = LVPC(10, coins_for_parties = coins_for_parties)
        case "Donner":
            method = Donner(10, coins_for_parties = coins_for_parties)
        case _:
            raise ValueError
    knowledge = Knowledge('know-all')
    payments = random_payments(100, 10, 2000000000)
    utility_function = example_utility_function_for_simulation
    utility = Utility(utility_function)
    return Simulation(payments, method, knowledge, utility)


def make_example_network_elmo_lvpc_donner(method_name, fee_intermediary = 1000000):
    match method_name:
        case "Elmo":
            method = Elmo(10, fee_intermediary = fee_intermediary)
        case "LVPC":
            method = LVPC(10, lvpc_fee_intermediary = fee_intermediary)
        case "Donner": 
            method = Donner(10, fee_intermediary = fee_intermediary)
        case _:
            raise ValueError

    method.network.add_channel(0, 3000000000., 2, 7000000000., None)
    method.network.add_channel(0, 6000000000., 1, 7000000000., None)
    method.network.add_channel(1, 4000000000., 4, 8000000000., None)
    method.network.add_channel(3, 9000000000., 4, 8000000000., None)
    method.network.add_channel(2, 9000000000., 3, 2000000000., None)
    method.network.add_channel(1, 10000000000., 2, 8000000000., None)
    method.network.add_channel(4, 10000000000., 7, 8000000000., None)
    method.network.add_channel(3, 10000000000., 8, 8000000000., None)
    return method

def make_example_network_elmo_lvpc_donner_and_future_payments(method_name, fee_intermediary = 1000000):
    method = make_example_network_elmo_lvpc_donner(method_name, fee_intermediary)
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 3000000000.)]
    return fee_intermediary, method, future_payments

# adjusted from tests_ln
def make_example_values_for_do_elmo_lvpc_donner(method_name):
    fee_intermediary, method, future_payments = (
        make_example_network_elmo_lvpc_donner_and_future_payments(method_name, fee_intermediary = 1000000)
    )
    value = 100000000.
    payment_options = method.get_payment_options(0, 7, value, future_payments)
    # review: ALL_CAPS case is customarily reserved for user-adjustable global constants
    MAX_COINS = method.plain_bitcoin.max_coins
    return fee_intermediary, method, future_payments, value, MAX_COINS

def test_get_payment_options_elmo_lvpc_donner_channel_exists(method_name):
    fee_intermediary, method, future_payments = make_example_network_elmo_lvpc_donner_and_future_payments(method_name)
    payment_options = method.get_payment_options(0, 2, 1000000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == method_name + '-pay'

def test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible(method_name):
    # virtual channel not possible because of too high value and future payments, would need too much balance
    fee_intermediary, method, future_payments = make_example_network_elmo_lvpc_donner_and_future_payments(method_name)
    payment_options = method.get_payment_options(0, 7, 10000000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == method_name + '-open-channel'

def test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible1(method_name):
    # shortest path should have length 3 and all channels are onchain, so it should give the same results for
    # Elmo, LVPC and Donner
    fee_intermediary, method, future_payments = make_example_network_elmo_lvpc_donner_and_future_payments(method_name)
    payment_options = method.get_payment_options(0, 4, 100000000., future_payments)
    assert len(payment_options) == 3
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == method_name + '-open-channel'
    assert payment_options[2]['payment_information']['kind'] == method_name + '-open-virtual-channel'

# adjusted from tests_ln
def test_do_onchain_elmo_lvpc_donner(method_name):
    fee_intermediary, method, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    payment_options = method.get_payment_options(0, 7, value, future_payments)
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    payment_information_onchain = payment_options[0]['payment_information']
    method.do(payment_information_onchain)
    # sender should have MAX_COINS - 1 - fee many coins, receiver MAX_COINS + 1
    assert method.plain_bitcoin.coins[0] == MAX_COINS - value - method.plain_bitcoin.get_fee() 
    assert method.plain_bitcoin.coins[7] == MAX_COINS + value

def test_do_new_channel_elmo_lvpc_donner(method_name):
    fee_intermediary, method, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    payment_options = method.get_payment_options(0, 8, value, future_payments)
    assert payment_options[1]['payment_information']['kind'] == method_name + '-open-channel'
    payment_information_new_channel = payment_options[1]['payment_information']

    method.do(payment_information_new_channel)
    # check first the coins of the parties
    sum_future_payments = sum_future_payments_to_counterparty(0, 8, future_payments)
    sender_coins = MULTIPLIER_CHANNEL_BALANCE * sum_future_payments
    receiver_coins = value
    tx_size = method.opening_transaction_size
    assert method.plain_bitcoin.coins[0] == MAX_COINS - method.plain_bitcoin.get_fee(tx_size) - sender_coins - receiver_coins 
    assert method.plain_bitcoin.coins[8] == MAX_COINS
    # test the balances on ln (-2 for base fee and payment, +1 for payment).
    assert method.network.graph[0][8]['balance'] == sender_coins
    assert method.network.graph[8][0]['balance'] == receiver_coins

def test_do_new_virtual_channel_elmo_lvpc_donner(method_name):
    # the new_virtual_channel_option is the same for elmo, lvpc and donner as it is a channel on two existing onchain channels.
    fee_intermediary, method, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    payment_options = method.get_payment_options(0, 4, value, future_payments)
    assert payment_options[2]['payment_information']['kind'] == method_name + '-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']

    previous_balance01 = method.network.graph[0][1]['balance']
    previous_balance10 = method.network.graph[1][0]['balance']
    previous_balance14 = method.network.graph[1][4]['balance']
    previous_balance41 = method.network.graph[4][1]['balance']
    previous_balance12 = method.network.graph[1][2]['balance']

    method.do(payment_information_new_virtual_channel)
    # check first the coins of the parties
    sum_future_payments = sum_future_payments_to_counterparty(0, 4, future_payments)
    wanted_sender_coins = MULTIPLIER_CHANNEL_BALANCE * sum_future_payments
    new_virtual_channel_fee = method.get_new_virtual_channel_fee([0,1,4])
    sender_coins = min(
        method.network.graph[0][1]['balance'] - value - new_virtual_channel_fee,
        method.network.graph[1][4]['balance'] - value - new_virtual_channel_fee,
        wanted_sender_coins
    )
    locked_coins = sender_coins + value
    # review: consider testing all channels in two for loops: one for the on-path channels, of which the balances & locked coins have changed, and one for all untouched coins
    assert method.network.graph[1][4]['locked_coins'] == locked_coins
    assert method.network.graph[0][1]['balance'] == previous_balance01 - new_virtual_channel_fee - value - sender_coins
    assert method.network.graph[1][0]['locked_coins'] == 0
    assert method.network.graph[1][0]['balance'] == previous_balance10 + new_virtual_channel_fee
    assert method.network.graph[1][4]['balance'] == previous_balance14 - locked_coins
    assert method.network.graph[4][1]['balance'] == previous_balance41
    assert method.network.graph[4][1]['locked_coins'] == 0
    assert method.network.graph[1][2]['locked_coins'] == 0
    assert method.network.graph[1][2]['balance'] == previous_balance12
    assert method.network.graph.get_edge_data(5, 0) is None

def test_do_elmo_lvpc_donner_pay(method_name):
    fee_intermediary, method, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    payment_options = method.get_payment_options(0, 2, value, future_payments)
    assert payment_options[1]['payment_information']['kind'] == method_name + '-pay'
    payment_information_pay = payment_options[1]['payment_information']

    previous_balance02 = method.network.graph[0][2]['balance']
    previous_balance20 = method.network.graph[2][0]['balance']
    previous_balance01 = method.network.graph[0][1]['balance']

    method.do(payment_information_pay)
    assert method.network.graph[0][2]['balance'] == previous_balance02 - value
    assert method.network.graph[2][0]['balance'] == previous_balance20 + value
    assert method.network.graph[0][2]['locked_coins'] == 0
    assert method.network.graph[0][1]['balance'] == previous_balance01

def test_do_elmo_lvpc_donner(method_name):
    # TODO: test exceptions
    test_do_onchain_elmo_lvpc_donner(method_name)
    test_do_new_channel_elmo_lvpc_donner(method_name)
    test_do_new_virtual_channel_elmo_lvpc_donner(method_name)
    test_do_elmo_lvpc_donner_pay(method_name)


def test_update_balances_new_virtual_channel_true_elmo_lvpc_donner(method_name):
    # Here locking isn't done yet.
    method = make_example_network_elmo_lvpc_donner(method_name)
    path = [0, 1, 4, 7]
    value = 2000000000
    fee_intermediary = method.fee_intermediary
    sender_coins = 100000000
    method.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = True)
    # review: it's unclear where the numbers come from
    # review: better extract them from elmo
    # review: do this in all similar spots
    assert_eq(method.network.graph[0][1]['balance'],6000000000 - 2*fee_intermediary)
    assert_eq(method.network.graph[1][0]['balance'], 7000000000 + 2*fee_intermediary)
    assert_eq(method.network.graph[1][4]['balance'], 4000000000 - fee_intermediary)
    assert_eq(method.network.graph[4][1]['balance'], 8000000000 + fee_intermediary)
    assert_eq(method.network.graph[4][7]['balance'], 10000000000)
    assert_eq(method.network.graph[7][4]['balance'], 8000000000)
    assert_eq(method.network.graph[1][2]['balance'], 10000000000)

def test_update_balances_new_virtual_channel_reverse_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    channels_before = [channel for channel in method.network.graph.edges.data("balance")]
    path = [0, 1, 4, 7]
    value = 2000000000
    sender_coins = 100000000
    method.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = True)
    # balances are updated, now we want to revert it
    method.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = False)
    channels_after = [channel for channel in method.network.graph.edges.data("balance")]
    for i in range(len(channels_before)):
        assert_eq(channels_before[i][2], channels_after[i][2])
    assert_eq(method.network.graph[0][1]['balance'],6000000000)
    assert_eq(method.network.graph[1][0]['balance'], 7000000000)
    assert_eq(method.network.graph[1][4]['balance'], 4000000000)
    assert_eq(method.network.graph[4][1]['balance'], 8000000000)
    assert_eq(method.network.graph[4][7]['balance'], 10000000000)
    assert_eq(method.network.graph[7][4]['balance'], 8000000000)
    assert_eq(method.network.graph[1][2]['balance'], 10000000000)

def test_update_balances_new_virtual_channel_not_enough_money_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    method.fee_intermediary = 9999999999999999
    path = [0, 1, 4, 7]
    value = 2000000000000
    balances = nx.get_edge_attributes(method.network.graph, "balance")
    sender_coins = 100000000
    try:
        method.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = True)
        assert False, 'update_balances() should raise a ValueError'
    except ValueError:
        balances_after_failure = nx.get_edge_attributes(method.network.graph, "balance")
        for key in balances.keys():
            assert_eq(balances[key], balances_after_failure[key])

def test_update_balances_new_virtual_channel_elmo_lvpc_donner(method_name):
    test_update_balances_new_virtual_channel_true_elmo_lvpc_donner(method_name)
    test_update_balances_new_virtual_channel_reverse_elmo_lvpc_donner(method_name)
    test_update_balances_new_virtual_channel_not_enough_money_elmo_lvpc_donner(method_name)

def test_locking_and_unlocking_enough_balance_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    path = [0, 1, 4, 7]
    value = 2000000000
    sender_coins = 100000000
    lock_value = value + sender_coins
    method.network.lock_coins(path, lock_value)
    assert_eq(method.network.graph[0][1]['balance'],6000000000 - lock_value)
    assert_eq(method.network.graph[1][0]['balance'], 7000000000)
    assert_eq(method.network.graph[1][4]['balance'], 4000000000 - lock_value)
    assert_eq(method.network.graph[4][1]['balance'], 8000000000)
    assert_eq(method.network.graph[4][7]['balance'], 10000000000 - lock_value)
    assert_eq(method.network.graph[7][4]['balance'], 8000000000)
    assert_eq(method.network.graph[1][2]['balance'], 10000000000)
    assert_eq(method.network.graph[0][1]['locked_coins'], lock_value)
    assert_eq(method.network.graph[1][0]['locked_coins'], 0)
    assert_eq(method.network.graph[1][4]['locked_coins'], lock_value)
    assert_eq(method.network.graph[4][1]['locked_coins'], 0)
    assert_eq(method.network.graph[4][7]['locked_coins'], lock_value)
    assert_eq(method.network.graph[7][4]['locked_coins'], 0)
    assert_eq(method.network.graph[1][2]['locked_coins'], 0)

    method.network.undo_locking(path, lock_value)
    assert_eq(method.network.graph[0][1]['balance'], 6000000000)
    assert_eq(method.network.graph[1][0]['balance'], 7000000000)
    assert_eq(method.network.graph[1][4]['balance'], 4000000000)
    assert_eq(method.network.graph[4][1]['balance'], 8000000000)
    assert_eq(method.network.graph[4][7]['balance'], 10000000000)
    assert_eq(method.network.graph[7][4]['balance'], 8000000000)
    assert_eq(method.network.graph[1][2]['balance'], 10000000000)
    assert_eq(method.network.graph[0][1]['locked_coins'], 0)
    assert_eq(method.network.graph[1][0]['locked_coins'], 0)
    assert_eq(method.network.graph[1][4]['locked_coins'], 0)
    assert_eq(method.network.graph[4][1]['locked_coins'], 0)
    assert_eq(method.network.graph[4][7]['locked_coins'], 0)
    assert_eq(method.network.graph[7][4]['locked_coins'], 0)
    assert_eq(method.network.graph[1][2]['locked_coins'], 0)

def test_locking_not_enough_balance_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    path = [0, 1, 4, 7]
    value = 2000000000000
    sender_coins = 100000000
    lock_value = value + sender_coins
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(method.network.graph, "locked_coins")
    try:
        method.network.lock_coins(path, lock_value)
        assert False, "should raise ValueError"
    except ValueError:
        balances_after_failure = nx.get_edge_attributes(method.network.graph, "balance")
        locked_coins_after_failure = nx.get_edge_attributes(method.network.graph, "locked_coins")
        for key in balances_before.keys():
            assert_eq(balances_before[key], balances_after_failure[key])
        for key in locked_coins_before.keys():
            assert_eq(locked_coins_before[key], locked_coins_after_failure[key])

def test_lock_and_unlock_elmo_lvpc_donner(method_name):
    test_locking_and_unlocking_enough_balance_elmo_lvpc_donner(method_name)
    test_locking_not_enough_balance_elmo_lvpc_donner(method_name)

def test_pay_enough_balance_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    sender = 0
    receiver = 2
    value = 20000000
    method.pay(sender, receiver, value)
    assert_eq(method.network.graph[sender][receiver]['balance'], 3000000000 - value)
    assert_eq(method.network.graph[receiver][sender]['balance'], 7000000000 + value)
    assert_eq(method.network.graph[0][1]['balance'], 6000000000)
    assert_eq(method.network.graph[sender][receiver]['locked_coins'], 0)

def test_pay_not_enough_balance_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    sender = 0
    receiver = 2
    value = 20000000000000
    try:
        method.pay(sender, receiver, value)
        assert False, "should raise ValueError"
    except ValueError:
        assert_eq(method.network.graph[sender][receiver]['balance'], 3000000000)
        assert_eq(method.network.graph[receiver][sender]['balance'], 7000000000)
        assert_eq(method.network.graph[0][1]['balance'], 6000000000)
        assert_eq(method.network.graph[sender][receiver]['locked_coins'], 0)

def test_pay_elmo_lvpc_donner(method_name):
    test_pay_enough_balance_elmo_lvpc_donner(method_name)
    test_pay_not_enough_balance_elmo_lvpc_donner(method_name)

def test_undo_new_virtual_channel_elmo_lvpc_donner(method_name):
    fee_intermediary, method, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    # virtual channel has length 2 and both underlying channel are onchain -> equal for all 3 methods
    payment_options = method.get_payment_options(0, 4, value, future_payments)
    sender_coins = method.plain_bitcoin.coins[0]
    receiver_coins = method.plain_bitcoin.coins[4]
    assert payment_options[2]['payment_information']['kind'] == method_name + '-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(method.network.graph, "locked_coins")

    method.do(payment_information_new_virtual_channel)
    method.undo(payment_information_new_virtual_channel)
    balances_after_failure = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_after_failure = nx.get_edge_attributes(method.network.graph, "locked_coins")
    for key in balances_before.keys():
        assert_eq(balances_before[key], balances_after_failure[key])
    for key in locked_coins_before.keys():
        assert_eq(locked_coins_before[key], locked_coins_after_failure[key])
    assert sender_coins == method.plain_bitcoin.coins[0]
    assert receiver_coins == method.plain_bitcoin.coins[4]

def test_undo_elmo_lvpc_donner_pay(method_name):
    #TODO: tests are very similar. Check how to unify them.
    fee_intermediary, method, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    payment_options = method.get_payment_options(0, 2, value, future_payments)
    assert payment_options[1]['payment_information']['kind'] == method_name + '-pay'
    payment_information_pay = payment_options[1]['payment_information']
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(method.network.graph, "locked_coins")
    method.do(payment_information_pay)
    method.undo(payment_information_pay)
    balances_after_failure = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_after_failure = nx.get_edge_attributes(method.network.graph, "locked_coins")
    for key in balances_before.keys():
        assert_eq(balances_before[key], balances_after_failure[key])
    for key in locked_coins_before.keys():
        assert_eq(locked_coins_before[key], locked_coins_after_failure[key])

def test_undo_elmo_lvpc_donner(method_name):
    test_undo_new_virtual_channel_elmo_lvpc_donner(method_name)
    test_undo_elmo_lvpc_donner_pay(method_name)

def test_coop_close_channel_first_virtual_layer_no_layer_above_elmo_lvpc_donner(method_name):
    # virtual channel is possible for elmo, lvpc and donner
    fee_intermediary, method, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    payment_options = method.get_payment_options(0, 4, value, future_payments)
    assert payment_options[2]['payment_information']['kind'] == method_name + '-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']

    method.do(payment_information_new_virtual_channel)
    assert method.network.graph[0][4]['channels_below'] == [0,1,4]
    assert method.network.graph[4][0]['channels_below'] == [4,1,0]
    assert method.network.graph[0][1]['channels_above'] == [{0,4}]
    assert method.network.graph[1][0]['channels_above'] == [{0,4}]
    assert method.network.graph[4][1]['channels_above'] == [{0,4}]
    assert method.network.graph[1][4]['channels_above'] == [{0,4}]
    assert method.network.graph[0][2]['channels_above'] == []
    assert method.network.graph[2][0]['channels_above'] == []
    method.network.cooperative_close_channel(0, 4)
    assert method.network.graph[0][1]['channels_above'] == []
    assert method.network.graph[0][1]['channels_below'] is None
    assert method.network.graph[1][0]['channels_above'] == []
    assert method.network.graph[4][1]['channels_above'] == []
    assert method.network.graph[1][4]['channels_above'] == []

def test_force_close_channel_onchain_layer_one_layer_above_elmo_lvpc_donner(method_name):
    fee_intermediary, method, future_payments, value, MAX_COINS = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    payment_options = method.get_payment_options(0, 4, value, future_payments)
    assert payment_options[2]['payment_information']['kind'] == method_name + '-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']

    method.do(payment_information_new_virtual_channel)
    assert method.network.graph[0][4]['channels_below'] == [0,1,4]
    assert method.network.graph[4][0]['channels_below'] == [4,1,0]
    method.network.force_close_channel(0, 1)
    assert method.network.graph[0][4]['channels_below'] is None
    assert method.network.graph[4][0]['channels_below'] is None
    assert method.network.graph.get_edge_data(1, 4) is None

# The following two tests should give the same result for elmo, lvpc and donner as in the beginning,
# of the simulation the differences in the virtual channel don't show up yet.
def test_simulation_with_elmo_lvpc_donner_ignore_centrality(method_name):
    match method_name:
        case "Elmo":
            method = Elmo(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                fee_intermediary = 1000000, opening_transaction_size = 200, elmo_pay_delay = 0.05,
                elmo_new_virtual_channel_delay = 1
            )
        case "LVPC":
            method = LVPC(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                lvpc_fee_intermediary = 1000000, opening_transaction_size = 200, lvpc_pay_delay = 0.05,
                lvpc_new_virtual_channel_delay = 1
            )
        case "Donner":
            method = Donner(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                fee_intermediary = 1000000, opening_transaction_size = 200, donner_pay_delay = 0.05,
                donner_new_virtual_channel_delay = 1
            )
        case _:
            raise ValueError
    knowledge = Knowledge('know-all')
    payments = collections.deque([(0, 1, 100000000000), (0, 1, 10000000000)])
    utility_function = make_example_utility_function(10000, 5000, 10000, 0)
    utility = Utility(utility_function)
    simulation = Simulation(payments, method, knowledge, utility)
    results = simulation.run()
    done_payment0, payment0_info = results[0]
    assert done_payment0 == True
    assert payment0_info['kind'] == method_name + '-open-channel'
    done_payment1, payment1_info = results[1]
    assert done_payment1 == True
    assert payment1_info['kind'] == method_name + '-pay'
    assert len(results) == 2

def test_simulation_with_elmo_lvpc_donner_ignore_centrality_and_distance(method_name):
    match method_name:
        case "Elmo":
            method = Elmo(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                fee_intermediary = 1000000, opening_transaction_size = 200, elmo_pay_delay = 0.05,
                elmo_new_virtual_channel_delay = 1
            )
        case "LVPC":
            method = LVPC(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                lvpc_fee_intermediary = 1000000, opening_transaction_size = 200, lvpc_pay_delay = 0.05,
                lvpc_new_virtual_channel_delay = 1
            )
        case "Donner":
            method = Donner(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                fee_intermediary = 1000000, opening_transaction_size = 200, donner_pay_delay = 0.05,
                donner_new_virtual_channel_delay = 1
            )
    knowledge = Knowledge('know-all')
    payments = collections.deque([(0, 1, 100000000000), (0, 1, 10000000000)])
    utility_function = make_example_utility_function(10000, 5000, 0, 0)
    utility = Utility(utility_function)
    simulation = Simulation(payments, method, knowledge, utility)
    results = simulation.run()
    done_payment0, payment0_info = results[0]
    assert done_payment0 == True
    assert payment0_info['kind'] == 'onchain'
    done_payment1, payment1_info = results[1]
    assert done_payment1 == True
    assert payment1_info['kind'] == 'onchain'
    assert len(results) == 2

def test_simulation_with_previous_channels_elmo_lvpc_donner_ignore_centrality(method_name):
    # the open-virtual-channel option is the same for elmo, lvpc, donner
    # TODO: make tests for simulation where it is different
    match method_name:
        case "Elmo":
            method = Elmo(4, fee_intermediary = 1000000)
        case "LVPC":
            method = LVPC(4, lvpc_fee_intermediary = 1000000)
        case "Donner":
            method = Donner(4, fee_intermediary = 1000000)
    
    method.network.add_channel(0, 3000000000000., 1, 7000000000000., None)
    method.network.add_channel(1, 6000000000000., 2, 7000000000000., None)
    method.network.add_channel(2, 4000000000000., 3, 8000000000000., None)
    method.network.add_channel(1, 1000000000000., 3, 800000000000., [1,2,3])
    method.network.add_channel(0, 100000000000., 3, 80000000000., [0,1,3])
    knowledge = Knowledge('know-all')
    payments = collections.deque([(0, 2, 1000000000), (0, 1, 20000000000)])
    utility_function = make_example_utility_function(10000, 5000, 1, 0)
    utility = Utility(utility_function)
    simulation = Simulation(payments, method, knowledge, utility)
    results = simulation.run()
    done_payment0, payment0_info = results[0]
    done_payment1, payment1_info = results[1]
    assert done_payment0 == True
    assert payment0_info['kind'] == method_name + '-open-virtual-channel'
    assert done_payment1 == True
    assert payment1_info['kind'] == method_name + '-pay'
    assert len(results) == 2
    assert set(method.network.graph.edges()) == set(
        [(0, 1), (1, 0), (0, 2), (2, 0), (0, 3), (3, 0), (1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2)]
    )
    assert method.network.graph[0][1]['locked_coins'] == 1000000000
    assert method.network.graph[1][2]['locked_coins'] == 1000000000
    assert method.network.graph[1][0]['locked_coins'] == 0


if __name__ == "__main__":
    test_cheapest_path()
    print("Success")
