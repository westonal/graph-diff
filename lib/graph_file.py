import re

import networkx as nx

from lib.error import fail


def load_graph(input_file: str):
    with open(input_file, "r") as file:
        lines = file.readlines()
        return load_graph_from_lines(lines)


def load_graph_from_lines(lines):
    graph = nx.DiGraph()
    for line in lines:
        search = re.search(r"(\S*) -> (\S*)", line)
        if not search:
            fail("[red]Malformed input [line]")
        u = search.group(1)
        v = search.group(2)
        graph.add_edge(u, v)
    return graph
