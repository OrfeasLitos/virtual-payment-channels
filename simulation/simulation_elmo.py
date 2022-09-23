
import random
import pickle
import time
import tqdm
import numpy as np

from utility import Utility
from knowledge import Knowledge
from elmo import Elmo
from simulation import Simulation, SEED, ROUNDS_RANDOM_PAYMENTS

if __name__ == "__main__":

    random.seed(SEED + 100)
    np.random.seed(SEED + 100)
    
    pickled_file_zipf = open("random_payments_zipf.pickle", 'rb')
    payments_zipf = pickle.load(pickled_file_zipf)

    utility = Utility(
        'sum_of_inverses', personalization = ("50-50", 1000),
        parameters = [(1, 100000000, 1000, 0.001, 0.1), (1, 1000000, 10000, 0.001, 0.1)]
    )
    knowledge = Knowledge('10-next-mine')
    method = Elmo(1000)
    for i in tqdm(range(ROUNDS_RANDOM_PAYMENTS)):
        payments = payments_zipf[(1000, 2., i)]
        print("Number payments: ", len(payments))
        sim = Simulation(payments, method, knowledge, utility)
        start = time.time()
        results = sim.run()
        end = time.time()
        print("Time one round: ", end - start)
        with open("example_results_" + method.method_name + "_{}".format(i) + ".pickle", 'wb') as file:
            pickle.dump(results, file)

