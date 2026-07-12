from __future__ import annotations

from enum import Enum

from tiny_swarm_world.application.ports.host import PortHostEnvironmentDetector
from tiny_swarm_world.domain.preflight import HostEnvironmentKind
from tiny_swarm_world.infrastructure.adapters.host import HostEnvironmentDetector


class OsTypes(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    WSL_LINUX = "wsl_linux"

    @staticmethod
    def get_enum_from_value(value: str) -> "OsTypes":
        normalized_value = value.lower()
        if normalized_value in {"wsl", "wsl2", "wsl_linux"}:
            return OsTypes.WSL_LINUX
        for enum_member in OsTypes:
            if enum_member.value.lower() == normalized_value:
                return enum_member
        raise ValueError(f"Value '{value}' does not match any OsType.")

    @staticmethod
    def detect_current(
        detector: PortHostEnvironmentDetector | None = None,
    ) -> "OsTypes":
        report = (detector or HostEnvironmentDetector()).detect()
        if report.environment is HostEnvironmentKind.WSL2:
            return OsTypes.WSL_LINUX
        if report.environment is HostEnvironmentKind.NATIVE_LINUX:
            return OsTypes.LINUX
        raise ValueError(
            f"Unsupported host environment: {report.environment.value}"
        )


def _has_wsl_signal(
    detector: PortHostEnvironmentDetector | None = None,
) -> bool:
    report = (detector or HostEnvironmentDetector()).detect()
    return report.environment in {
        HostEnvironmentKind.WSL2,
        HostEnvironmentKind.WSL1_UNSUPPORTED,
    }
