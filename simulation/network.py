# maybe Network should extend a class "LabeledGraph"
import numpy as np
import networkx as nx
import math

UNIT_COST = 1
# TODO: Check whether that's reasonable
INIT_ONCHAIN_COINS = 10000

class Network:

    def __init__(self, nr_vertices):
        self.graph = nx.empty_graph(nr_vertices, create_using=nx.DiGraph)
        self.edge_id = 0
        for vertex in range(nr_vertices):
            self.graph.nodes[vertex]['balance_wallet'] = INIT_ONCHAIN_COINS

    def add_node(self, node):
        self.graph.add_node(node)
        # do we need this method? If we need it we need sth like a convention that a new vertex gets the number len(self.vertices).

    def add_channel(self, idA, balA, idB, balB):
        assert(balA > 0 or balB > 0)
        edges = [(idA, idB, dict({'balance': balA, 'cost' : UNIT_COST})),(idB, idA, dict({'balance': balB, 'cost' : UNIT_COST}))]
        self.graph.add_edges_from(edges)
        self.edge_id += 1

    def close_channel(self, idA, idB):
        edges = [(idA, idB) ,(idB, idA)]
        self.graph.remove_edges_from(edges)

    def get_weight_function(self, amount):
        """
        This function returns the weight function we use in the following.
        The balance acts as a threshold. If the amount is bigger than the balance the weight is math.inf, otherwise it is 1.
        """
        # TODO: Check whether higher order functions make some optimizations harder.
        def weight_function(sender, receiver, edge_attributes):
            if edge_attributes['balance'] >= amount:
                return 1
            else:
                return math.inf
        
        return weight_function

    def find_cheapest_path(self, start, end, amount):
        # maybe the output of this function should be modified.
        # TODO: find_cheapest_path doesn't work yet as expected.
        self.graph.nodes[start]['amount'] = -amount
        self.graph.nodes[end]['amount'] = amount
        try:
            cost, path = nx.network_simplex(self.graph, demand='amount', capacity='balance', weight='cost')
            # cost should be number of edges - 1. The cost of the simplex algorithm is per unit of amount, so we have to divide by amount
            res = cost/amount - 1, path
        except nx.NetworkXUnfeasible:
            res = None
        self.graph.nodes[start]['amount'] = 0
        self.graph.nodes[end]['amount'] = 0
        return res

    # TODO: check for sensible definition of centrality of a graph with many components or take connectedness into account in the utility
    # (to give less emphasis on the centrality in a graph with many components)
    def get_harmonic_centrality(self):
        return nx.harmonic_centrality(self.graph)

    # TODO: check for sensible definition of centrality of a graph with many components or take connectedness into account in the utility
    # (to give less emphasis on the centrality in a graph with many components)
    def get_harmonic_centrality(self):
        return nx.harmonic_centrality(self.graph)

    def __eq__(self, other):
        # review: is this method tested? does networkx graph equality work as expected?
        return (self.graph == other.graph)

    # TODO: remove vertices, edges ...
