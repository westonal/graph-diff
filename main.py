import os.path
import re

from gvgen import GvGen
from rich import print as rprint, inspect

from lib.Graph import Graph, Edge


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
    graph = Graph()
    with open(input_file, "r") as file:
        for line in file.readlines():
            search = re.search(r"(\S*) -> (\S*)", line)
            if not search:
                rprint("[red]Malformed input [line]")
            node_a = search.group(1)
            node_b = search.group(2)
            rprint(f"[cyan]{node_a}[/cyan] depends on [cyan]{node_b}[/cyan]")
            rprint(Edge(node_a, node_b))
            graph.add_edge(Edge(node_a, node_b))
    rprint(graph)
    return graph


def gen(graph: Graph):
    dot = GvGen()
    nodes = {}
    for node in graph.nodes:
        nodes[node] = dot.newItem(node)
    for edge in graph.edges:
        dot.newLink(nodes[edge.a], nodes[edge.b])
    with open("output/graph.dot", "w") as file:
        dot.dot(file)


def main():
    dependencies_to_graph(input_file="output/dependencies.txt", output_file="output/output.txt")
    g = load_graph(input_file="output/output.txt")
    gen(g)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
