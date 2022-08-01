
from lvpc import LVPC
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
    test_simulation_with_elmo_lvpc_donner_ignore_centrality_and_distance
)


def make_example_network_lvpc(lvpc_fee_intermediary = 1000000):
    lvpc = make_example_network_elmo_lvpc_donner("LVPC", lvpc_fee_intermediary)
    return lvpc

def make_example_network_lvpc_and_future_payments(fee_intermediary = 1000000):
    return make_example_network_elmo_lvpc_donner_and_future_payments("LVPC", fee_intermediary)

def make_example_simulation_lvpc(seed = 12345, coins_for_parties = 'max_value'):
    return make_example_simulation_for_all("LVPC", seed, coins_for_parties)

def test_get_payment_options_lvpc_channel_exists():
    test_get_payment_options_elmo_lvpc_donner_channel_exists("LVPC")

def test_get_payment_options_lvpc_no_channel_exists_virtual_channel_possible():
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible1("LVPC")

def test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible1():
    fee_intermediary, lvpc, future_payments = make_example_network_lvpc_and_future_payments()
    payment_options = lvpc.get_payment_options(0, 7, 100000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'LVPC-open-channel'

def test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible2():
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible("LVPC")

def test_get_payment_options_lvpc():
    test_get_payment_options_lvpc_channel_exists()
    test_get_payment_options_lvpc_no_channel_exists_virtual_channel_possible()
    test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible1()
    test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible2()

def test_do_lvpc():
    test_do_elmo_lvpc_donner("LVPC")

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
    lvpc = LVPC(4, lvpc_fee_intermediary = 1000000)

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

def test_simulation_with_lvpc():
    test_simulation_with_lvpc_ignore_centrality()
    test_simulation_with_lvpc_ignore_centrality_and_distance()
    simulation = make_example_simulation_lvpc()
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
