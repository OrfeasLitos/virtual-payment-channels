import random
import sys
import collections
from network import *
from knowledge import *
from paymentmethod import *
from utility import *

def random_payments(num_pays, players, max_pay):
    res = []
    for i in range(num_pays):
        sender = random.randrange(players)
        receiver = random.randrange(players)
        while receiver == sender:
            receiver = random.randrange(players)
        value = random.randrange(max_pay)
        res.append((sender, receiver, value))
    return collections.deque(res)

class Simulation:
    """
    Here the simulation takes place.

    There's an update method which is one step in the simulation.
    Running the simulation is equivalent to calling the update method as long as it's possible.
    """

    def __init__(self, nr_players, payments, payment_method, knowledge, utility):
        """
        payments should be a deque.
        """
        self.nr_players = nr_players
        self.network = Network(self.nr_players)
        self.payments = payments
        self.payment_method = payment_method
        self.knowledge = knowledge
        self.utility = utility

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.payments) > 0:
            payment = self.payments.popleft()
            sender, receiver, value = payment
            # Here method means just Plainbitcoin vs new channel on-chain vs new channel off-chain (for want of a better word).
            method = self.payment_method.compare_utilites(self.utility, payment, self.knowledge)
            self.network.add_edge_with_check((method, (sender, receiver)))
            self.network.add_edge_with_check((method, (receiver, sender)))
            return (method, payment)
        else:
            raise StopIteration

    def run(self):
        res = []
        end = False
        while end == False:
            try:
                next = self.__next__()
                res.append(next)
            except StopIteration:
                end = True
        return res


if __name__ == "__main__":

    #seed = random.randrange(sys.maxsize)
    seed = 12345
    random.seed(seed)
    nr_players = 20
    # 1000 transactions, 100 players, max 10000 Bitcoin per transaction
    payments = random_payments(1000, 100, 100000)
    bitcoin = PlainBitcoin()
    # Player know everything
    def knowledge_function(party, payments):
        return payments
    knowledge = Knowledge(0, payments, knowledge_function)
    # very simple utility function
    def utility_add(cost, time, knowledge):
        return cost + time
    utility = Utility(utility_add)
    simulation = Simulation(nr_players, payments, bitcoin, knowledge, utility)
    payments_with_method = simulation.run()
    print(len(payments_with_method))
    network = simulation.network
    print(len(network.edges))
    print(payments_with_method[:30])
    print(network.edges[:60])
    """
    for parties in [10, 100, 1000, 10000]:
        for num_payments in [100, 1000, 10000, 100000]:
            for payments in random_payments(num_payments, parties, MAX_COINS/5) * 10:
                for method in [PlainBitcoin(), LN(), Elmo(), Donner(), LVPC()]:
                    for utility in [
                        Utility('only-fee'), Utility('only-time'),
                        Utility('add'), Utility('mul')
                    ]:
                        for knowledge in [
                            Knowledge('all'), Knowledge('only-mine'),
                            Knowledge('only-next'), Knowledge('10-next'),
                            Knowledge('10-next-mine')
                        ]:
                            sim = Simulation(parties, payments, method, utility, knowledge)
                            sim.run()
                            # for step in sim:
                            #    print(step)
    """

