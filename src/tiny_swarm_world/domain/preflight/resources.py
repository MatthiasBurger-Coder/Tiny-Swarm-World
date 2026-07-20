from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ResourceAssessment(StrEnum):
    SUPPORTED = "SUPPORTED"
    SUPPORTED_WITH_WARNINGS = "SUPPORTED_WITH_WARNINGS"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True)
class HostResources:
    cpu_threads: int
    memory_bytes: int
    cgroup_memory_limit_bytes: int | None
    current_memory_usage_bytes: int
    free_disk_bytes: int

    @property
    def effective_memory_bytes(self) -> int:
        if self.cgroup_memory_limit_bytes is None:
            return self.memory_bytes
        return min(self.memory_bytes, self.cgroup_memory_limit_bytes)


@dataclass(frozen=True)
class ResourceRequirements:
    cpu_threads: int
    memory_bytes: int
    free_disk_bytes: int


@dataclass(frozen=True)
class ResourceProfile:
    name: str
    minimum: ResourceRequirements
    recommended: ResourceRequirements


@dataclass(frozen=True)
class PlannedContainerLimit:
    name: str
    cpu_threads: int
    memory_bytes: int


def default_resource_profiles() -> dict[str, ResourceProfile]:
    return {
        "service-access": ResourceProfile(
            "service-access",
            ResourceRequirements(8, 16 * 1024**3, 150 * 1024**3),
            ResourceRequirements(12, 24 * 1024**3, 250 * 1024**3),
        ),
        "default": ResourceProfile(
            "default",
            ResourceRequirements(4, 8 * 1024**3, 60 * 1024**3),
            ResourceRequirements(8, 16 * 1024**3, 120 * 1024**3),
        ),
    }


@dataclass(frozen=True)
class ResourceAssessmentResult:
    assessment: ResourceAssessment
    resources: HostResources
    requirements: ResourceRequirements
    remaining_memory_bytes: int
    reason: str


@dataclass(frozen=True)
class MemoryPressureReport:
    memory_current: int
    memory_max: int | None
    memory_high: int | None
    oom_events: int
    oom_kill_events: int
    reclaim_events: int
    assessment: str
    confidence: str


def assess_resources(
    resources: HostResources,
    requirements: ResourceRequirements,
    *,
    recommended: ResourceRequirements | None = None,
) -> ResourceAssessmentResult:
    insufficient = (
        resources.cpu_threads < requirements.cpu_threads
        or resources.effective_memory_bytes < requirements.memory_bytes
        or resources.free_disk_bytes < requirements.free_disk_bytes
    )
    if insufficient:
        status = ResourceAssessment.INSUFFICIENT
        reason = "Host resources are below the selected profile minimum."
    elif recommended and (
        resources.cpu_threads < recommended.cpu_threads
        or resources.effective_memory_bytes < recommended.memory_bytes
        or resources.free_disk_bytes < recommended.free_disk_bytes
    ):
        status = ResourceAssessment.SUPPORTED_WITH_WARNINGS
        reason = "Host meets minimum resources but is below the recommendation."
    else:
        status = ResourceAssessment.SUPPORTED
        reason = "Host meets the selected resource profile."
    return ResourceAssessmentResult(
        status,
        resources,
        requirements,
        max(resources.effective_memory_bytes - requirements.memory_bytes, 0),
        reason,
    )


def validate_container_limits(
    resources: HostResources,
    active_cpu: int,
    active_memory_bytes: int,
    requested_cpu: int,
    requested_memory_bytes: int,
    *,
    allow_overcommit: bool = False,
) -> bool:
    if allow_overcommit:
        return True
    return (
        active_cpu + requested_cpu <= resources.cpu_threads
        and active_memory_bytes + requested_memory_bytes
        <= resources.effective_memory_bytes
    )


def validate_planned_container_limits(
    resources: HostResources,
    planned: tuple[PlannedContainerLimit, ...],
    *,
    allow_overcommit: bool = False,
) -> bool:
    if allow_overcommit:
        return True
    return (
        sum(item.cpu_threads for item in planned) <= resources.cpu_threads
        and sum(item.memory_bytes for item in planned) <= resources.effective_memory_bytes
    )
