"""Compose the separately consented capability after package/Python/Incus stages."""
from __future__ import annotations

from pathlib import Path


def build_network_preparation_service(prerequisites, paths, validate_paths, *, service_profile: str = "service-access"):
    from tiny_swarm_world.application.services.network_preparation import NetworkPreparationService
    from tiny_swarm_world.infrastructure.adapters.network_preparation.adapter import LocalNetworkPreparation
    from tiny_swarm_world.domain.native_preparation import preparation_target

    facts = prerequisites.plan().facts
    windows = None
    if facts.is_wsl:
        from tiny_swarm_world.infrastructure.adapters.host.windows_command_runner import WindowsCommandRunner
        from tiny_swarm_world.infrastructure.adapters.network_preparation.windows import WindowsNetworkPreparation
        windows = WindowsNetworkPreparation(WindowsCommandRunner(), paths.repository_root, paths.config_root)

    def target():
        plan = prerequisites.plan()
        if not plan.qualified or plan.missing_packages:
            raise RuntimeError("Network prerequisites changed; rerun Linux preparation.")
        return preparation_target(plan.facts) + validate_paths(paths.repository_root, plan.facts.is_wsl)

    return NetworkPreparationService(LocalNetworkPreparation(paths.repository_root, paths.config_root,
                release=facts.version_id, profile=service_profile, target_snapshot=target, windows=windows))


def run_network_preparation(*, read_only: bool, service_profile: str) -> int:
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
            print("BLOCKED: Network preparation requires prepared Python dependencies.")
            return 2
    args: tuple[str, ...] = (python, "-B", "-m", "tiny_swarm_world.prepare_network", "--service-profile", service_profile)
    if read_only:
        args += ("--dry-run",)
    try:
        return SubprocessProcessRunner().run_text(args, env=env, capture_output=False, timeout=900).returncode
    except ProcessTimeoutError:
        print("PARTIAL: Network stage budget exceeded; inspect a fresh read-only plan.")
        return 124
    except ProcessLaunchError:
        print("BLOCKED: Network preparation could not start.")
        return 2
