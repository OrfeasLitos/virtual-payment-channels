from abc import ABC, abstractmethod

# review: each class that inherits from PaymentMethod should be able to return a payment method, ready to be compared against others by Utility
class PaymentMethod:
    """
    This is an abstract class so far.
    The class PlainBitcoin is derived from it.
    """
    MAX_COINS = None
    fee = None
    delay = None
    # TODO: check how to handle the PlainBitcoin case as there is no opening transaction.
    opening_transaction_size = None
    # This method gives the cost of a transaction of fixed size.
    @abstractmethod
    def get_unit_transaction_cost(self):
        pass

    # Should there also be a payment?
    def get_payment_time(self, path=None):
        return self.delay

    def get_payment_fee(self, payment, path=None):
        """
        payment is a tuple (sender, receiver, value).
        """
        value = payment[2]
        return value * self.fee

class PlainBitcoin(PaymentMethod):
    MAX_COINS = 1000000
    fee = 1  # Should probably be modified
    delay = 3600  # 1h = 3600 seconds
    def __init__(self):
        super(PlainBitcoin, self).__init__()

    def get_unit_transaction_cost(self):
        return (self.fee, self.delay)
    
    # review: IIUC, this method is now obsolete
    def compare_utilites(self, utility, payment, knowledge):
        # This says that in the class PlainBitcoin PlainBitcoin is always the best (since only) way. Should this be string or some other object?
        # I suspect this function will need to be moved/changed. For now I changed its return value to number so that the set() hash is deterministic (strings result in non-deterministic hashing)
        return 0

# review: this class should return an off-chain payment method (if any is found) and an open-new-channel payment method
class LN(PaymentMethod):
    MAX_COINS = 1000000
    # This is just for sake of having fees and time. TODO: look up actual fees and time
    fee = 0.001
    delay = 0.05
    # This is for opening a new channel, TODO: look up real value
    opening_transaction_size = 1
    # maybe there's a better name than base fee and fee.
    # With base fee I mean the part of the fee that has to be payed for every transaction and with fee the part of the fee that depends on the number of intermediaries.
    base_fee = 0.01

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