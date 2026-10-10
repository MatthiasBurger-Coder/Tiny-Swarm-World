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
    allow_wsl: bool = False,
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
        allow_wsl=allow_wsl,
    )


def build_native_preparation_evidence_writer(*, service_profile: str = "service-access") -> NativePreparationEvidenceWriter:
    return NativePreparationEvidenceWriter(selection=service_profile)


def validate_preparation_paths(repository_root: Path, *, is_wsl: bool) -> tuple[str, ...]:
    from tiny_swarm_world.infrastructure.adapters.installation.prerequisites import (
        validate_assets, validate_user_paths,
    )
    from tiny_swarm_world.infrastructure.composition_installation import _paths_from_env
    import os

    validate_assets(repository_root)
    validate_user_paths(repository_root, _paths_from_env(os.environ, repository_root).native_linux_venv, is_wsl=is_wsl)

    from tiny_swarm_world.infrastructure.adapters.network_preparation.source_identity import preparation_asset_hashes

    return preparation_asset_hashes(repository_root, is_wsl=is_wsl)


def _prerequisite_snapshot(inspector: NativePreparationInspector, root: Path, profile: str) -> tuple[object, ...]:
    facts = inspector.inspect()
    failures = qualification_failures(facts, needs_network=True, prerequisites_only=True,
                                      allow_wsl=True, service_profile=profile)
    if failures:
        raise RuntimeError("Host prerequisites changed; review ./prepare_linux.sh --dry-run.")
    return preparation_target(facts) + validate_preparation_paths(root, is_wsl=facts.is_wsl)


def package_preparation_observation(facts, missing: tuple[str, ...]) -> str:
    return NativePreparationEvidenceWriter.fingerprint((preparation_target(facts), missing))


def python_preparation_observation(status: str) -> str:
    observed_ready = {"started": False, "succeeded": True}.get(status)
    return NativePreparationEvidenceWriter.fingerprint(("dependencies_importable", observed_ready))


def record_python_preparation(status: str, *, writer: NativePreparationEvidenceWriter | None = None) -> Path:
    from tiny_swarm_world.infrastructure.adapters.host.native_preparation import _os_release

    return (writer or build_native_preparation_evidence_writer()).write(
        platform_release=_os_release().get("VERSION_ID", "unknown"),
        status=status, planned=("python:environment",),
        added=("python:environment",) if status == "succeeded" else (),
        uncertain=() if status == "succeeded" else ("python:environment",),
        stage="python_environment_" + status, capability="python",
        observation=python_preparation_observation(status),
        cause=status if status in {"failed", "interrupted"} else "none",
    )


def build_incus_preparation_service(*, service_profile: str = "service-access"):
    from tiny_swarm_world.infrastructure import composition_incus_preparation

    paths = composition_incus_preparation.preparation_paths()
    prerequisites = build_native_preparation_service(paths.repository_root,
                            service_profile=service_profile, prerequisites_only=True)
    return composition_incus_preparation.build_incus_preparation_service(
        prerequisites, paths, lambda root, wsl: validate_preparation_paths(root, is_wsl=wsl),
    )


def run_incus_preparation(*, read_only: bool, service_profile: str) -> int:
    from tiny_swarm_world.infrastructure import composition_incus_preparation

    return composition_incus_preparation.run_incus_preparation(read_only=read_only, service_profile=service_profile)


async def request_incus_consent(*, capability: str = "Incus") -> bool:
    from tiny_swarm_world.infrastructure import composition_incus_preparation

    return await composition_incus_preparation.request_incus_consent(capability=capability)


def run_network_preparation(*, read_only: bool, service_profile: str) -> int:
    from tiny_swarm_world.infrastructure import composition_network_preparation

    return composition_network_preparation.run_network_preparation(read_only=read_only, service_profile=service_profile)


def build_network_preparation_service(*, service_profile: str = "service-access"):
    from tiny_swarm_world.infrastructure import composition_network_preparation, composition_incus_preparation

    paths = composition_incus_preparation.preparation_paths()
    prerequisites = build_native_preparation_service(paths.repository_root, service_profile=service_profile, prerequisites_only=True)
    return composition_network_preparation.build_network_preparation_service(prerequisites, paths,
             lambda root, wsl: validate_preparation_paths(root, is_wsl=wsl), service_profile=service_profile)


async def request_network_consent() -> bool:
    return await request_incus_consent(capability="network prerequisite")
