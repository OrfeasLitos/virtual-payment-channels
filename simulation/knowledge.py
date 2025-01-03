import collections
import itertools

def get_mine(party, payments):
    return collections.deque([payment for payment in payments if payment[0] == party])

def know_mine(party, payments):
    my_payments = get_mine(party, payments)
    return my_payments, len(my_payments), len(payments)

def know_all(party, payments):
    return payments, len(get_mine(party, payments)), len(payments)

def get_know_next_n(n):
    # works also for empty list
    def know_next_n(party, payments):
        return (
            collections.deque(itertools.islice(payments, 0, n)),
            len(get_mine(party, payments)), len(payments)
        )
    return know_next_n

know_next = get_know_next_n(1)
know_next_10 = get_know_next_n(10)

def get_know_my_next_n(n):
    def know_my_next_n(party, payments):
        my_payments = [payment for payment in payments if payment[0] == party]
        return (
            collections.deque(my_payments[:n]),
            len(get_mine(party, payments)), len(payments)
        )
    return know_my_next_n

know_my_next_10 = get_know_my_next_n(10)

class Knowledge:
    def __init__(self, knowledge_mode, knowledge_function = None):
        if knowledge_mode == 'customized':
            self.knowledge_function = knowledge_function
        elif knowledge_mode == 'all':
            self.knowledge_function = know_all
        elif knowledge_mode == 'mine':
            self.knowledge_function = know_mine
        elif knowledge_mode == 'next':
            self.knowledge_function = know_next
        elif knowledge_mode == '10-next':
            self.knowledge_function = know_next_10
        elif knowledge_mode == '10-next-mine':
            self.knowledge_function = know_my_next_10
        elif knowledge_mode == '100-next-mine':
            self.knowledge_function = get_know_my_next_n(100)
        else:
            raise ValueError


    def get_knowledge(self, party, payments):
        return self.knowledge_function(party, payments)

    def __eq__(self, other):
        return self.knowledge_function == other.knowledge_function
