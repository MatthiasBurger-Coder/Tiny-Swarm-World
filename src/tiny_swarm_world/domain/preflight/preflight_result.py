from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from tiny_swarm_world.domain.preflight.preflight_check import (
    PreflightCheck,
    PreflightSeverity,
)
from tiny_swarm_world.domain.preflight.setup_manifest import SetupProfile


@dataclass(frozen=True)
class PreflightResult:
    checks: tuple[PreflightCheck, ...]
    setup_profile: SetupProfile = SetupProfile.FULL
    manifest_summary: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "manifest_summary",
            MappingProxyType(dict(self.manifest_summary)),
        )

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def resource_gated(self) -> bool:
        return bool(self.failed_checks) and all(
            check.severity == PreflightSeverity.RESOURCE_GATED
            for check in self.failed_checks
        )

    @property
    def status(self) -> str:
        if self.passed:
            return "PASSED"
        if self.resource_gated:
            return "RESOURCE_GATED"
        return "FAILED"

    @property
    def failed_checks(self) -> tuple[PreflightCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "setup_profile": self.setup_profile.value,
            "manifest": dict(self.manifest_summary),
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_evidence(self) -> dict[str, object]:
        """Return redacted, structured host-preflight evidence."""
        host = next((check for check in self.checks if check.check_id == "HOST"), None)
        resource = next(
            (check for check in self.checks if check.check_id == "RESOURCE-STRUCTURED"),
            None,
        )
        bridge = next(
            (check for check in self.checks if check.check_id == "WINDOWS-WSL-BRIDGE"),
            None,
        )
        return {
            "status": self.status,
            "host_environment": dict(host.evidence) if host else {},
            "host_resources": dict(resource.evidence) if resource else {},
            "resource_assessment": resource.evidence.get("assessment") if resource else "UNKNOWN",
            "network_preparation": dict(bridge.evidence) if bridge else {},
            "overrides": [
                "allow-wsl-windows-filesystem"
                for check in self.checks
                if check.check_id == "HOST-FILESYSTEM"
                and check.evidence.get("override_applied") == "true"
            ],
        }
