"""Operator entry point for separate native Linux host preparation."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from tiny_swarm_world.infrastructure.composition_native_preparation import (
    build_native_preparation_evidence_writer,
    build_native_preparation_service,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare an Ubuntu 24.04 or 26.04 host for Tiny Swarm World.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="Validate without changing the host.")
    mode.add_argument("--dry-run", action="store_true", help="Show the package plan without changing the host.")
    parser.add_argument(
        "--service-profile",
        choices=("default", "service-access"),
        default="service-access",
        help="Select the supported host dependency profile.",
    )
    args = parser.parse_args(argv)

    service = build_native_preparation_service(Path.cwd(), service_profile=args.service_profile)
    try:
        plan = service.plan()
    except (OSError, RuntimeError, ValueError):
        print("ERROR: Native preparation inventory failed; inspect host package tools.", file=sys.stderr)
        return 1
    if plan.failures:
        for failure in plan.failures:
            print(f"BLOCKED: {failure}", file=sys.stderr)
        print("No host packages were changed.", file=sys.stderr)
        return 1
    print(f"Native Ubuntu {plan.facts.version_id} x86_64 preflight passed.")
    if not plan.missing_packages:
        print("Host packages are already prepared; no changes needed.")
        if not (args.preflight or args.dry_run):
            try:
                path = build_native_preparation_evidence_writer().write(
                    platform_release=plan.facts.version_id,
                    status="noop",
                    planned=(),
                    added=(),
                    uncertain=(),
                    stage="package_inventory",
                )
            except OSError:
                print("ERROR: Protected local evidence could not be written; check owner and mode 0700 of Tiny Swarm World state directories.", file=sys.stderr)
                return 1
            print(f"Evidence: {path}")
        return _prepare_python_dependencies(read_only=args.preflight or args.dry_run)
    print("Missing host packages: " + ", ".join(plan.missing_packages))
    if args.preflight or args.dry_run:
        print("No host packages were changed.")
        return 0

    try:
        answer = input("Install these host packages with APT? Type 'yes' to continue: ")
    except EOFError:
        answer = ""
    except KeyboardInterrupt:
        print("\nPreparation interrupted before package installation.", file=sys.stderr)
        return 130
    if answer != "yes":
        print("Preparation cancelled; no host packages were changed.")
        return 2

    evidence = build_native_preparation_evidence_writer()
    try:
        started_path = evidence.write(
            platform_release=plan.facts.version_id,
            status="started",
            planned=plan.missing_packages,
            added=(),
            uncertain=plan.missing_packages,
            stage="package_install_pending",
        )
    except OSError:
        print("ERROR: Protected local evidence cannot be written; check owner and mode 0700 of Tiny Swarm World state directories. No host packages were changed.", file=sys.stderr)
        return 1
    print(f"Preparation started; evidence: {started_path}")
    try:
        added = service.apply(plan)
    except (OSError, RuntimeError, ValueError, KeyboardInterrupt) as error:
        # Inventory after a failed APT invocation distinguishes confirmed
        # additions from packages whose state remains uncertain.
        try:
            after = service.plan()
            added = tuple(
                item for item in plan.missing_packages if item not in after.missing_packages
            )
            uncertain = tuple(
                item for item in plan.missing_packages if item in after.missing_packages
            )
        except (OSError, RuntimeError, ValueError):
            added, uncertain = (), plan.missing_packages
        try:
            path = evidence.write(
                platform_release=plan.facts.version_id,
                status="interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                planned=plan.missing_packages,
                added=added,
                uncertain=uncertain,
                stage="package_install_or_verify",
            )
        except OSError:
            print("ERROR: Package preparation failed and local evidence could not be written.", file=sys.stderr)
            return 130 if isinstance(error, KeyboardInterrupt) else 1
        print("ERROR: Package preparation stopped. Inspect APT state, then rerun preparation.", file=sys.stderr)
        print(f"Evidence: {path}", file=sys.stderr)
        return 130 if isinstance(error, KeyboardInterrupt) else 1
    try:
        path = evidence.write(
            platform_release=plan.facts.version_id,
            status="succeeded",
            planned=plan.missing_packages,
            added=added,
            uncertain=(),
            stage="package_verify",
        )
    except OSError:
        print("ERROR: Packages were installed but local evidence could not be written; verify the host before retrying.", file=sys.stderr)
        return 1
    print("Native host package preparation completed.")
    print(f"Evidence: {path}")
    python_result = _prepare_python_dependencies(read_only=False)
    if python_result != 0:
        return python_result
    print("Next: run ./install.sh after reviewing the installer preflight.")
    return 0


def _prepare_python_dependencies(*, read_only: bool) -> int:
    from tiny_swarm_world.infrastructure import composition_installation as installer

    env = os.environ
    paths = installer._paths_from_env(env, Path.cwd())
    prepared_python = paths.native_linux_venv / "bin" / "python"
    if installer._python_imports_available(sys.executable, env) or (
        prepared_python.is_file()
        and installer._python_imports_available(prepared_python.as_posix(), env)
    ):
        print("Python dependencies are already prepared.")
        return 0
    print("Python dependencies are missing from the system interpreter and prepared venv.")
    if read_only:
        print("No Python environment was changed; run ./prepare_linux.sh to prepare it.")
        return 0
    try:
        answer = input("Prepare the local Python environment? Type 'yes' to continue: ")
    except EOFError:
        answer = ""
    except KeyboardInterrupt:
        print("\nPython preparation interrupted before bootstrap.", file=sys.stderr)
        return 130
    if answer != "yes":
        print("Python preparation cancelled; rerun ./prepare_linux.sh before installing.")
        return 2
    try:
        python_bin = installer.ensure_python_environment(
            installer.detect_host_runtime(env), paths, env
        )
        if not installer._python_imports_available(python_bin, env):
            raise installer.InstallerError("Prepared Python dependencies are not importable.")
    except (installer.InstallerError, OSError, RuntimeError):
        print("ERROR: Python preparation failed; inspect the local venv and rerun ./prepare_linux.sh.", file=sys.stderr)
        return 1
    print("Local Python dependencies are prepared.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
