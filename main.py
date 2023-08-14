import os.path
import subprocess
from pathlib import Path

from rich import print as rprint

from lib.diff_render import Renderer
from lib.error import fail
from lib.gradle import project_dependencies_to_graph, gradle_split
from lib.graph_diff import compare_graph
from lib.graph_file import load_graph, load_graph_from_lines


def main():
    project_dependencies_to_graph(input_file="examples/dependencies.txt", output_file="output/sample.deps")
    g = load_graph(input_file="output/sample.deps")
    Renderer(g).gen_delta(file=Path("output/sample.dot"))
    render_dot_file(Path("output/sample.dot"), Path("output/sample.png"))

    g1 = load_graph(input_file="examples/revision1.deps")
    g2 = load_graph(input_file="examples/revision2.deps")
    g3 = compare_graph(g1, g2)
    Renderer(g3).gen_delta(file=Path("output/example.dot"))
    render_dot_file(Path("output/example.dot"), Path("output/example.png"))


def run_tests(path):
    rprint(f"[yellow][bold]Running test suite: [cyan]{path}[/cyan]")
    for file_path in map(lambda p: os.path.join(path, p), os.listdir(path)):
        if os.path.isfile(file_path):
            run_test(file_path)
        if os.path.isdir(file_path):
            run_tests(file_path)


def run_test(file_path):
    rprint(f"[yellow][bold]Running test [cyan]{file_path}[/cyan]")
    with open(file_path) as file:
        lines = file.readlines()
        if lines[0] != "> Before\n":
            fail('First line must be "> Before"')
        after = lines.index("> After\n")
        before = load_graph_from_lines(lines[1:after])
        after = load_graph_from_lines(lines[after + 1:])
        compared = compare_graph(before, after, parent_function=gradle_split)
        test_output_dot = Path(os.path.join("test_output", file_path)).with_suffix(".dot")
        test_output_png = Path(os.path.join("output", file_path)).with_suffix(".png")
        Renderer(compared).gen_delta(file=test_output_dot)
        os.makedirs(test_output_png.parent, exist_ok=True)
        render_dot_file(test_output_dot, test_output_png)


def render_dot_file(input_dot_path, output_png_path):
    subprocess.run(["dot", "-Tpng", input_dot_path, "-o", output_png_path])


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run_tests(Path("tests"))
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
