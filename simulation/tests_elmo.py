
import networkx as nx
from numpy.testing import assert_almost_equal as assert_eq
from elmo import Elmo
from tests import (make_example_network_elmo_lvpc_donner,
    make_example_network_elmo_lvpc_donner_and_future_payments,
    make_example_simulation_for_all, make_example_utility_function,
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
    test_simulation_with_previous_channels_elmo_donner_lvpc_recursive_ignore_centrality
)

def make_example_network_elmo(base_fee = 1000000):
    elmo = make_example_network_elmo_lvpc_donner("Elmo", base_fee)
    return elmo

def make_example_network_elmo_and_future_payments(base_fee = 1000000):
    return make_example_network_elmo_lvpc_donner_and_future_payments("Elmo", base_fee)

def make_example_simulation_elmo(seed = 12345, nr_players = 10, coins_for_parties = 'max_value'):
    return make_example_simulation_for_all("Elmo", seed, nr_players, coins_for_parties)

def test_get_payment_options_elmo_channel_exists():
    test_get_payment_options_elmo_lvpc_donner_channel_exists("Elmo")

def test_get_payment_options_elmo_no_channel_exists_no_virtual_channel_possible():
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible("Elmo")

def test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible1():
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible1("Elmo")

def test_get_payment_options_elmo_no_channel_exists_virtual_channel_possible2():
    base_fee, elmo, future_payments = make_example_network_elmo_and_future_payments()
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

def test_update_balances_new_virtual_channel_elmo():
    test_update_balances_new_virtual_channel_elmo_lvpc_donner("Elmo")

def test_lock_and_unlock_elmo():
    test_lock_and_unlock_elmo_lvpc_donner("Elmo")

def test_pay_elmo():
    test_pay_elmo_lvpc_donner("Elmo")

def test_undo_elmo():
    test_undo_elmo_lvpc_donner("Elmo")

def test_coop_close_channel_first_virtual_layer_no_layer_above_elmo():
    test_coop_close_channel_first_virtual_layer_no_layer_above_elmo_lvpc_donner("Elmo")

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
    test_force_close_channel_onchain_layer_one_layer_above_elmo_lvpc_donner("Elmo")

def test_close_channel_elmo():
    test_coop_close_channel_first_virtual_layer_no_layer_above_elmo()
    test_coop_close_channel_first_virtual_layer_one_layer_above_elmo(forward = True)
    test_coop_close_channel_first_virtual_layer_one_layer_above_elmo(forward = False)
    test_force_close_channel_onchain_layer_one_layer_above_elmo()

def test_force_close1_elmo():
    elmo = Elmo(6, base_fee = 1000000)

    elmo.network.add_channel(0, 3000000000., 1, 7000000000., None)
    elmo.network.add_channel(1, 6000000000., 2, 7000000000., None)
    elmo.network.add_channel(2, 4000000000., 3, 8000000000., None)
    elmo.network.add_channel(4, 9000000000., 5, 8000000000., None)
    elmo.network.add_channel(1, 9000000000., 4, 2000000000., None)
    elmo.network.add_channel(0, 1000000000., 2, 800000000., [0,1,2])
    elmo.network.lock_unlock([0,1,2], 1000000000. + 800000000., lock=True)
    elmo.network.add_channel(3, 1000000000., 4, 800000000., [3,2,1,4])
    elmo.network.lock_unlock([3,2,1,4], 1000000000. + 800000000., lock=True)
    elmo.network.add_channel(2, 100000000., 4, 80000000., [2,3,4])
    elmo.network.lock_unlock([2,3,4], 100000000. + 80000000., lock=True)
    elmo.network.add_channel(0, 90000000., 5, 20000000., [0,2,4,5])
    elmo.network.lock_unlock([0,2,4,5], 9000000. + 2000000., lock=True)
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
    elmo = Elmo(4, base_fee = 1000000)

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
    test_simulation_with_elmo_lvpc_donner_ignore_centrality("Elmo")

def test_simulation_with_elmo_ignore_centrality_and_distance():
    test_simulation_with_elmo_lvpc_donner_ignore_centrality_and_distance("Elmo")

def test_simulation_with_previous_channels_elmo_ignore_centrality():
    test_simulation_with_previous_channels_elmo_lvpc_donner_ignore_centrality("Elmo")

def test_simulation_with_previous_channels_elmo_long_path_ignore_centrality():
    test_simulation_with_previous_channels_elmo_donner_lvpc_long_path_ignore_centrality("Elmo")

def test_simulation_with_previous_channels_elmo_recursive_ignore_centrality():
    test_simulation_with_previous_channels_elmo_donner_lvpc_recursive_ignore_centrality("Elmo")

def test_simulation_with_elmo():
    simulation = make_example_simulation_elmo(nr_players=20)
    results = simulation.run()
    print(results)
    test_simulation_with_elmo_ignore_centrality()
    test_simulation_with_elmo_ignore_centrality_and_distance()
    test_simulation_with_previous_channels_elmo_ignore_centrality()
    test_simulation_with_previous_channels_elmo_long_path_ignore_centrality()
    test_simulation_with_previous_channels_elmo_recursive_ignore_centrality()

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
