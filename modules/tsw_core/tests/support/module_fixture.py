"""Copy the real core layout into disposable source-checkout fixtures."""
from pathlib import Path
import shutil


def copy_core_source(repository: Path, destination: Path) -> None:
    source = repository / "modules/tsw_core"
    target = destination / "modules/tsw_core"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "__init__.py", target / "__init__.py")
    shutil.copytree(
        source / "src", target / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
