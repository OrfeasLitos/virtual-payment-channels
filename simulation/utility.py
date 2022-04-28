from paymentmethod import PlainBitcoin
from knowledge import Knowledge
import math

class Utility:

    def __init__(self, utility_function):
        """
        Utility function should have cost, time and knowledge as input
        """
        self.utility_function = utility_function

    def get_utility(self, fee, delay, distance, centrality):
        return self.utility_function(fee, delay, distance, centrality)

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
            if option != None:
                fee = option['fee']
                delay = option['delay']
                centrality = option['centrality']
                distance = option['distance']
                if self.get_utility(fee, delay, distance, centrality) > best_score:
                    best = option['payment']
        return best
