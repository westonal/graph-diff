import os
import re


def project_dependencies_to_graph(input_file: str, output_file: str):
    """Reads output of gradle dependencies and outputs a graph file containing the local projects interdependencies"""
    stack = []
    with open(os.path.expanduser(input_file)) as file:
        with open(output_file, "w") as output:
            for line in file.readlines():
                if not stack:
                    app = re.search("Project '([^']*)'", line)
                    if app:
                        stack.append(app.group(1))
                else:
                    search = re.search(r"((?:[\\| ] {4}|[\\+]--- )*)project ([^ \n]*)", line)
                    if search:
                        module = search.group(2)
                        depth = len(search.group(1)) // 5
                        while len(stack) > depth:
                            stack.pop()
                        top = stack[len(stack) - 1]
                        stack.append(module)
                        print(f"{top} -> {module}", file=output)


def gradle_split(name):
    """A parent finding function that splits on :"""
    split = re.findall(r":[^:]+", name)
    if not split:
        return None, name
    else:
        return split[0:-1], split[-1]
