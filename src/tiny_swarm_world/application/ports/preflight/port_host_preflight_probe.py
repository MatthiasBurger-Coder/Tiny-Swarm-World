from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    SetupPath,
)


class PortHostPreflightProbe(ABC):
    @abstractmethod
    def is_linux_or_wsl(self) -> bool:
        pass

    def host_environment_report(self) -> HostEnvironmentReport:
        if self.is_linux_or_wsl():
            return HostEnvironmentReport(
                environment=HostEnvironmentKind.NATIVE_LINUX,
                setup_path=SetupPath.NATIVE_LINUX,
                remediation=("Provide a typed host probe for WSL2-specific classification.",),
                evidence={"classification": "legacy_boolean_compatible"},
            )
        return HostEnvironmentReport(
            environment=HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
            setup_path=SetupPath.UNSUPPORTED,
            remediation=("Run Tiny Swarm World from Linux or WSL2.",),
            evidence={"classification": "legacy_boolean_unsupported"},
        )

    @abstractmethod
    def python_version(self) -> str:
        pass

    @abstractmethod
    def executable_available(self, name: str) -> bool:
        pass

    @abstractmethod
    def cpu_count(self) -> int:
        pass

    @abstractmethod
    def memory_bytes(self) -> int:
        pass

    @abstractmethod
    def disk_free_bytes(self, path: str) -> int:
        pass

    @abstractmethod
    def port_available(self, port: int) -> bool:
        pass

    @abstractmethod
    def port_matches_expected_service(self, port: int, service: str) -> bool:
        pass

    @abstractmethod
    def secret_available(self, name: str) -> bool:
        pass

    @abstractmethod
    def path_ignored_by_git(self, path: str) -> bool:
        pass

    @abstractmethod
    def forbidden_tracked_secret_fingerprints(
        self,
        fingerprints: Mapping[str, str],
    ) -> Sequence[str]:
        pass
