from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Optional

import networkx as nx

from .dot_file import Dot


@dataclass
class DotStyle:
    new_color: str = "#158510"
    old_color: str = "#ff0000"
    bg_color: str = "#ffffff"
    fg_color: str = "#000000"
    font_name: str = "Courier New"

    def no_color(self):
        return DotStyle(
            new_color=self.fg_color,
            old_color=self.fg_color,
            bg_color=self.bg_color,
            fg_color=self.fg_color,
            font_name=self.font_name,
        )


light_mode_style = DotStyle()
dark_mode_style = DotStyle(
    new_color="#15ef10",
    old_color="#ef3f3f",
    bg_color="#222222",
    fg_color="#ffffff",
)


class Renderer(object):

    def __init__(self,
                 graph_delta: nx.Graph,
                 *,
                 style: DotStyle = None,
                 caption: str = "",
                 dark_mode: Optional[bool] = None,
                 ):
        if dark_mode:
            if style:
                raise Exception("Do not specify both style and dark_mode")
            style = dark_mode_style
        self.graph_delta = graph_delta
        self.style = style or light_mode_style
        self.nodes = {}
        self.caption = caption

    def _find_parent(self, dot: Dot, parents_with_state, parent=None):
        key = tuple(map(lambda p: p[0], parents_with_state))
        parent_node = self.nodes.get(key, None)
        if not parent_node:
            if len(parents_with_state) == 1:
                parent_name, state = parents_with_state[0]
                parent_node = dot.new_item(parent_name, parent=parent)
                color = None
                if state == "newer":
                    color = self.style.new_color
                elif state == "older":
                    color = self.style.old_color
                if color:
                    dot.property_append(parent_node, "color", color)
                    dot.property_append(parent_node, "fontcolor", color)
                self.nodes[key] = parent_node
            else:
                grand_parent = self._find_parent(dot, parents_with_state[0:-1])
                parent_node = self._find_parent(dot, parents_with_state[-1:], parent=grand_parent)
                self.nodes[key] = parent_node
        return parent_node

    def gen_delta_dot_file(self, file=Path("output/graph.dot")):
        dot = self.dot
        dot.write_dot_file(file)

    @cached_property
    def dot(self) -> Dot:
        dot = Dot(self.caption)
        dot.style_default_append("bgcolor", self.style.bg_color)
        dot.style_default_append("fontcolor", self.style.fg_color)
        dot.style_default_append("fontname", self.style.font_name)
        dot.node_style_default_append("shape", "rectangle")
        dot.node_style_default_append("fontname", self.style.font_name)
        dot.subgraph_style_default_append("style", "rounded")
        dot.subgraph_style_default_append("color", self.style.fg_color)
        dot.subgraph_style_default_append("fontname", self.style.font_name)
        new_nodes = self.graph_delta.nodes(data="new", default=False)
        old_nodes = self.graph_delta.nodes(data="old", default=False)
        parents = self.graph_delta.nodes(data="parent", default=None)
        labels = self.graph_delta.nodes(data="label", default=None)
        for node in sorted(self.graph_delta.nodes):
            parent_node = None
            node_parent = parents[node]
            if node_parent:
                parent_node = self._find_parent(dot, node_parent)
            label = labels[node] or node
            dot_node = dot.new_item(label, parent=parent_node)
            self.nodes[node] = dot_node
            if new_nodes[node]:
                color = self.style.new_color
            elif old_nodes[node]:
                color = self.style.old_color
            else:
                color = self.style.fg_color
            dot.property_append(dot_node, "color", color)
            dot.property_append(dot_node, "fontcolor", color)
        for u, v, data in self.graph_delta.edges.data():
            link = dot.new_link(self.nodes[u], self.nodes[v])
            if data.get("new"):
                color = self.style.new_color
            elif data.get("old"):
                color = self.style.old_color
            else:
                color = self.style.fg_color
            dot.property_append(link, "color", color)
            dot.property_append(link, "arrowhead", "empty")
            if data.get("indirect"):
                dot.property_append(link, "style", "dashed")
        return dot
