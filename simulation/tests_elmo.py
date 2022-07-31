
import networkx as nx
import collections
from numpy.testing import assert_almost_equal as assert_eq
from elmo import Elmo
from knowledge import Knowledge
from utility import Utility
from simulation import Simulation
from paymentmethod import sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE_ELMO
from tests import (make_example_network_elmo_lvpc_donner,
    make_example_network_elmo_lvpc_donner_and_future_payments,
    make_example_simulation_for_all, make_example_utility_function,
    test_get_payment_options_elmo_lvpc_donner_channel_exists,
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible,
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible1,
    test_do_elmo_lvpc_donner
)

def make_example_network_elmo(fee_intermediary = 1000000):
    elmo = make_example_network_elmo_lvpc_donner("Elmo", fee_intermediary)
    return elmo

def make_example_network_elmo_and_future_payments(fee_intermediary = 1000000):
    return make_example_network_elmo_lvpc_donner_and_future_payments("Elmo", fee_intermediary)

def make_example_simulation_elmo(seed = 12345, coins_for_parties = 'max_value'):
    return make_example_simulation_for_all("Elmo", seed, coins_for_parties)

def test_get_payment_options_elmo_channel_exists():
    test_get_payment_options_elmo_lvpc_donner_channel_exists("Elmo")

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
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible("Elmo")

def test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible1():
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible1("Elmo")

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

def test_do_elmo():
    test_do_elmo_lvpc_donner("Elmo")

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

if __name__ == "__main__":
    test_get_payment_options_elmo()
    test_do_elmo()
    test_update_balances_new_virtual_channel_elmo()
    test_lock_and_unlock_elmo()
    test_pay_elmo()
    test_undo_elmo()
    test_simulation_with_elmo()
    test_close_channel_elmo()
    test_force_close_elmo()
    print("Success")
