from paymentmethod import PlainBitcoin
from knowledge import Knowledge
import math

class Utility:

    def __init__(self, utility_function):
        """
        Utility function should have cost, time and knowledge as input
        """
        self.utility_function = utility_function

    def get_utility(self, payment, payment_method, knowledge, path=None):
        # review: this gives a -inf utility to on-chain payments
        # TODO: rewrite this function to take fee, delay, distance and centrality
        if path == None:
            return -math.inf

        num_hops = len(path) - 1
        return self.utility_function(payment_method.get_payment_fee(payment, num_hops), payment_method.get_payment_time(path), knowledge.get_knowledge())

    # review:
    #  * this method should take as input a list of candidate payments and choose the best one. It should be agnostic to the details of each payment method (e.g. no calls to PlainBitcoin)
    def choose_payment_method(self, payment_options):
        """
        This method should compare the utility of on-chain transactions with the utility of a new channel (opened on chain) and completely off-chain transactions and should
        returns the best of these possibilities.
        Returns 0 for off-chain, 1 for new channel, 2 for PlainBitcoin
        """

        best_score = 0
        for option in payment_options:
            if self.get_utility(option) > best_score:
                best = option['payment']
        return best
