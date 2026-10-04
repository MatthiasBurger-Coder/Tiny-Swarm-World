"""Composition for the separately consented Incus preparation capability."""
from __future__ import annotations

from pathlib import Path
from collections.abc import Callable
from tiny_swarm_world.application.services.native_preparation import NativePreparationService
from tiny_swarm_world.domain.native_preparation import preparation_target
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths, default_project_paths


def preparation_paths() -> ProjectPaths:
    return default_project_paths()


def build_incus_preparation_service(prerequisites: NativePreparationService, paths: ProjectPaths,
                                   validate_paths: Callable[[Path, bool], tuple[str, ...]]):
    from tiny_swarm_world.application.services.incus_preparation import IncusPreparationService
    from tiny_swarm_world.infrastructure.adapters.incus_preparation.adapter import LocalIncusPreparation

    def snapshot() -> tuple[object, ...]:
        plan = prerequisites.plan()
        if not plan.qualified or plan.missing_packages:
            raise RuntimeError("Ubuntu prerequisites changed; rerun ./prepare_linux.sh.")
        identity = validate_paths(paths.repository_root, plan.facts.is_wsl)
        return preparation_target(plan.facts) + identity

    facts = prerequisites.plan().facts
    return IncusPreparationService(LocalIncusPreparation(
        paths.config_root / "node-providers/provider_config.yaml",
        release=facts.version_id, target_snapshot=snapshot,
    ))


def run_incus_preparation(*, read_only: bool, service_profile: str) -> int:
    import os
    import sys
    from tiny_swarm_world.infrastructure import composition_installation as installer
    from tiny_swarm_world.infrastructure.process import ProcessLaunchError, ProcessTimeoutError, SubprocessProcessRunner

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    paths = installer._paths_from_env(env, Path.cwd())
    python = sys.executable
    if not installer._python_imports_available(python, env):
        python = (paths.native_linux_venv / "bin/python").as_posix()
        if not installer._python_imports_available(python, env):
            print("BLOCKED: Incus configuration needs prepared Python dependencies. Next: ./prepare_linux.sh")
            return 2
    args: tuple[str, ...] = (python, "-B", "-m", "tiny_swarm_world.prepare_incus", "--service-profile", service_profile)
    if read_only:
        args += ("--dry-run",)
    try:
        return SubprocessProcessRunner().run_text(args, env=env, capture_output=False, timeout=1800).returncode
    except ProcessTimeoutError:
        print("PARTIAL: Incus preparation timed out; inspect evidence/state. Next: ./prepare_linux.sh --dry-run")
        return 124
    except ProcessLaunchError:
        print("BLOCKED: Prepared Python cannot start Incus preparation. Next: ./prepare_linux.sh --dry-run")
        return 2
