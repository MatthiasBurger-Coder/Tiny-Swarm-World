from __future__ import annotations

from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.network import ContainerNetworkPlan
from tiny_swarm_world.domain.node_provider import (
    DockerSwarmInLxcProfileContract,
    SwarmNodeReadinessEvidence,
)


class DockerSwarmInLxcContractService:
    def validate_profile_contract(
        self,
        profile: DockerSwarmInLxcProfileContract,
    ) -> VerificationResult:
        errors = profile.validation_errors()
        if errors:
            return VerificationResult(
                target_id=f"platform:lxc-profile:{profile.profile_name}",
                status=VerificationStatus.BLOCKED,
                message="Nested profile contract blocks node creation.",
                evidence={
                    "phase": "pre_apply",
                    "classification": errors[0],
                    "profile": profile.profile_name,
                    "risk_label_count": str(len(profile.risk_labels)),
                    "error_count": str(len(errors)),
                },
            )
        return VerificationResult(
            target_id=f"platform:lxc-profile:{profile.profile_name}",
            status=VerificationStatus.VERIFIED,
            message="Nested profile contract is valid.",
            evidence={
                "phase": "pre_apply",
                "classification": "profile_contract_valid",
                "profile": profile.profile_name,
                "risk_label_count": str(len(profile.risk_labels)),
            },
        )

    def verify_swarm_node_readiness(
        self,
        readiness: SwarmNodeReadinessEvidence,
    ) -> VerificationResult:
        errors = readiness.readiness_errors()
        if not errors:
            return VerificationResult(
                target_id=f"platform:swarm-node:{readiness.node.name}",
                status=VerificationStatus.VERIFIED,
                message="Node readiness is verified from observed state.",
                evidence={
                    "phase": "verify",
                    "classification": "swarm_node_ready",
                    "node": readiness.node.name,
                    "role": readiness.node.role.value,
                    "swarm_state": readiness.swarm_state.value,
                },
            )
        status = (
            VerificationStatus.BLOCKED
            if errors[0] == "observed_state_missing"
            else VerificationStatus.FAILED_TO_VERIFY
        )
        return VerificationResult(
            target_id=f"platform:swarm-node:{readiness.node.name}",
            status=status,
            message="Node readiness is not verified.",
            evidence={
                "phase": "verify",
                "classification": errors[0],
                "node": readiness.node.name,
                "role": readiness.node.role.value,
                "swarm_state": readiness.swarm_state.value,
                "error_count": str(len(errors)),
            },
        )

    def validate_network_plan(
        self,
        plan: ContainerNetworkPlan,
    ) -> VerificationResult:
        errors = plan.validation_errors()
        if errors:
            return VerificationResult(
                target_id=f"platform:container-network:{plan.name}",
                status=VerificationStatus.BLOCKED,
                message="Container network plan is not safe for static configuration.",
                evidence={
                    "phase": "pre_apply",
                    "classification": errors[0],
                    "network": plan.name,
                    "purpose": plan.purpose.value,
                    "error_count": str(len(errors)),
                },
            )
        return VerificationResult(
            target_id=f"platform:container-network:{plan.name}",
            status=VerificationStatus.VERIFIED,
            message="Container network plan is safe for static configuration.",
            evidence={
                "phase": "pre_apply",
                "classification": "container_network_plan_valid",
                "network": plan.name,
                "purpose": plan.purpose.value,
            },
        )
