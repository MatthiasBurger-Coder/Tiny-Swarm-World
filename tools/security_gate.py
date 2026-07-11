"""Explicit local supply-chain checks kept outside the default quality gate."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PYTHON = sys.executable
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_LOCK = REPOSITORY_ROOT / "requirements.lock"
DEFAULT_SBOM = (
    REPOSITORY_ROOT
    / ".tiny-swarm-world"
    / "evidence"
    / "security"
    / "runtime-dependencies.cdx.json"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run explicit local dependency, SBOM, or container-config checks."
    )
    parser.add_argument(
        "command",
        choices=("dependencies", "sbom", "container-config"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_SBOM,
        help="Ignored local CycloneDX output path used by the sbom command.",
    )
    args = parser.parse_args()

    if args.command == "dependencies":
        _run(_dependency_audit_command())
        return
    if args.command == "sbom":
        output = args.output.resolve()
        _require_ignored_local_output(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        _run(_sbom_command(output))
        print(f"[security] Wrote ignored local SBOM: {output}", flush=True)
        return

    trivy = shutil.which("trivy")
    if trivy is None:
        raise SystemExit(
            "The 'trivy' executable is required for container-config checks. "
            "Install it explicitly; the default quality gate does not install external scanners."
        )
    _run(_container_config_command(trivy))


def _dependency_audit_command() -> list[str]:
    return [
        PYTHON,
        "-m",
        "pip_audit",
        "--strict",
        "--disable-pip",
        "--progress-spinner",
        "off",
        "--requirement",
        str(RUNTIME_LOCK),
    ]


def _sbom_command(output: Path) -> list[str]:
    return [
        *_dependency_audit_command(),
        "--format",
        "cyclonedx-json",
        "--output",
        str(output),
    ]


def _container_config_command(trivy: str) -> list[str]:
    return [
        trivy,
        "config",
        "--exit-code",
        "1",
        "--severity",
        "HIGH,CRITICAL",
        str(REPOSITORY_ROOT / "infra" / "config" / "compose"),
    ]


def _require_ignored_local_output(output: Path) -> None:
    local_root = (REPOSITORY_ROOT / ".tiny-swarm-world").resolve()
    if output == local_root or local_root not in output.parents:
        raise SystemExit("SBOM output must stay below ignored .tiny-swarm-world local state.")


def _run(command: list[str]) -> None:
    print(f"[security] Running: {' '.join(command)}", flush=True)
    completed = subprocess.run(command, check=False, cwd=REPOSITORY_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
