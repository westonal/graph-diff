from itertools import pairwise

import networkx as nx
from networkx.classes import DiGraph


def compare_graph(older: DiGraph,
                  newer: DiGraph,
                  parent_function=None,
                  *,
                  include_shortest_transitive_path: bool = False,
                  ):
    """The output is only changed edges and affected nodes"""
    new_edges = newer.edges - older.edges
    removed_edges = older.edges - newer.edges
    graph = nx.DiGraph()
    new_visible_graph = nx.DiGraph()
    visible_nodes = set()
    path_lengths_on_newer = dict(nx.all_pairs_bellman_ford_path_length(newer))

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
        graph.add_node(new_node)
        graph.nodes[new_node]["new"] = True
    old_nodes = older.nodes - newer.nodes
    for old_node in old_nodes:
        graph.add_node(old_node)
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

    if include_shortest_transitive_path:
        paths = dict(nx.all_pairs_bellman_ford_path(newer))
        for u in visible_nodes:
            for v in visible_nodes:
                path = (paths.get(u) or {}).get(v)
                if not path or len(path) <= 2:  # only transitive
                    continue
                for a, b in pairwise(path):
                    if a in visible_nodes and b in visible_nodes:
                        continue
                    get = graph.edges.get((a, b))
                    if not get:
                        graph.add_edge(a, b)
                        new_visible_graph.add_edge(a, b)
                        graph.edges[a, b]["transitive"] = True
                        for node in [a, b]:
                            if not node in visible_nodes:
                                graph.nodes[node]["transitive"] = True

    # Add existing edges for visible nodes that are linked
    for u in visible_nodes:
        for v in visible_nodes:
            distance = (path_lengths_on_newer.get(u) or {}).get(v) or 0
            if distance == 1:
                graph.add_edge(u, v)
                new_visible_graph.add_edge(u, v)

    # Add indirect edges for all affected nodes with indirect connections
    shortest_visible_lengths = dict(nx.all_pairs_bellman_ford_path_length(new_visible_graph))
    for u in visible_nodes:
        for v in visible_nodes:
            distance = (path_lengths_on_newer.get(u) or {}).get(v) or 0
            visible_distance = (shortest_visible_lengths.get(u) or {}).get(v) or 0
            if visible_distance == 0 and distance > 1:
                graph.add_edge(u, v)
                graph.edges[u, v]["indirect"] = True
                graph.edges[u, v]["indirect_distance"] = distance

    return graph
