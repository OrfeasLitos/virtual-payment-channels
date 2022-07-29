
from tests import make_example_network_elmo_lvpc_donner, make_example_simulation_for_all, test_get_payment_options_elmo_lvpc_donner_channel_exists


def make_example_network_donner(fee_intermediary = 1000000):
    donner = make_example_network_elmo_lvpc_donner("Donner", fee_intermediary)
    return donner

def make_example_simulation_donner(seed = 12345, coins_for_parties = 'max_value'):
    return make_example_simulation_for_all("Donner", seed, coins_for_parties)

def test_get_payment_options_donner_channel_exists():
    test_get_payment_options_elmo_lvpc_donner_channel_exists("Donner")

def test_get_payment_options_donner():
    donner = make_example_network_donner()
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 300000000.), (0, 3, 2500000000.)]
    value1 = 100000000
    payment_options1 = donner.get_payment_options(0, 3, value1, future_payments)
    assert payment_options1[2]['payment_information']['kind'] == 'Donner-open-virtual-channel'
    payment_information_new_virtual_channel1 = payment_options1[2]['payment_information']

    donner.do(payment_information_new_virtual_channel1)

    value2 = 1000000
    payment_options2 = donner.get_payment_options(0, 8, value2, future_payments)
    assert len(payment_options2) == 3
    assert payment_options2[2]['payment_information']['kind'] == 'Donner-open-virtual-channel'
    assert payment_options2[2]['payment_information']['data'][0] == [0, 2, 3, 8]
    payment_information_new_virtual_channel2 = payment_options2[2]['payment_information']
    donner.do(payment_information_new_virtual_channel2)

def test_simulation_with_donner():
    simulation = make_example_simulation_donner()
    results = simulation.run()
    print(results)

if __name__ == "__main__":
    test_get_payment_options_donner_channel_exists()
    test_get_payment_options_donner()
    test_simulation_with_donner()
    print("Success")