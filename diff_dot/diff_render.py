import dataclasses
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
    group_border_color: Optional[str] = None
    """fg_color if not overridden"""
    group_title_color: Optional[str] = None
    """fg_color if not overridden"""
    transitive_color: str = None
    """fg_color if not overridden"""

    def no_color(self):
        return self.copy(
            new_color=self.fg_color,
            old_color=self.fg_color,
        )

    def copy(self, /, **changes):
        return dataclasses.replace(self, **changes)


light_mode_style = DotStyle()
dark_mode_style = DotStyle(
    new_color="#15ef10",
    old_color="#ef3f3f",
    bg_color="#222222",
    fg_color="#ffffff",
    group_border_color="#7f7f7f",
    group_title_color="#bfbfbf",
    transitive_color="#7f7f7f",
)


class Renderer(object):

    def __init__(self,
                 graph_delta: nx.Graph,
                 *,
                 style: DotStyle = None,
                 caption: str = "",
                 dark_mode: Optional[bool] = None,
                 f_node_url=None,
                 node_name_map=None,
                 ):
        if dark_mode:
            if style:
                raise Exception("Do not specify both style and dark_mode")
            style = dark_mode_style
        self.f_node_url = f_node_url
        self.graph_delta = graph_delta
        self.style = style or light_mode_style
        self.nodes = {}
        self.caption = caption
        self.node_name_map = node_name_map

    def _find_parent(self, dot: Dot, parents_with_state: [str], parent=None):
        if len(parents_with_state) > 1:
            grand_parent = self._find_parent(dot, parents_with_state[0:-1])
            return self._find_parent(dot, parents_with_state[-1:], parent=grand_parent)

        parent_name, state = parents_with_state[0]
        key = f"{parent.full_name}{parent_name}" if parent else parent_name
        parent_node = self.nodes.get(key, None)
        if not parent_node:
            parent_name, state = parents_with_state[0]
            full_name = f"{parent.full_name}{parent_name}" if parent else parent_name
            node_name = self.node_name_map.get(full_name) if self.node_name_map else None
            parent_node = dot.new_item(label=parent_name, parent=parent, full_name=full_name, node_name=node_name)
            if state == "newer":
                color = self.style.new_color
            elif state == "older":
                color = self.style.old_color
            else:
                color = self.style.group_title_color or self.style.fg_color
            dot.property_append(parent_node, "color", color or self.style.group_border_color)
            dot.property_append(parent_node, "fontcolor", color or self.style.group_title_color)
            dot.property_append(parent_node, "tooltip", Dot.escape_new_line(parent_node.full_name))
            if self.f_node_url:
                dot.property_append(parent_node, "URL", self.f_node_url(parent_node.full_name))
            self.nodes[key] = parent_node
        return parent_node

    def gen_delta_dot_file(self, file=Path("output/graph.dot")):
        dot = self.dot
        dot.write_dot_file(file)

    @cached_property
    def dot(self) -> Dot:
        dot = Dot(self.caption, tooltip=self.caption)
        dot.style_default_append("bgcolor", self.style.bg_color)
        dot.style_default_append("fontcolor", self.style.fg_color)
        dot.style_default_append("fontname", self.style.font_name)
        dot.node_style_default_append("shape", "rectangle")
        dot.node_style_default_append("fontname", self.style.font_name)
        dot.edge_style_default_append("arrowhead", "vee")
        dot.subgraph_style_default_append("style", "rounded")
        dot.subgraph_style_default_append("fontname", self.style.font_name)
        new_nodes = self.graph_delta.nodes(data="new", default=False)
        old_nodes = self.graph_delta.nodes(data="old", default=False)
        parents = self.graph_delta.nodes(data="parent", default=None)
        labels = self.graph_delta.nodes(data="label", default=None)
        full_names = self.graph_delta.nodes(data="full_name", default=None)
        nodes_data = self.graph_delta.nodes.data()
        for node in sorted(self.graph_delta.nodes):
            parent_node = None
            node_parent = parents[node]
            if node_parent:
                parent_node = self._find_parent(dot, node_parent)
            label = labels[node] or node
            m_label = Dot.escape_new_line(label)
            node_name = self.node_name_map.get(full_names[node]) if self.node_name_map else None
            dot_node = dot.new_item(label=m_label, full_name=full_names[node] or label, parent=parent_node,
                                    node_name=node_name)
            self.nodes[node] = dot_node
            if new_nodes[node]:
                color = self.style.new_color
            elif old_nodes[node]:
                color = self.style.old_color
            else:
                color = self.style.fg_color
            if nodes_data[node].get("transitive"):
                color = self.style.transitive_color or color
            dot.property_append(dot_node, "color", color)
            dot.property_append(dot_node, "fontcolor", color)
            dot.property_append(dot_node, "tooltip", Dot.escape_new_line(dot_node.full_name))
            if nodes_data[node].get("highlight"):
                dot.property_append(dot_node, "fillcolor", "#add8e6")
                dot.property_append(dot_node, "style", "filled")
            else:
                fillcolor = nodes_data[node].get("fillcolor")
                if fillcolor is not None:
                    dot.property_append(dot_node, "fillcolor", fillcolor)
                    dot.property_append(dot_node, "style", "filled")
            if self.f_node_url:
                dot.property_append(dot_node, "URL", self.f_node_url(node))
        for u, v, data in self.graph_delta.edges.data():
            link = dot.new_link(self.nodes[u], self.nodes[v])
            if data.get("new"):
                color = self.style.new_color
            elif data.get("old"):
                color = self.style.old_color
            else:
                color = self.style.fg_color
            if data.get("transitive"):
                color = self.style.transitive_color or color
            dot.property_append(link, "color", color)
            dot.property_append(link, "tooltip",
                                Dot.escape_new_line(f"{self.nodes[u].full_name}\n   ->\n{self.nodes[v].full_name}"))

            if data.get("indirect"):
                dot.property_append(link, "style", "dashed")
                distance = data.get("indirect_distance")
                # 1 hop is a direct connection
                # 2 can be an assumed number of hops for unlabelled
                # 3 or more,we'll point out
                if distance > 2:
                    dot.property_append(link, "label", f'({distance})')
                    dot.property_append(link, "fontcolor", color)
                    dot.property_append(link, "fontname", self.style.font_name)

        if dot.needs_compound():
            dot.style_default_append("compound", True)

        return dot
