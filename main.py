import os.path
import re

from gvgen import GvGen
from rich import print as rprint, inspect

import networkx as nx


def dependencies_to_graph(input_file: str, output_file: str):
    # file = "~/signal-deps.txt"
    stack = []
    with open(os.path.expanduser(input_file)) as file:
        with open(output_file, "w") as output:
            for line in file.readlines():
                if not stack:
                    app = re.search("Project '([^']*)'", line)
                    if app:
                        stack.append(app.group(1))
                else:
                    search = re.search(r"((?:[\\| ]    |[\\+]--- )*)project ([^ \n]*)", line)
                    if search:
                        module = search.group(2)
                        depth = len(search.group(1)) // 5
                        while len(stack) > depth:
                            stack.pop()
                        top = stack[len(stack) - 1]
                        stack.append(module)
                        rprint(f"{top} -> {module}", file=output)


def load_graph(input_file: str):
    graph = nx.DiGraph()
    with open(input_file, "r") as file:
        for line in file.readlines():
            search = re.search(r"(\S*) -> (\S*)", line)
            if not search:
                rprint("[red]Malformed input [line]")
            node_a = search.group(1)
            node_b = search.group(2)
            rprint(f"[cyan]{node_a}[/cyan] depends on [cyan]{node_b}[/cyan]")
            graph.add_edge(node_a, node_b)
    rprint(graph)
    return graph


def gen(graph: nx.DiGraph):
    dot = GvGen()
    nodes = {}
    for node in graph.nodes:
        nodes[node] = dot.newItem(node)
    for edge in graph.edges:
        dot.newLink(nodes[edge[0]], nodes[edge[1]])
    with open("output/graph.dot", "w") as file:
        dot.dot(file)


def gen_delta(graph_delta: nx.Graph, new_color="#158510", old_color="#ff0000"):
    dot = GvGen()
    dot.styleDefaultAppend("shape", "rectangle")
    graph = graph_delta
    nodes = {}
    new_nodes = graph.nodes(data="new", default=False)
    old_nodes = graph.nodes(data="old", default=False)
    for node in sorted(graph.nodes):
        dot_node = dot.newItem(node)
        nodes[node] = dot_node
        color = None
        if new_nodes[node]:
            color = new_color
        elif old_nodes[node]:
            color = old_color
        if color:
            dot.propertyAppend(dot_node, "color", color)
            dot.propertyAppend(dot_node, "fontcolor", color)
    for u, v, data in graph.edges.data():
        link = dot.newLink(nodes[u], nodes[v])
        color = None
        if data.get("new"):
            color = new_color
        elif data.get("old"):
            color = old_color
        if color:
            dot.propertyAppend(link, "color", color)
        if data.get("indirect"):
            dot.propertyAppend(link, "style", "dashed")
    with open("output/graph.dot", "w") as file:
        dot.dot(file)


def compare_graph(older, newer):
    """Self is the older graph, and this compares to a newer graph, the output is only changed edges and affected
    nodes"""
    new_edges = newer.edges - older.edges
    removed_edges = older.edges - newer.edges
    graph = nx.DiGraph()
    visible_nodes = set()
    for u, v in new_edges:
        graph.add_edge(u, v)
        graph.edges[u, v]["new"] = True
        visible_nodes.update({u, v})
    for u, v in removed_edges:
        graph.add_edge(u, v)
        graph.edges[u, v]["old"] = True
        visible_nodes.update({u, v})
    new_nodes = newer.nodes - older.nodes
    for new_node in new_nodes:
        graph.nodes[new_node]["new"] = True
    old_nodes = older.nodes - newer.nodes
    for old_node in old_nodes:
        graph.nodes[old_node]["old"] = True
    # Add edges for all affected nodes with indirect connections
    pairs = dict(nx.all_pairs_bellman_ford_path_length(newer))
    rprint(pairs)
    for u in visible_nodes:
        for v in visible_nodes:
            if ((pairs.get(u) or {}).get(v) or 0) > 1:
                graph.add_edge(u, v)
                graph.edges[u, v]["indirect"] = True

    return graph


def main():
    dependencies_to_graph(input_file="output/dependencies.txt", output_file="output/sample.deps")
    g = load_graph(input_file="examples/revision1.deps")
    gen_delta(g)

    g1 = load_graph(input_file="examples/revision1.deps")
    g2 = load_graph(input_file="examples/revision2.deps")
    g3 = compare_graph(g1, g2)
    gen_delta(g3)
    # g3 = g1.compare_graph(g2)
    #
    # gen_delta(g3)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
