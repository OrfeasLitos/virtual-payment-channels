import paymentmethod
import knowledge

class Utility:

    def __init__(self, utility_function):
        """
        Utility function should have cost, time and knowledge as input
        """
        self.utility_function = utility_function

    # Should there also be a payment?
    def get_payment_time(self, payment_method):
        return payment_method.delay

    def get_payment_cost(self, payment, payment_method):
        """
        payment is a tuple (sender, receiver, value).
        """
        value = payment[2]
        return value * payment_method.fee
    
    def get_utility(self, payment, payment_method, knowledge):
        return self.utility_function(self.get_payment_cost(payment, payment_method), self.get_payment_time(payment_method), knowledge.get_knowledge())

    def compare_utilites(self, payment, payment_method, knowledge, network):
        """
        This method should compare the utility of on-chain transactions with the utility of a new channel (opened on chain) and completely off-chain transactions and should
        returns the best of these possibilities.
        """
        # There should be if's to calculate utilities and check whether to make a plain bitcoin transaction, open a new channel on chain or do everything off-chain (for Lightning)
        # For other protocols similarly.

        # The last argument "network" could maybe be replaced by the length of the shortest path (e.g. for LN, where time and fee depend only on the length of the path)
        # but for now I used greater generality. Also this has the advantage that we can call find_shortest_path here and don't have to do it in the simulation.

        sender, receiver, value = payment
        try:
            cost, shortest_path = self.network.find_cheapest_path(sender, receiver, value)
            

        except Exception:
            pass
