import subprocess
from pathlib import Path

from .cmd import is_tool
from .error import fail


def render_dot_file(input_dot_path, output_image_path):
    if not is_tool("dot"):
        fail("Dot is not installed, see [link=https://github.com/westonal/graph-diff#setup]README.md/setup[/link]")
    extension = Path(output_image_path).suffix.lower()
    if extension == ".svg":
        type = "svg"
    else:
        type = "png"
    command = ["dot", f"-T{type}", input_dot_path, "-o", output_image_path]
    return_code = subprocess.run(command).returncode
    if return_code != 0:
        join = ' '.join(map(lambda a: f"{a}", command))
        fail(f"Dot failed return code {return_code} [cyan]{join}")
