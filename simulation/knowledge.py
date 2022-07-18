
def know_all_function(party, payments):
    return payments

class Knowledge:
    def __init__(self, knowledge_mode, knowledge_function = None):
        match knowledge_mode:
            case 'customized':
                self.knowledge_function = knowledge_function
            case 'know-all':
                self.knowledge_function = know_all_function
            # ...
            case _:
                raise ValueError


    def get_knowledge(self, party, payments):
        return self.knowledge_function(party, payments)

    def __eq__(self, other):
        return self.knowledge_function == other.knowledge_function