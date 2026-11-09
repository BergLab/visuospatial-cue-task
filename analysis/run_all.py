"""Generate all figure panels and run every statement script."""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "statements")]

scripts = [HERE / "fig2.py", HERE / "fig3.py", HERE / "fig4.py",
           *sorted((HERE / "statements").glob("s*.py"))]
for path in scripts:
    print(f"\n{'#' * 20} {path.name}")
    runpy.run_path(str(path), run_name="__main__")
