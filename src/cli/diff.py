import os.path
from pathlib import Path

import click
import networkx as nx
from rich import print as rprint

from src.cli.commands import commands
from src.diff_render import Renderer
from src.dot import render_dot_file
from src.gradle import gradle_split
from src.graph_diff import compare_graph
from src.graph_file import load_graph_from_argument, ensure_diff_not_empty


@commands.command(name="diff", help="Diff two deps files or gradle -q dependencies outputs")
@click.argument("file1")
@click.argument("file2", default="")
@click.option("--output", "-o", default=None)
def cmd_diff(file1, file2, output):
    os.makedirs("output", exist_ok=True)
    if file2:
        g1 = load_graph_from_argument(file1, "output/graph1.deps")
        g2 = load_graph_from_argument(file2, "output/graph2.deps")
        g = compare_graph(g1, g2, parent_function=gradle_split)
        ensure_diff_not_empty(g)
        dot_file_path = Path("output/compare_two_graphs.dot")
        Renderer(g).gen_delta(file=dot_file_path)
    else:
        g = load_graph_from_argument(file1, "output/single_graph.deps")
        g = compare_graph(nx.DiGraph(), g, parent_function=gradle_split)
        dot_file_path = Path("output/single_graph.dot")
        Renderer(g, new_color="#000000").gen_delta(file=dot_file_path)
    output_png = Path(output) if output else dot_file_path.with_suffix(".png")
    os.makedirs(output_png.parent, exist_ok=True)
    render_dot_file(dot_file_path, output_png)
    rprint(f"Created [cyan]{output_png}[/cyan]")
