"""Dot file generation"""
import copy
import os
from functools import cached_property
from io import TextIOWrapper, StringIO, SEEK_SET
from os import PathLike
from pathlib import Path
from typing import Optional


class Props(object):
    def __init__(self, content=None):
        self.props = content or {}

    def __setitem__(self, key, value):
        self.props[key] = value

    def __copy__(self):
        return Props(content=dict(self.props))

    def lines(self, *, sort=False):
        for key in sorted(self.props) if sort else self.props:
            value = self.props[key]
            if type(value) is bool:
                yield f'{key}={"true" if value else "false"}'
            elif type(value) is str and value.startswith("< ") and value.endswith(" >"):
                yield f'{key}={value}'
            else:
                yield f'{key}="{value}"'

    def properties_string(self):
        result = ""
        for line in self.lines(sort=True):
            result += f'{line},'
        return result

    def __str__(self):
        return self.properties_string()

    def override(self, override_props):
        copy = dict(self.props)
        copy.update(override_props.props)
        return Props(content=copy)

    def copy_from(self, props: "Props"):
        self.props = dict(props.props)


class Link(object):
    def __init__(self, u: "Node", v: "Node", props: Optional[Props] = None):
        self.u = u
        self.v = v
        self.props = Props()
        if props:
            self.props.copy_from(props)

    def __str__(self):
        return f'{self.u} -> {self.v}'


class Node(object):
    def __init__(self, *, name, label, full_name, parent):
        self.name = name
        self.label = label
        self.full_name = full_name
        self.parent = parent
        self.children = []
        self.props = Props()

    def add_child(self, node):
        self.children += [node]

    def __str__(self):
        return f'{self.name} ("{self.label}")'

    @cached_property
    def cluster_name(self):
        return f'cluster_{self.name}'

    def link(self) -> "Node":
        """Which node should be linked to"""
        if self.children:
            return self.children[0].link()
        return self

    def find_in_hierarchy(self, other: "Node") -> Optional["Node"]:
        if other == self:
            return self
        if self.parent:
            return self.parent.find_in_hierarchy(other)
        return None


class Dot(object):

    def __init__(self,
                 caption: str = "",
                 tooltip: Optional[str] = None):
        self._nodes = {}
        self._links = []
        self._cluster_nodes = {}
        self._root_props = Props()
        self._node_default_style = Props()
        self._edge_default_style = Props()
        self._subgraph_default_style = Props()
        if tooltip:
            self._root_props["tooltip"] = self.escape_new_line(tooltip or caption)
        if caption:
            self.style_default_append("label", self.escape_new_line(caption))
            self.style_default_append("tooltip", self.escape_new_line(tooltip or caption))

    def new_item(self, *, label: str, full_name: str, parent=None, node_name=None):
        node_name = node_name or self._auto_node_name()
        existing = self._nodes.get(node_name)
        if existing:
            return existing
        node = Node(name=node_name, label=label, full_name=full_name, parent=parent)
        self._nodes[node_name] = node
        if parent:
            parent.add_child(node)
        return node

    @classmethod
    def escape_new_line(cls, string: str):
        return string.replace("\n", "\\n")

    @staticmethod
    def property_append(node_or_link, param_key, param_value):
        node_or_link.props[param_key] = param_value

    def node_style_default_append(self, param_key, param_value):
        self._node_default_style[param_key] = param_value

    def edge_style_default_append(self, param_key, param_value):
        self._edge_default_style[param_key] = param_value

    def subgraph_style_default_append(self, param_key, param_value):
        self._subgraph_default_style[param_key] = param_value

    def style_default_append(self, param_key, param_value):
        self._root_props[param_key] = param_value

    def __str__(self) -> str:
        io = StringIO()
        self.write_dot_file(io)
        io.flush()
        io.seek(0, SEEK_SET)
        return io.read()

    def write_dot_file(self, file: [TextIOWrapper | PathLike | str], make_dirs: bool = True):
        if isinstance(file, PathLike) or type(file) == str:
            if make_dirs:
                os.makedirs(Path(file).parent, exist_ok=True)
            with open(file, "w") as fileIO:
                self.write_dot_file(fileIO)
            return

        writer = IndentedWriter(file)
        writer.write_line("digraph D {")
        with writer.indent():
            if writer.write_props(self._root_props):
                writer.write_line()

            link_lines = [self._link_line(link) for link in sorted(self._links, key=lambda l: (l.u.name, l.v.name))]

            for node in sorted(filter(lambda p: not p.parent, self._nodes.values()), key=lambda n: n.name):
                self.write_node(writer, node)
                writer.write_line()

            for link in link_lines:
                writer.write_line(link)
        writer.write_line("}")

    def _link_line(self, link: Link) -> str:
        from_node = link.u.link()
        to_node = link.v.link()
        props = copy.copy(link.props)
        if from_node != link.u:
            ancestor = to_node.find_in_hierarchy(link.u)
            if ancestor:
                from_node = self.cluster_node(ancestor)
            else:
                props["ltail"] = link.u.cluster_name
        if to_node != link.v:
            ancestor = from_node.find_in_hierarchy(link.v)
            if ancestor:
                to_node = self.cluster_node(ancestor)
            else:
                props["lhead"] = link.v.cluster_name
        return f"{from_node.name} -> {to_node.name} [{props}]"

    def write_node(self, writer, node):
        def label_line(node):
            if node.label.startswith("< ") and node.label.endswith(" >"):
                return f'label={node.label}'
            else:
                return f'label="{node.label}"'

        if node.children:
            writer.write_line(f'subgraph {node.cluster_name} {{ /* {node.label} */')
            with writer.indent():
                writer.write_line(f"{label_line(node)};")
                props = self._subgraph_default_style.override(node.props)
                writer.write_props(props)
                writer.write_line()
                for child in node.children:
                    self.write_node(writer, child)
            writer.write_line("}")
        else:
            writer.write_line(f'{node.name} [{self._node_default_style.override(node.props)}{label_line(node)}]')

    def new_link(self, node_u: Node, node_v: Node):
        link = Link(node_u, node_v, self._edge_default_style)
        self._links.append(link)
        return link

    def _auto_node_name(self):
        return f"node{len(self._nodes) + 1}"

    def needs_compound(self):
        return any([l.u.link() != l.u or l.v.link() != l.v for l in self._links])

    def cluster_node(self, node: Node):
        cluster_node = self._cluster_nodes.get(node, None)
        if not cluster_node:
            cluster_node = self.new_item(label="", full_name="", parent=node)
            cluster_node.props.copy_from(node.props)
            cluster_node.props["shape"] = "point"
            self._cluster_nodes[node] = cluster_node
        return cluster_node


class IndentedWriter(object):
    def __init__(self, writer, indent=0):
        self._indent = indent
        self.writer = writer

    def write_line(self, line=""):
        for i in range(self._indent):
            self.writer.write("    ")
        self.writer.write(line)
        self.writer.write("\n")

    def increment_indent(self):
        self._indent += 1

    def decrement_indent(self):
        self._indent -= 1

    def indent(self):
        return Indenter(self)

    def write_props(self, props: Props) -> bool:
        for prop in props.lines():
            self.write_line(f'{prop};')
        return True if props.props else False


class Indenter(object):

    def __init__(self, writer):
        self._writer = writer

    def __enter__(self):
        self._writer.increment_indent()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._writer.decrement_indent()
