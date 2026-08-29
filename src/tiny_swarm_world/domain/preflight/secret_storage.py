"""Pure policy for mutable live secret storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind


class SecretStorageDecision(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SecretStorageInspection:
    """Filesystem facts for a secret file, without exposing its path in repr."""

    resolved_path: str = field(repr=False)
    filesystem_kind: ProjectFilesystemKind
    filesystem_type: str
    exists: bool
    is_regular_file: bool
    owner_uid: int | None
    group_gid: int | None
    mode: int | None
    parent_exists: bool
    parent_owner_uid: int | None
    parent_group_gid: int | None
    parent_mode: int | None
    classification_source: str = "unknown"

    def to_safe_dict(self, *, expected_uid: int, expected_gid: int) -> dict[str, str]:
        return {
            "storage_classification": self.filesystem_kind.value,
            "filesystem_type": self.filesystem_type,
            "exists": _bool_text(self.exists),
            "regular_file": _bool_text(self.is_regular_file),
            "owner_matches": _bool_text(self.owner_uid == expected_uid),
            "group_matches": _bool_text(self.group_gid == expected_gid),
            "file_mode_private": _mode_text(self.mode == 0o600),
            "parent_exists": _bool_text(self.parent_exists),
            "parent_owner_matches": _bool_text(self.parent_owner_uid == expected_uid),
            "parent_group_matches": _bool_text(self.parent_group_gid == expected_gid),
            "parent_mode_private": _mode_text(self.parent_mode == 0o700),
            "classification_source": self.classification_source,
        }


@dataclass(frozen=True)
class SecretStorageAssessment:
    host_environment: HostEnvironmentKind
    inspection: SecretStorageInspection
    expected_uid: int
    expected_gid: int
    decision: SecretStorageDecision
    reasons: tuple[str, ...] = ()
    remediation: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.decision is SecretStorageDecision.ALLOWED

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "host_environment": self.host_environment.value,
            **self.inspection.to_safe_dict(
                expected_uid=self.expected_uid,
                expected_gid=self.expected_gid,
            ),
            "decision": self.decision.value,
            "accepted": _bool_text(self.allowed),
            "reasons": list(self.reasons),
            "remediation": list(self.remediation),
        }


def assess_secret_storage(
    host_environment: HostEnvironmentKind,
    inspection: SecretStorageInspection,
    *,
    expected_uid: int,
    expected_gid: int,
    require_existing_file: bool,
) -> SecretStorageAssessment:
    reasons: list[str] = []
    allowed_kinds = {
        ProjectFilesystemKind.NATIVE_LINUX,
        ProjectFilesystemKind.WSL_LINUX,
    }
    if host_environment not in {
        HostEnvironmentKind.NATIVE_LINUX,
        HostEnvironmentKind.WSL2,
    }:
        reasons.append("host_unsupported")
    if inspection.filesystem_kind not in allowed_kinds:
        reasons.append("storage_filesystem_not_linux_native")
    if require_existing_file and not inspection.exists:
        reasons.append("secret_file_missing")
    if inspection.exists and not inspection.is_regular_file:
        reasons.append("secret_path_not_regular_file")
    if inspection.exists and inspection.owner_uid != expected_uid:
        reasons.append("secret_file_owner_mismatch")
    if inspection.exists and inspection.group_gid != expected_gid:
        reasons.append("secret_file_group_mismatch")
    if inspection.exists and inspection.mode != 0o600:
        reasons.append("secret_file_mode_not_0600")
    if not inspection.parent_exists:
        reasons.append("secret_parent_missing")
    if inspection.parent_exists and inspection.parent_owner_uid != expected_uid:
        reasons.append("secret_parent_owner_mismatch")
    if inspection.parent_exists and inspection.parent_group_gid != expected_gid:
        reasons.append("secret_parent_group_mismatch")
    if inspection.parent_exists and inspection.parent_mode != 0o700:
        reasons.append("secret_parent_mode_not_0700")

    if not reasons:
        return SecretStorageAssessment(
            host_environment=host_environment,
            inspection=inspection,
            expected_uid=expected_uid,
            expected_gid=expected_gid,
            decision=SecretStorageDecision.ALLOWED,
        )
    return SecretStorageAssessment(
        host_environment=host_environment,
        inspection=inspection,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
        decision=SecretStorageDecision.BLOCKED,
        reasons=tuple(reasons),
        remediation=(
            "Materialize the live environment file under a WSL-native Linux path, "
            "for example $HOME/.local/state/tiny-swarm-world/live-installation.env.",
            "Create its parent with mode 0700 and the file with mode 0600, then "
            "set TSW_INSTALL_ENV_FILE to that path and rerun preflight.",
        ),
    )


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _mode_text(value: bool) -> str:
    return "verified" if value else "not_verified"
