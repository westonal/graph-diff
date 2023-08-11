import os.path
import re

from rich import print as rprint, inspect

from lib.Graph import Graph, Edge


def stage1():
    # file = "~/signal-deps.txt"
    file = "output/dependencies.txt"
    stack = []
    with open(os.path.expanduser(file)) as file:
        with open("output/output.txt", "w") as output:
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


def stage2():
    graph = Graph()
    with open("output/output.txt", "r") as input:
        for line in input.readlines():
            search = re.search(r"(\S*) -> (\S*)", line)
            if not search:
                rprint("[red]Malformed input [line]")
            node_a = search.group(1)
            node_b = search.group(2)
            rprint(f"[cyan]{node_a}[/cyan] depends on [cyan]{node_b}[/cyan]")
            rprint(Edge(node_a, node_b))
            graph.add_edge(Edge(node_a, node_b))

    inspect(graph.nodes)
    inspect(graph.edges)
    rprint(graph)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    stage1()
    stage2()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
