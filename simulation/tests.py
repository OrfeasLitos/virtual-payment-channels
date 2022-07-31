
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
    fee_intermediary, elmo, future_payments = make_example_network_elmo_lvpc_donner_and_future_payments(method_name)
    payment_options = elmo.get_payment_options(0, 4, 100000000., future_payments)
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



if __name__ == "__main__":
    test_cheapest_path()
    print("Success")
