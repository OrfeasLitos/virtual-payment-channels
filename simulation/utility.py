import numpy as np

class Utility:

    def __init__(self, utility_mode, utility_function = None, parameters  = None):
        """
        Utility function should have fee, delay, centrality and distances as input
        """
        match utility_mode:
            case 'sum_of_inverses':
                add_fee, mult_fee, mult_delay, mult_distance, mult_centrality = parameters
                def utility_function(fee, delay, distance, centrality):
                    weight_distance_array = np.array(distance)
                    inverse_distance_array = 1/ weight_distance_array[:,1]
                    weight_array = weight_distance_array[:,0]
                    return (
                        mult_fee/(add_fee+fee) +
                        mult_delay/delay +
                        mult_distance * np.transpose(inverse_distance_array) @ weight_array +
                        mult_centrality * centrality
                    )
                self.utility_function = utility_function
            case 'customized':
                self.utility_function = utility_function
            case _:
                raise ValueError

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
                best = (option['payment_information'], fee, delay)
                best_score = utility
        return best

    def __eq__(self, other):
        return self.utility_function == other.utility_function