import os
import tempfile
from pathlib import Path

import click
from rich import print as rprint

from .commands import commands
from ..diff_render import Renderer
from ..dot import render_dot_file
from ..error import fail
from ..gradle import gradle_split
from ..graph_diff import compare_graph
from ..graph_file import load_graph_from_deps_lines


@commands.command(name="tests", help="Run dot file generation tests")
@click.argument("path", default="tests")
@click.option("--update", "-u", is_flag=True, help="Rewrite expected outputs")
def cmd_tests(path, update):
    passed_count, failed_count = 0, 0
    for include_shortest_transitive_path in [False, True]:
        for dark_mode in [False, True]:
            mode_passed_count, mode_failed_count = run_tests(path, update, dark_mode=dark_mode,
                                                             include_shortest_transitive_path=include_shortest_transitive_path)
            passed_count += mode_passed_count
            failed_count += mode_failed_count
        if failed_count:
            fail(f"{failed_count}/{failed_count + passed_count} Tests failed")
        else:
            if not update:
                rprint(f"[green]All {passed_count} tests passed")
            else:
                rprint(f"[green]{passed_count} tests updated")


def run_tests(path, update, dark_mode: bool, include_shortest_transitive_path: bool, indent: int = 0):
    passed_count = 0
    failed_count = 0
    if os.path.isfile(path):
        if run_test(path, update=update, indent=indent,
                    dark_mode=dark_mode,
                    include_shortest_transitive_path=include_shortest_transitive_path):
            passed_count += 1
        else:
            failed_count += 1
    else:
        action = "Running" if not update else "Updating"
        rprint(f"[yellow][bold]{action} test suite{' ([blue]dark mode[/])' if dark_mode else ''}: [cyan]{path}[/cyan]")
        for file_path in sorted(map(lambda p: os.path.join(path, p), os.listdir(path)), key=lambda f: os.path.isdir(f)):
            passed, failed = run_tests(file_path, update=update, indent=indent + 1, dark_mode=dark_mode,
                                       include_shortest_transitive_path=include_shortest_transitive_path)
            passed_count += passed
            failed_count += failed
    return passed_count, failed_count


def run_test(file_path: Path, update, indent: int, dark_mode: bool, include_shortest_transitive_path: bool):
    file_path = Path(file_path)
    action = "Running" if not update else "Updating"
    for i in range(indent):
        rprint("  ", end="")
    rprint(f"[yellow][bold]{action} test{' ([blue]dark mode[/])' if dark_mode else ''} [cyan]{file_path}[/cyan]...",
           end="")
    with (open(file_path) as file):
        lines = file.readlines()
        if lines[0] != "> Before\n":
            fail('First line must be "> Before"')
        after = lines.index("> After\n")
        before = load_graph_from_deps_lines(lines[1:after])
        after = load_graph_from_deps_lines(lines[after + 1:])
        compared = compare_graph(before, after, parent_function=gradle_split,
                                 include_shortest_transitive_path=include_shortest_transitive_path,
                                 )
        output_path_1 = "dark_mode" if dark_mode else "light_mode"
        output_path_2 = "include_transitive" if include_shortest_transitive_path else ""
        output_path = os.path.join(output_path_1, output_path_2)
        expected_test_output_dot = Path(os.path.join("test_output", output_path, file_path)).with_suffix(".dot")
        actual_dot = Renderer(compared,
                              caption=file_path.stem.replace("_", " "),
                              dark_mode=dark_mode,
                              ).dot
        actual_lines = f"{actual_dot}"

        if not update:
            if not os.path.exists(expected_test_output_dot):
                rprint("[red]Expected output missing")
                return False
            with open(expected_test_output_dot) as expected:
                expected_lines = expected.read()
            if expected_lines != actual_lines:
                rprint("[red]Output not as expected")
                return False
            else:
                rprint("[green]pass")
                return True
        else:
            os.makedirs(expected_test_output_dot.parent, exist_ok=True)
            with open(expected_test_output_dot, "w") as expected:
                expected.write(actual_lines)
            for extension in [".png", ".svg"]:
                test_output_image = Path(os.path.join("output", output_path, file_path)).with_suffix(extension)
                test_output_image.parent.mkdir(parents=True, exist_ok=True)
                render_dot_file(input_dot_path=expected_test_output_dot, output_image_path=test_output_image)
            rprint("[green]Done")
            return True
