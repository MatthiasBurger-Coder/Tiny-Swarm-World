from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from tiny_swarm_world.domain.preflight.sanitized_evidence import sanitized_evidence


class HostEnvironmentKind(str, Enum):
    NATIVE_LINUX = "native_linux"
    WSL2 = "wsl2"
    WSL1_UNSUPPORTED = "wsl1_unsupported"
    UNKNOWN_UNSUPPORTED = "unknown_unsupported"
    SANDBOX_UNVERIFIED = "sandbox_unverified"


class SetupPath(str, Enum):
    NATIVE_LINUX = "native_linux"
    WSL2 = "wsl2"
    UNSUPPORTED = "unsupported"
    SANDBOX_UNVERIFIED = "sandbox_unverified"


@dataclass(frozen=True)
class HostEnvironmentReport:
    environment: HostEnvironmentKind
    setup_path: SetupPath
    remediation: tuple[str, ...] = ()
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_setup_path(self.environment, self.setup_path)
        object.__setattr__(self, "remediation", tuple(self.remediation))
        object.__setattr__(self, "evidence", sanitized_evidence(self.evidence))

    @property
    def supported(self) -> bool:
        return self.setup_path in {SetupPath.NATIVE_LINUX, SetupPath.WSL2}

    @property
    def allows_live_setup(self) -> bool:
        return self.supported

    @property
    def static_validation_only(self) -> bool:
        return self.setup_path == SetupPath.SANDBOX_UNVERIFIED

    def to_dict(self) -> dict[str, object]:
        return {
            "environment": self.environment.value,
            "setup_path": self.setup_path.value,
            "supported": self.supported,
            "allows_live_setup": self.allows_live_setup,
            "static_validation_only": self.static_validation_only,
            "remediation": list(self.remediation),
            "evidence": dict(self.evidence),
        }


def _validate_setup_path(
    environment: HostEnvironmentKind,
    setup_path: SetupPath,
) -> None:
    expected_paths = {
        HostEnvironmentKind.NATIVE_LINUX: SetupPath.NATIVE_LINUX,
        HostEnvironmentKind.WSL2: SetupPath.WSL2,
        HostEnvironmentKind.WSL1_UNSUPPORTED: SetupPath.UNSUPPORTED,
        HostEnvironmentKind.UNKNOWN_UNSUPPORTED: SetupPath.UNSUPPORTED,
        HostEnvironmentKind.SANDBOX_UNVERIFIED: SetupPath.SANDBOX_UNVERIFIED,
    }
    expected_path = expected_paths[environment]
    if setup_path != expected_path:
        raise ValueError("host environment and setup path are inconsistent")
