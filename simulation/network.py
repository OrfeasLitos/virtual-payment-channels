# maybe Network should extend a class "LabeledGraph"
from re import S
import numpy as np
import networkx as nx

UNIT_COST = 1

class Network:

    def __init__(self, nr_vertices):
        # TODO: change multigraph to graph
        self.multigraph = nx.empty_graph(nr_vertices, create_using=nx.DiGraph)
        self.edge_id = 0

    def add_node(self, node):
        self.multigraph.add_node(node)
        # do we need this method? If we need it we need sth like a convention that a new vertex gets the number len(self.vertices).

    def add_channel(self, idA, balA, idB, balB):
        assert(balA > 0 or balB > 0)
        edges = [(idA, idB, dict({'balance': balA, 'cost' : UNIT_COST})),(idB, idA, dict({'balance': balB, 'cost' : UNIT_COST}))]
        self.multigraph.add_edges_from(edges)
        self.edge_id += 1
        
    def __eq__(self, other):
        return (self.edges == other.edges and self.vertices == other.vertices)

    # TODO: remove vertices, edges ...