import os.path
import subprocess
import tempfile
from pathlib import Path

import click
from git import Repo
from rich import print as rprint

from src.cd import cd
from src.cli.commands import commands
from src.diff_render import Renderer
from src.dot import render_dot_file
from src.error import fail
from src.git_utils import new_temp_worktree
from src.gradle import project_dependencies_lines_to_deps
from src.graph_diff import compare_graph
from src.graph_file import load_graph_from_deps_lines, ensure_diff_not_empty


@commands.command(name="git_gradle_diff", help="Diff dependencies across two commits in a gradle repo")
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


def gradle_graph_using_worktree(repo, worktree_name, commitish, app, configuration):
    tmp_worktree = new_temp_worktree(repo, worktree_name, commitish)
    with cd(tmp_worktree):
        rprint("[yellow]Running gradle dependencies...", end="")
        command = ["./gradlew", "-q", f"{app}:dependencies", "--configuration", configuration]
        result = subprocess.run(command, capture_output=True, text=True, cwd=tmp_worktree)
        if result.returncode != 0:
            fail(
                f"Command failed ({result.returncode}) in [cyan]{tmp_worktree}[/cyan] [cyan]{' '.join(command)}[reset]\n"
                f"{result.stderr}"
            )
        rprint(f"[green]Complete")
    deps = project_dependencies_lines_to_deps(result.stdout.splitlines())
    g1 = load_graph_from_deps_lines(deps)
    return g1
