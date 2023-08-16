"""Dot file generation"""


class Props(object):
    def __init__(self, content=None):
        self.props = content or {}

    def __setitem__(self, key, value):
        self.props[key] = value

    def properties_string(self):
        result = ""
        for key in sorted(self.props):
            result += f'{key}="{self.props[key]}",'
        return result

    def __str__(self):
        return self.properties_string()

    def override(self, override_props):
        copy = dict(self.props)
        copy.update(override_props.props)
        return Props(content=copy)


class Link(object):
    def __init__(self, u, v):
        self.u = u
        self.v = v
        self.props = Props()

    def __str__(self):
        return f'{self.u} -> {self.v}'


class Node(object):
    def __init__(self, name, label, parent):
        self.name = name
        self.label = label
        self.parent = parent
        self.children = []
        self.props = Props()

    def add_child(self, node):
        self.children += [node]

    def __str__(self):
        return f'{self.name} ("{self.label}")'


class Dot(object):

    def __init__(self):
        self._nodes = {}
        self._links = []
        self._node_default_style = Props()
        self._subgraph_default_style = Props()

    def new_item(self, label, parent=None, node_name=None):
        node_name = node_name or self._auto_node_name()
        existing = self._nodes.get(node_name)
        if existing:
            return existing
        node = Node(name=node_name, label=label, parent=parent)
        self._nodes[node_name] = node
        if parent:
            parent.add_child(node)
        return node

    @staticmethod
    def property_append(node_or_link, param_key, param_value):
        node_or_link.props[param_key] = param_value

    def node_style_default_append(self, param_key, param_value):
        self._node_default_style[param_key] = param_value

    def subgraph_style_default_append(self, param_key, param_value):
        self._subgraph_default_style[param_key] = param_value

    def dot(self, file):
        writer = IndentedWriter(file)
        writer.write_line("digraph D {")
        with writer.indent():
            for node in sorted(filter(lambda p: not p.parent, self._nodes.values()), key=lambda n: n.name):
                self.write_node(writer, node)
                writer.write_line()

            for link in sorted(self._links, key=lambda l: (l.u.name, l.v.name)):
                writer.write_line(f"{link.u.name} -> {link.v.name} [{link.props}]")
        writer.write_line("}")

    def write_node(self, writer, node):
        if node.children:
            writer.write_line(f'subgraph cluster_{node.name} {{ /* {node.label} */')
            with writer.indent():
                writer.write_line(f'label="{node.label}";')
                props = self._subgraph_default_style.override(node.props).props
                for prop in props:
                    writer.write_line(f'{prop}="{props[prop]}";')
                writer.write_line()
                for child in node.children:
                    self.write_node(writer, child)
            writer.write_line("}")
        else:
            writer.write_line(f'{node.name} [{self._node_default_style.override(node.props)}label="{node.label}"]')

    def new_link(self, node_u, node_v):
        link = Link(node_u, node_v)
        self._links.append(link)
        return link

    def _auto_node_name(self):
        return f"node{len(self._nodes) + 1}"


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


class Indenter(object):

    def __init__(self, writer):
        self._writer = writer

    def __enter__(self):
        self._writer.increment_indent()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._writer.decrement_indent()
