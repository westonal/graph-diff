import re
from dataclasses import dataclass
from functools import cached_property

import networkx as nx
from networkx.classes import DiGraph


@dataclass(frozen=True)
class Dependency:
    from_name: str
    to_name: str

    @cached_property
    def reversed(self):
        return Dependency(self.to_name, self.from_name)

    def __str__(self):
        return f"{self.from_name} -> {self.to_name}"

    @cached_property
    def rich_str(self):
        return f"[cyan]{self.from_name}[/] [yellow]->[/] [cyan]{self.to_name}[/]"

    @cached_property
    def rich_str_both(self):
        return f"[cyan]{self.from_name}[/] [yellow]<-->[/] [cyan]{self.to_name}[/]"


class Dependencies:

    def __init__(self):
        self._dependencies = set()

    def __iter__(self):
        return self._dependencies.__iter__()

    def add_dependency(self, from_name: str, to_name: str):
        self._dependencies.add(Dependency(from_name, to_name))

    def add_str(self, line):
        search = re.search(r"^(\S*)((?: -> \S*)*)", line)
        if not search:
            raise IOError(f"Malformed input: {line}")
        u = search.group(1)
        vs = search.group(2)
        if not vs:
            self._dependencies.add(Dependency(u, u))
        else:
            all_v = re.findall(r"(?: -> )(\S*)", vs)
            for v in all_v:
                self._dependencies.add(Dependency(u, v))
                u = v

    def list(self) -> [Dependency]:
        return sorted(list(self._dependencies), key=lambda d: (d.from_name, d.to_name))

    def add_lines(self, lines: [str]):
        for line in lines:
            self.add_str(line)

    def copy(self):
        new_dependencies = Dependencies()
        new_dependencies._dependencies.update(self._dependencies)
        return new_dependencies

    def remove(self, d: Dependency):
        self._dependencies.remove(d)

    def to_digraph(self) -> DiGraph:
        graph = nx.DiGraph()
        for dependency in self:
            if dependency.from_name == dependency.to_name:
                graph.add_node(dependency.from_name)
            else:
                graph.add_edge(dependency.from_name, dependency.to_name)
        return graph

    def flatten(self, lamda):
        ...

    def __contains__(self, item):
        return item in self._dependencies

    def map_nodes(self, lamda):
        new_dependencies = Dependencies()
        for d in self:
            new_dependencies.add_dependency(lamda(d.from_name), lamda(d.to_name))
        return new_dependencies

    def filter_nodes(self, lamda):
        new_dependencies = Dependencies()
        for d in self:
            if lamda(d.from_name) and lamda(d.to_name):
                new_dependencies.add_dependency(d.from_name, d.to_name)
        return new_dependencies

    def filter(self, lamda):
        new_dependencies = Dependencies()
        for d in self:
            if lamda(d):
                new_dependencies.add_dependency(d.from_name, d.to_name)
        return new_dependencies

    def len(self):
        return len(self._dependencies)
