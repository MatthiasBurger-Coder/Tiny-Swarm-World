"""Pure project-filesystem facts and live-installation policy."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from tiny_swarm_world.domain.host_environment import HostEnvironmentKind

LINUX_HOME_RECOMMENDATION = "/home/<user>/projects/Tiny-Swarm-World"


class ProjectFilesystemKind(str, Enum):
    NATIVE_LINUX = "native_linux"
    WSL_LINUX = "wsl_linux"
    WINDOWS_MOUNTED = "windows_mounted"
    UNKNOWN = "unknown"


class ProjectFilesystemDecision(str, Enum):
    ALLOWED = "allowed"
    ALLOWED_BY_OVERRIDE = "allowed_by_override"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ProjectFilesystemInspection:
    kind: ProjectFilesystemKind
    resolved_project_path: str = field(repr=False)
    filesystem_type: str = "unknown"
    classification_source: str = "unknown"

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "filesystem_classification": self.kind.value,
            "filesystem_type": _safe_filesystem_type(self.filesystem_type),
            "windows_mounted": self.kind is ProjectFilesystemKind.WINDOWS_MOUNTED,
            "classification_source": self.classification_source,
        }


@dataclass(frozen=True)
class ProjectFilesystemAssessment:
    host_environment: HostEnvironmentKind
    inspection: ProjectFilesystemInspection
    decision: ProjectFilesystemDecision
    override_requested: bool
    override_applied: bool
    remediation: tuple[str, ...] = ()
    evidence_status: str = "not_required"

    @property
    def allowed(self) -> bool:
        return self.decision is not ProjectFilesystemDecision.BLOCKED

    @property
    def blocked(self) -> bool:
        return not self.allowed

    def mark_evidence_recorded(self) -> "ProjectFilesystemAssessment":
        if self.decision is not ProjectFilesystemDecision.ALLOWED_BY_OVERRIDE:
            return self
        return replace(self, evidence_status="recorded")

    def block_for_evidence_failure(self) -> "ProjectFilesystemAssessment":
        return replace(
            self,
            decision=ProjectFilesystemDecision.BLOCKED,
            override_applied=False,
            remediation=(
                "Store the override decision on a verified Linux-native owner-only filesystem.",
            ),
            evidence_status="protected_evidence_unavailable",
        )

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "host_environment": self.host_environment.value,
            **self.inspection.to_safe_dict(),
            "decision": self.decision.value,
            "override_requested": self.override_requested,
            "override_applied": self.override_applied,
            "evidence_status": self.evidence_status,
            "remediation": list(self.remediation),
        }

    def to_protected_evidence_dict(self) -> dict[str, object]:
        if (
            self.decision is not ProjectFilesystemDecision.ALLOWED_BY_OVERRIDE
            or not self.override_applied
        ):
            raise ValueError("protected evidence requires an applied filesystem override")
        return {
            "schema_version": 1,
            "project_path": self.inspection.resolved_project_path,
            "filesystem_classification": self.inspection.kind.value,
            "override_requested": self.override_requested,
            "override_applied": self.override_applied,
            "decision": self.decision.value,
        }


def assess_project_filesystem(
    host_environment: HostEnvironmentKind,
    inspection: ProjectFilesystemInspection,
    *,
    allow_wsl_windows_filesystem: bool,
) -> ProjectFilesystemAssessment:
    override_requested = bool(allow_wsl_windows_filesystem)
    if host_environment is HostEnvironmentKind.NATIVE_LINUX:
        return ProjectFilesystemAssessment(
            host_environment=host_environment,
            inspection=inspection,
            decision=ProjectFilesystemDecision.ALLOWED,
            override_requested=override_requested,
            override_applied=False,
        )
    if host_environment is not HostEnvironmentKind.WSL2:
        return ProjectFilesystemAssessment(
            host_environment=host_environment,
            inspection=inspection,
            decision=ProjectFilesystemDecision.BLOCKED,
            override_requested=override_requested,
            override_applied=False,
            remediation=("Use a supported native Linux or WSL2 host first.",),
        )
    if inspection.kind is ProjectFilesystemKind.WINDOWS_MOUNTED:
        if override_requested:
            return ProjectFilesystemAssessment(
                host_environment=host_environment,
                inspection=inspection,
                decision=ProjectFilesystemDecision.ALLOWED_BY_OVERRIDE,
                override_requested=True,
                override_applied=True,
                evidence_status="required",
            )
        return ProjectFilesystemAssessment(
            host_environment=host_environment,
            inspection=inspection,
            decision=ProjectFilesystemDecision.BLOCKED,
            override_requested=False,
            override_applied=False,
            remediation=(
                LINUX_HOME_RECOMMENDATION,
                "Rerun only when necessary with --allow-wsl-windows-filesystem.",
            ),
        )
    if inspection.kind in {
        ProjectFilesystemKind.WSL_LINUX,
        ProjectFilesystemKind.NATIVE_LINUX,
    }:
        return ProjectFilesystemAssessment(
            host_environment=host_environment,
            inspection=inspection,
            decision=ProjectFilesystemDecision.ALLOWED,
            override_requested=override_requested,
            override_applied=False,
        )
    return ProjectFilesystemAssessment(
        host_environment=host_environment,
        inspection=inspection,
        decision=ProjectFilesystemDecision.BLOCKED,
        override_requested=override_requested,
        override_applied=False,
        remediation=(
            "Make /proc/self/mountinfo readable and rerun host preflight.",
            LINUX_HOME_RECOMMENDATION,
        ),
    )


def _safe_filesystem_type(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized in {"ext2", "ext3", "ext4", "xfs", "btrfs", "9p", "v9fs", "drvfs"}:
        return normalized
    return "unknown"
