"""Operator entry point for separate native Linux host preparation."""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path

from tiny_swarm_world.infrastructure.composition_native_preparation import (
    build_native_preparation_evidence_writer,
    build_native_preparation_service,
    record_python_preparation,
    run_incus_preparation,
    run_network_preparation,
)



def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare native or WSL2 Ubuntu 24.04/26.04 package/Python prerequisites, separately from services.")
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

    service = build_native_preparation_service(Path.cwd(), service_profile=args.service_profile, prerequisites_only=True)
    try:
        plan = service.plan()
    except (OSError, RuntimeError, ValueError):
        print("ERROR: Native preparation inventory failed; inspect host package tools.", file=sys.stderr)
        return 1
    if not (args.preflight or args.dry_run):
        try:
            path_identity = _validate_mutation_paths(is_wsl=plan.facts.is_wsl)
        except (OSError, RuntimeError):
            print("BLOCKED: Use an ordinary account, complete trusted release and owned Linux-native checkout/venv. Next: ./prepare_linux.sh --dry-run", file=sys.stderr)
            return 2
    if plan.failures:
        for failure in plan.failures:
            print(f"BLOCKED: {failure}", file=sys.stderr)
        print("No host packages were changed.", file=sys.stderr)
        return 1
    print(f"Ubuntu {plan.facts.version_id} x86_64 prerequisite preflight passed (WSL2={plan.facts.is_wsl}).")
    if not plan.missing_packages:
        print("Host packages are already prepared; no changes needed.")
        return _prepare_remaining(read_only=args.preflight or args.dry_run,
                                  service_profile=args.service_profile)
    print("Missing host packages: " + ", ".join(plan.missing_packages))
    if args.preflight or args.dry_run:
        print("No host packages were changed.")
        _prepare_python_dependencies(read_only=True)
        return 2

    try:
        answer = input("Refresh APT indexes, then review exact package candidates? Type 'yes' to continue: ")
    except EOFError:
        answer = ""
    except KeyboardInterrupt:
        print("\nPreparation interrupted before package installation.", file=sys.stderr)
        return 130
    if answer != "yes":
        print("Preparation cancelled; no host packages were changed.")
        return 2

    try:
        if _validate_mutation_paths(is_wsl=plan.facts.is_wsl) != path_identity:
            raise RuntimeError("Release assets changed.")
    except (OSError, RuntimeError):
        print("BLOCKED: Release/path changed after consent. Next: ./prepare_linux.sh --dry-run", file=sys.stderr)
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
        print("ERROR: Package preparation stopped. Inspect APT connectivity/locks; package indexes may have changed. Next: ./prepare_linux.sh --dry-run", file=sys.stderr)
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
    return _prepare_remaining(read_only=False, service_profile=args.service_profile)


def _prepare_remaining(*, read_only: bool, service_profile: str) -> int:
    result = _prepare_python_dependencies(read_only=read_only)
    if result:
        return result
    result = run_incus_preparation(read_only=read_only, service_profile=service_profile)
    if result:
        return result
    result = run_network_preparation(read_only=read_only, service_profile=service_profile)
    if result == 0:
        command = f"cd -- {shlex.quote(str(Path.cwd()))} && ./install.sh --service-profile {shlex.quote(service_profile)}"
        print("Linux preparation ready; services are not verified.")
        print("Next: " + command)
    return result


def _prepare_python_dependencies(*, read_only: bool) -> int:
    from tiny_swarm_world.infrastructure import composition_installation as installer

    env = os.environ
    paths = installer._paths_from_env(env, Path.cwd())
    prepared_python = paths.native_linux_venv / "bin" / "python"
    try:
        ready = installer._python_imports_available(sys.executable, env)
        if not ready and prepared_python.is_file():
            runtime = installer.detect_host_runtime(env)
            _validate_mutation_paths(is_wsl=runtime.name == "wsl2")
            ready = installer._python_imports_available(prepared_python.as_posix(), env)
    except (installer.InstallerError, OSError, RuntimeError):
        print("BLOCKED: Python probe failed or timed out. Next: ./prepare_linux.sh --dry-run", file=sys.stderr)
        return 2
    if ready:
        print("Python dependencies are already prepared; services are not verified.")
        print("Next: ./prepare_linux.sh --preflight")
        return 0
    print("Python dependencies are missing from the system interpreter and prepared venv.")
    if read_only:
        print("BLOCKED: No Python environment was changed. Next: ./prepare_linux.sh")
        return 2
    try:
        runtime = installer.detect_host_runtime(env)
        identity = _validate_mutation_paths(is_wsl=runtime.name == "wsl2")
    except (OSError, RuntimeError):
        print("BLOCKED: Python target is unsafe. Next: ./prepare_linux.sh --dry-run", file=sys.stderr)
        return 2
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
        if _validate_mutation_paths(is_wsl=runtime.name == "wsl2") != identity:
            raise RuntimeError("Python release assets changed after consent.")
        print(f"Python preparation evidence: {record_python_preparation('started')}")
        python_bin = installer.ensure_python_environment(
            runtime, paths, env
        )
        if not installer._python_imports_available(python_bin, env):
            raise installer.InstallerError("Prepared Python dependencies are not importable.")
        record_python_preparation("succeeded")
    except KeyboardInterrupt:
        _record_python_failure("interrupted")
        print("PARTIAL: Python preparation interrupted. Next: ./prepare_linux.sh --dry-run", file=sys.stderr)
        return 130
    except (installer.InstallerError, OSError, RuntimeError):
        _record_python_failure("failed")
        print("ERROR: Python preparation failed; inspect the local venv and rerun ./prepare_linux.sh.", file=sys.stderr)
        return 1
    print("Local Python dependencies are prepared; Incus/network readiness and services are not verified.")
    return 0


def _validate_mutation_paths(*, is_wsl: bool) -> tuple[str, ...]:
    from tiny_swarm_world.infrastructure.composition_native_preparation import validate_preparation_paths

    return validate_preparation_paths(Path.cwd(), is_wsl=is_wsl)


def _record_python_failure(status: str) -> None:
    try:
        record_python_preparation(status)
    except OSError:
        print("PARTIAL: Python preparation stopped and evidence write failed. Next: ./prepare_linux.sh --dry-run", file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
