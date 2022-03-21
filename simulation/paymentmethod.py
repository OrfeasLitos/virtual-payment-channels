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

    @abstractmethod
    def compare_utilites(self, utility, payment, knowledge):
        """
        This method should compare the utility of on-chain transactions with the utility of a new channel (opened on chain) and completely off-chain transactions and should
        returns the best of these possibilities.
        """
        # There should be if's to calculate utilities and check whether to make a plain bitcoin transaction, open a new channel on chain or do everything off-chain (for Lightning)
        # For other protocols similarly.
        pass

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
        return "PlainBitcoin"