from __future__ import annotations

import asyncio

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    PortSwarmStackRuntime,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class VerifyExternalSwarmInput:
    verification_target_id = "deployment:service-access-external-input"

    def __init__(
        self,
        swarm_runtime: PortSwarmStackRuntime,
        resource_name: str,
        source_ref: str = "default",
    ):
        if not resource_name:
            raise ValueError("external Swarm input name must not be empty")
        self.swarm_runtime = swarm_runtime
        self.resource_name = resource_name
        self.source_ref = _safe_source_ref(source_ref)

    async def verify(self) -> VerificationResult:
        await asyncio.sleep(0)
        try:
            present = self.swarm_runtime.external_secret_exists(self.resource_name)
        except Exception as exc:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=f"External Swarm input verification failed: {exc.__class__.__name__}",
                evidence=_input_evidence("unknown", self.source_ref),
            )

        if present:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.VERIFIED,
                message="Required external Swarm input is present.",
                evidence=_input_evidence("true", self.source_ref),
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message="Required external Swarm input is missing.",
            evidence=_input_evidence("false", self.source_ref),
        )


def _input_evidence(resource_present: str, source_ref: str) -> dict[str, str]:
    return {
        "phase": "pre_apply",
        "resource_kind": "external_swarm_input",
        "resource_present": resource_present,
        "source_ref": source_ref,
    }


def _safe_source_ref(source_ref: str) -> str:
    if source_ref in {"default", "operator_env"}:
        return source_ref
    return "custom"
