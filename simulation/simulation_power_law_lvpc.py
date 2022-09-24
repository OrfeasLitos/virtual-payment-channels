
import random
import pickle
import time
from tqdm import tqdm
import numpy as np

from utility import Utility
from knowledge import Knowledge
from lvpc import LVPC
from simulation import Simulation, SEED, ROUNDS_RANDOM_PAYMENTS

if __name__ == "__main__":

    random.seed(SEED + 100)
    np.random.seed(SEED + 100)

    utility = Utility(
        'sum_of_inverses', personalization = ("50-50", 500),
        parameters = [(1, 100000000, 1000, 0.001, 0.1), (1, 1000000, 10000, 0.001, 0.1)]
    )
    knowledge = Knowledge('10-next-mine')
    for i in tqdm(range(ROUNDS_RANDOM_PAYMENTS)):
        method = LVPC(500)
        with open('random_payments_zipf_500_' + '_{}_'.format(i) + '.pickle', 'rb') as pickled_file_zipf:
            payments_zipf = pickle.load(pickled_file_zipf)
        print("Number payments: ", len(payments_zipf))
        sim = Simulation(payments_zipf, method, knowledge, utility)
        start = time.time()
        results = sim.run()
        end = time.time()
        print("Time one round: ", end - start)
        with open("results_power_law" + method.method_name + "_{}".format(i) + ".pickle", 'wb') as file:
            pickle.dump(results, file)
