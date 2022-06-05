

class Knowledge:
    def __init__(self, knowledge_function):
        self.knowledge_function = knowledge_function


    def get_knowledge(self, party, payments):
        return self.knowledge_function(party, payments)

    def __eq__(self, other):
        return self.knowledge_function == other.knowledge_function