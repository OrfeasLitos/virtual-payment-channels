
def know_all_function(party, payments):
    return payments

def know_mine_function(party, payments):
    return [payment for payment in payments if payment[0] == party]

def get_know_next_n_function(n):
    # works also for empty list
    def know_next_n_function(party, payments):
        return payments[:n]
    return know_next_n_function

know_next_function = get_know_next_n_function(1)
know_next_10_function = get_know_next_n_function(10)

def get_know_my_next_n_function(n):
    def know_my_next_n_function(party, payments):
        my_payments = [payment for payment in payments if payment[0] == party]
        return my_payments[:10]
    return know_my_next_n_function

know_my_next_10_function = get_know_my_next_n_function(10)


class Knowledge:
    def __init__(self, knowledge_mode, knowledge_function = None):
        match knowledge_mode:
            case 'customized':
                self.knowledge_function = knowledge_function
            case 'know-all':
                self.knowledge_function = know_all_function
            case 'know-mine':
                self.knowledge_function = know_mine_function
            case 'know-next':
                self.knowledge_function = know_next_function
            case 'know-next-10':
                self.knowledge_function = know_next_10_function
            case 'know-my-next-10-':
                self.knowledge_function = know_my_next_10_function
            case _:
                raise ValueError


    def get_knowledge(self, party, payments):
        return self.knowledge_function(party, payments)

    def __eq__(self, other):
        return self.knowledge_function == other.knowledge_function