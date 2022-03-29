# maybe Network should extend a class "LabeledGraph"
import numpy as np

class Network:

    def __init__(self, nr_vertices):
        self.vertices = list(range(nr_vertices))
        self.edge_id = 0
        self.edges = set()
        # maybe self.adjacency_matrix would be good for finding all paths, espicially if I call some functions recursively.
        # but then the weights can't be relative to the amount of money on the network, since in the beginning the amount would be 0.

    def add_vertex(self, vertex):
        self.vertices.append(vertex)

    def add_channel(self, idA, balA, idB, balB):
        AtoB = (self.edge_id, (idA, idB), balA)
        BtoA = (self.edge_id, (idB, idA), balB)
        self.edge_id += 1
        self.edges.add(AtoB)
        self.edges.add(BtoA)

    def has_edge(self, edge):
        return edge in self.edges

    def get_weighted_adjacency_matrix(self):
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

    # following the code from the following link (Dijkstra)
    # https://stackoverflow.com/questions/24471136/how-to-find-all-paths-between-two-graph-nodes
    def find_all_paths(self, start, end, amount, path = []):
        adjacency_matrix = self.get_weighted_adjacency_matrix()
        # or self.adjacency_matrix
        nr_vertices = len(self.vertices)
        path = path + [start]
        if start == end:
            return set(path)
        if start not in self.vertices:
            raise ValueError("start not in vertices")
        paths = set()
        for vertex in range(nr_vertices):
            if adjacency_matrix[start, vertex] >= amount and vertex not in path:
                newpaths = self.find_all_paths(vertex, end, amount, path)
                for newpath in newpaths:
                    paths.add(newpath)
        return paths

    def __eq__(self, other):
        return (self.edges == other.edges and self.vertices == other.vertices)

    # TODO: remove vertices, edges ...
