from abc import ABC, abstractmethod
from network import Network

# review: each class that inherits from PaymentMethod should be able to return a payment method, ready to be compared against others by Utility

class PlainBitcoin():
    # TODO: check for reasonable default values
    def __init__(self, MAX_COINS = 1000000, fee = 1, delay = 3600):
        self.MAX_COINS = MAX_COINS
        self.fee = fee
        self.delay = delay

    def get_unit_transaction_cost(self):
        return (self.fee, self.delay)


# review: this class should return an off-chain payment method (if any is found) and an open-new-channel payment method
class LN(PlainBitcoin):
    # TODO: look up reasonable default values
    def __init__(self, nr_players, MAX_COINS = 1000000, fee = 0.001, delay = 0.05, opening_transaction_size = 1, base_fee = 0.01):
        self.MAX_COINS = MAX_COINS
        self.fee = fee
        self.delay = delay
        self.opening_transaction_size = opening_transaction_size
        self.base_fee = base_fee
        self.network = Network(nr_players)

    def get_payment_time(self, path):
        # review:
        #  * the next should be `len(path)` (without `- 1`), since even an 1-hop payment has this delay
        #  * no need to assign to `time`, just return directly
        time = self.delay * (len(path) - 1)
        return time
    
    def get_payment_fee(self, payment, path):
        # TODO: check if cost in reality depends on the payment or just on the path in the network
        # for PlainBitcoin it probably depends on the payment so I need the argument payment here.
        # review: the next comment is a good point. Let's add a test to ensure equality and if it is always equal, we can just use the fastest
        # cost actually should not depend on the path, but just on the length of the path, so we could use the cost_output of the method find cheapest path
        # which should actually be len(path) - 1
        # review:
        #   * the base_fee should be payed for each hop and the fee should be additionally multiplied with the payment value
        #   * no need to assign to `payment_fee`, just return directly
        payment_fee = self.base_fee + self.fee * (len(path) - 1)
        return payment_fee