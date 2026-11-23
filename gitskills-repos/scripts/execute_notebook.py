"""Execute the analysis with this Python environment and save cell outputs."""

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
# Keep Jupyter runtime files inside the project, including in restricted setups.
os.environ.setdefault("JUPYTER_RUNTIME_DIR", str(ROOT / ".jupyter" / "runtime"))
os.environ.setdefault("IPYTHONDIR", str(ROOT / ".jupyter" / "ipython"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".jupyter" / "matplotlib"))
Path(os.environ["JUPYTER_RUNTIME_DIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["IPYTHONDIR"]).mkdir(parents=True, exist_ok=True)

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpec

path = ROOT / "notebooks" / "skills_per_repository.ipynb"
notebook = nbformat.read(path, as_version=4)
nbformat.validate(notebook)
manager = KernelManager(kernel_name="python3")
manager._kernel_spec = KernelSpec(
    argv=[sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
    display_name="Python 3 (GitSkills)",
    language="python",
)
client = NotebookClient(
    notebook,
    km=manager,
    timeout=600,
    resources={"metadata": {"path": str(ROOT / "notebooks")}},
    allow_errors=False,
    on_cell_start=lambda cell, cell_index: print(f"Executing cell {cell_index + 1}", flush=True),
)
try:
    print("Starting Jupyter kernel...", flush=True)
    client.execute(cleanup_kc=True)
finally:
    nbformat.write(notebook, path)
print(f"Executed successfully: {path}")
