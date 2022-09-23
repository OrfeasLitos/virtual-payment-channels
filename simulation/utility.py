import numpy as np
import random

def sum_of_inverses_utility_function(
        add_fee, mult_fee, mult_delay, mult_distance, mult_centrality,
        fee, delay, distance, centrality
    ):
    weight_distance_array = np.array(distance)
    inverse_distance_array = 1/ weight_distance_array[:,1]
    weight_array = weight_distance_array[:,0]
    utility_fee = mult_fee/(add_fee+fee)
    utility_delay = mult_delay/delay
    utility_distance = mult_distance * np.transpose(inverse_distance_array) @ weight_array
    utility_centrality = mult_centrality * centrality
    return utility_fee + utility_delay + utility_distance + utility_centrality

class Utility:

    def __init__(self, utility_mode, personalization = None, parameters = None, utility_function = None):
        """
        Utility function should have fee, delay, centrality and distances as input
        """
        if utility_mode == 'sum_of_inverses':
            if personalization is None:
                raise ValueError
            else:
                personalization_kind, num_parties = personalization
            if personalization_kind == "same-utility":
                add_fee, mult_fee, mult_delay, mult_distance, mult_centrality = parameters[0]
                def utility_function(party, fee, delay, distance, centrality):
                    return sum_of_inverses_utility_function(
                        add_fee, mult_fee, mult_delay, mult_distance, mult_centrality,
                        fee, delay, distance, centrality
                    )
                self.utility_function = utility_function
            elif personalization_kind == "50-50":
                add_fee0, mult_fee0, mult_delay0, mult_distance0, mult_centrality0 = parameters[0]
                add_fee1, mult_fee1, mult_delay1, mult_distance1, mult_centrality1 = parameters[1]
                parties_parameters0 = []
                parties_parameters1 = []
                for party in range(num_parties):
                    if random.uniform(0, 1) < 0.5:
                        parties_parameters0.append(party)
                    else:
                        parties_parameters1.append(party)
                def utility_function(party, fee, delay, distance, centrality):
                    if party in parties_parameters0:
                        return sum_of_inverses_utility_function(
                            add_fee0, mult_fee0, mult_delay0, mult_distance0, mult_centrality0,
                            fee, delay, distance, centrality
                        )
                    else:
                        return sum_of_inverses_utility_function(
                            add_fee1, mult_fee1, mult_delay1, mult_distance1, mult_centrality1,
                            fee, delay, distance, centrality
                        )
                self.utility_function = utility_function

        elif utility_mode == 'customized':
            self.utility_function = utility_function
        else:
            raise ValueError

    def get_utility(self, party, fee, delay, distance, centrality):
        return self.utility_function(party, fee, delay, distance, centrality)

    def choose_payment_method(self, party, payment_options):
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
            utility = self.get_utility(party, fee, delay, distance, centrality)
            if utility >= best_score:
                best = (option['payment_information'], fee, delay)
                best_score = utility
        return best

    def __eq__(self, other):
        return self.utility_function == other.utility_function