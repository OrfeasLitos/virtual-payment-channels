import collections
import itertools

def know_all(party, payments):
    return payments

def know_mine(party, payments):
    return collections.deque([payment for payment in payments if payment[0] == party])

def get_know_next_n(n):
    # works also for empty list
    def know_next_n(party, payments):
        return collections.deque(itertools.islice(payments, 0, n))
    return know_next_n

know_next = get_know_next_n(1)
know_next_10 = get_know_next_n(10)

def get_know_my_next_n(n):
    def know_my_next_n(party, payments):
        my_payments = [payment for payment in payments if payment[0] == party]
        return collections.deque(my_payments[:n])
    return know_my_next_n

know_my_next_10 = get_know_my_next_n(10)


class Knowledge:
    def __init__(self, knowledge_mode, knowledge_function = None):
        match knowledge_mode:
            case 'customized':
                self.knowledge_function = knowledge_function
            case 'all':
                self.knowledge_function = know_all
            case 'mine':
                self.knowledge_function = know_mine
            case 'next':
                self.knowledge_function = know_next
            case '10-next':
                self.knowledge_function = know_next_10
            case '10-next-mine':
                self.knowledge_function = know_my_next_10
            case _:
                raise ValueError


    def get_knowledge(self, party, payments):
        return self.knowledge_function(party, payments)

    def __eq__(self, other):
        return self.knowledge_function == other.knowledge_function