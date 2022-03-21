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
