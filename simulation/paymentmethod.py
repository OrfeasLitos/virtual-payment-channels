from abc import ABC, abstractmethod

class PaymentMethod:
    """
    This is an abstract class so far.
    The class PlainBitcoin is derived from it.
    """
    MAX_COINS = None
    fee = None
    delay = None
    # This method gives the cost of a transaction of fixed size.
    @abstractmethod
    def get_unit_transaction_cost(self):
        pass

    # Should there also be a payment?
    def get_payment_time(self, path=None):
        return self.delay

    def get_payment_cost(self, payment, path=None):
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
    
    def compare_utilites(self, utility, payment, knowledge):
        # This says that in the class PlainBitcoin PlainBitcoin is always the best (since only) way. Should this be string or some other object?
        # I suspect this function will need to be moved/changed. For now I changed its return value to number so that the set() hash is deterministic (strings result in non-deterministic hashing)
        return 0

class LN(PaymentMethod):
    MAX_COINS = 1000000
    # This is just for sake of having fees and time. TODO: look up actual fees and time
    fee = 0.001
    delay = 0.05
    # maybe there's a better name than base fee and fee.
    # With base fee I mean the part of the fee that has to be payed for every transaction and with fee the part of the fee that depends on the number of intermediaries.
    base_fee = 0.01

    def get_payment_time(self, path):
        time = self.delay * (len(path) - 1)
        return time
    
    def get_payment_cost(self, payment, path):
        # TODO: check if cost in reality depends on the payment or just on the path in the network
        payment_fee = self.base_fee + self.fee * (len(path) - 1)
        return payment_fee