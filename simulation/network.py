# maybe Network should extend a class "LabeledGraph"
import math
import networkx as nx


UNIT_COST = 1

class Network:

    def __init__(self, nr_vertices):
        self.graph = nx.empty_graph(nr_vertices, create_using=nx.DiGraph)
        self.edge_id = 0

    def get_new_edges(self, idA, balA, idB, balB, method_data):
        assert(balA > 0 or balB > 0)
        edges = [
            (idA, idB, {'balance': balA, 'cost' : UNIT_COST}),
            (idB, idA, {'balance': balB, 'cost' : UNIT_COST})
        ]
        return edges

    def add_channel(self, idA, balA, idB, balB, method_data = None):
        edges = self.get_new_edges(idA, balA, idB, balB, method_data)
        self.graph.add_edges_from(edges)
        self.edge_id += 1

    def close_channel(self, idA, idB):
        edges = [(idA, idB) ,(idB, idA)]
        self.graph.remove_edges_from(edges)

    def get_weight_function(self, amount):
        """
        This function returns the weight function we use in the following.
        The balance acts as a threshold.
        If the amount is bigger than the balance the weight is math.inf, otherwise it is 1.
        """
        # TODO: Check whether higher order functions make some optimizations harder.
        def weight_function(sender, receiver, edge_attributes):
            if edge_attributes['balance'] >= amount:
                return 1
            return math.inf
        return weight_function

    def find_cheapest_path(self, sender, receiver, amount, fee_intermediary):
        try:
            weight_function = self.get_weight_function(amount)
            cheapest_path = nx.shortest_path(self.graph, sender, receiver, weight_function)
            # this is a check that the cheapest path really can be used for a transaction
            # (cheapest path could still have distance math.inf)
            for i in range(len(cheapest_path)-1):
                sender = cheapest_path[i]
                receiver = cheapest_path[i+1]
                if self.graph.get_edge_data(sender, receiver)['balance'] < amount + (len(cheapest_path) - 1) * fee_intermediary:
                    return None
            return len(cheapest_path) - 1, cheapest_path
        except nx.exception.NetworkXNoPath:
            return None

    def get_harmonic_centrality(self):
        return nx.harmonic_centrality(self.graph)

# review: why do we need a separate Network class for Elmo?
class Network_Elmo(Network):
    def __init__(self, nr_vertices):
        super().__init__(nr_vertices)

    def get_new_edges(self, idA, balA, idB, balB, path):
        assert(balA > 0 or balB > 0)
        edges = [
            (idA, idB,
                {'balance': balA, 'locked_coins' : 0, 'cost' : UNIT_COST,
                'channels_underneath' : path, 'channels_above': []}
            ),
            # Question: should I reverse path here?
            # review: leave it like this for now, we can reverse it if needed later
            (idB, idA,
                {'balance': balB, 'locked_coins' : 0, 'cost' : UNIT_COST,
                'channels_underneath' : path, 'channels_above': []}
            )
        ]
        return edges

    def add_channel(self, idA, balA, idB, balB, path):
        edges = self.get_new_edges(idA, balA, idB, balB, path)
        self.graph.add_edges_from(edges)
        
        if path is not None:
            for i in range(len(path) - 1):
                sender = path[i]
                receiver = path[i+1]
                # TODO: think if pair is ok here or if we want all the information of the channels to be stored.
                # review: let's update this on an as-needed basis
                self.graph[sender][receiver]['channels_above'].append((idA, idB))
                self.graph[receiver][sender]['channels_above'].append((idA, idB))
        self.edge_id += 1
