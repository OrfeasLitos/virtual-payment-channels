# maybe Network should extend a class "LabeledGraph"
import numpy as np

class Network:

    def __init__(self, nr_vertices):
        self.vertices = list(range(nr_vertices))

        self.edges = set()

    def add_vertex(self, vertex):
        self.vertices.append(vertex)

    def add_edge(self, edge):
        self.edges.add(edge)

    def has_edge(self, edge):
        return edge in self.edges

    def get_weighted_adjacency_matrix(self):
        # what should an edge be? Maybe for parties a, b with a < b a 3-tuple (set({a, b}), money of a on channel, money of b on channel)
        # in this way we can identify the balance for each party and still have some symmetry (in that we don't need (a,b) and (b,a))
        # Doesn't seem that elegant yet.
        nr_vertices = len(network.vertices)
        weighted_adjacency_matrix = np.zeros((nr_vertices, nr_vertices))
        money_on_network = 0
        for edge in self.edges:
            parties, balance_a, balance_b = edge
            a, b = parties
            # the if is not necessary if we are only interested in the sum of the balances.
            if a >= b:
                tmp = a
                a = b
                b = tmp
            weighted_adjacency_matrix[a, b] = weighted_adjacency_matrix[b,a] = balance_a + balance_b
            money_on_network += balance_a + balance_b
        # This is for the case that the weight should be relative to the overall amount on the network. Otherwise not necessary.
        # The exception is for the case that no money is on the network, i.e. division by zero
        try:
            for i in range(nr_vertices):
                for j in range(nr_vertices):
                    weighted_adjacency_matrix[i, j] = weighted_adjacency_matrix / money_on_network
        except ZeroDivisionError:
            raise Exception("There needs to be money on at least one channel")
    
    def __eq__(self, other):
        return (self.edges == other.edges and self.vertices == other.vertices)

    # TODO: remove vertices, edges ...
