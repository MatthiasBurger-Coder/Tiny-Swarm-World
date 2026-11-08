from __future__ import annotations

from typing import Protocol

from tiny_swarm_world.domain.inventory import VerificationResult


class PortainerVerificationService(Protocol):
    async def verify(self) -> VerificationResult:
        ...


class PortainerEndpointVerifyStep:
    returns_verification_result = True
    verification_target_id = "deployment:portainer-local-endpoint"

    def __init__(self, service: PortainerVerificationService) -> None:
        self.service = service

    async def run(self) -> VerificationResult:
        return await self.service.verify()
