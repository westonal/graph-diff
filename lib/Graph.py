from typing import Set

import attr


class Graph(object):
    def __init__(self):
        self._edges = set()
        self._nodes = set()

    def add_edge(self, edge):
        self._edges.update({edge})
        self._nodes.update({edge.a, edge.b})

    @property
    def edges(self):
        return set(self._edges)

    @property
    def nodes(self):
        return set(self._nodes)

    def __str__(self):
        return f"Graph with {len(self.nodes)} nodes and {len(self.edges)} edges"

    def compare_graph(self, newer):
        """Self is the older graph, and this compares to a newer graph, the output is only changed edges and affected
        nodes"""
        older = self
        new_edges = newer.edges - older.edges
        removed_edges = older.edges - newer.edges
        graph = Graph()
        for edge in new_edges:
            graph.add_edge(edge)
        for edge in removed_edges:
            graph.add_edge(edge)
        return GraphDelta(graph=graph, new_edges=new_edges,
                          removed_edges=removed_edges,
                          new_nodes=newer.nodes - older.nodes,
                          removed_nodes=older.nodes - newer.nodes)


@attr.s(frozen=True, auto_attribs=True)
class GraphDelta(object):
    graph: Graph
    new_edges: Set
    removed_edges: Set
    new_nodes: Set
    removed_nodes: Set
    #
    #
    # def __init__(self):
    # pass


@attr.s(frozen=True, auto_attribs=True)
class Edge(object):
    a: str
    b: str

    def __str__(self):
        return f"{self.a} -> {self.b}"
