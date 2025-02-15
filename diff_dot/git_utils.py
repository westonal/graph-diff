import os
from pathlib import Path
from tempfile import gettempdir

from git import Repo
from rich import print as rprint


def create_worktree(repo: Repo, path, commitish):
    repo.git.execute(["git", "worktree", "add", "-f", "--detach", path, commitish])


def new_temp_worktree(repo: Repo, worktree_name, commitish):
    tmp_worktree = os.path.join(Path(gettempdir()), worktree_name)
    hexsha = repo.commit(commitish).hexsha
    if os.path.exists(tmp_worktree):
        worktree = Repo(tmp_worktree)
        worktree.head.reset(commit=hexsha, working_tree=True)
        rprint(
            f"[yellow]Reset worktree [cyan]{worktree_name}[/cyan] to [cyan]{commitish}[/cyan] ([cyan]{hexsha[0:11]}[/cyan])"
        )
    else:
        rprint(
            f"[yellow]Creating [cyan]{worktree_name}[/cyan] at [cyan]{commitish}[/cyan] ([cyan]{hexsha[0:11]}[/cyan])"
        )
        create_worktree(repo, tmp_worktree, commitish)
    return tmp_worktree
