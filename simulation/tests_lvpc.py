
from lvpc import LVPC
import networkx as nx
from paymentmethod import sum_future_payments_to_counterparty, MULTIPLIER_CHANNEL_BALANCE
from tests import (
    make_example_network_elmo_lvpc_donner,
    make_example_network_elmo_lvpc_donner_and_future_payments,
    make_example_simulation_for_all,
    test_get_payment_options_elmo_lvpc_donner_channel_exists,
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible,
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible1,
    test_do_elmo_lvpc_donner,
    test_update_balances_new_virtual_channel_elmo_lvpc_donner,
    test_lock_and_unlock_elmo_lvpc_donner,
    test_pay_elmo_lvpc_donner, test_undo_elmo_lvpc_donner,
    test_coop_close_channel_first_virtual_layer_no_layer_above_elmo_lvpc_donner,
    test_force_close_channel_onchain_layer_one_layer_above_elmo_lvpc_donner,
    test_simulation_with_elmo_lvpc_donner_ignore_centrality,
    test_simulation_with_elmo_lvpc_donner_ignore_centrality_and_distance,
    test_simulation_with_previous_channels_elmo_lvpc_donner_ignore_centrality,
    test_simulation_with_previous_channels_elmo_donner_lvpc_long_path_ignore_centrality,
    test_simulation_with_previous_channels_elmo_donner_lvpc_recursive_ignore_centrality,
    make_example_values_for_do_elmo_lvpc_donner
)


def make_example_network_lvpc(base_fee = 1000000):
    lvpc = make_example_network_elmo_lvpc_donner("LVPC", base_fee)
    return lvpc

def make_example_network_lvpc_and_future_payments(base_fee = 1000000):
    return make_example_network_elmo_lvpc_donner_and_future_payments("LVPC", base_fee)

def make_example_simulation_lvpc(seed = 12345, nr_players = 10, coins_for_parties = 'max_value'):
    return make_example_simulation_for_all("LVPC", seed, nr_players, coins_for_parties)

def test_get_payment_options_lvpc_channel_exists():
    test_get_payment_options_elmo_lvpc_donner_channel_exists("LVPC")

def test_get_payment_options_lvpc_no_channel_exists_virtual_channel_possible():
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible1("LVPC")

def test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible2():
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible("LVPC")

def test_get_payment_options_lvpc():
    test_get_payment_options_lvpc_channel_exists()
    test_get_payment_options_lvpc_no_channel_exists_virtual_channel_possible()
    #test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible1()
    test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible2()

def test_do_new_virtual_channel_long_path_lvpc():
    # the new_virtual_channel_option is the same for elmo, lvpc and donner as it is a channel on two existing onchain channels.
    lvpc = make_example_network_lvpc()
    value = 10000000.
    future_payments = [(0,1,2000000000.), (0, 8, 3000000000.)]
    balances_before = nx.get_edge_attributes(lvpc.network.graph, "balance")
    payment_options = lvpc.get_payment_options(0, 7, value, future_payments)
    print(payment_options)
    assert payment_options[2]['payment_information']['kind'] == 'LVPC-open-virtual-channel'
    payment_information_new_virtual_channel = payment_options[2]['payment_information']

    lvpc.do(payment_information_new_virtual_channel)
    # check first the coins of the parties
    sum_future_payments = sum_future_payments_to_counterparty(0, 7, future_payments)
    wanted_sender_coins = MULTIPLIER_CHANNEL_BALANCE * sum_future_payments
    assert wanted_sender_coins == 0
    sender_coins = 0
    new_virtual_channel_fee_first_channel = lvpc.get_new_virtual_channel_fee([0,1,4], value)

    locked_coins = sender_coins + value
    """
    assert lvpc.network.graph[1][4]['locked_coins'] == locked_coins
    assert lvpc.network.graph[0][1]['balance'] == balances_before[(0, 1)] - new_virtual_channel_fee_first_channel - locked_coins
    assert lvpc.network.graph[1][0]['locked_coins'] == 0
    assert lvpc.network.graph[1][0]['balance'] == balances_before[(1, 0)] + new_virtual_channel_fee_first_channel
    assert lvpc.network.graph[1][4]['balance'] == balances_before[(1, 4)] - locked_coins
    assert lvpc.network.graph[4][1]['balance'] == balances_before[(4, 1)]
    assert lvpc.network.graph[4][1]['locked_coins'] == 0
    assert lvpc.network.graph[1][2]['locked_coins'] == 0
    assert lvpc.network.graph[1][2]['balance'] == balances_before[(1, 2)]
    assert lvpc.network.graph[0][4]['balance'] == 0
    assert lvpc.network.graph[4][0]['balance'] == value
    assert lvpc.network.graph.get_edge_data(5, 0) is None
    """

def test_do_lvpc():
    test_do_elmo_lvpc_donner("LVPC")
    test_do_new_virtual_channel_long_path_lvpc()

def test_update_balances_new_virtual_channel_lvpc():
    test_update_balances_new_virtual_channel_elmo_lvpc_donner("LVPC")

def test_lock_and_unlock_lvpc():
    test_lock_and_unlock_elmo_lvpc_donner("LVPC")

def test_pay_lvpc():
    test_pay_elmo_lvpc_donner("LVPC")

def test_undo_lvpc():
    test_undo_elmo_lvpc_donner("LVPC")

def test_coop_close_channel_first_virtual_layer_no_layer_above_lvpc():
    test_coop_close_channel_first_virtual_layer_no_layer_above_elmo_lvpc_donner("LVPC")

def test_force_close_channel_onchain_layer_one_layer_above_lvpc():
    test_force_close_channel_onchain_layer_one_layer_above_elmo_lvpc_donner("LVPC")

# adjusted from Elmo
def test_force_close2_lvpc():
    lvpc = LVPC(4, base_fee = 1000000)

    lvpc.network.add_channel(0, 3000000000., 1, 7000000000., None)
    lvpc.network.add_channel(1, 6000000000., 2, 7000000000., None)
    lvpc.network.add_channel(2, 4000000000., 3, 8000000000., None)
    lvpc.network.add_channel(1, 1000000000., 3, 800000000., [1,2,3])
    lvpc.network.add_channel(0, 100000000., 3, 80000000., [0,1,3])
    lvpc.network.force_close_channel(0, 1)
    assert set(lvpc.network.graph.edges()) == set([(0, 3), (3, 0)])
    assert lvpc.network.graph[0][3]['channels_below'] is None
    assert lvpc.network.graph[0][3]['channels_above'] == []
    assert lvpc.network.graph[3][0]['channels_below'] is None
    assert lvpc.network.graph[3][0]['channels_above'] == []

def test_close_channel_lvpc():
    test_coop_close_channel_first_virtual_layer_no_layer_above_lvpc()
    test_force_close_channel_onchain_layer_one_layer_above_lvpc()
    test_force_close2_lvpc()

def test_simulation_with_lvpc_ignore_centrality():
    test_simulation_with_elmo_lvpc_donner_ignore_centrality("LVPC")

def test_simulation_with_lvpc_ignore_centrality_and_distance():
    test_simulation_with_elmo_lvpc_donner_ignore_centrality_and_distance("LVPC")

def test_simulation_with_previous_channels_lvpc_ignore_centrality():
    test_simulation_with_previous_channels_elmo_lvpc_donner_ignore_centrality("LVPC")

def test_simulation_with_previous_channels_lvpc_long_path_ignore_centrality():
    test_simulation_with_previous_channels_elmo_donner_lvpc_long_path_ignore_centrality("LVPC")

def test_simulation_with_previous_channels_lvpc_recursive_ignore_centrality():
    test_simulation_with_previous_channels_elmo_donner_lvpc_recursive_ignore_centrality("LVPC")

def test_simulation_with_lvpc():
    test_simulation_with_lvpc_ignore_centrality()
    test_simulation_with_lvpc_ignore_centrality_and_distance()
    test_simulation_with_previous_channels_lvpc_ignore_centrality()
    test_simulation_with_previous_channels_lvpc_long_path_ignore_centrality()
    test_simulation_with_previous_channels_lvpc_recursive_ignore_centrality()
    simulation = make_example_simulation_lvpc(nr_players = 20)
    results = simulation.run()
    print(results)

if __name__ == "__main__":
    test_get_payment_options_lvpc()
    test_simulation_with_lvpc()
    test_do_lvpc()
    test_update_balances_new_virtual_channel_lvpc()
    test_lock_and_unlock_lvpc()
    test_undo_lvpc()
    test_pay_lvpc()
    test_close_channel_lvpc()
    print("Success")
