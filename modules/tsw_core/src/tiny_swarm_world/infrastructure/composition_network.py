"""Network capability wiring for the public composition root."""

from __future__ import annotations

from tiny_swarm_world.application.services.network import (
    NetworkDoctorService,
    NetworkRepairOptions,
    NetworkRepairService,
)
from tiny_swarm_world.infrastructure.adapters.network import (
    SubprocessNetworkProbe,
    SubprocessNetworkRepair,
)
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)

from . import composition_runtime as _runtime


def build_network_doctor_service() -> NetworkDoctorService:
    project_paths = _runtime.default_project_paths()
    port_registry = PortRegistryYamlRepository(project_paths=project_paths).load()
    return NetworkDoctorService(
        SubprocessNetworkProbe(
            host_environment_detector=_runtime.build_host_environment_detector()
        ),
        port_registry,
    )


def build_network_repair_service() -> NetworkRepairService:
    return NetworkRepairService(
        SubprocessNetworkProbe(
            host_environment_detector=_runtime.build_host_environment_detector()
        ),
        SubprocessNetworkRepair(),
    )


def build_network_repair_options(
    *,
    runtime: str | None,
    linux_forwarding: bool,
    incus: bool,
    apply: bool,
) -> NetworkRepairOptions:
    return NetworkRepairOptions(
        runtime=runtime,
        linux_forwarding=linux_forwarding,
        incus=incus,
        apply=apply,
    )
