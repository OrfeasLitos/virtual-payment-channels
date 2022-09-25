
import random
import pickle
import time
from tqdm import tqdm
import numpy as np

from utility import Utility
from knowledge import Knowledge
from ln import LN
from simulation import Simulation, SEED, ROUNDS_RANDOM_PAYMENTS

if __name__ == "__main__":

    random.seed(SEED + 100)
    np.random.seed(SEED + 100)

    utility = Utility(
        'sum_of_inverses', personalization = ("50-50", 100),
        parameters = [(1, 100000000, 1000, 0.001, 0.1), (1, 1000000, 10000, 0.001, 0.1)]
    )
    knowledge = Knowledge('mine')
    for i in tqdm(range(ROUNDS_RANDOM_PAYMENTS)):
        method = LN(100)
        with open('random_payments_preferred_receiver_1000' + '_{}'.format(i) + '.pickle', 'rb') as pickled_file_preferred_receiver:
            payments_preferred_receiver = pickle.load(pickled_file_preferred_receiver)
        print("Number payments: ", len(payments_preferred_receiver))
        sim = Simulation(payments_preferred_receiver, method, knowledge, utility)
        start = time.time()
        results = sim.run()
        end = time.time()
        print("Time one round: ", end - start)
        with open("results_preferred_receiver" + method.method_name + "_{}".format(i) + ".pickle", 'wb') as file:
            pickle.dump(results, file)
