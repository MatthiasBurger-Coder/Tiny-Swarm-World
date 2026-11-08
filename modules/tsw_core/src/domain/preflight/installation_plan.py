from __future__ import annotations

import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, TypeVar


PHASE_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
WorkflowPhase = TypeVar("WorkflowPhase")


@dataclass(frozen=True)
class InstallationPhase:
    phase_id: str
    order: int
    required: bool = True
    depends_on: tuple[str, ...] = ()
    services: tuple[str, ...] = ()
    workflow_phase_names: tuple[str, ...] = ()
    parallel_group: str | None = None

    def __post_init__(self) -> None:
        _validate_phase_identifier(self.phase_id, "phase_id")
        if not isinstance(self.order, int) or self.order < 0:
            raise ValueError("installation phase order must be a non-negative integer")
        depends_on = tuple(_normalized_identifier(item, "depends_on") for item in self.depends_on)
        if self.phase_id in depends_on:
            raise ValueError("installation phase cannot depend on itself")
        object.__setattr__(self, "depends_on", depends_on)
        object.__setattr__(self, "services", _normalized_non_empty_tuple(self.services, "services"))
        object.__setattr__(
            self,
            "workflow_phase_names",
            _normalized_non_empty_tuple(self.workflow_phase_names, "workflow_phase_names"),
        )
        if self.parallel_group is not None:
            object.__setattr__(
                self,
                "parallel_group",
                _normalized_identifier(self.parallel_group, "parallel_group"),
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.phase_id,
            "order": self.order,
            "required": self.required,
            "depends_on": list(self.depends_on),
            "services": list(self.services),
            "workflow_phases": list(self.workflow_phase_names),
            "parallel_group": self.parallel_group,
        }


@dataclass(frozen=True)
class InstallationPhaseGroup:
    group_id: str
    phase_ids: tuple[str, ...]
    maximum_concurrency: int
    serial_barrier: bool = True

    def __post_init__(self) -> None:
        _validate_phase_identifier(self.group_id, "group_id")
        phase_ids = tuple(_normalized_identifier(item, "phase_ids") for item in self.phase_ids)
        if not phase_ids:
            raise ValueError("installation phase group must contain phases")
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("installation phase group contains duplicate phases")
        if not isinstance(self.maximum_concurrency, int) or self.maximum_concurrency <= 0:
            raise ValueError("installation phase group concurrency must be positive")
        object.__setattr__(self, "phase_ids", phase_ids)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.group_id,
            "phase_ids": list(self.phase_ids),
            "maximum_concurrency": self.maximum_concurrency,
            "serial_barrier": self.serial_barrier,
        }


@dataclass(frozen=True)
class InstallationPlan:
    phases: tuple[InstallationPhase, ...]
    required_phase_ids: tuple[str, ...] = ()
    required_services: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        phases = tuple(self.phases)
        required_phase_ids = tuple(
            _normalized_identifier(item, "required_phase_ids")
            for item in self.required_phase_ids
        )
        required_services = _normalized_non_empty_tuple(
            self.required_services,
            "required_services",
        )
        _reject_duplicate_phase_ids(phases)
        _reject_missing_dependencies(phases)
        _reject_missing_required_phases(phases, required_phase_ids)
        _ordered_installation_phases(phases)
        _reject_missing_required_services(phases, required_services)
        object.__setattr__(self, "phases", phases)
        object.__setattr__(self, "required_phase_ids", required_phase_ids)
        object.__setattr__(self, "required_services", required_services)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def phase_ids(self) -> tuple[str, ...]:
        return tuple(phase.phase_id for phase in self.phases)

    @property
    def required_workflow_phase_names(self) -> tuple[str, ...]:
        return tuple(
            workflow_phase
            for phase in self.ordered_phases()
            if phase.required
            for workflow_phase in phase.workflow_phase_names
        )

    def ordered_phases(self) -> tuple[InstallationPhase, ...]:
        return _ordered_installation_phases(self.phases)

    def ordered_workflow_phase_names(self) -> tuple[str, ...]:
        return tuple(
            workflow_phase
            for phase in self.ordered_phases()
            for workflow_phase in phase.workflow_phase_names
        )

    def phase_groups(self, maximum_concurrency: int = 2) -> tuple[InstallationPhaseGroup, ...]:
        if not isinstance(maximum_concurrency, int) or maximum_concurrency <= 0:
            raise ValueError("maximum phase concurrency must be positive")
        phases_by_id = {phase.phase_id: phase for phase in self.phases}
        group_phase_ids: dict[str, list[str]] = {}
        for phase in self.ordered_phases():
            group_id = phase.parallel_group or phase.phase_id
            group_phase_ids.setdefault(group_id, []).append(phase.phase_id)
        phase_to_group = {
            phase_id: group_id
            for group_id, phase_ids in group_phase_ids.items()
            for phase_id in phase_ids
        }
        dependencies: dict[str, set[str]] = {group_id: set() for group_id in group_phase_ids}
        for phase in phases_by_id.values():
            group_id = phase_to_group[phase.phase_id]
            for dependency in phase.depends_on:
                dependency_group = phase_to_group[dependency]
                if dependency_group == group_id:
                    raise ValueError(
                        f"installation phase group '{group_id}' contains a dependency edge"
                    )
                dependencies[group_id].add(dependency_group)

        pending = set(group_phase_ids)
        ordered_group_ids: list[str] = []
        while pending:
            ready = sorted(
                (
                    group_id
                    for group_id in pending
                    if dependencies[group_id].isdisjoint(pending)
                ),
                key=lambda group_id: (
                    min(phases_by_id[phase_id].order for phase_id in group_phase_ids[group_id]),
                    group_id,
                ),
            )
            if not ready:
                raise ValueError("installation phase group dependency graph contains a cycle")
            group_id = ready[0]
            ordered_group_ids.append(group_id)
            pending.remove(group_id)

        return tuple(
            InstallationPhaseGroup(
                group_id=group_id,
                phase_ids=tuple(group_phase_ids[group_id]),
                maximum_concurrency=min(maximum_concurrency, len(group_phase_ids[group_id])),
            )
            for group_id in ordered_group_ids
        )

    def arrange_workflow_phases(
        self,
        phases: tuple[WorkflowPhase, ...],
    ) -> tuple[WorkflowPhase, ...]:
        by_name: dict[str, WorkflowPhase] = {}
        for phase in phases:
            name = str(getattr(phase, "name", "")).strip()
            if not name:
                raise ValueError("setup workflow phase must have a non-empty name")
            if name in by_name:
                raise ValueError(f"duplicate setup workflow phase '{name}'")
            by_name[name] = phase

        declared_names = self.ordered_workflow_phase_names()
        declared_name_set = set(declared_names)
        missing_required = tuple(
            name for name in self.required_workflow_phase_names if name not in by_name
        )
        if missing_required:
            raise ValueError(
                "required setup workflow phases are missing: "
                + ", ".join(missing_required)
            )

        unknown = tuple(name for name in by_name if name not in declared_name_set)
        if unknown:
            raise ValueError(
                "setup workflow phases are not declared in installation plan: "
                + ", ".join(unknown)
            )

        return tuple(by_name[name] for name in declared_names if name in by_name)

    def to_dict(self) -> dict[str, object]:
        return {
            "metadata": dict(self.metadata),
            "required_phase_ids": list(self.required_phase_ids),
            "required_services": list(self.required_services),
            "phases": [phase.to_dict() for phase in self.phases],
            "phase_groups": [group.to_dict() for group in self.phase_groups()],
        }


def default_installation_plan() -> InstallationPlan:
    return InstallationPlan(
        phases=(
            InstallationPhase(
                phase_id="preflight",
                order=0,
                workflow_phase_names=("preflight", "artifact contract preflight"),
            ),
            InstallationPhase(
                phase_id="host-preparation",
                order=5,
                depends_on=("preflight",),
                workflow_phase_names=("host prepare", "host verify"),
            ),
            InstallationPhase(
                phase_id="platform",
                order=10,
                depends_on=("host-preparation",),
                workflow_phase_names=("platform init", "platform reconcile"),
            ),
            InstallationPhase(
                phase_id="cluster",
                order=20,
                depends_on=("platform",),
                services=("docker", "swarm"),
                workflow_phase_names=(
                    "cluster docker",
                    "cluster swarm bootstrap",
                    "cluster verify",
                ),
            ),
            InstallationPhase(
                phase_id="network-routing",
                order=30,
                depends_on=("cluster",),
                services=("traefik",),
                workflow_phase_names=("platform expose",),
            ),
            InstallationPhase(
                phase_id="secrets",
                order=40,
                depends_on=("network-routing",),
                services=("infisical",),
                workflow_phase_names=("deployment bootstrap",),
            ),
            InstallationPhase(
                phase_id="artifacts",
                order=50,
                depends_on=("secrets",),
                services=("nexus",),
                workflow_phase_names=(
                    "artifact bootstrap",
                    "artifact readiness gate",
                    "artifacts prepare",
                    "artifacts verify",
                ),
            ),
            InstallationPhase(
                phase_id="cicd",
                order=60,
                depends_on=("artifacts", "secrets"),
                services=("jenkins",),
                parallel_group="independent-services",
            ),
            InstallationPhase(
                phase_id="quality",
                order=70,
                depends_on=("artifacts", "secrets"),
                services=("sonarqube",),
                parallel_group="independent-services",
            ),
            InstallationPhase(
                phase_id="messaging",
                order=80,
                depends_on=("secrets",),
                services=("pulsar",),
                parallel_group="independent-services",
            ),
            InstallationPhase(
                phase_id="observability",
                order=90,
                required=False,
                depends_on=("network-routing",),
                services=("prometheus", "grafana", "loki", "alertmanager"),
                parallel_group="independent-services",
            ),
            InstallationPhase(
                phase_id="control",
                order=100,
                depends_on=("cicd", "quality", "messaging"),
                services=("service-access",),
            ),
            InstallationPhase(
                phase_id="docs",
                order=110,
                depends_on=("control",),
                services=("swagger", "openapi-aggregator"),
            ),
            InstallationPhase(
                phase_id="validation",
                order=120,
                depends_on=("docs",),
                workflow_phase_names=(
                    "deployment apply",
                    "deployment verify",
                    "platform verify",
                ),
            ),
        ),
        required_phase_ids=(
            "preflight",
            "host-preparation",
            "platform",
            "cluster",
            "network-routing",
            "secrets",
            "artifacts",
            "cicd",
            "quality",
            "messaging",
            "control",
            "docs",
            "validation",
        ),
        required_services=(
            "docker",
            "swarm",
            "traefik",
            "infisical",
            "nexus",
            "jenkins",
            "sonarqube",
            "pulsar",
            "service-access",
            "swagger",
        ),
        metadata={
            "workflow_id": "workflow-install-order-and-port-allocation-20260620",
            "public_ingress_owner": "traefik",
        },
    )


def _ordered_installation_phases(
    phases: tuple[InstallationPhase, ...],
) -> tuple[InstallationPhase, ...]:
    by_id = {phase.phase_id: phase for phase in phases}
    pending = set(by_id)
    ordered: list[InstallationPhase] = []
    while pending:
        ready = sorted(
            (
                by_id[phase_id]
                for phase_id in pending
                if all(dependency not in pending for dependency in by_id[phase_id].depends_on)
            ),
            key=lambda phase: (phase.order, phase.phase_id),
        )
        if not ready:
            raise ValueError("installation phase dependency graph contains a cycle")
        phase = ready[0]
        ordered.append(phase)
        pending.remove(phase.phase_id)
    return tuple(ordered)


def _reject_duplicate_phase_ids(phases: tuple[InstallationPhase, ...]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for phase in phases:
        if phase.phase_id in seen:
            duplicates.append(phase.phase_id)
        seen.add(phase.phase_id)
    if duplicates:
        raise ValueError("duplicate installation phase ids: " + ", ".join(sorted(duplicates)))


def _reject_missing_dependencies(phases: tuple[InstallationPhase, ...]) -> None:
    phase_ids = {phase.phase_id for phase in phases}
    missing = sorted(
        {
            dependency
            for phase in phases
            for dependency in phase.depends_on
            if dependency not in phase_ids
        }
    )
    if missing:
        raise ValueError("installation phase dependencies are missing: " + ", ".join(missing))


def _reject_missing_required_phases(
    phases: tuple[InstallationPhase, ...],
    required_phase_ids: tuple[str, ...],
) -> None:
    phase_ids = {phase.phase_id for phase in phases}
    missing = sorted(set(required_phase_ids) - phase_ids)
    if missing:
        raise ValueError("required installation phases are missing: " + ", ".join(missing))


def _reject_missing_required_services(
    phases: tuple[InstallationPhase, ...],
    required_services: tuple[str, ...],
) -> None:
    declared_services = {service for phase in phases if phase.required for service in phase.services}
    missing = sorted(set(required_services) - declared_services)
    if missing:
        raise ValueError("required installation services are missing: " + ", ".join(missing))


def _validate_phase_identifier(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not PHASE_IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} contains invalid characters")


def _normalized_identifier(value: str, field_name: str) -> str:
    normalized = value.strip()
    _validate_phase_identifier(normalized, field_name)
    return normalized


def _normalized_non_empty_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(value.strip() for value in values)
    if any(not value for value in normalized):
        raise ValueError(f"{field_name} entries must be non-empty")
    return normalized
