
import random
import sys
import numpy as np
import math
from numpy.testing import assert_almost_equal as assert_eq
import networkx as nx
import unittest

from simulation import Simulation, random_payments
from paymentmethod import PlainBitcoin, LN, Elmo, sum_future_payments_to_counterparty
from utility import Utility
from knowledge import Knowledge
from network import Network
from tests import know_all, make_example_utility_function , example_utility_function_for_simulation
from paymentmethod import MULTIPLIER_CHANNEL_BALANCE_ELMO

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
    value = 1000000000.
    payment_options = elmo.get_payment_options(0, 7, value, future_payments)
    MAX_COINS = elmo.plain_bitcoin.max_coins
    return fee_intermediary, elmo, future_payments, value, MAX_COINS

def test_get_payment_options_elmo_no_channel_exists_no_virtual_channel_possible():
    # virtual channel not possible because too much future payments, would need top much balance
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
    payment_options = elmo.get_payment_options(0, 7, value, future_payments)

def test_do():
    test_do_onchain()
    test_do_new_channel()
    test_do_new_virtual_channel()

def test_simulation_with_elmo():
    # TODO: test with differnt coins for parties and make real tests.
    simulation = make_example_simulation_elmo()
    results = simulation.run()
    print(results)

if __name__ == "__main__":
    test_get_payment_options_elmo()
    test_simulation_with_elmo()
    test_do()
    print("Success")