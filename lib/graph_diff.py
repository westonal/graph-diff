import networkx as nx


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
