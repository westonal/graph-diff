import re
from pathlib import Path

import networkx as nx
from rich import print as rprint

from src.error import fail
from src.gradle import project_dependencies_to_deps


def load_graph(input_file: str):
    with open(input_file, "r") as file:
        lines = file.readlines()
        return load_graph_from_deps_lines(lines)


def load_graph_from_deps_lines(lines):
    graph = nx.DiGraph()
    for line in lines:
        search = re.search(r"^(\S*)((?: -> \S*)*)", line)
        if not search:
            fail("[red]Malformed input [line]")
        u = search.group(1)
        vs = search.group(2)
        if not vs:
            graph.add_node(u)
        else:
            all_v = re.findall(r"(?: -> )(\S*)", vs)
            for v in all_v:
                graph.add_edge(u, v)
                u = v

    return graph


def load_graph_from_argument(input_file: str, output_file: str):
    if Path(input_file).suffix == ".deps":
        return load_graph(input_file=input_file)
    else:
        project_dependencies_to_deps(input_file=input_file, output_file=output_file)
        return load_graph(input_file=output_file)


def ensure_diff_not_empty(g):
    if len(g.nodes) == 0:
        rprint("[yellow]No differences to render")
        exit(0)
