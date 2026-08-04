from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from tiny_swarm_world.application.ports.host import (
    PortHostEnvironmentDetector,
    PortHostPreparation,
)
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.preflight import (
    HostPreparationResult,
    HostPreparationStatus,
    LiveConsent,
)


@dataclass(frozen=True)
class HostPreparationAdapterFactory:
    """Creates one host adapter only after host classification selects it."""

    create: Callable[[], PortHostPreparation]


class HostPreparationService:
    """Selects the host-specific adapter while keeping OS commands out of application code."""

    def __init__(
        self,
        detector: PortHostEnvironmentDetector,
        native_linux: PortHostPreparation | HostPreparationAdapterFactory,
        wsl2: PortHostPreparation | HostPreparationAdapterFactory,
        live_consent: LiveConsent | None = None,
    ) -> None:
        self.detector = detector
        self.native_linux = native_linux
        self.wsl2 = wsl2
        self.live_consent = live_consent

    def prepare(self) -> HostPreparationResult:
        return self._run("prepare", mutating=True)

    def verify(self) -> HostPreparationResult:
        return self._run("verify", mutating=False)

    def cleanup(self) -> HostPreparationResult:
        return self._run("cleanup", mutating=True)

    def _run(self, operation: str, *, mutating: bool) -> HostPreparationResult:
        if mutating and (self.live_consent is None or not self.live_consent.accepted):
            return HostPreparationResult(
                operation,
                "unknown",
                HostPreparationStatus.BLOCKED,
                "Live consent is required for host preparation mutation.",
                evidence={"reason": "live_consent_missing"},
            )
        report = self.detector.detect()
        if report.environment is HostEnvironmentKind.NATIVE_LINUX:
            adapter = _resolve_adapter(self.native_linux)
        elif report.environment is HostEnvironmentKind.WSL2:
            adapter = _resolve_adapter(self.wsl2)
        else:
            return HostPreparationResult(
                operation,
                report.environment.value,
                HostPreparationStatus.BLOCKED,
                "Host environment is not supported for this operation.",
                evidence={"remediation": "; ".join(report.remediation)},
            )
        if operation == "prepare":
            return adapter.prepare()
        if operation == "verify":
            return adapter.verify()
        if operation == "cleanup":
            return adapter.cleanup()
        raise ValueError(f"Unsupported host preparation operation: {operation}")


def _resolve_adapter(
    adapter: PortHostPreparation | HostPreparationAdapterFactory,
) -> PortHostPreparation:
    if isinstance(adapter, HostPreparationAdapterFactory):
        return adapter.create()
    return adapter
