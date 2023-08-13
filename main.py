import os.path
import re
import subprocess
from pathlib import Path

import networkx as nx
from gvgen import GvGen
from rich import print as rprint


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
                    search = re.search(r"((?:[\\| ] {4}|[\\+]--- )*)project ([^ \n]*)", line)
                    if search:
                        module = search.group(2)
                        depth = len(search.group(1)) // 5
                        while len(stack) > depth:
                            stack.pop()
                        top = stack[len(stack) - 1]
                        stack.append(module)
                        rprint(f"{top} -> {module}", file=output)


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
        # rprint(f"[cyan]{u}[/cyan] depends on [cyan]{v}[/cyan]")
        graph.add_edge(u, v)
    return graph


def fail(message):
    rprint(message)
    exit(1)


def gen(graph: nx.DiGraph):
    dot = GvGen()
    nodes = {}
    for node in graph.nodes:
        nodes[node] = dot.newItem(node)
    for edge in graph.edges:
        dot.newLink(nodes[edge[0]], nodes[edge[1]])
    with open("output/graph.dot", "w") as file:
        dot.dot(file)


class Renderer(object):

    def __init__(self, split_on=":"):
        self.split_on = split_on
        self.dot = GvGen()
        self.nodes = {}

    def find_parent(self, parents_with_state, parent=None, new_color="#158510", old_color="#ff0000"):
        key = tuple(map(lambda p: p[0], parents_with_state))
        parent_node = self.nodes.get(key, None)
        if not parent_node:
            if len(parents_with_state) == 1:
                parent_name, state = parents_with_state[0]
                parent_node = self.dot.newItem(parent_name, parent=parent)
                color = None
                if state == "newer":
                    color = new_color
                elif state == "older":
                    color = old_color
                if color:
                    self.dot.propertyAppend(parent_node, "color", color)
                    self.dot.propertyAppend(parent_node, "fontcolor", color)
                self.nodes[key] = parent_node
            else:
                grand_parent = self.find_parent(parents_with_state[0:-1])
                parent_node = self.find_parent(parents_with_state[-1:], parent=grand_parent)
                self.nodes[key] = parent_node
        return parent_node


def gen_delta(graph_delta: nx.Graph, new_color="#158510", old_color="#ff0000",
              file=Path("output/graph.dot")):
    r = Renderer()
    dot = r.dot
    dot.styleDefaultAppend("shape", "rectangle")
    graph = graph_delta
    nodes = r.nodes
    new_nodes = graph.nodes(data="new", default=False)
    old_nodes = graph.nodes(data="old", default=False)
    parents = graph.nodes(data="parent", default=None)
    labels = graph.nodes(data="label", default=None)
    # Construct all subgraphs first due to GvGen limitation/bug https://github.com/stricaud/gvgen/issues/12
    for (node, parent) in parents:
        if parent:
            r.find_parent(parent)
    for node in sorted(graph.nodes):
        parent_node = None
        node_parent = parents[node]
        if node_parent:
            parent_node = r.find_parent(node_parent)
        label = labels[node] or node
        dot_node = dot.newItem(label, parent=parent_node)
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
    os.makedirs(Path(file).parent, exist_ok=True)
    with open(file, "w") as file:
        dot.dot(file)


def compare_graph(older, newer, parent_function=None):
    """The output is only changed edges and affected nodes"""
    new_edges = newer.edges - older.edges
    removed_edges = older.edges - newer.edges
    graph = nx.DiGraph()
    new_visible_graph = nx.DiGraph()
    visible_nodes = set()

    def all_parents(nodes):
        result = set()
        for n in nodes:
            p, _ = parent_function(n)
            result.update(expand(p))
        return result

    def expand(p):
        result = list()
        if p:
            for i in range(1, len(p) + 1):
                result += [tuple(p[0:i])]
        return result

    for u, v in new_edges:
        graph.add_edge(u, v)
        graph.edges[u, v]["new"] = True
        visible_nodes.update({u, v})
        new_visible_graph.add_edge(u, v)
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
    if parent_function:
        old_parents = all_parents(older.nodes)
        new_parents = all_parents(newer.nodes)
        older_parents = old_parents - new_parents
        newer_parents = new_parents - old_parents

        def get_state(expanded):
            state = None
            if expanded in newer_parents:
                state = "newer"
            elif expanded in older_parents:
                state = "older"
            return state

        def get_states(p):
            expanded = expand(p)
            return zip(p, list(map(get_state, expanded)))

        for node in visible_nodes:
            parents, name = parent_function(node)
            if parents:
                states = list(get_states(parents))
                graph.nodes[node]["parent"] = states
                graph.nodes[node]["label"] = name
    # Add existing edges for visible nodes that are linked
    pairs = dict(nx.all_pairs_bellman_ford_path_length(newer))
    for u in visible_nodes:
        for v in visible_nodes:
            distance = (pairs.get(u) or {}).get(v) or 0
            if distance == 1:
                graph.add_edge(u, v)
                new_visible_graph.add_edge(u, v)
    # Add edges for all affected nodes with indirect connections
    graph_paths = dict(nx.all_pairs_bellman_ford_path_length(new_visible_graph))
    for u in visible_nodes:
        for v in visible_nodes:
            distance = (pairs.get(u) or {}).get(v) or 0
            visible_distance = (graph_paths.get(u) or {}).get(v) or 0
            if visible_distance == 0 and distance > 1:
                graph.add_edge(u, v)
                graph.edges[u, v]["indirect"] = True

    return graph


def main():
    dependencies_to_graph(input_file="examples/dependencies.txt", output_file="output/sample.deps")
    g = load_graph(input_file="output/sample.deps")
    gen_delta(g, file=Path("output/sample.dot"))

    g1 = load_graph(input_file="examples/revision1.deps")
    g2 = load_graph(input_file="examples/revision2.deps")
    g3 = compare_graph(g1, g2)
    gen_delta(g3, file=Path("output/example.dot"))
    # g3 = g1.compare_graph(g2)
    #
    # gen_delta(g3)


def run_tests(dir):
    rprint(f"[yellow][bold]Running test suite: [cyan]{dir}[/cyan]")
    for file_path in map(lambda p: os.path.join(dir, p), os.listdir(dir)):
        if os.path.isfile(file_path):
            run_test(file_path)
        if os.path.isdir(file_path):
            run_tests(file_path)


def run_test(file_path):
    rprint(f"[yellow][bold]Running test [cyan]{file_path}[/cyan]")
    with open(file_path) as file:
        lines = file.readlines()
        if lines[0] != "> Before\n":
            fail('First line must be "> Before"')
        after = lines.index("> After\n")
        before = load_graph_from_lines(lines[1:after])
        after = load_graph_from_lines(lines[after + 1:])
        compared = compare_graph(before, after, parent_function=gradle_split)
        test_output_dot = Path(os.path.join("test_output", file_path)).with_suffix(".dot")
        test_output_png = Path(os.path.join("output", file_path)).with_suffix(".png")
        gen_delta(compared, file=test_output_dot)
        os.makedirs(test_output_png.parent, exist_ok=True)
        subprocess.run(["dot", "-Tpng", test_output_dot, "-o", test_output_png])


def gradle_split(name):
    split = re.findall(r":[^:]+", name)
    if not split:
        return None, name
    else:
        return split[0:-1], split[-1]


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run_tests("tests")
    # main()
    # run_test("tests/nesting/group_change_inside_unchanging_group.diff")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
