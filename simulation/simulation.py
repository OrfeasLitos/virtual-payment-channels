import random
import sys
import collections
from network import Network
from knowledge import Knowledge
from paymentmethod import PaymentMethod, PlainBitcoin
from utility import Utility

def random_payments(num_pays, players, max_pay):
    res = collections.deque()
    for i in range(num_pays):
        sender = random.randrange(players)
        receiver = random.randrange(players)
        while receiver == sender:
            receiver = random.randrange(players)
        value = random.randrange(max_pay)
        res.append((sender, receiver, value))
    return res

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
        self.network = Network(nr_players)
        self.payments = payments
        self.payment_method = payment_method
        self.knowledge = knowledge
        self.utility = utility

    def __iter__(self):
        return self

    def __next__(self):
        try:
            payment = self.payments.popleft()
            sender, receiver, value = payment
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

            try:
                # change next line to sth like:
                #payment_options = self.payment_method.get_payment_options(sender, receiver, value)
                cost, shortest_path = network.find_cheapest_path(sender, receiver, value)
                # Here method means just PlainBitcoin vs new channel on-chain vs new channel off-chain (for want of a better word).
                method_num = self.utility.compare_utilities(self.payment_method, payment, self.knowledge, shortest_path)
                if method_num == 1:
                    # TODO: think about a reasonable balance that should be put on the new channel. For the sender it should be >= value
                    self.network.add_channel(sender, value, receiver, 0)
                    # TODO: make a function that updates the balance of a party (hereby I mean the balance that is not on a channel, so just the Bitcoins in a Wallet)
                    # TODO: make a function that does the transaction and updates the balance on the channel (or both updates in one)
                    # probably add_channel should automatically update the balance of the wallets when they are transfered to the channel.
                    # then only the balance on the channel has to be updated.
                    self.network.update_balance(sender, amount_sender, receiver, amount_receiver, intermediaries, amount_intermediaries)
                    # TODO: keep actually track of the balance of a party in his wallet.
                else:
                    # TODO: make two more cases (with elif else)
                    self.network.update_balance(sender, amount_sender, receiver, amount_receiver, intermediaries, amount_intermediaries)
                return (method_num, payment)
            except Exception:
                # TODO: make two cases (opening of channel, PlainBitcoin transaction)
                method_num = self.utility.compare_utilities(self.payment_method, payment, self.knowledge, shortest_path)
                self.network.update_balance(sender, amount_sender, receiver, amount_receiver, intermediaries, amount_intermediaries)

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
            self.network == other.network
            and self.payments == other.payments
            and self.payment_method == other.payment_method
            and self.knowledge == other.knowledge
            and self.utility == other.utility
        )

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
    print(list(network.edges)[:60])
    """
    for parties in [10, 100, 1000, 10000]:
        for num_payments in [100, 1000, 10000, 100000]:
            for payments in random_payments(num_payments, parties, MAX_COINS/5) * 10:
                for method in [LN(), Elmo(), Donner(), LVPC()]:
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

