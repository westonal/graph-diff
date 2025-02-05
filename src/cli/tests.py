import os
import tempfile
from pathlib import Path

import click
from rich import print as rprint

from src.cli.commands import commands
from src.diff_render import Renderer
from src.dot import render_dot_file
from src.error import fail
from src.gradle import gradle_split
from src.graph_diff import compare_graph
from src.graph_file import load_graph_from_deps_lines


@commands.command(name="tests", help="Run dot file generation tests")
@click.argument("path", default="tests")
@click.option("--update", "-u", is_flag=True, help="Rewrite expected outputs")
def cmd_tests(path, update):
    passed_count, failed_count = run_tests(path, update)
    if failed_count:
        fail(f"{failed_count}/{failed_count + passed_count} Tests failed")
    else:
        if not update:
            rprint(f"[green]All {passed_count} tests passed")
        else:
            rprint(f"[green]{passed_count} tests updated")


def run_tests(path, update, indent=0):
    passed_count = 0
    failed_count = 0
    if os.path.isfile(path):
        if run_test(path, update=update, indent=indent):
            passed_count += 1
        else:
            failed_count += 1
    else:
        action = "Running" if not update else "Updating"
        rprint(f"[yellow][bold]{action} test suite: [cyan]{path}[/cyan]")
        for file_path in sorted(map(lambda p: os.path.join(path, p), os.listdir(path)), key=lambda f: os.path.isdir(f)):
            passed, failed = run_tests(file_path, update=update, indent=indent + 1)
            passed_count += passed
            failed_count += failed
    return passed_count, failed_count


def run_test(file_path, update, indent):
    action = "Running" if not update else "Updating"
    for i in range(indent):
        rprint("  ", end="")
    rprint(f"[yellow][bold]{action} test [cyan]{file_path}[/cyan]...", end="")
    with open(file_path) as file:
        lines = file.readlines()
        if lines[0] != "> Before\n":
            fail('First line must be "> Before"')
        after = lines.index("> After\n")
        before = load_graph_from_deps_lines(lines[1:after])
        after = load_graph_from_deps_lines(lines[after + 1:])
        compared = compare_graph(before, after, parent_function=gradle_split)
        test_output_png = Path(os.path.join("output", file_path)).with_suffix(".png")
        test_output_png.parent.mkdir(parents=True, exist_ok=True)
        expected_test_output_dot = Path(os.path.join("test_output", file_path)).with_suffix(".dot")
        file_output_dot = expected_test_output_dot if update else Path(
            os.path.join(tempfile.gettempdir(), file_path)).with_suffix(".dot")
        Renderer(compared).gen_delta(file=file_output_dot)
        os.makedirs(file_output_dot.parent, exist_ok=True)
        render_dot_file(file_output_dot, test_output_png)
        if not update:
            if not os.path.exists(expected_test_output_dot):
                rprint("[red]Expected output missing")
                return False
            with open(expected_test_output_dot) as expected:
                expected_lines = expected.readlines()
            with open(file_output_dot) as actual:
                actual_lines = actual.readlines()
            if expected_lines != actual_lines:
                rprint("[red]Output not as expected")
                return False
            else:
                rprint("[green]pass")
                return True
        else:
            rprint("[green]Done")
            return True
