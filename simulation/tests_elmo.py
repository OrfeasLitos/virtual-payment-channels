
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
    print(payment_options)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-pay'

def test_get_payment_options_elmo_no_channel_exists_no_virtual_channel_possible():
    # virtual channel not possible because too much future payments, would need top much balance
    fee_intermediary, elmo, future_payments = make_example_network_elmo_and_future_payments()
    payment_options = elmo.get_payment_options(0, 7, 1000000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-open-channel'

def test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible():
    fee_intermediary, elmo, future_payments = make_example_network_elmo_and_future_payments()
    payment_options = elmo.get_payment_options(0, 4, 1000000000., future_payments)
    assert len(payment_options) == 3
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Elmo-open-channel'
    assert payment_options[2]['payment_information']['kind'] == 'Elmo-open-virtual-channel'

def test_get_payment_options_elmo():
    test_get_payment_options_elmo_channel_exists()
    test_get_payment_options_elmo_no_channel_exists_no_virtual_channel_possible()
    test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible()

def test_simulation_with_elmo():
    # TODO: test with differnt coins for parties and make real tests.
    simulation = make_example_simulation_elmo()
    results = simulation.run()
    print(results)

if __name__ == "__main__":
    test_get_payment_options_elmo()
    test_simulation_with_elmo()
    print("Success")