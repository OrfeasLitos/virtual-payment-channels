# maybe Network should extend a class "LabeledGraph"
import numpy as np
import networkx as nx

class Network:

    def __init__(self, nr_vertices):
        self.multigraph = nx.empty_graph(nr_vertices, create_using=nx.MultiDiGraph)
        self.edge_id = 0


    def add_node(self, node):
        self.multigraph.add_node(node)
        # do we need this method? If we need it we need sth like a convention that a new vertex gets the number len(self.vertices).

    def add_channel(self, idA, balA, idB, balB):
        self.multigraph.add_weighted_edges_from([(idA, idB, balA)], weight = "balanceSender", edge_id = self.edge_id)
        self.multigraph.add_weighted_edges_from([(idB, idA, balB)], weight = "balanceSender", edge_id = self.edge_id)
        self.edge_id += 1
        

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
