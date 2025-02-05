import subprocess

from src.cmd import is_tool
from src.error import fail


def render_dot_file(input_dot_path, output_png_path):
    if not is_tool("dot"):
        fail("Dot is not installed, see [link=https://github.com/westonal/graph-diff#setup]README.md/setup[/link]")
    command = ["dot", "-Tpng", input_dot_path, "-o", output_png_path]
    return_code = subprocess.run(command).returncode
    if return_code != 0:
        join = ' '.join(map(lambda a: f"{a}", command))
        fail(f"Dot failed return code {return_code} [cyan]{join}")
