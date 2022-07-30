

from tests import (make_example_network_elmo_lvpc_donner, make_example_network_elmo_lvpc_donner_and_future_payments, make_example_simulation_for_all,
    test_get_payment_options_elmo_lvpc_donner_channel_exists, test_get_payment_options_elmo_lvpc_donner_no_channel_exists_no_virtual_channel_possible,
    test_get_payment_options_elmo_lvpc_donner_no_channel_exists_virtual_channel_possible1
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

def test_simulation_with_lvpc():
    simulation = make_example_simulation_lvpc()
    results = simulation.run()
    print(results)

if __name__ == "__main__":
    test_get_payment_options_lvpc()
    test_simulation_with_lvpc()
    print("Success")