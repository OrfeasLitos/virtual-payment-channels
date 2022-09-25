import random
import numpy as np
import collections
import pickle
from paymentmethod import MAX_COINS
from simulation import random_payments, ROUNDS_RANDOM_PAYMENTS, SEED
from tqdm import tqdm


def all_random_payments_preferred_receiver():
    # preferred receiver
    for parties in [100]:
        for num_payments in [100000]:
            for i in tqdm(range(ROUNDS_RANDOM_PAYMENTS)):
                payments = random_payments(parties, 'preferred-receiver', num_payments)
                with open('random_payments_preferred_receiver' + '_{}_'.format(parties) + '{}'.format(i) + '.pickle', 'wb') as file:
                    pickle.dump(payments, file)



if __name__ == "__main__":

    #flamegraph.start_profile_thread(fd=open("./perf_1.log", "w"))
    #seed = random.randrange(sys.maxsize)
    
    # uncomment to generate random payments.
    
    random.seed(SEED)
    np.random.seed(SEED)
    all_random_payments_preferred_receiver()


