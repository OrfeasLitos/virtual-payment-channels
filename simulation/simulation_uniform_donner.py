
import random
import pickle
import time
from tqdm import tqdm
import numpy as np

from utility import Utility
from knowledge import Knowledge
from donner import Donner
from simulation import Simulation, SEED, ROUNDS_RANDOM_PAYMENTS

if __name__ == "__main__":

    random.seed(SEED + 100)
    np.random.seed(SEED + 100)

    utility = Utility(
        'sum_of_inverses', personalization = ("same-utility", 3000),
        parameters = [(1, 100000000, 1000, 0.001, 0.1)]
    )
    knowledge = Knowledge('10-next-mine')
    method = Donner(3000)
    for i in tqdm(range(ROUNDS_RANDOM_PAYMENTS)):
        pickled_file_uniform = open('random_payments_uniform_3000_' + '_{}_'.format(i) + '.pickle', 'rb')
        payments_uniform = pickle.load(pickled_file_uniform)
        print("Number payments: ", len(payments_uniform))
        sim = Simulation(payments_uniform, method, knowledge, utility)
        start = time.time()
        results = sim.run()
        end = time.time()
        print("Time one round: ", end - start)
        with open("results_power_law" + method.method_name + "_{}".format(i) + ".pickle", 'wb') as file:
            pickle.dump(results, file)
