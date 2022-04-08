# maybe Network should extend a class "LabeledGraph"
from re import S
import numpy as np
import networkx as nx

UNIT_COST = 1

class Network:

    def __init__(self, nr_vertices):
        self.graph = nx.empty_graph(nr_vertices, create_using=nx.DiGraph)
        self.edge_id = 0

    def add_node(self, node):
        self.graph.add_node(node)
        # do we need this method? If we need it we need sth like a convention that a new vertex gets the number len(self.vertices).

    def add_channel(self, idA, balA, idB, balB):
        assert(balA > 0 or balB > 0)
        edges = [(idA, idB, dict({'balance': balA, 'cost' : UNIT_COST})),(idB, idA, dict({'balance': balB, 'cost' : UNIT_COST}))]
        self.graph.add_edges_from(edges)
        self.edge_id += 1
    
    def find_cheapest_path(self, start, end, amount):
        self.graph.nodes[start]['amount'] = -amount
        self.graph.nodes[end]['amount'] = amount
        cost, path = nx.network_simplex(self.graph, demand='amount', capacity='balance', weight='cost')
        self.graph.nodes[start]['amount'] = 0
        self.graph.nodes[end]['amount'] = 0
        # cost should be number of edges - 1
        return cost - 1, path

    def __eq__(self, other):
        return (self.graph == other.graph)

    # TODO: remove vertices, edges ...