import os.path
import subprocess
import tempfile
from pathlib import Path

import click
import networkx as nx
from git import Repo
from rich import print as rprint

from lib.cd import cd
from lib.cmd import is_tool
from lib.diff_render import Renderer
from lib.error import fail
from lib.git_utils import new_temp_worktree
from lib.gradle import project_dependencies_to_deps, gradle_split, project_dependencies_lines_to_deps
from lib.graph_diff import compare_graph
from lib.graph_file import load_graph, load_graph_from_deps_lines


@click.group
def commands():
    pass


def run_tests(path, update):
    passed_count = 0
    failed_count = 0
    if os.path.isfile(path):
        if run_test(path, update=update):
            passed_count += 1
        else:
            failed_count += 1
    else:
        action = "Running" if not update else "Updating"
        rprint(f"[yellow][bold]{action} test suite: [cyan]{path}[/cyan]")
        for file_path in map(lambda p: os.path.join(path, p), os.listdir(path)):
            passed, failed = run_tests(file_path, update=update)
            passed_count += passed
            failed_count += failed
    return passed_count, failed_count


def run_test(file_path, update):
    action = "Running" if not update else "Updating"
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
        expected_test_output_dot = Path(os.path.join("test_output", file_path)).with_suffix(".dot")
        file_output_dot = expected_test_output_dot if update else Path(
            os.path.join(tempfile.gettempdir(), file_path)).with_suffix(".dot")
        Renderer(compared).gen_delta(file=file_output_dot)
        os.makedirs(file_output_dot.parent, exist_ok=True)
        render_dot_file(file_output_dot, test_output_png)
        if not update:
            with open(expected_test_output_dot) as expected:
                expected_lines = expected.readlines()
            with open(file_output_dot) as actual:
                actual_lines = actual.readlines()
            if expected_lines != actual_lines:
                rprint("[red]Output not as expected")
                return False
            else:
                rprint("[green]Correct")
                return True
        else:
            rprint("[green]Done")
            return True


def render_dot_file(input_dot_path, output_png_path):
    if not is_tool("dot"):
        fail("Dot is not installed, see [link=https://github.com/westonal/graph-diff#setup]README.md/setup[/link]")
    command = ["dot", "-Tpng", input_dot_path, "-o", output_png_path]
    return_code = subprocess.run(command).returncode
    if return_code != 0:
        join = ' '.join(map(lambda a: f"{a}", command))
        fail(f"Dot failed return code {return_code} [cyan]{join}")


def load_graph_from_argument(input_file: str, output_file: str):
    if Path(input_file).suffix == ".deps":
        return load_graph(input_file=input_file)
    else:
        project_dependencies_to_deps(input_file=input_file, output_file=output_file)
        return load_graph(input_file=output_file)


@commands.command(name="tests")
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


@commands.command(name="diff")
@click.argument("file1")
@click.argument("file2", default="")
@click.option("--output", "-o", default=None)
def cmd_diff(file1, file2, output):
    os.makedirs("output", exist_ok=True)
    if file2:
        g1 = load_graph_from_argument(file1, "output/double_file_1.deps")
        g2 = load_graph_from_argument(file2, "output/double_file_2.deps")
        g = compare_graph(g1, g2, parent_function=gradle_split)
        ensure_diff_not_empty(g)
        dot_file_path = Path("output/double_file.dot")
        Renderer(g).gen_delta(file=dot_file_path)
    else:
        g = load_graph_from_argument(file1, "output/single_file.deps")
        g = compare_graph(nx.DiGraph(), g, parent_function=gradle_split)
        dot_file_path = Path("output/single_file.dot")
        Renderer(g, new_color="#000000").gen_delta(file=dot_file_path)
    output_png = Path(output) if output else dot_file_path.with_suffix(".png")
    os.makedirs(output_png.parent, exist_ok=True)
    render_dot_file(dot_file_path, output_png)
    rprint(f"Created [cyan]{output_png}[/cyan]")


@commands.command(name="git_gradle_diff")
@click.argument("repo")
@click.argument("commitish1")
@click.argument("commitish2")
@click.option("--app", "-a", default=":app")
@click.option("--configuration", "-c", default="releaseRuntimeClasspath")
@click.option("--output", "-o", default=None)
def cmd_gradle_diff(repo, commitish1, commitish2, app, configuration, output):
    repo = Repo(repo)

    g1 = gradle_graph_using_worktree(repo, "diff_tmp", commitish1, app, configuration)
    g2 = gradle_graph_using_worktree(repo, "diff_tmp", commitish2, app, configuration)

    g3 = compare_graph(g1, g2)
    ensure_diff_not_empty(g3)
    output_dot = Path(tempfile.tempdir, "tmp.dot")
    output_png = Path(output) if output else output_dot.with_suffix(".png")
    os.makedirs(output_png.parent, exist_ok=True)
    Renderer(g3).gen_delta(file=output_dot)
    render_dot_file(output_dot, output_png)
    rprint(f"Created [cyan]{output_png}[/cyan]")


def ensure_diff_not_empty(g):
    if len(g.nodes) == 0:
        rprint("[yellow]No differences to render")
        exit(0)


def gradle_graph_using_worktree(repo, worktree_name, commitish, app, configuration):
    tmp_worktree = new_temp_worktree(repo, worktree_name, commitish)
    with cd(tmp_worktree):
        rprint("[yellow]Running gradle dependencies...", end="")
        command = ["./gradlew", "-q", f"{app}:dependencies", "--configuration", configuration]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            fail(
                f"Command failed ({result.returncode}) in [cyan]{tmp_worktree}[/cyan] [cyan]{' '.join(command)}[reset]\n"
                f"{result.stderr}"
            )
        rprint(f"[green]Complete")
    deps = project_dependencies_lines_to_deps(result.stdout.splitlines())
    g1 = load_graph_from_deps_lines(deps)
    return g1


if __name__ == '__main__':
    commands()
