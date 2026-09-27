"""Guard host mutation with preflight before resolving the host adapter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from tiny_swarm_world.application.ports.host import PortHostPreparation
from tiny_swarm_world.application.ports.preflight import PortPlatformPreflight
from tiny_swarm_world.domain.preflight import HostPreparationResult, LiveConsent, PreflightResult


@dataclass(frozen=True)
class HostPreparationOutcome:
    preflight: PreflightResult
    preparation: HostPreparationResult | None


class PrepareHostWithPreflight:
    def __init__(
        self,
        preflight: PortPlatformPreflight,
        create_preparation: Callable[[], PortHostPreparation],
    ) -> None:
        self.preflight = preflight
        self.create_preparation = create_preparation

    async def run(self, action: str, live_consent: LiveConsent | None) -> HostPreparationOutcome:
        if live_consent is None or not live_consent.accepted:
            raise ValueError("host preparation requires accepted live consent")
        result = await self.preflight.run(live_consent)
        if not result.passed:
            return HostPreparationOutcome(result, None)
        preparation = self.create_preparation()
        if action == "prepare":
            return HostPreparationOutcome(result, preparation.prepare())
        if action == "cleanup":
            return HostPreparationOutcome(result, preparation.cleanup())
        raise ValueError(f"Unsupported host preparation action: {action}")
