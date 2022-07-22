import random
from lvpc import LVPC
from knowledge import Knowledge
from simulation import Simulation, random_payments
from utility import Utility
from tests import example_utility_function_for_simulation

def make_example_simulation_lvpc(seed = 12345, coins_for_parties = 'max_value'):
    random.seed(seed)
    lvpc = LVPC(10, coins_for_parties=coins_for_parties)
    knowledge = Knowledge('know-all')
    payments = random_payments(100, 10, 2000000000)
    utility_function = example_utility_function_for_simulation
    utility = Utility(utility_function)
    return Simulation(payments, lvpc, knowledge, utility)

def test_simulation_with_lvpc():
    simulation = make_example_simulation_lvpc()
    results = simulation.run()
    print(results)

if __name__ == "__main__":
    test_simulation_with_lvpc()