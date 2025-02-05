from rich import print as rprint


def fail(message):
    rprint(f"[red]{message}")
    exit(1)
