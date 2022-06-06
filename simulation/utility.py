

class Utility:

    def __init__(self, utility_function):
        """
        Utility function should have fee, delay, centrality and distances as input
        """
        self.utility_function = utility_function

    def get_utility(self, fee, delay, distance, centrality):
        return self.utility_function(fee, delay, distance, centrality)

    def choose_payment_method(self, payment_options):
        """
        This method should compare the utility of on-chain transactions
        with the utility of a new channel (opened on chain)
        and completely off-chain transactions and should return the best of these possibilities.
        Returns 0 for off-chain, 1 for new channel, 2 for PlainBitcoin
        """

        best_score = 0
        if payment_options is []:
            raise ValueError
        for option in payment_options:
            fee = option['fee']
            delay = option['delay']
            centrality = option['centrality']
            distance = option['distance']
            utility = self.get_utility(fee, delay, distance, centrality)
            if utility >= best_score:
                best = option['payment_information']
                best_score = utility
        return best
