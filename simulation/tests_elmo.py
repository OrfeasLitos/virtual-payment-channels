
import random
import sys
import numpy as np
import math
import copy
from numpy.testing import assert_almost_equal as assert_eq
import networkx as nx
import unittest

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin, LN, Elmo, sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE_ELMO
from utility import Utility
from knowledge import Knowledge
from network import Network
from tests import know_all, make_example_utility_function , example_utility_function_for_simulation

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

def make_example_simulation_elmo(seed = 0, coins_for_parties = 'max_value'):
    random.seed(seed)
    elmo = Elmo(10, coins_for_parties=coins_for_parties)
    knowledge = Knowledge(know_all)
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
def make_example_values_for_do():
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
    payment_options = elmo.get_payment_options(0, 7, 1000000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-open-channel'

def test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible():
    fee_intermediary, elmo, future_payments = make_example_network_elmo_and_future_payments()
    payment_options = elmo.get_payment_options(0, 4, 100000000., future_payments)
    assert len(payment_options) == 3
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-open-channel'
    assert payment_options[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'

def test_get_payment_options_elmo():
    test_get_payment_options_elmo_channel_exists()
    test_get_payment_options_elmo_no_channel_exists_no_virtual_channel_possible()
    test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible()

# adjusted from tests_ln
def test_do_onchain():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do()
    )
    payment_options = elmo.get_payment_options(0, 7, value, future_payments)
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    payment_information_onchain = payment_options[0]['payment_information']
    elmo.do(payment_information_onchain)
    # sender should have MAX_COINS - 1 - fee many coins, receiver MAX_COINS + 1
    assert elmo.plain_bitcoin.coins[0] == MAX_COINS - value - elmo.plain_bitcoin.get_fee() 
    assert elmo.plain_bitcoin.coins[7] == MAX_COINS + value

def test_do_new_channel():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do()
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

def test_do_new_virtual_channel():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do()
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
        make_example_values_for_do()
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

def test_do():
    # TODO: test exceptions
    test_do_onchain()
    test_do_new_channel()
    test_do_new_virtual_channel()
    test_do_elmo_pay()

def test_update_balances_new_virtual_channel_true():
    # Here locking isn't done yet.
    elmo = make_example_network_elmo()
    path = [0, 1, 4, 7]
    value = 2000000000
    fee_intermediary = elmo.fee_intermediary
    sender_coins = 100000000
    elmo.update_balances_new_virtual_channel(path, value, sender_coins, new_channel = True)
    assert_eq(elmo.network.graph[0][1]['balance'],6000000000 - 2*fee_intermediary)
    assert_eq(elmo.network.graph[1][0]['balance'], 7000000000 + 2*fee_intermediary)
    assert_eq(elmo.network.graph[1][4]['balance'], 4000000000 - fee_intermediary)
    assert_eq(elmo.network.graph[4][1]['balance'], 8000000000 + fee_intermediary)
    assert_eq(elmo.network.graph[4][7]['balance'], 10000000000)
    assert_eq(elmo.network.graph[7][4]['balance'], 8000000000)
    assert_eq(elmo.network.graph[1][2]['balance'], 10000000000)

def test_update_balances_new_virtual_channel_reverse():
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

def test_update_balances_new_virtual_channel_not_enough_money():
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

def test_update_balances_new_virtual_channel():
    test_update_balances_new_virtual_channel_true()
    test_update_balances_new_virtual_channel_reverse()
    test_update_balances_new_virtual_channel_not_enough_money()

def test_locking_and_unlocking_enough_balance():
    elmo = make_example_network_elmo()
    path = [0, 1, 4, 7]
    value = 2000000000
    sender_coins = 100000000
    lock_value = value + sender_coins
    elmo.lock_coins(path, lock_value)
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

    elmo.undo_locking(path, lock_value)
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

def test_locking_not_enough_balance():
    elmo = make_example_network_elmo()
    path = [0, 1, 4, 7]
    value = 2000000000000
    sender_coins = 100000000
    lock_value = value + sender_coins
    balances_before = nx.get_edge_attributes(elmo.network.graph, "balance")
    locked_coins_before = nx.get_edge_attributes(elmo.network.graph, "locked_coins")
    try:
        elmo.lock_coins(path, lock_value)
        assert False, "should raise ValueError"
    except ValueError:
        balances_after_failure = nx.get_edge_attributes(elmo.network.graph, "balance")
        locked_coins_after_failure = nx.get_edge_attributes(elmo.network.graph, "locked_coins")
        for key in balances_before.keys():
            assert_eq(balances_before[key], balances_after_failure[key])
        for key in locked_coins_before.keys():
            assert_eq(locked_coins_before[key], locked_coins_after_failure[key])

def test_lock_and_unlock():
    test_locking_and_unlocking_enough_balance()
    test_locking_not_enough_balance()

def test_undo_new_virtual_channel():
    fee_intermediary, elmo, future_payments, value, MAX_COINS = (
        make_example_values_for_do()
    )
    payment_options = elmo.get_payment_options(0, 4, value, future_payments)
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

def test_undo_elmo_pay():
    pass

def test_undo():
    test_undo_new_virtual_channel()
    test_undo_elmo_pay()

def test_simulation_with_elmo():
    # TODO: test with differnt coins for parties and make real tests.
    simulation = make_example_simulation_elmo()
    results = simulation.run()
    print(results)

if __name__ == "__main__":
    test_get_payment_options_elmo()
    test_do()
    test_update_balances_new_virtual_channel()
    test_lock_and_unlock()
    test_undo()
    test_simulation_with_elmo()
    print("Success")