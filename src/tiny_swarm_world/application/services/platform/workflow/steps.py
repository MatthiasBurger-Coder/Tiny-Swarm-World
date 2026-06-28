from __future__ import annotations

from typing import Protocol

from tiny_swarm_world.domain.inventory import VerificationResult


class AsyncWorkflowStep(Protocol):
    async def run(self) -> object:
        # Protocol declaration; concrete workflow steps perform platform work.
        pass


class VerifiableWorkflowStep(AsyncWorkflowStep, Protocol):
    verification_target_id: str

    async def verify(self) -> VerificationResult:
        # Protocol declaration; concrete steps provide verification evidence.
        pass
