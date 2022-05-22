

class Knowledge:
    def __init__(self, party, payments, knowledge_function):
        """
        Knowledge could be a list of payments or a probability distribution.
        Or a function as Orfeas said.
        For beginning just take the complete list of payments.
        """
        self.party = party
        self.payments = payments
        self.knowledge_function = knowledge_function


    def get_knowledge(self):
        return self.knowledge_function(self.party, self.payments)

    def __eq__(self, other):
        # review: this is my favorite style, if you like this try to apply this everywhere:
        # return (
        #     self.party == other.party
        #     and self.payments == other.payments
        #     and self.knowledge_function == other.knowledge_function
        # )
        # review: note that the parentheses are redundant and the first clause could also go to the `return` line
        return (
            self.party == other.party
            and self.payments == other.payments
            and self.knowledge_function == other.knowledge_function
        )