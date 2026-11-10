"""Developer- and CI-friendly quality gate runner."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

PYTHON = sys.executable
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = REPOSITORY_ROOT / "modules/tsw_core/src"
PACKAGE_ROOT = SOURCE_ROOT
TEST_ROOT = REPOSITORY_ROOT / "modules"
TEST_ROOTS = [TEST_ROOT / module / "tests" for module in (
    "tsw_core", "tsw_native_linux", "tsw_windows_wsl",
)]
SOURCE_TARGETS = [
    PACKAGE_ROOT / "__main__.py",
    PACKAGE_ROOT / "cli_presentation.py",
    PACKAGE_ROOT / "installer.py",
    PACKAGE_ROOT / "simple_installer.py",
    PACKAGE_ROOT / "application",
    PACKAGE_ROOT / "domain",
    PACKAGE_ROOT / "infrastructure",
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
    "verification-policy": [
        PYTHON,
        str(REPOSITORY_ROOT / "modules/tsw_core/tools/linux" / "check_verification_policy_consistency.py"),
    ],
    "complexity": [
        PYTHON,
        str(REPOSITORY_ROOT / "modules/tsw_core/tools/linux" / "check_complexity_guardrails.py"),
    ],
    "lint": [
        PYTHON,
        "-m",
        "ruff",
        "check",
        *map(str, SOURCE_TARGETS),
        *map(str, TEST_ROOTS),
    ],
    "arch-tests": [
        PYTHON,
        "-m",
        "unittest",
        "modules.tsw_core.tests.architecture.test_hexagonal_imports",
        "modules.tsw_core.tests.architecture.test_architecture_regressions",
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
QUALITY_GATE_ORDER = [
    "verification-policy",
    "complexity",
    "lint",
    "arch-lint",
    "arch-tests",
    "typecheck",
    "test",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local and CI quality gates.")
    parser.add_argument(
        "command",
        nargs="?",
        default="quality",
        choices=[
            "verification-policy",
            "complexity",
            "lint",
            "arch-lint",
            "arch-tests",
            "typecheck",
            "test",
            "quality",
        ],
        help="The quality command to run.",
    )
    args = parser.parse_args()

    if args.command == "quality":
        for command_name in QUALITY_GATE_ORDER:
            _run_named_command(command_name)
        return

    _run_named_command(args.command)


def _run_named_command(command_name: str) -> None:
    if command_name == "typecheck":
        _run_typecheck()
        return
    command = _command_for_name(command_name)
    print(f"[quality] Running {command_name}: {' '.join(command)}", flush=True)
    completed = subprocess.run(
        command,
        check=False,
        cwd=REPOSITORY_ROOT,
        env=_python_environment(),
        stdin=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _run_typecheck() -> None:
    """Check the declared package layout, which mypy cannot infer from PEP 660."""
    metadata = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())
    packages = metadata["tool"]["setuptools"]["package-dir"]
    with tempfile.TemporaryDirectory(prefix="tsw-typecheck-") as directory:
        staging = Path(directory)
        built = subprocess.run(
            [PYTHON, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation",
             "--no-index", "--wheel-dir", str(staging), str(REPOSITORY_ROOT)],
            cwd=REPOSITORY_ROOT, env=_python_environment(),
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
        )
        if built.returncode:
            print(built.stdout + built.stderr, end="")
            raise SystemExit(built.returncode)
        wheels = list(staging.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Typecheck requires exactly one locally built project wheel.")
        package_root = staging / "packages"
        with zipfile.ZipFile(wheels[0]) as archive:
            archive.extractall(package_root)
        targets = []
        for name, source in packages.items():
            target = package_root.joinpath(*name.split("."))
            if not (target / "__init__.py").is_file():
                raise RuntimeError(f"Built wheel is missing declared package {name}.")
            targets.append(str(target))
            if REPOSITORY_ROOT / source == SOURCE_ROOT:
                for path in SOURCE_ROOT.rglob("*.py"):
                    relative = path.relative_to(SOURCE_ROOT)
                    packaged = target / relative
                    if not packaged.is_file() or packaged.read_bytes() != path.read_bytes():
                        raise RuntimeError(f"Typecheck wheel omits or changes source {relative}.")
        environment = _python_environment()
        environment["MYPYPATH"] = _prepend_environment_path(
            str(package_root), environment.get("MYPYPATH"),
        )
        command = [
            PYTHON, "-m", "mypy", "--no-incremental", "--explicit-package-bases",
            "--cache-dir", str(staging / "cache"), *targets, *map(str, TEST_ROOTS),
        ]
        print(f"[quality] Running typecheck against current built packages: {' '.join(packages)}", flush=True)
        checked = subprocess.run(
            command, cwd=REPOSITORY_ROOT, env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True,
        )
        output = checked.stdout
        for name, source in packages.items():
            output = output.replace(
                str(package_root.joinpath(*name.split("."))), str(REPOSITORY_ROOT / source),
            )
        print(output, end="")
        if checked.returncode:
            raise SystemExit(checked.returncode)


def _command_for_name(command_name: str) -> list[str]:
    if command_name == "arch-lint":
        return _lint_imports_command()
    return COMMANDS[command_name]


def _python_environment() -> dict[str, str]:
    environment = os.environ.copy()
    python_path = str(REPOSITORY_ROOT)
    existing_python_path = environment.get("PYTHONPATH")
    if existing_python_path:
        python_path = os.pathsep.join([python_path, existing_python_path])
    environment["PYTHONPATH"] = python_path
    environment["MYPYPATH"] = _prepend_environment_path(
        str(REPOSITORY_ROOT),
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
    main()
