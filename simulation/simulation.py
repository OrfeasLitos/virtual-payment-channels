from abc import ABC, abstractmethod

# TODO: when this starts to get big, split classes into separate files

# TODO: move these constants inside `PlainBitcoin`
Bitcoin_money_const = 1  # Should probably be modified
Bitcoin_time_const = 3600  # 1h = 3600 seconds


# maybe Network should extend a class "LabeledGraph"
class Network:

    def __init__(self, nr_vertices):
        self.vertices = list(range(nr_vertices))
        self.edges = []

    def add_vertex(self, vertex):
        self.vertices.append(vertex)

    def add_edge(self, edge):
        self.edges.append(edge)

    # remove vertices, edges ...


class Knowledge:

    def __init__(self, party, knowledge_function):
        """
        Knowledge could be a list of payments or a probability distribution.
        Or a function as Orfeas said.
        For beginning just take the complete list of payments.
        """
        #self.knowledge = fct(party, lst_payments)  # fct has to be specified
        # or
        self.knowledge = knowledge_function
        self.party = party

    def eval(self, lst_payments):
        return (self.knowledge(self.party, lst_payments)) # TODO (also elsewhere): drop parentheses around output

    # maybe an update method


class Payment:
    """
    In this class the payment method, sender, receiver and content are specified.
    It is possible to get the cost of a transaction.
    """

    def __init__(self, payment_method, sender, receiver, content):
        # TODO: I think `payment_method` shouldn't be part of payment objects,
        #       as payments are generated at the beginning of the sim,
        #       whereas the suitable payment method is decided during the sim.
        self.payment_method = payment_method
        self.content = content
        self.sender = sender
        self.receiver = receiver
        #self.size = get_payment_size()
        self.size = 5

    #def get_payment_size(self):
    # to be done

    # TODO: Rename to `get_payment_cost()`,
    #       better keep 'transaction' for the thing that can enter Bitcoin blocks
    def get_transaction_cost(self):
        # TODO: this function should probably be in `Utility`
        #       and take, among others, a `Payment` object as input
        # TODO: `unit_money_cost` -> `fee`
        # TODO: `unit_time_cost` -> `delay`
        unit_money_cost, unit_time_cost = self.payment_method.get_unit_transaction_cost()
        return (self.size * unit_money_cost, unit_time_cost)


class PaymentMethod:
    """
    This is an abstract class so far.
    The class PlainBitcoin is derived from it.
    """
    # This method gives the cost of a transaction of fixed size.
    @abstractmethod
    def get_unit_transaction_cost(self):
        pass


class PlainBitcoin(PaymentMethod):

    def __init__(self):
        super(PlainBitcoin, self).__init__()

    def get_unit_transaction_cost(self):
        return (Bitcoin_money_const, Bitcoin_time_const)


class Utility:

    def __init__(self, function):
        self.function = function

    def evaluate(self, parameters):
        return self.function(parameters)


class Simulation:
    """
    Here the simulation takes place.

    There's an update method which is one step in the simulation.
    Running the simulation is equivalent to calling the update method as long as it's possible.
    """

    def __init__(self, nr_players, payment_lst, knowledge, utility_fct,
                 payment_method):
        self.nr_players = nr_players
        self.network = Network(None, None, self.nr_players)
        print(payment_lst)
        # maybe pop instead of iterator
        # TODO: even better, use deque and `popleft()` to maintain performance and sanity
        #       https://docs.python.org/2/library/collections.html#collections.deque
        self.payments_iterator = iter(payment_lst)
        self.knowledge = knowledge
        self.utility_fct = utility_fct
        self.payment_method = payment_method  # probably not necessary here

    # TODO: `update` -> `step` (and change doc)
    # TODO: alternatively, it may make sense to have `Simulation` be an iterator,
    #       so that we can write
    #       `for state in simulation:`
    #       and inspect the `state` at will
    def update(self):
        payment = next(self.payments_iterator, None)
        if payment == None:
            return False
        # classes Lightning,... don't exist yet.
        # normally the update should depend on the utility for the party
        if isinstance(payment.payment_method, PlainBitcoin):
            edge = (payment.payment_method, (payment.sender, payment.receiver))
            # TODO: In plain bitcoin, there won't be any real network,
            #       maybe just a dummy one.
            #       In each other payment method PM, the network will change
            #       based on what PM decides.
            self.network.add_edge(edge)
        return True

    # TODO: if we turn it into an iterator, this function won't be needed
    def run(self):
        update_possible = True
        while update_possible:
            update_possible = self.update()
        return

    # Should Simulation extend Iterator?
    # TODO: You're in my head :)
    #       It's done by defining `__iter__()` and ``__next__()` methods


if __name__ == "__main__":

    def identity_fct(x):
        return x

    def identity_2(*args):
        return args

    utility = Utility(identity_fct)
    print(utility.evaluate(5))
    bitcoin = PlainBitcoin()
    print(bitcoin.get_unit_transaction_cost())
    payment = Payment(bitcoin, 1, 3, "foo")
    print(payment.get_transaction_cost())
    payment2 = Payment(bitcoin, 0, 4, "bar")
    network = Network(None, None, 5)
    print(network.vertices, network.edges)
    edge = (bitcoin, ((1, 2)))
    network.add_edge(edge)
    print(network.vertices, network.edges)
    knowledge = Knowledge(1, identity_2)
    print(knowledge.eval([payment, payment2]))
    payment_lst = [payment, payment2]
    payment_iterator = iter(payment_lst)
    print("paymment list", payment_lst)
    simulation = Simulation(6, payment_lst, knowledge, utility, bitcoin)
    simulation.run()
    print(simulation.network.vertices, simulation.network.edges)
    print(simulation.nr_players)
