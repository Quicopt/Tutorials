"""Execute tutorial notebooks against the live Quicopt server and store the outputs.

A notebook here is executed once and committed with its outputs. Every solve's
output includes ``solve_time``. The first call after a pause takes several times
longer than the calls that follow, so this script warms the server up with one
small solve first. It also runs the notebooks one after another rather than in
parallel, because concurrent solves slow each other down.

After execution, the output of the ``%pip install`` cell is cleared (pip prints
local paths), and ``metadata.quicopt`` records which client version produced the
outputs, and on which date.

Usage (from the repo root, with the environment from requirements.txt)::

    .venv/bin/python tools/execute.py notebooks/knapsack.ipynb [more.ipynb ...]
"""
import argparse
import datetime
import importlib.metadata
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from ortools.math_opt.python import mathopt
from quicopt import Client


def warm_up() -> None:
    """Send one small linear program to the server, so later solves run warm."""
    model = mathopt.Model(name="warm-up")
    x = model.add_variable(lb=0.0, ub=1.0, name="x")
    model.maximize(x)
    Client().solve(model)


def is_install_cell(cell: nbformat.NotebookNode) -> bool:
    """Return whether a cell is the notebook's ``%pip install`` line.

    Args:
        cell: Any notebook cell.

    Returns:
        True for a code cell whose source starts with ``%pip install``.
    """
    return cell.cell_type == "code" and cell.source.startswith("%pip install")


def execute(path: Path) -> None:
    """Execute one notebook in place, top to bottom, on the generic python3 kernel.

    Args:
        path: The notebook to execute; it is overwritten with its outputs.

    Raises:
        nbclient.exceptions.CellExecutionError: If any cell raises.
    """
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(notebook, kernel_name="python3", timeout=600, record_timing=False,
                            resources={"metadata": {"path": str(path.parent)}})
    client.execute()
    for cell in filter(is_install_cell, notebook.cells):
        cell.outputs = []
    notebook.metadata["quicopt"] = {
        "client": importlib.metadata.version("quicopt"),
        "executed": datetime.date.today().isoformat(),
    }
    nbformat.write(notebook, path)


def main() -> None:
    """Warm the server up, then execute the given notebooks one after another.

    A notebook whose execution fails is left untouched on disk and reported;
    the others still run. The exit status is 1 if any failed.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("notebooks", type=Path, nargs="+")
    args = parser.parse_args()

    warm_up()
    failed = []
    for path in args.notebooks:
        try:
            execute(path)
            print(f"executed {path}")
        except CellExecutionError as error:
            failed.append(path)
            print(f"FAILED {path}\n{error}", file=sys.stderr)
    if failed:
        sys.exit(f"{len(failed)} failed: {', '.join(map(str, failed))}")


if __name__ == "__main__":
    main()
