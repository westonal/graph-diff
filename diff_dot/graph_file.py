from pathlib import Path

from networkx.classes import DiGraph
from rich import print as rprint

from .dependencies import Dependencies
from .gradle import project_dependencies_to_deps


def load_graph(input_file: str) -> DiGraph:
    with open(input_file, "r") as file:
        lines = file.readlines()
        return load_graph_from_deps_lines(lines)


def load_graph_from_deps_lines(lines) -> DiGraph:
    dependencies = Dependencies()
    dependencies.add_lines(lines)
    return dependencies.to_digraph()


def load_graph_from_argument(input_file: str, output_file: str) -> DiGraph:
    if Path(input_file).suffix == ".deps":
        return load_graph(input_file=input_file)
    else:
        project_dependencies_to_deps(input_file=input_file, output_file=output_file)
        return load_graph(input_file=output_file)


def ensure_diff_not_empty(g):
    if len(g.nodes) == 0:
        rprint("[yellow]No differences to render")
        exit(0)
