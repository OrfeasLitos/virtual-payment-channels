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

    def get_adjacency_matrix(self):
        # edge is just a set of vertices
        nr_vertices = len(self.vertices)
        adjacency_matrix = np.zeros((nr_vertices, nr_vertices))
        for vertex1 in self.vertices:
            for vertex2 in self.vertices:
                if set(vertex1, vertex2) in self.edges:
                    adjacency_matrix[vertex1, vertex2] = 1
        return adjacency_matrix

    def __eq__(self, other):
        return (self.edges == other.edges and self.vertices == other.vertices)

    # TODO: remove vertices, edges ...
