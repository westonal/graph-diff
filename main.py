import os.path
import subprocess
from pathlib import Path

import click
from rich import print as rprint

from lib.diff_render import Renderer
from lib.error import fail
from lib.gradle import project_dependencies_to_graph, gradle_split
from lib.graph_diff import compare_graph
from lib.graph_file import load_graph, load_graph_from_lines


@click.group
def commands():
    pass


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
    command = ["dot", "-Tpng", input_dot_path, "-o", output_png_path]
    return_code = subprocess.run(command).returncode
    if return_code != 0:
        join = ' '.join(map(lambda a: f"{a}", command))
        fail(f"Dot failed return code {return_code} [cyan]{join}")


def load_graph_from_argument(input_file: str, output_file: str):
    if Path(input_file).suffix == ".deps":
        return load_graph(input_file=input_file)
    else:
        project_dependencies_to_graph(input_file=input_file, output_file=output_file)
        return load_graph(input_file=output_file)


@commands.command(name="tests")
@click.argument("path", default="tests")
def cmd_tests(path):
    run_tests(path)


@commands.command(name="diff")
@click.argument("file1")
@click.argument("file2", default="")
@click.option("--output", "-o", default=None)
def cmd_diff(file1, file2, output):
    if file2:
        g1 = load_graph_from_argument(file1, "output/double_file_1.deps")
        g2 = load_graph_from_argument(file2, "output/double_file_2.deps")
        g = compare_graph(g1, g2, parent_function=gradle_split)
        dot_file_path = Path("output/double_file.dot")
    else:
        g = load_graph_from_argument(file1, "output/single_file.deps")
        dot_file_path = Path("output/single_file.dot")
    output_png = Path(output) if output else dot_file_path.with_suffix(".png")
    Renderer(g).gen_delta(file=dot_file_path)
    os.makedirs(output_png.parent, exist_ok=True)
    render_dot_file(dot_file_path, output_png)
    rprint(f"Created [cyan]{output_png}[/cyan]")


if __name__ == '__main__':
    commands()
