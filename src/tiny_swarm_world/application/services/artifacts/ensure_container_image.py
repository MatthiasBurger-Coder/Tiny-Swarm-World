from __future__ import annotations

from tiny_swarm_world.application.ports.clients.port_container_image_publisher import (
    PortContainerImagePublisher,
)
from tiny_swarm_world.domain.artifacts import ContainerImageContract
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class EnsureContainerImage:
    def __init__(
        self,
        image_publisher: PortContainerImagePublisher,
        contract: ContainerImageContract,
    ):
        self.image_publisher = image_publisher
        self.contract = contract
        self.artifact_target_id = contract.artifact_target_id
        self.verification_target_id = contract.verification_target_id

    async def run(self) -> None:
        self.image_publisher.publish_image(self.contract)

    async def verify(self) -> VerificationResult:
        try:
            available = self.image_publisher.image_available(self.contract)
        except Exception as exc:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=f"Container image verification failed: {exc.__class__.__name__}",
                evidence=_image_evidence(self.contract, available="unknown"),
            )

        if available:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.VERIFIED,
                message="Container image is available in the local registry.",
                evidence=_image_evidence(self.contract, available="true"),
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Container image is missing from the local registry.",
            evidence=_image_evidence(self.contract, available="false"),
        )


def _image_evidence(
    contract: ContainerImageContract,
    *,
    available: str,
) -> dict[str, str]:
    return {
        "available": available,
        "build_context": contract.build_context,
        "image_ref": contract.image_ref,
        "phase": "verify",
    }
