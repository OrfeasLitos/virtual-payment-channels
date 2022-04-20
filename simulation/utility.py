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
        if path == None:
            return -math.inf

        return self.utility_function(payment_method.get_payment_fee(payment, path), payment_method.get_payment_time(path), knowledge.get_knowledge())

    # review:
    #  * this method should take as input a list of candidate payments and choose the best one. It should be agnostic to the details of each payment method (e.g. no calls to PlainBitcoin)
    #  * I was thinking of naming this method `choose_payment_method`
    def get_best_option(self, payment_options):
        """
        This method should compare the utility of on-chain transactions with the utility of a new channel (opened on chain) and completely off-chain transactions and should
        returns the best of these possibilities.
        Returns 0 for off-chain, 1 for new channel, 2 for PlainBitcoin
        """
        # There should be if's to calculate utilities and check whether to make a plain bitcoin transaction, open a new channel on chain or do everything off-chain (for Lightning)
        # For other protocols similarly.

        # The last argument "shortest_path" could maybe be replaced by the length of the shortest path (e.g. for LN, where time and fee depend only on the length of the path)
        # but for now I used greater generality. Also this has the advantage that we can call find_shortest_path here and don't have to do it in the simulation.

        best_score = 0
        for option in payment_options:
            if self.get_utility(option) > best_score:
                best = option['payment']
        return best
