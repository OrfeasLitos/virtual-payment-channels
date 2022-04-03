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

    def get_weighted_adjacency_list(self):
        # the i-th element of the adjacency list is the list of vertices adjacent to vertex i. Could also be a dict or deque.
        # Maybe it would be convenient to be able to access all edges going from A to B at once, i.e to have sth like adjacency_list[idA][idB] to be a list of tuples (edge_id, balA).
        adjacency_list = [[] for i in range(len(self.vertices))]
        for edge in self.edges:
            edge_id, ids_parties, balA = edge
            idA, idB = ids_parties
            adjacency_list[idA].append((idB, edge_id, balA))
        return adjacency_list

    # following the code from the following link (Dijkstra)
    # https://stackoverflow.com/questions/24471136/how-to-find-all-paths-between-two-graph-nodes
    # TODO: find library function that does this for us
    def find_all_paths(self, start, end, amount, path = []):
        # TODO: use adjacency_list or simply directly self.edges (2nd option slower)
        adjacency_matrix = self.get_weighted_adjacency_matrix()
        # or self.adjacency_matrix
        nr_vertices = len(self.vertices)
        path = path + [start]
        if start == end:
            return set(path)
        # TODO: remove the next if, if we're too slow
        if start not in self.vertices:
            raise ValueError("start not in vertices")
        paths = set()
        # TODO: use adjacency_list
        for vertex in range(nr_vertices):
            if adjacency_matrix[start, vertex] >= amount and vertex not in path:
                newpaths = self.find_all_paths(vertex, end, amount, path)
                for newpath in newpaths:
                    paths.add(newpath)
        return paths

    def __eq__(self, other):
        return (self.edges == other.edges and self.vertices == other.vertices)

    # TODO: remove vertices, edges ...
