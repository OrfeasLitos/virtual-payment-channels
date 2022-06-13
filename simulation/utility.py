

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
        This method compares the utility of on-chain transactions
        with the utility of a new channel (opened on chain)
        and completely off-chain transactions and returns the best of these possibilities.
        """

        best_score = 0
        if payment_options == []:
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

    def __eq__(self, other):
        return self.utility_function == other.utility_function