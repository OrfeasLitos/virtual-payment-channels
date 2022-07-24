import random
from lvpc import LVPC
from knowledge import Knowledge
from simulation import Simulation, random_payments
from utility import Utility
from tests import example_utility_function_for_simulation

def make_example_network_lvpc(lvpc_fee_intermediary = 1000000):
    lvpc = LVPC(10, lvpc_fee_intermediary = lvpc_fee_intermediary)

    lvpc.network.add_channel(0, 3000000000., 2, 7000000000., None)
    lvpc.network.add_channel(0, 6000000000., 1, 7000000000., None)
    lvpc.network.add_channel(1, 4000000000., 4, 8000000000., None)
    lvpc.network.add_channel(3, 9000000000., 4, 8000000000., None)
    lvpc.network.add_channel(2, 9000000000., 3, 2000000000., None)
    lvpc.network.add_channel(1, 10000000000., 2, 8000000000., None)
    lvpc.network.add_channel(4, 10000000000., 7, 8000000000., None)
    lvpc.network.add_channel(3, 10000000000., 8, 8000000000., None)
    return lvpc

# copied from elmo
def make_example_network_lvpc_and_future_payments(fee_intermediary = 1000000):
    lvpc = make_example_network_lvpc(fee_intermediary)
    future_payments = [(0,1,2000000000.), (0, 7, 1500000000.), (0,7,2100000000.), (0, 8, 3000000000.)]
    return fee_intermediary, lvpc, future_payments

# copied from elmo
def make_example_simulation_lvpc(seed = 12345, coins_for_parties = 'max_value'):
    random.seed(seed)
    lvpc = LVPC(10, coins_for_parties=coins_for_parties)
    knowledge = Knowledge('know-all')
    payments = random_payments(100, 10, 2000000000)
    utility_function = example_utility_function_for_simulation
    utility = Utility(utility_function)
    return Simulation(payments, lvpc, knowledge, utility)

def test_get_payment_options_lvpc_no_channel_exists_virtual_channel_possible():
    fee_intermediary, lvpc, future_payments = make_example_network_lvpc_and_future_payments()
    payment_options = lvpc.get_payment_options(0, 4, 100000000., future_payments)
    assert len(payment_options) == 3
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'LVPC-open-channel'
    assert payment_options[2]['payment_information']['kind'] == 'LVPC-open-virtual-channel'

def test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible():
    fee_intermediary, lvpc, future_payments = make_example_network_lvpc_and_future_payments()
    payment_options = lvpc.get_payment_options(0, 7, 100000000., future_payments)
    assert len(payment_options) == 2
    assert payment_options[0]['payment_information']['kind'] == 'onchain'
    assert payment_options[1]['payment_information']['kind'] == 'LVPC-open-channel'

def test_get_payment_options():
    test_get_payment_options_lvpc_no_channel_exists_virtual_channel_possible()
    test_get_payment_options_lvpc_no_channel_exists_no_virtual_channel_possible()

def test_simulation_with_lvpc():
    simulation = make_example_simulation_lvpc()
    results = simulation.run()
    print(results)

if __name__ == "__main__":
    test_get_payment_options()
    test_simulation_with_lvpc()
    print("Success")