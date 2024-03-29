
from tests import (make_example_network_elmo_lvpc_donner, make_example_simulation_for_all,
    make_example_network_elmo_lvpc_donner_and_future_payments, get_knowledge_sender,
    test_get_payment_options_elmo_lvpc_donner_channel_exists,
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible,
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible,
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



def make_example_network_donner(fee_intermediary = 1000000):
    donner = make_example_network_elmo_lvpc_donner("Donner", fee_intermediary)
    return donner

def make_example_network_donner_and_future_payments(fee_intermediary = 1000000):
    return make_example_network_elmo_lvpc_donner_and_future_payments("Donner", fee_intermediary)

def make_example_simulation_donner(seed = 12345, nr_players = 10, coins_for_parties = 'max_value'):
    return make_example_simulation_for_all("Donner", seed, nr_players, coins_for_parties)

def test_get_payment_options_donner_channel_exists():
    test_get_payment_options_elmo_lvpc_donner_channel_exists("Donner")

def test_get_payment_options_donner_no_channel_exists_no_virtual_channel_possible():
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible("Donner")

def test_get_payment_options_donner_no_channel_exists_virtual_channel_possible1():
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible("Donner")

# same as in Elmo
def test_get_payment_options_donner_no_channel_exists_virtual_channel_possible2():
    fee_intermediary, donner, future_payments = make_example_network_donner_and_future_payments()
    sender = 0
    knowledge_sender = get_knowledge_sender(sender, future_payments)
    payment_options = donner.get_payment_options(sender, 7, 100000000., knowledge_sender)
    assert len(payment_options) == 3
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'Donner-open-channel'
    assert payment_options[2]['payment_information']['kind'] == 'Donner-open-virtual-channel'

def test_get_payment_options_donner():
    test_get_payment_options_donner_channel_exists()
    test_get_payment_options_donner_no_channel_exists_no_virtual_channel_possible()
    test_get_payment_options_donner_no_channel_exists_virtual_channel_possible1()
    test_get_payment_options_donner_no_channel_exists_virtual_channel_possible2()

def test_get_payment_options_and_weight_function_donner():
    donner = make_example_network_donner()
    future_payments = [
        (0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.),
        (0, 8, 300000000.), (0, 3, 2500000000.)
    ]
    sender1 = 0
    knowledge_sender1 = get_knowledge_sender(sender1, future_payments)
    value1 = 100000000
    payment_options1 = donner.get_payment_options(sender1, 3, value1, knowledge_sender1)
    assert payment_options1[2]['payment_information']['kind'] == 'Donner-open-virtual-channel'
    payment_information_new_virtual_channel1 = payment_options1[2]['payment_information']

    donner.do(payment_information_new_virtual_channel1)

    value2 = 1000000
    sender2 = 0
    knowledge_sender2 = get_knowledge_sender(sender2, future_payments)
    payment_options2 = donner.get_payment_options(sender2, 8, value2, knowledge_sender2)
    assert len(payment_options2) == 3
    assert payment_options2[2]['payment_information']['kind'] == 'Donner-open-virtual-channel'
    assert payment_options2[2]['payment_information']['data'][0] == [0, 2, 3, 8]
    payment_information_new_virtual_channel2 = payment_options2[2]['payment_information']
    donner.do(payment_information_new_virtual_channel2)

def test_do_donner():
    test_do_elmo_lvpc_donner("Donner")

def test_update_balances_new_virtual_channel_donner():
    test_update_balances_new_virtual_channel_elmo_lvpc_donner("Donner")

def test_lock_and_unlock_donner():
    test_lock_and_unlock_elmo_lvpc_donner("Donner")

def test_pay_donner():
    test_pay_elmo_lvpc_donner("Donner")

def test_undo_donner():
    test_undo_elmo_lvpc_donner("Donner")

def test_coop_close_channel_first_virtual_layer_no_layer_above_donner():
    test_coop_close_channel_first_virtual_layer_no_layer_above_elmo_lvpc_donner("Donner")

def test_force_close_channel_onchain_layer_one_layer_above_donner():
    test_force_close_channel_onchain_layer_one_layer_above_elmo_lvpc_donner("Donner")

def test_close_channel_donner():
    test_coop_close_channel_first_virtual_layer_no_layer_above_donner()
    test_force_close_channel_onchain_layer_one_layer_above_donner()

def test_simulation_with_donner_ignore_centrality():
    test_simulation_with_elmo_lvpc_donner_ignore_centrality("Donner")

def test_simulation_with_donner_ignore_centrality_and_distance():
    test_simulation_with_elmo_lvpc_donner_ignore_centrality_and_distance("Donner")

def test_simulation_with_previous_channels_donner_ignore_centrality():
    test_simulation_with_previous_channels_elmo_lvpc_donner_ignore_centrality("Donner")

def test_simulation_with_previous_channels_donner_long_path_ignore_centrality():
    test_simulation_with_previous_channels_elmo_donner_lvpc_long_path_ignore_centrality("Donner")

def test_simulation_with_previous_channels_donner_recursive_ignore_centrality():
    test_simulation_with_previous_channels_elmo_donner_lvpc_recursive_ignore_centrality("Donner")

def test_simulation_with_donner():
    test_simulation_with_donner_ignore_centrality()
    test_simulation_with_donner_ignore_centrality_and_distance()
    test_simulation_with_previous_channels_donner_ignore_centrality()
    test_simulation_with_previous_channels_donner_long_path_ignore_centrality()
    test_simulation_with_previous_channels_donner_recursive_ignore_centrality()
    simulation = make_example_simulation_donner(nr_players = 20)
    results = simulation.run()

if __name__ == "__main__":
    test_get_payment_options_donner()
    test_get_payment_options_and_weight_function_donner()
    test_do_donner()
    test_update_balances_new_virtual_channel_donner()
    test_lock_and_unlock_donner()
    test_pay_donner()
    test_undo_donner()
    test_close_channel_donner()
    test_simulation_with_donner()
    print("Success")
