import random
import numpy as np
import sys
import collections
import pickle
#from scipy.special import zeta
from knowledge import Knowledge
from paymentmethod import PlainBitcoin
from ln import LN
from elmo import Elmo
from donner import Donner
from lvpc import LVPC
from utility import Utility

# max_coins of PlainBitcoin divided by 5
MAX_PAY = 2000000000000000//5

def random_payments(players, max_pay, distribution = 'uniform', num_pays = None, power = None):
    res = collections.deque()
    match distribution:
        case 'uniform':
            for _ in range(num_pays):
                sender = random.randrange(players)
                receiver = random.randrange(players)
                while receiver == sender:
                    receiver = random.randrange(players)
                value = random.randrange(max_pay)
                res.append((sender, receiver, value))
        case 'zipf':
            # For a > 2, we could calculate the expectation (i.e. expected number of payments)
            # by means of the zeta function to have a similar number of payments as in the case
            # for 'uniform' und 'preferred-receiver'.
            # But we can't do that for a = 2, since the expectation is infinite.
            # And even for a > 2 the convergence in the lln would probably be slow, so it 
            # doesn't make that much sense to look at the expectation.
            incoming_payments_per_player = np.random.zipf(power, players)
            # assume incoming payments come from unifrom distribution
            # example: big player that everyone pays to (in real world maybe Netflix), but
            # that doesn't have that many outgoing payments.
            for receiver in range(len(incoming_payments_per_player)):
                for j in range(incoming_payments_per_player[receiver]):
                    sender = random.randrange(players)
                    while sender == receiver:
                        sender = random.randrange(players)
                    value = random.randrange(max_pay)
                    res.append((sender, receiver, value))
            random.shuffle(res)
        case 'preferred-receiver':
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
                value = random.randrange(max_pay)
                res.append((sender, receiver, value))
        case _:
            raise ValueError

    return res

def all_random_payments():
    # uniform
    payments_for_uniform = {}
    for parties in [10, 100, 1000, 10000]:
        for num_payments in [100, 1000, 10000, 100000]:
            for i in range(10):
                payments = random_payments(parties, MAX_PAY, 'uniform', num_payments)
                payments_for_uniform[(parties, num_payments, i)] = payments

    # preferred receiver
    payments_for_preferred_receiver = {}
    for parties in [10, 100, 1000, 10000]:
        for num_payments in [100, 1000, 10000, 100000]:
            for i in range(10):
                payments = random_payments(parties, MAX_PAY, 'preferred-receiver', num_payments)
                payments_for_preferred_receiver[(parties, num_payments, i)] = payments
    
    # power law
    payments_for_zipf = {}
    for parties in [10, 100, 1000, 10000]:
        for a in [3, 2.5, 2]:
            for i in range(10):
                payments = random_payments(parties, MAX_PAY, 'zipf', a)
                payments_for_zipf[(parties, a, i)] = payments
    
    #TODO: pickle the outputs.
    return payments_for_uniform, payments_for_preferred_receiver, payments_for_zipf


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
            future_payments = self.knowledge.get_knowledge(sender, self.payments)
            payment_options = self.payment_method.get_payment_options(sender, receiver, value, future_payments)
            try:
                payment_option = self.utility.choose_payment_method(payment_options)
                self.payment_method.do(payment_option)
                # True for payment done, False if not done.
                return True, payment_option
            except ValueError:
                return False, (sender, receiver, value)

        except IndexError:
            raise StopIteration

    def run(self):
        res = []
        for step in self:
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

    #seed = random.randrange(sys.maxsize)
    seed = 12345
    random.seed(seed)
    np.random.seed(seed)
    
    # uncomment to generate random payments.
    """
    payments_uniform, payments_preferred_receiver, payments_zipf = all_random_payments()
    with open('random_payments_uniform.pickle', 'wb') as file:
        pickle.dump(payments_uniform, file)
    with open('random_payments_preferred_receiver.pickle', 'wb') as file:
        pickle.dump(payments_preferred_receiver, file)
    with open('random_payments_zipf.pickle', 'wb') as file:
        pickle.dump(payments_zipf, file)
    """
    pickled_file = open("random_payments_zipf.pickle", 'rb')
    payments_zipf = pickle.load(pickled_file)
    

    
    payments = payments_zipf[(10000, 2, 0)]
    utilities = [
        Utility('sum_of_inverses', parameters = (1000, 1000000, 1000, 10000, 0)),
        Utility('sum_of_inverses', parameters = (1000, 1000000, 1000, 10000, 1000000)),
        Utility('sum_of_inverses', parameters = (1000, 10000, 10000, 10000, 0))
    ]
    for method in [LN(10000), Elmo(10000), Donner(10000), LVPC(10000)]:
        for utility in utilities:
            for knowledge in [
                Knowledge('all'), Knowledge('mine'), Knowledge('next'),
                Knowledge('10-next'), Knowledge('10-next-mine')
            ]:
                sim = Simulation(payments, method, knowledge, utility)
                results = sim.run()
                # for step in sim:
                #    print(step)
    
