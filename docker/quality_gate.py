"""Developer- and CI-friendly quality gate runner."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable
DOCKER_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = DOCKER_ROOT.parent
TEST_ROOT = REPOSITORY_ROOT / "tests"
SOURCE_TARGETS = [
    DOCKER_ROOT / "application",
    DOCKER_ROOT / "domain",
    DOCKER_ROOT / "infrastructure",
]


def _local_lint_imports_path() -> str | None:
    candidate_names = ["lint-imports", "lint-imports.exe"]
    script_directories = [
        Path(PYTHON).parent,
        Path(sys.prefix) / "bin",
        Path(PYTHON).resolve().parent,
    ]
    for scripts_directory in dict.fromkeys(script_directories):
        for candidate_name in candidate_names:
            candidate = scripts_directory / candidate_name
            if candidate.exists():
                return str(candidate)
    return None


LINT_IMPORTS = shutil.which("lint-imports") or _local_lint_imports_path()


def _lint_imports_command() -> list[str]:
    if not LINT_IMPORTS:
        raise RuntimeError(
            "The 'lint-imports' executable was not found on PATH. "
            "Install the development quality tools before running the architecture lint gate."
        )
    return [LINT_IMPORTS, "--config", str(REPOSITORY_ROOT / ".importlinter")]


COMMANDS: dict[str, list[str]] = {
    "lint": [
        PYTHON,
        "-m",
        "ruff",
        "check",
        *map(str, SOURCE_TARGETS),
        str(TEST_ROOT),
    ],
    "arch-tests": [
        PYTHON,
        "-m",
        "unittest",
        "tests.architecture.test_hexagonal_imports",
    ],
    "typecheck": [
        PYTHON,
        "-m",
        "mypy",
        "--explicit-package-bases",
        *map(str, SOURCE_TARGETS),
        str(TEST_ROOT),
    ],
    "test": [
        PYTHON,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(TEST_ROOT),
        "-t",
        str(REPOSITORY_ROOT),
    ],
}
QUALITY_GATE_ORDER = ["lint", "arch-lint", "arch-tests", "typecheck", "test"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local and CI quality gates.")
    parser.add_argument(
        "command",
        nargs="?",
        default="quality",
        choices=["lint", "arch-lint", "arch-tests", "typecheck", "test", "quality"],
        help="The quality command to run.",
    )
    args = parser.parse_args()

    if args.command == "quality":
        for command_name in QUALITY_GATE_ORDER:
            _run_named_command(command_name)
        return 0

    _run_named_command(args.command)
    return 0


def _run_named_command(command_name: str) -> None:
    command = _command_for_name(command_name)
    print(f"[quality] Running {command_name}: {' '.join(command)}", flush=True)
    completed = subprocess.run(
        command,
        check=False,
        cwd=REPOSITORY_ROOT,
        env=_python_environment(),
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _command_for_name(command_name: str) -> list[str]:
    if command_name == "arch-lint":
        return _lint_imports_command()
    return COMMANDS[command_name]


def _python_environment() -> dict[str, str]:
    environment = os.environ.copy()
    python_path = str(DOCKER_ROOT)
    existing_python_path = environment.get("PYTHONPATH")
    if existing_python_path:
        python_path = os.pathsep.join([python_path, existing_python_path])
    environment["PYTHONPATH"] = python_path
    environment["MYPYPATH"] = _prepend_environment_path(
        str(DOCKER_ROOT),
        environment.get("MYPYPATH"),
    )
    environment["PATH"] = _prepend_environment_path(
        str(Path(PYTHON).parent),
        environment.get("PATH"),
    )
    return environment


def _prepend_environment_path(path: str, existing_path: str | None) -> str:
    if existing_path:
        return os.pathsep.join([path, existing_path])
    return path


if __name__ == "__main__":
    raise SystemExit(main())
