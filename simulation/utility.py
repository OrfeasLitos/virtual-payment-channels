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
    def compare_utilities(self, payment, payment_method, knowledge, shortest_path):
        """
        This method should compare the utility of on-chain transactions with the utility of a new channel (opened on chain) and completely off-chain transactions and should
        returns the best of these possibilities.
        Returns 0 for off-chain, 1 for new channel, 2 for PlainBitcoin
        """
        # There should be if's to calculate utilities and check whether to make a plain bitcoin transaction, open a new channel on chain or do everything off-chain (for Lightning)
        # For other protocols similarly.

        # The last argument "shortest_path" could maybe be replaced by the length of the shortest path (e.g. for LN, where time and fee depend only on the length of the path)
        # but for now I used greater generality. Also this has the advantage that we can call find_shortest_path here and don't have to do it in the simulation.

        sender, receiver, value = payment
        off_chain_utility = self.get_utility(payment, payment_method, knowledge, shortest_path)
        plain_bitcoin = PlainBitcoin()
        opening_transaction_fee = plain_bitcoin.get_payment_fee(payment_method.opening_transaction_size)
        # TODO: probably the fee of the opening transaction shouldn't go to the receiver. Check how to handle the fee for opening a new channel.
        # But for the utility of the sender one could pretend the money goes to the receiver (as done in the next line).
        opening_transaction = (sender, receiver, opening_transaction_fee)
        new_channel_utility = self.get_utility(opening_transaction, plain_bitcoin, knowledge)
        plain_bitcoin_utility = self.get_utility(payment, plain_bitcoin, knowledge)
        if new_channel_utility >= off_chain_utility and new_channel_utility >= plain_bitcoin_utility:
            return 1
        elif off_chain_utility >= new_channel_utility and off_chain_utility >= plain_bitcoin_utility:
            return 0
        else:
            return 2
