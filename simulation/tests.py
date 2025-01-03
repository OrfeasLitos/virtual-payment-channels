
import random
import numpy as np
from numpy.testing import assert_almost_equal as assert_eq
import networkx as nx
import collections

from simulation import Simulation, random_payments
from paymentmethod import (
    sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE,
    MAX_COINS
)
from custom_elmo_lvpc_donner import AVAILABILITY_FACTOR
from ln import LN
from elmo import Elmo
from lvpc import LVPC
from donner import Donner
from utility import Utility
from knowledge import Knowledge
from network import Network


def make_example_utility_function(factor_fee, factor_delay, factor_distance, factor_centrality):
    def utility_function(party, fee, delay, distance, centrality):
        weight_distance_array = np.array(distance)
        inverse_distance_array = 1/ weight_distance_array[:,1]
        weight_array = weight_distance_array[:,0]
        return (
            factor_fee/(100+fee) +
            factor_delay/delay +
            factor_distance * np.transpose(inverse_distance_array) @ weight_array +
            factor_centrality * centrality
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

def make_example_simulation_for_all(method_name, seed = 12345, nr_players = 10, coins_for_parties = 'max_value', distribution = 'uniform'):
    random.seed(seed)
    np.random.seed(seed)
    match method_name:
        case "LN":
            method = LN(nr_players = nr_players, coins_for_parties = coins_for_parties)
        case "Elmo":
            method = Elmo(nr_players = nr_players, coins_for_parties = coins_for_parties)
        case "LVPC":
            method = LVPC(nr_players = nr_players, coins_for_parties = coins_for_parties)
        case "Donner":
            method = Donner(nr_players = nr_players, coins_for_parties = coins_for_parties)
        case _:
            raise ValueError
    knowledge = Knowledge('all')
    payments = random_payments(nr_players, distribution=distribution, num_pays = 100)
    utility_function = example_utility_function_for_simulation
    utility = Utility('customized', utility_function=utility_function)
    return Simulation(payments, method, knowledge, utility)


def make_example_network_elmo_lvpc_donner(method_name, base_fee = 1000000):
    match method_name:
        case "Elmo":
            method = Elmo(10, base_fee = base_fee)
        case "LVPC":
            method = LVPC(10, base_fee = base_fee)
        case "Donner": 
            method = Donner(10, base_fee = base_fee)
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

def make_example_network_elmo_lvpc_donner_and_future_payments(method_name, base_fee = 1000000):
    method = make_example_network_elmo_lvpc_donner(method_name, base_fee)
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 3000000000.)]
    return base_fee, method, future_payments

def get_knowledge_sender(sender, future_payments):
    """
    For the case the sender knows all future_payments
    """
    return (
        future_payments, len([payment for payment in future_payments if payment[0] == sender]),
        len(future_payments)
    )

def make_example_values_for_do_elmo_lvpc_donner(method_name):
    base_fee, method, future_payments = (
        make_example_network_elmo_lvpc_donner_and_future_payments(method_name, base_fee = 1000000)
    )
    value = 100000000.
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(0, 7, value, knowledge_sender)
    return base_fee, method, future_payments, value

def test_dict_before_and_after_equal(dict_before, dict_after):
    """
    tests if keys are equal and if values are almost equal
    """
    assert dict_before.keys() == dict_after.keys()
    for edge in dict_before:
        assert_eq(dict_before[edge], dict_after[edge])

def test_get_payment_options_elmo_lvpc_donner_channel_exists(method_name):
    base_fee, method, future_payments = make_example_network_elmo_lvpc_donner_and_future_payments(method_name)
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 2, 1000000000., knowledge_sender)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == method_name + '-pay'

def test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible(method_name):
    # virtual channel not possible because value and future payments are too high, would need too much balance
    base_fee, method, future_payments = make_example_network_elmo_lvpc_donner_and_future_payments(method_name)
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 7, 10000000000., knowledge_sender)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == method_name + '-open-channel'

def test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible(method_name):
    # shortest path should have length 3 and all channels are onchain, so it should give the same results for
    # Elmo, LVPC and Donner
    base_fee, method, future_payments = make_example_network_elmo_lvpc_donner_and_future_payments(method_name)
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 4, 100000000., knowledge_sender)
    assert len(payment_options) == 3
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == method_name + '-open-channel'
    assert payment_options[2]['payment_information']['kind'] == method_name + '-open-virtual-channel'

def test_do_onchain_elmo_lvpc_donner(method_name):
    base_fee, method, future_payments, value = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 7, value, knowledge_sender)
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    payment_information_onchain = payment_options[0]['payment_information']
    method.do(payment_information_onchain)
    # sender should have MAX_COINS - value - fee many coins, receiver MAX_COINS + value
    assert method.plain_bitcoin.coins[0] == MAX_COINS- value - method.plain_bitcoin.get_fee() 
    assert method.plain_bitcoin.coins[7] == MAX_COINS + value

def test_do_new_channel_elmo_lvpc_donner(method_name):
    base_fee, method, future_payments, value = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 8, value, knowledge_sender)
    assert payment_options[1]['payment_information']['kind'] == method_name + '-open-channel'
    payment_information_new_channel = payment_options[1]['payment_information']

    method.do(payment_information_new_channel)
    # check first the coins of the parties
    sum_future_payments = sum_future_payments_to_counterparty(0, 8, future_payments)
    sender_coins = sum_future_payments + MULTIPLIER_CHANNEL_BALANCE * value
    receiver_coins = value
    tx_size = method.opening_transaction_size
    assert method.plain_bitcoin.coins[0] == MAX_COINS - method.plain_bitcoin.get_fee(tx_size) - sender_coins - receiver_coins 
    assert method.plain_bitcoin.coins[8] == MAX_COINS
    assert method.network.graph[0][8]['balance'] == sender_coins
    assert method.network.graph[8][0]['balance'] == receiver_coins

def test_do_new_virtual_channel_elmo_lvpc_donner(method_name):
    # the new_virtual_channel_option is the same for elmo, lvpc and donner
    # since it is a channel on two existing onchain channels.
    base_fee, method, future_payments, value = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 4, value, knowledge_sender)
    assert payment_options[2]['payment_information']['kind'] == (
        method_name + '-open-virtual-channel'
    )
    payment_information_new_virtual_channel = payment_options[2]['payment_information']

    sum_future_payments = sum_future_payments_to_counterparty(sender, 4, future_payments)
    wanted_sender_coins = sum_future_payments + MULTIPLIER_CHANNEL_BALANCE * value
    assert wanted_sender_coins == MULTIPLIER_CHANNEL_BALANCE * value
    path = [0,1,4]
    available_balances = np.array([
        method.network.graph[path[i]][path[i+1]]['balance'] /
        AVAILABILITY_FACTOR for i in range(len(path)-1)
    ])
    sender_coins = method.determine_sender_coins(
        value, path, wanted_sender_coins, available_balances
    )
    locked_coins = sender_coins + value
    new_virtual_channel_fee = method.get_new_virtual_channel_fee(path, locked_coins)

    method.do(payment_information_new_virtual_channel)

    assert method.network.graph[1][4]['locked_coins'] == locked_coins
    assert method.network.graph[0][1]['balance'] == balances_before[(0, 1)] - new_virtual_channel_fee - locked_coins
    assert method.network.graph[1][0]['locked_coins'] == 0
    assert method.network.graph[1][0]['balance'] == balances_before[(1, 0)] + new_virtual_channel_fee
    assert method.network.graph[1][4]['balance'] == balances_before[(1, 4)] - locked_coins
    assert method.network.graph[4][1]['balance'] == balances_before[(4, 1)]
    assert method.network.graph[4][1]['locked_coins'] == 0
    assert method.network.graph[1][2]['locked_coins'] == 0
    assert method.network.graph[1][2]['balance'] == balances_before[(1, 2)]
    assert method.network.graph[0][4]['balance'] == sender_coins
    assert method.network.graph[4][0]['balance'] == value
    assert method.network.graph.get_edge_data(5, 0) is None

def test_do_new_virtual_channel_not_enough_balance_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    value = 1000
    sender_coins = 99999999999999999999999
    path = [0,1,4]
    payment_information_new_virtual_channel = {
        'kind': method_name + '-new-virtual-channel',
        'data': (path, value, sender_coins)
    }
    try:
        method.do(payment_information_new_virtual_channel)
        assert False, 'should raise exception as amount is too high'
    except ValueError:
        pass

def test_do_elmo_lvpc_donner_pay(method_name):
    base_fee, method, future_payments, value = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 2, value, knowledge_sender)
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
    test_do_onchain_elmo_lvpc_donner(method_name)
    test_do_new_channel_elmo_lvpc_donner(method_name)
    test_do_new_virtual_channel_elmo_lvpc_donner(method_name)
    test_do_elmo_lvpc_donner_pay(method_name)
    test_do_new_virtual_channel_not_enough_balance_elmo_lvpc_donner(method_name)


def test_update_balances_new_virtual_channel_true_elmo_lvpc_donner(method_name):
    # This is before locking.
    method = make_example_network_elmo_lvpc_donner(method_name)
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    path = [0, 1, 4, 7]
    value = 2000000000
    base_fee = method.base_fee
    sender_coins = 100000000
    method.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = True)
    assert_eq(
        method.network.graph[0][1]['balance'],
        balances_before[(0, 1)] - 2*(base_fee + (value + sender_coins) * method.fee_rate)
    )
    assert_eq(
        method.network.graph[1][0]['balance'],
        balances_before[(1, 0)] + 2*(base_fee + (value + sender_coins) * method.fee_rate)
    )
    assert_eq(
        method.network.graph[1][4]['balance'],
        balances_before[(1, 4)] - (base_fee + (value + sender_coins) * method.fee_rate)
    )
    assert_eq(
        method.network.graph[4][1]['balance'],
        balances_before[(4, 1)] + (base_fee + (value + sender_coins) * method.fee_rate)
    )
    assert_eq(method.network.graph[4][7]['balance'], balances_before[(4, 7)])
    assert_eq(method.network.graph[7][4]['balance'], balances_before[(7, 4)])
    assert_eq(method.network.graph[1][2]['balance'], balances_before[(1, 2)])

def test_update_balances_new_virtual_channel_reverse_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    path = [0, 1, 4, 7]
    value = 2000000000
    sender_coins = 100000000
    method.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = True)
    # balances are updated, now we want to revert it
    method.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = False)
    balances_after = nx.get_edge_attributes(method.network.graph, "balance")
    test_dict_before_and_after_equal(balances_before, balances_after)

def test_update_balances_new_virtual_channel_not_enough_money_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    method.base_fee = 9999999999999999
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
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    path = [0, 1, 4, 7]
    value = 2000000000
    sender_coins = 100000000
    lock_value = value + sender_coins
    method.network.lock_unlock(path, lock_value, lock=True)
    assert_eq(method.network.graph[0][1]['balance'], balances_before[(0, 1)] - lock_value)
    assert_eq(method.network.graph[1][0]['balance'], balances_before[(1, 0)])
    assert_eq(method.network.graph[1][4]['balance'], balances_before[(1, 4)] - lock_value)
    assert_eq(method.network.graph[4][1]['balance'], balances_before[(4, 1)])
    assert_eq(method.network.graph[4][7]['balance'], balances_before[(4, 7)] - lock_value)
    assert_eq(method.network.graph[7][4]['balance'], balances_before[(7, 4)])
    assert_eq(method.network.graph[1][2]['balance'], balances_before[(1, 2)])
    assert_eq(method.network.graph[0][1]['locked_coins'], lock_value)
    assert_eq(method.network.graph[1][0]['locked_coins'], 0)
    assert_eq(method.network.graph[1][4]['locked_coins'], lock_value)
    assert_eq(method.network.graph[4][1]['locked_coins'], 0)
    assert_eq(method.network.graph[4][7]['locked_coins'], lock_value)
    assert_eq(method.network.graph[7][4]['locked_coins'], 0)
    assert_eq(method.network.graph[1][2]['locked_coins'], 0)

    method.network.lock_unlock(path, lock_value, lock = False)
    assert_eq(method.network.graph[0][1]['balance'], balances_before[(0, 1)])
    assert_eq(method.network.graph[1][0]['balance'], balances_before[(1, 0)])
    assert_eq(method.network.graph[1][4]['balance'], balances_before[(1, 4)])
    assert_eq(method.network.graph[4][1]['balance'], balances_before[(4, 1)])
    assert_eq(method.network.graph[4][7]['balance'], balances_before[(4, 7)])
    assert_eq(method.network.graph[7][4]['balance'], balances_before[(7, 4)])
    assert_eq(method.network.graph[1][2]['balance'], balances_before[(1, 2)])
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
        method.network.lock_unlock(path, lock_value, lock=True)
        assert False, "should raise ValueError"
    except ValueError:
        balances_after_failure = nx.get_edge_attributes(method.network.graph, "balance")
        locked_coins_after_failure = nx.get_edge_attributes(method.network.graph, "locked_coins")
        test_dict_before_and_after_equal(balances_before, balances_after_failure)
        test_dict_before_and_after_equal(locked_coins_before, locked_coins_after_failure)

def test_lock_and_unlock_elmo_lvpc_donner(method_name):
    test_locking_and_unlocking_enough_balance_elmo_lvpc_donner(method_name)
    test_locking_not_enough_balance_elmo_lvpc_donner(method_name)

def test_pay_enough_balance_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    sender = 0
    receiver = 2
    value = 20000000
    method.pay(sender, receiver, value)
    assert_eq(method.network.graph[sender][receiver]['balance'], balances_before[(sender, receiver)] - value)
    assert_eq(method.network.graph[receiver][sender]['balance'], balances_before[(receiver, sender)] + value)
    assert_eq(method.network.graph[0][1]['balance'], balances_before[(0, 1)])
    assert_eq(method.network.graph[sender][receiver]['locked_coins'], 0)

def test_pay_not_enough_balance_elmo_lvpc_donner(method_name):
    method = make_example_network_elmo_lvpc_donner(method_name)
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    sender = 0
    receiver = 2
    value = 20000000000000
    try:
        method.pay(sender, receiver, value)
        assert False, "should raise ValueError"
    except ValueError:
        assert_eq(method.network.graph[sender][receiver]['balance'], balances_before[(sender, receiver)])
        assert_eq(method.network.graph[receiver][sender]['balance'], balances_before[(receiver, sender)])
        assert_eq(method.network.graph[0][1]['balance'], balances_before[(0, 1)])
        assert_eq(method.network.graph[sender][receiver]['locked_coins'], 0)

def test_pay_elmo_lvpc_donner(method_name):
    test_pay_enough_balance_elmo_lvpc_donner(method_name)
    test_pay_not_enough_balance_elmo_lvpc_donner(method_name)

def test_undo_new_virtual_channel_elmo_lvpc_donner(method_name):
    base_fee, method, future_payments, value = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    # virtual channel has length 2 and both underlying channel are onchain -> equal for all 3 methods
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 4, value, knowledge_sender)
    sender_coins = method.plain_bitcoin.coins[0]
    receiver_coins = method.plain_bitcoin.coins[4]
    assert payment_options[2]['payment_information']['kind'] == method_name + '-open-virtual-channel'
    path = payment_options[2]['payment_information']['data'][0]
    assert path == [0, 1, 4]
    payment_information_new_virtual_channel = payment_options[2]['payment_information']
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(method.network.graph, "locked_coins")

    method.do(payment_information_new_virtual_channel)
    method.undo(payment_information_new_virtual_channel)
    balances_after = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_after = nx.get_edge_attributes(method.network.graph, "locked_coins")
    test_dict_before_and_after_equal(balances_before, balances_after)
    test_dict_before_and_after_equal(locked_coins_before, locked_coins_after)
    assert sender_coins == method.plain_bitcoin.coins[0]
    assert receiver_coins == method.plain_bitcoin.coins[4]

def test_undo_new_virtual_channel_long_path_elmo_lvpc_donner(method_name):
    base_fee, method, future_payments, value = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 7, value, knowledge_sender)
    assert payment_options[2]['payment_information']['kind'] == method_name + '-open-virtual-channel'
    path = payment_options[2]['payment_information']['data'][0]
    assert path == [0, 1, 4, 7]
    payment_information_new_virtual_channel = payment_options[2]['payment_information']
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(method.network.graph, "locked_coins")

    method.do(payment_information_new_virtual_channel)
    method.undo(payment_information_new_virtual_channel)
    balances_after = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_after = nx.get_edge_attributes(method.network.graph, "locked_coins")
    test_dict_before_and_after_equal(balances_before, balances_after)
    test_dict_before_and_after_equal(locked_coins_before, locked_coins_after)

def test_undo_elmo_lvpc_donner_pay(method_name):
    base_fee, method, future_payments, value = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 2, value, knowledge_sender)
    assert payment_options[1]['payment_information']['kind'] == method_name + '-pay'
    payment_information_pay = payment_options[1]['payment_information']
    balances_before = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(method.network.graph, "locked_coins")
    method.do(payment_information_pay)
    method.undo(payment_information_pay)
    balances_after = nx.get_edge_attributes(method.network.graph, "balance")
    locked_coins_after = nx.get_edge_attributes(method.network.graph, "locked_coins")
    test_dict_before_and_after_equal(balances_before, balances_after)
    test_dict_before_and_after_equal(locked_coins_before, locked_coins_after)

def test_undo_elmo_lvpc_donner(method_name):
    test_undo_new_virtual_channel_elmo_lvpc_donner(method_name)
    test_undo_new_virtual_channel_long_path_elmo_lvpc_donner(method_name)
    test_undo_elmo_lvpc_donner_pay(method_name)

def test_coop_close_channel_first_virtual_layer_no_layer_above_elmo_lvpc_donner(method_name):
    # virtual channel is possible for elmo, lvpc and donner
    base_fee, method, future_payments, value = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 4, value, knowledge_sender)
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
    base_fee, method, future_payments, value = (
        make_example_values_for_do_elmo_lvpc_donner(method_name)
    )
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = method.get_payment_options(sender, 4, value, knowledge_sender)
    assert payment_options[2]['payment_information']['kind'] == method_name + '-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']

    method.do(payment_information_new_virtual_channel)
    assert method.network.graph[0][4]['channels_below'] == [0,1,4]
    assert method.network.graph[4][0]['channels_below'] == [4,1,0]
    method.network.force_close_channel(0, 1)
    assert method.network.graph[0][4]['channels_below'] is None
    assert method.network.graph[4][0]['channels_below'] is None
    assert method.network.graph.get_edge_data(1, 4) is None

# The following two tests should give the same result for elmo, lvpc and donner as in the beginning
# of the simulation the differences in the virtual channel don't show up yet.
def test_simulation_with_elmo_lvpc_donner_ignore_centrality(method_name):
    match method_name:
        case "Elmo":
            method = Elmo(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                base_fee = 1000000, opening_transaction_size = 200
            )
        case "LVPC":
            method = LVPC(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                base_fee = 1000000, opening_transaction_size = 200
            )
        case "Donner":
            method = Donner(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                base_fee = 1000000, opening_transaction_size = 200
            )
        case _:
            raise ValueError
    knowledge = Knowledge('all')
    payments = collections.deque([(0, 1, 100000000000), (0, 1, 10000000000)])
    utility_function = make_example_utility_function(10000, 5000, 10000, 0)
    utility = Utility('customized', utility_function=utility_function)
    simulation = Simulation(payments, method, knowledge, utility)
    results = simulation.run()
    done_payment0, payment0_info, fee0, delay0 = results[0]
    assert done_payment0 == True
    assert payment0_info['kind'] == method_name + '-open-channel'
    done_payment1, payment1_info, fee1, delay1 = results[1]
    assert done_payment1 == True
    assert payment1_info['kind'] == method_name + '-pay'
    assert len(results) == 2

def test_simulation_with_elmo_lvpc_donner_ignore_centrality_and_distance(method_name):
    match method_name:
        case "Elmo":
            method = Elmo(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                base_fee = 1000000, opening_transaction_size = 200
            )
        case "LVPC":
            method = LVPC(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                base_fee = 1000000, opening_transaction_size = 200
            )
        case "Donner":
            method = Donner(
                nr_players = 3, bitcoin_fee = 1000000, bitcoin_delay = 3600, coins_for_parties='max_value',
                base_fee = 1000000, opening_transaction_size = 200
            )
    knowledge = Knowledge('all')
    payments = collections.deque([(0, 1, 100000000000), (0, 1, 10000000000)])
    utility_function = make_example_utility_function(10000, 5000, 0, 0)
    utility = Utility('customized', utility_function=utility_function)
    simulation = Simulation(payments, method, knowledge, utility)
    results = simulation.run()
    done_payment0, payment0_info, _, _ = results[0]
    assert done_payment0 == True
    assert payment0_info['kind'] == 'onchain'
    done_payment1, payment1_info, _, _ = results[1]
    assert done_payment1 == True
    assert payment1_info['kind'] == 'onchain'
    assert len(results) == 2

def test_simulation_with_previous_channels_elmo_lvpc_donner_ignore_centrality(method_name):
    # the open-virtual-channel option is the same for elmo, lvpc, donner
    match method_name:
        case "Elmo":
            method = Elmo(4, base_fee = 1000000)
        case "LVPC":
            method = LVPC(4, base_fee = 1000000)
        case "Donner":
            method = Donner(4, base_fee = 1000000)
        case _:
            raise ValueError
    
    method.network.add_channel(0, 3000000000000., 1, 7000000000000., None)
    method.network.add_channel(1, 6000000000000., 2, 7000000000000., None)
    method.network.add_channel(2, 4000000000000., 3, 8000000000000., None)
    method.network.add_channel(1, 1000000000000., 3, 800000000000., [1,2,3])
    knowledge = Knowledge('all')
    value0 = 1000000000
    value1 = 20000000000
    payments = collections.deque([(0, 2, value0), (0, 1, value1)])
    utility_function = make_example_utility_function(10000, 5000, 1, 0)
    utility = Utility('customized', utility_function=utility_function)
    simulation = Simulation(payments, method, knowledge, utility)
    results = simulation.run()
    done_payment0, payment0_info, _, _ = results[0]
    done_payment1, payment1_info, _, _ = results[1]
    assert done_payment0 == True
    assert payment0_info['kind'] == method_name + '-open-virtual-channel'
    assert done_payment1 == True
    assert payment1_info['kind'] == method_name + '-pay'
    assert len(results) == 2
    assert set(method.network.graph.edges()) == set(
        [(0, 1), (1, 0), (0, 2), (2, 0), (1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2)]
    )
    sum_future_payments0 = 0
    wanted_sender_coins0 = sum_future_payments0 + MULTIPLIER_CHANNEL_BALANCE * value0
    assert wanted_sender_coins0 == MULTIPLIER_CHANNEL_BALANCE * value0
    path0 = [0,1,2]
    available_balances = np.array([
        method.network.graph[path0[i]][path0[i+1]]['balance'] /
        AVAILABILITY_FACTOR for i in range(len(path0)-1)
    ])
    sender_coins = method.determine_sender_coins(
        value0, path0, wanted_sender_coins0, available_balances
    )
    locked_coins0 = sender_coins + value0
    assert method.network.graph[0][1]['locked_coins'] == locked_coins0
    assert method.network.graph[1][2]['locked_coins'] == locked_coins0
    assert method.network.graph[1][0]['locked_coins'] == 0

def test_simulation_with_previous_channels_elmo_donner_lvpc_long_path_ignore_centrality(method_name):
    # the open-virtual-channel option is the same for elmo, lvpc, donner
    match method_name:
        case "Elmo":
            method = Elmo(4, base_fee = 1000000)
        case "LVPC":
            method = LVPC(4, base_fee = 1000000)
        case "Donner":
            method = Donner(4, base_fee = 1000000)
        case _:
            raise ValueError
    
    method.network.add_channel(0, 3000000000000., 1, 7000000000000., None)
    method.network.add_channel(1, 6000000000000., 2, 7000000000000., None)
    method.network.add_channel(2, 4000000000000., 3, 8000000000000., None)

    knowledge = Knowledge('all')
    value = 10000000000
    payments = collections.deque([(0, 3, value), (0, 3, value / 10)])
    utility_function = make_example_utility_function(10000, 5000, 1, 0)
    utility = Utility('customized', utility_function=utility_function)
    simulation = Simulation(payments, method, knowledge, utility)
    results = simulation.run()
    assert len(results) == 2
    done_payment0, payment_info0, _, _ = results[0]
    done_payment1, payment_info1, _, _ = results[1]
    assert done_payment0 == True
    assert done_payment1 == True
    assert payment_info0['kind'] == method_name + '-open-virtual-channel'
    assert payment_info1['kind'] == method_name + '-pay'
    if method_name != "LVPC":
        assert set(method.network.graph.edges()) == set(
            [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (0, 3), (3, 0)]
        )
    else:
        assert set(method.network.graph.edges()) == set(
            [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (0, 3), (3, 0), (0, 2), (2, 0)]
        )
    assert method.network.graph[1][0]['locked_coins'] == 0

def test_simulation_with_previous_channels_elmo_donner_lvpc_recursive_ignore_centrality(method_name):
    """
    test that elmo and lvpc use recursive procedure when possible
    and donner variadic.
    """
    # the open-virtual-channel option is the same for elmo, lvpc, donner
    match method_name:
        case "Elmo":
            method = Elmo(4, base_fee = 1000000)
        case "LVPC":
            method = LVPC(4, base_fee = 1000000)
        case "Donner":
            method = Donner(4, base_fee = 1000000)
        case _:
            raise ValueError
    
    method.network.add_channel(0, 3000000000000., 1, 7000000000000., None)
    method.network.add_channel(1, 6000000000000., 2, 7000000000000., None)
    method.network.add_channel(2, 4000000000000., 3, 8000000000000., None)

    knowledge = Knowledge('all')
    value = 10000000000
    payments = collections.deque([(0, 2, value), (0, 3, value / 10), (0, 2, value / 5)])
    utility_function = make_example_utility_function(10000, 5000, 1, 0)
    utility = Utility('customized', utility_function=utility_function)
    simulation = Simulation(payments, method, knowledge, utility)
    results = simulation.run()
    done_payment0, payment_info0, _, _ = results[0]
    done_payment1, payment_info1, _, _ = results[1]
    assert done_payment0 == True
    assert done_payment1 == True
    assert payment_info0['kind'] == method_name + '-open-virtual-channel'
    assert payment_info1['kind'] == method_name + '-open-virtual-channel'
    assert set(method.network.graph.edges()) == set(
            [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (0, 2), (2, 0), (0, 3), (3, 0)]
    )
    path0, _, _ = payment_info0['data']
    path1, _, _ = payment_info1['data']
    assert len(path0) == 3
    if method_name != "Donner":
        assert len(path1) == 3
    else:
        assert len(path1) == 4

if __name__ == "__main__":
    test_cheapest_path()
    print("Success")
