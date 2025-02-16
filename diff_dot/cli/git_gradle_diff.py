import os.path
import subprocess
import tempfile
from pathlib import Path

import click
from git import Repo
from rich import print as rprint

from ..cd import cd
from ..cli.commands import commands
from ..diff_render import Renderer
from ..dot import render_dot_file
from ..error import fail
from ..git_utils import new_temp_worktree
from ..gradle import project_dependencies_lines_to_deps, gradle_split
from ..graph_diff import compare_graph
from ..graph_file import load_graph_from_deps_lines, ensure_diff_not_empty


@commands.command(name="git_gradle_diff", help="Diff dependencies across two commits in a gradle repo")
@click.argument("repo")
@click.argument("commitish1")
@click.argument("commitish2")
@click.option("--app", "-a", default=":app")
@click.option("--configuration", "-c", default="releaseRuntimeClasspath")
@click.option("--caption", "-t", default="", help="Caption underneath diagram")
@click.option("--output", "-o", default=None)
@click.option("--group", "-g", is_flag=True, default=False, help="Group nested modules")
@click.option("include_shortest_transitive_path", "--shortest-transitive", "-s", is_flag=True, default=False,
              help="Include shortest transitive path")
@click.option("--dark-mode", "-d", is_flag=True, default=False)
def cmd_gradle_diff(repo: str,
                    commitish1: str, commitish2: str,
                    app: str, configuration: str,
                    caption: str,
                    output: str,
                    dark_mode: bool,
                    include_shortest_transitive_path: bool,
                    group: bool,
                    ):
    repo = Repo(repo)

    if caption:
        caption = caption.replace("{old}", commitish1).replace("{new}", commitish2)

    g1 = gradle_graph_using_worktree(repo, "diff_tmp", commitish1, app, configuration)
    g2 = gradle_graph_using_worktree(repo, "diff_tmp", commitish2, app, configuration)

    g3 = compare_graph(g1, g2, parent_function=gradle_split if group else None,
                       include_shortest_transitive_path=include_shortest_transitive_path)
    ensure_diff_not_empty(g3)
    output_dot = Path(tempfile.tempdir, "tmp.dot")
    output_png = Path(output) if output else output_dot.with_suffix(".png")
    os.makedirs(output_png.parent, exist_ok=True)
    Renderer(g3, dark_mode=dark_mode, caption=caption).gen_delta_dot_file(file=output_dot)
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
    return load_graph_from_deps_lines(deps)
