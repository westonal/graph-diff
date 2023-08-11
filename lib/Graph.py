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


@attr.s(frozen=True, auto_attribs=True)
class Edge(object):
    a: str
    b: str

    def __str__(self):
        return f"{self.a} -> {self.b}"
