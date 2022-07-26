import random
from donner import Donner
from knowledge import Knowledge
from simulation import Simulation, random_payments
from tests import example_utility_function_for_simulation
from utility import Utility

def make_example_network_donner(fee_intermediary = 1000000):
    donner = Donner(10, fee_intermediary = fee_intermediary)

    donner.network.add_channel(0, 3000000000., 2, 7000000000., None)
    donner.network.add_channel(0, 6000000000., 1, 7000000000., None)
    donner.network.add_channel(1, 4000000000., 4, 8000000000., None)
    donner.network.add_channel(3, 9000000000., 4, 8000000000., None)
    donner.network.add_channel(2, 9000000000., 3, 2000000000., None)
    donner.network.add_channel(1, 10000000000., 2, 8000000000., None)
    donner.network.add_channel(4, 10000000000., 7, 8000000000., None)
    donner.network.add_channel(3, 10000000000., 8, 8000000000., None)
    return donner

# copied from elmo
def make_example_simulation_donner(seed = 12345, coins_for_parties = 'max_value'):
    random.seed(seed)
    donner = Donner(10, coins_for_parties=coins_for_parties)
    knowledge = Knowledge('know-all')
    payments = random_payments(100, 10, 2000000000)
    utility_function = example_utility_function_for_simulation
    utility = Utility(utility_function)
    return Simulation(payments, donner, knowledge, utility)


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
    test_get_payment_options_donner()
    test_simulation_with_donner()
    print("Success")