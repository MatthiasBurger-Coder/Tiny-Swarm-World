"""Dependency-light composition for pre-installation host preparation."""

from __future__ import annotations

from pathlib import Path
from tiny_swarm_world.domain.native_preparation import preparation_target, qualification_failures
import platform

from tiny_swarm_world.application.services.native_preparation import (
    NativePreparationService,
)
from tiny_swarm_world.infrastructure.adapters.host.native_preparation import (
    NativePreparationInspector,
    WslUbuntuPreparationInspector,
)
from tiny_swarm_world.infrastructure.adapters.native_package_manager import (
    AptHostPackageManager,
    confirm_apt_candidates,
)
from tiny_swarm_world.infrastructure.adapters.native_preparation_evidence import (
    NativePreparationEvidenceWriter,
)


def build_native_preparation_service(
    repository_root: Path, *, service_profile: str = "service-access",
    prerequisites_only: bool = False,
) -> NativePreparationService:
    kernel = platform.release().casefold()
    inspector_type = WslUbuntuPreparationInspector if "microsoft" in kernel or "wsl" in kernel else NativePreparationInspector
    inspector = inspector_type(repository_root, service_profile=service_profile)
    return NativePreparationService(
        inspector,
        AptHostPackageManager(candidate_consent=confirm_apt_candidates if prerequisites_only else None,
                              target_snapshot=(lambda: _prerequisite_snapshot(inspector, repository_root, service_profile)) if prerequisites_only else None),
        service_profile=service_profile,
        prerequisites_only=prerequisites_only,
    )


def build_native_preparation_evidence_writer() -> NativePreparationEvidenceWriter:
    return NativePreparationEvidenceWriter()


def validate_preparation_paths(repository_root: Path, *, is_wsl: bool) -> tuple[str, ...]:
    from tiny_swarm_world.infrastructure.adapters.installation.prerequisites import (
        validate_assets, validate_user_paths,
    )
    from tiny_swarm_world.infrastructure.composition_installation import _paths_from_env
    import os
    import hashlib

    validate_assets(repository_root)
    validate_user_paths(repository_root, _paths_from_env(os.environ, repository_root).native_linux_venv, is_wsl=is_wsl)

    return tuple(hashlib.sha256((repository_root / name).read_bytes()).hexdigest()
                 for name in ("requirements.lock", "requirements.build.lock", "pyproject.toml"))


def _prerequisite_snapshot(inspector: NativePreparationInspector, root: Path, profile: str) -> tuple[object, ...]:
    facts = inspector.inspect()
    failures = qualification_failures(facts, needs_network=True, prerequisites_only=True,
                                      allow_wsl=True, service_profile=profile)
    if failures:
        raise RuntimeError("Host prerequisites changed; review ./prepare_linux.sh --dry-run.")
    return preparation_target(facts) + validate_preparation_paths(root, is_wsl=facts.is_wsl)


def record_python_preparation(status: str) -> Path:
    from tiny_swarm_world.infrastructure.adapters.host.native_preparation import _os_release

    return build_native_preparation_evidence_writer().write(
        platform_release=_os_release().get("VERSION_ID", "unknown"),
        status=status, planned=(), added=(), uncertain=(),
        stage="python_environment_" + status,
    )
