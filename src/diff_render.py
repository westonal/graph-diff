import os
from pathlib import Path

import networkx as nx

from src.dot_file import Dot


class Renderer(object):

    def __init__(self, graph_delta: nx.Graph, new_color="#158510", old_color="#ff0000"):
        self.graph_delta = graph_delta
        self.old_color = old_color
        self.new_color = new_color
        self.dot = Dot()
        self.nodes = {}

    def find_parent(self, parents_with_state, parent=None):
        key = tuple(map(lambda p: p[0], parents_with_state))
        parent_node = self.nodes.get(key, None)
        if not parent_node:
            if len(parents_with_state) == 1:
                parent_name, state = parents_with_state[0]
                parent_node = self.dot.new_item(parent_name, parent=parent)
                color = None
                if state == "newer":
                    color = self.new_color
                elif state == "older":
                    color = self.old_color
                if color:
                    self.dot.property_append(parent_node, "color", color)
                    self.dot.property_append(parent_node, "fontcolor", color)
                self.nodes[key] = parent_node
            else:
                grand_parent = self.find_parent(parents_with_state[0:-1])
                parent_node = self.find_parent(parents_with_state[-1:], parent=grand_parent)
                self.nodes[key] = parent_node
        return parent_node

    def gen_delta(self, file=Path("output/graph.dot")):
        self.dot.node_style_default_append("shape", "rectangle")
        self.dot.node_style_default_append("fontname", "Courier New")
        self.dot.subgraph_style_default_append("shape", "rectangle")
        self.dot.subgraph_style_default_append("fontname", "Courier New")
        new_nodes = self.graph_delta.nodes(data="new", default=False)
        old_nodes = self.graph_delta.nodes(data="old", default=False)
        parents = self.graph_delta.nodes(data="parent", default=None)
        labels = self.graph_delta.nodes(data="label", default=None)
        for node in sorted(self.graph_delta.nodes):
            parent_node = None
            node_parent = parents[node]
            if node_parent:
                parent_node = self.find_parent(node_parent)
            label = labels[node] or node
            dot_node = self.dot.new_item(label, parent=parent_node)
            self.nodes[node] = dot_node
            color = None
            if new_nodes[node]:
                color = self.new_color
            elif old_nodes[node]:
                color = self.old_color
            if color:
                self.dot.property_append(dot_node, "color", color)
                self.dot.property_append(dot_node, "fontcolor", color)
        for u, v, data in self.graph_delta.edges.data():
            link = self.dot.new_link(self.nodes[u], self.nodes[v])
            color = None
            if data.get("new"):
                color = self.new_color
            elif data.get("old"):
                color = self.old_color
            if color:
                self.dot.property_append(link, "color", color)
            if data.get("indirect"):
                self.dot.property_append(link, "style", "dashed")
        os.makedirs(Path(file).parent, exist_ok=True)
        with open(file, "w") as file:
            self.dot.dot(file)
