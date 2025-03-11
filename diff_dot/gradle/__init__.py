import re
from dataclasses import dataclass
from typing import Optional, Tuple

_pattern = re.compile(
    r"(?P<Indent>(?:[\\| ] {4}|[\\+]--- )*)(?:project (?P<Project>[^ \n]*)|(?P<Coordinate>\S+:\S+):(?P<VersionRequested>\S*)(?: -> (?P<VersionGot>\S+))?(?P<Repeated> \(\*\))?)")


@dataclass
class Project:
    name: str


@dataclass
class GradleCoordinate:
    name: str


def gradle_line_parse(line: str) -> Optional[Tuple[int, Project | GradleCoordinate]]:
    search = _pattern.search(line)
    if search:
        depth = len(search["Indent"]) // 5
        module = search["Project"]
        if module:
            return depth, Project(module)
        else:
            return depth, GradleCoordinate(search["Coordinate"])


def project_dependencies_to_deps_lines(input_file: str) -> [str]:
    import os
    """Reads output of gradle dependencies and returns a graph file containing the local projects interdependencies"""
    with open(os.path.expanduser(input_file)) as file:
        return project_dependencies_lines_to_deps(lines=file.readlines())


def project_dependencies_to_deps(input_file: str, output_file: str):
    """Reads output of gradle dependencies and outputs a graph file containing the local projects interdependencies"""
    lines = project_dependencies_to_deps_lines(input_file)
    with open(output_file, "w") as output:
        output.writelines(lines)


def project_dependencies_lines_to_deps(lines, *, include_external: bool = False) -> [str]:
    stack = []
    output_lines = []
    for line in lines:
        if not stack:
            app = re.search("Project '([^']*)'", line)
            if app:
                stack.append(app.group(1))
        else:
            depth_and_module = gradle_line_parse(line)
            if depth_and_module:
                depth, search = depth_and_module
                if not include_external and isinstance(search, GradleCoordinate):
                    continue
                module = search.name
                while len(stack) > depth:
                    stack.pop()
                top = stack[len(stack) - 1]
                stack.append(module)
                output_lines += [f"{top} -> {module}\n"]
    return output_lines


def gradle_split(name):
    """A parent finding function that splits on :"""
    split = re.findall(r":?[^:.]+", name)
    if not split:
        return None, name
    else:
        return split[0:-1], split[-1]
