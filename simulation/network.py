# maybe Network should extend a class "LabeledGraph"
from re import S
import numpy as np
import networkx as nx

UNIT_COST = 1
# TODO: Check whether that's reasonable
# review: rename next var to `INIT_ONCHAIN_COINS` or similar
INITIAL_BALANCE_WALLET = 10000

class Network:

    def __init__(self, nr_vertices):
        self.graph = nx.empty_graph(nr_vertices, create_using=nx.DiGraph)
        self.edge_id = 0
        for vertex in range(nr_vertices):
            self.graph.nodes[vertex]['balance_wallet'] = INITIAL_BALANCE_WALLET

    def add_node(self, node):
        self.graph.add_node(node)
        # do we need this method? If we need it we need sth like a convention that a new vertex gets the number len(self.vertices).

    def add_channel(self, idA, balA, idB, balB):
        assert(balA > 0 or balB > 0)
        edges = [(idA, idB, dict({'balance': balA, 'cost' : UNIT_COST})),(idB, idA, dict({'balance': balB, 'cost' : UNIT_COST}))]
        self.graph.add_edges_from(edges)
        self.edge_id += 1

    def close_channel(self, idA, balA, idB, balB):
        assert(balA > 0 or balB > 0)
        edges = [(idA, idB, dict({'balance': balA, 'cost' : UNIT_COST})),(idB, idA, dict({'balance': balB, 'cost' : UNIT_COST}))]
        self.graph.remove_edges_from(edges)

    def find_cheapest_path(self, start, end, amount):
        self.graph.nodes[start]['amount'] = -amount
        self.graph.nodes[end]['amount'] = amount
        try:
            cost, path = nx.network_simplex(self.graph, demand='amount', capacity='balance', weight='cost')
            # cost should be number of edges - 1
            res = cost - 1, path
        except nx.NetworkXUnfeasible:
            res = None
        self.graph.nodes[start]['amount'] = 0
        self.graph.nodes[end]['amount'] = 0
        return res

    # TODO: check for sensible definition of centrality of a graph with many components or take connectedness into account in the utility
    # (to give less emphasis on the centrality in a graph with many components)
    def get_harmonic_centrality(self):
        return nx.harmonic_centrality(self.graph)

    def __eq__(self, other):
        # review: is this method tested? does networkx graph equality work as expected?
        return (self.graph == other.graph)

    # TODO: remove vertices, edges ...
