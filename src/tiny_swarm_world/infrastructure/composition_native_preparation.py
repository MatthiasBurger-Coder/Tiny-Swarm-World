"""Dependency-light composition for pre-installation host preparation."""

from __future__ import annotations

from pathlib import Path

from tiny_swarm_world.application.services.native_preparation import (
    NativePreparationService,
)
from tiny_swarm_world.infrastructure.adapters.host.native_preparation import (
    NativePreparationInspector,
)
from tiny_swarm_world.infrastructure.adapters.native_package_manager import (
    AptHostPackageManager,
)
from tiny_swarm_world.infrastructure.adapters.native_preparation_evidence import (
    NativePreparationEvidenceWriter,
)


def build_native_preparation_service(
    repository_root: Path, *, service_profile: str = "service-access"
) -> NativePreparationService:
    return NativePreparationService(
        NativePreparationInspector(repository_root, service_profile=service_profile),
        AptHostPackageManager(),
        service_profile=service_profile,
    )


def build_native_preparation_evidence_writer() -> NativePreparationEvidenceWriter:
    return NativePreparationEvidenceWriter()
