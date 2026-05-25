from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from tiny_swarm_world.domain.preflight import HostRuntimeReadiness


class PortHostPreflightProbe(ABC):
    @abstractmethod
    def is_linux_or_wsl(self) -> bool:
        pass

    @abstractmethod
    def python_version(self) -> str:
        pass

    @abstractmethod
    def executable_available(self, name: str) -> bool:
        pass

    @abstractmethod
    def multipass_runtime_readiness(
        self,
        expected_driver: str | None = None,
    ) -> HostRuntimeReadiness:
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
