from __future__ import annotations

from tiny_swarm_world.application.ports.host import PortHostPreparation
from tiny_swarm_world.domain.preflight import HostPreparationResult, HostPreparationStatus


class NativeLinuxHostPreparation(PortHostPreparation):
    """Native Linux has no Windows bridge side effects."""

    def prepare(self) -> HostPreparationResult:
        return self._result("prepare", verified=True)

    def verify(self) -> HostPreparationResult:
        return self._result("verify", verified=True)

    def cleanup(self) -> HostPreparationResult:
        return self._result("cleanup", verified=True)

    def _result(self, operation: str, *, verified: bool) -> HostPreparationResult:
        return HostPreparationResult(
            operation,
            "native_linux",
            HostPreparationStatus.SUCCESS,
            "No Windows/WSL host preparation is applicable on native Linux.",
            verified=verified,
            evidence={
                "windows_command_runner": "not_selected",
                "mutation": "none",
            },
        )
