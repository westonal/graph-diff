from itertools import pairwise
from random import shuffle
from typing import Any, Tuple, Dict

import networkx as nx
from networkx.classes import DiGraph
from networkx.exception import NetworkXNoPath, NodeNotFound


def shuffled(visible_nodes):
    visible_nodes = list(visible_nodes)
    shuffle(visible_nodes)
    return visible_nodes


def compare_graph(older: DiGraph,
                  newer: DiGraph,
                  parent_function=None,
                  *,
                  include_shortest_transitive_path: bool = False,
                  include_new: bool = True,
                  include_old: bool = True,
                  ):
    """The output is only changed edges and affected nodes"""
    new_edges = newer.edges - older.edges if include_new else []
    removed_edges = older.edges - newer.edges if include_old else []
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
    new_nodes = newer.nodes - older.nodes if include_new else []
    for new_node in new_nodes:
        graph.add_node(new_node)
        visible_nodes.add(new_node)
        graph.nodes[new_node]["new"] = True
    old_nodes = older.nodes - newer.nodes if include_old else []
    for old_node in old_nodes:
        graph.add_node(old_node)
        visible_nodes.add(old_node)
        graph.nodes[old_node]["old"] = True

    if include_shortest_transitive_path:
        paths = dict(nx.all_pairs_bellman_ford_path(newer))
        currently_visible_nodes = list(visible_nodes)
        for u in currently_visible_nodes:
            for v in currently_visible_nodes:
                path = (paths.get(u) or {}).get(v)
                if not path or len(path) <= 2:  # only transitive
                    continue
                for a, b in pairwise(path):
                    if a in currently_visible_nodes and b in currently_visible_nodes:
                        continue
                    get = graph.edges.get((a, b))
                    if not get:
                        graph.add_edge(a, b)
                        new_visible_graph.add_edge(a, b)
                        visible_nodes.update({a, b})
                        graph.edges[a, b]["transitive"] = True
                        for node in [a, b]:
                            if not node in currently_visible_nodes:
                                graph.nodes[node]["transitive"] = True

    # Add existing edges for visible nodes that are linked
    for u in visible_nodes:
        for v in visible_nodes:
            if u == v:
                continue
            distance = (path_lengths_on_newer.get(u) or {}).get(v) or 0
            if distance == 1:
                graph.add_edge(u, v)
                new_visible_graph.add_edge(u, v)

    # Add indirect edges for all affected nodes with indirect connections
    pairs_by_distance = _all_reachability_by_length(newer)

    for distance in sorted(pairs_by_distance):
        if distance <= 1:
            continue

        for (u, v) in pairs_by_distance[distance]:
            if u not in visible_nodes or v not in visible_nodes:
                continue

            # If we cannot currently reach from u to v, it's indirect, add it
            if _can_reach(new_visible_graph, u, v) == 0:
                graph.add_edge(u, v)
                new_visible_graph.add_edge(u, v)
                graph.edges[u, v]["indirect"] = True
                graph.edges[u, v]["indirect_distance"] = distance

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
                graph.nodes[node]["full_name"] = node
            else:
                graph.nodes[node]["full_name"] = name
            graph.nodes[node]["label"] = name

    return graph


def _can_reach(graph, u, v) -> int:
    try:
        return nx.bellman_ford_path_length(graph, u, v)
    except NetworkXNoPath:
        return 0
    except NodeNotFound:
        return 0


def _all_reachability_by_length(graph: DiGraph) -> Dict[int, Tuple[Any, Any]]:
    shortest_lengths = dict(nx.all_pairs_bellman_ford_path_length(graph))
    pairs_by_distance = {}
    for a in shortest_lengths:
        reachables = shortest_lengths[a]
        for b in reachables:
            distance = reachables[b]
            if distance:
                l = pairs_by_distance.get(distance) or []
                l.append((a, b))
                pairs_by_distance[distance] = l
    return pairs_by_distance
