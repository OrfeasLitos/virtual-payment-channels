
def know_all_function(party, payments):
    return payments

def know_mine_function(party, payments):
    return [payment for payment in payments if payment[0] == party]

def know_next_function(party, payments):
    # works also for empty list
    return payments[:1]

class Knowledge:
    def __init__(self, knowledge_mode, knowledge_function = None):
        match knowledge_mode:
            case 'customized':
                self.knowledge_function = knowledge_function
            case 'know-all':
                self.knowledge_function = know_all_function
            case 'know-mine':
                self.knowledge_function = know_mine_function
            case 'know_next':
                self.knowledge_function = know_next_function
            case _:
                raise ValueError


    def get_knowledge(self, party, payments):
        return self.knowledge_function(party, payments)

    def __eq__(self, other):
        return self.knowledge_function == other.knowledge_function