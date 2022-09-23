import random
import numpy as np
import collections
import pickle
from paymentmethod import MAX_COINS
from tqdm import tqdm

ROUNDS_RANDOM_PAYMENTS = 20
SEED = 12345

def random_payments(players, distribution = 'uniform', num_pays = None, power = None):
    """
    num_pays gives the number of total payments
    """
    res = collections.deque()
    if distribution == 'uniform':
        for _ in range(num_pays):
            sender = random.randrange(players)
            receiver = random.randrange(players)
            while receiver == sender:
                receiver = random.randrange(players)
            value = random.randrange(MAX_COINS * players // num_pays)
            res.append((sender, receiver, value))
    elif distribution == 'zipf':
        # assume incoming payments come from power law distribution
        # and the parties that pay from a uniform distribution
        # example: big player that everyone pays to, but
        # that doesn't have that many outgoing payments.
        incoming_payments_per_player = np.random.zipf(power, players) * 50
        num_pays = sum(incoming_payments_per_player)
        # we want a parameter for the payment value of 2.16
        # for approximately 80-20 rule (and power law).
        # the mean of a zeta variable with parameter 2.16 is approximately 7.25
        values = np.random.zipf(2.16, num_pays) * (MAX_COINS * players // (2 * num_pays * 7.25))
        num_value = 0
        for receiver in range(len(incoming_payments_per_player)):
            for j in range(incoming_payments_per_player[receiver]):
                sender = random.randrange(players)
                while sender == receiver:
                    sender = random.randrange(players)
                value = values[num_value]
                num_value += 1
                res.append((sender, receiver, value))
        random.shuffle(res)
    elif distribution == 'preferred-receiver':
        # with probability p the party sends the amount to preferred receiver
        # with probability q to a random party.
        preferred_receivers = []
        for sender in range(players):
            preferred_receiver = random.randrange(players)
            while sender == preferred_receiver:
                preferred_receiver = random.randrange(players)
            preferred_receivers.append(preferred_receiver)
        p = 0.5
        q = 1-p
        for _ in range(num_pays):
            sender = random.randrange(players)
            receiver = random.randrange(players) if random.uniform(0, 1) > p else preferred_receivers[sender]
            while receiver == sender:
                receiver = random.randrange(players)
            value = random.randrange(MAX_COINS * players // num_pays)
            res.append((sender, receiver, value))
    else:
        raise ValueError

    return res

def all_random_payments():
    # power law
    # only up to 1000 parties
    for parties in [500]:
        print(parties)
        for a in [2]:
            for i in tqdm(range(ROUNDS_RANDOM_PAYMENTS)):
                payments = random_payments(parties, 'zipf', power=a)
                with open('random_payments_zipf' + '_{}_'.format(parties) + '_{}_'.format(i) + '.pickle', 'wb') as file:
                    pickle.dump(payments, file)

    # uniform
    for parties in [3000]:
        for num_payments in [90000]:
            for i in tqdm(range(ROUNDS_RANDOM_PAYMENTS)):
                payments = random_payments(parties, 'uniform', num_payments)
                with open('random_payments_uniform' + '_{}_'.format(parties) + '_{}_'.format(i) + '.pickle', 'wb') as file:
                    pickle.dump(payments, file)

class Simulation:
    """
    Here the simulation takes place.

    This is implemented as an iterator
    """

    def __init__(self, payments, payment_method, knowledge, utility):
        """
        payments should be a deque.
        """
        self.payments = payments
        self.payment_method = payment_method
        self.knowledge = knowledge
        self.utility = utility

    def __iter__(self):
        return self

    def __next__(self):
        try:
            sender, receiver, value = self.payments.popleft()
            # TODO
            # 1. query network for payment methods that satisfy this payment
            #list_of_candidate_payment_methods = self.network.payment_options(payment)
            # 2a. if no candidates exist, write this down as a failed payment (and decide later how to measure them)
            # 2b. find which method is the cheapest
            #    * use discussed heuristics, i.e. distance from future paying parties and our centrality
            #  for each candidate, calculate: candidate_network = self.network.apply(candidate)
            #    * our new centrality: candidate_centrality = candidate_network.centrality(sender)
            #    * our distance from future paying parties: candidate_distance = candidate_network.distance(sender)
            #  for each candidate, apply the utility function, which takes (fee, time, current_ - candidate_centrality, current_ - candidate_distance)
            # 3. instruct network to carry out cheapest method
            #self.network = self.network.apply(best_method)

            # ideally, one could take the initial network state and the list of payments and reach the final network state
            knowledge_sender = self.knowledge.get_knowledge(sender, self.payments)
            payment_options = self.payment_method.get_payment_options(sender, receiver, value, knowledge_sender)
            try:
                payment_option, fee, delay = self.utility.choose_payment_method(sender, payment_options)
                self.payment_method.do(payment_option)
                # True for payment done, False if not done.
                return True, payment_option, fee, delay
            except ValueError:
                return False, (sender, receiver, value)

        except IndexError:
            raise StopIteration

    def run(self):
        res = []
        for step in tqdm(self):
            res.append(step)
        return res

    def __eq__(self, other):
        # two simulations are equal iff all attributes are equal.
        return (
            self.payments == other.payments
            and self.payment_method == other.payment_method
            and self.knowledge == other.knowledge
            and self.utility == other.utility
        )


if __name__ == "__main__":

    #flamegraph.start_profile_thread(fd=open("./perf_1.log", "w"))
    #seed = random.randrange(sys.maxsize)
    
    # uncomment to generate random payments.
    
    random.seed(SEED)
    np.random.seed(SEED)
    all_random_payments()


    