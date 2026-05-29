from __future__ import annotations

from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.network import ContainerNetworkPlan
from tiny_swarm_world.domain.node_provider import (
    ContainerDockerInstallOutcome,
    ContainerDockerReadiness,
    DockerSwarmInLxcProfileContract,
    SwarmManagerBootstrapOutcome,
    SwarmNodeReadinessEvidence,
    SwarmWorkerJoinOutcome,
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

    def verify_container_docker_readiness(
        self,
        readiness: ContainerDockerReadiness,
    ) -> VerificationResult:
        errors = readiness.readiness_errors()
        if not errors:
            return VerificationResult(
                target_id=f"platform:container-docker:{readiness.node.name}",
                status=VerificationStatus.VERIFIED,
                message="Container Docker runtime is verified.",
                evidence={
                    "phase": "verify",
                    "classification": "container_docker_ready",
                    "node": readiness.node.name,
                    "role": readiness.node.role.value,
                    "engine_state": readiness.engine_state.value,
                },
            )
        status = (
            VerificationStatus.BLOCKED
            if errors[0] == "docker_observed_state_missing"
            else VerificationStatus.FAILED_TO_VERIFY
        )
        return VerificationResult(
            target_id=f"platform:container-docker:{readiness.node.name}",
            status=status,
            message="Container Docker runtime is not verified.",
            evidence={
                "phase": "verify",
                "classification": errors[0],
                "node": readiness.node.name,
                "role": readiness.node.role.value,
                "engine_state": readiness.engine_state.value,
            },
        )

    def verify_container_docker_install(
        self,
        outcome: ContainerDockerInstallOutcome,
    ) -> VerificationResult:
        errors = outcome.install_errors()
        if not errors:
            return VerificationResult(
                target_id=f"platform:container-docker-install:{outcome.node.name}",
                status=VerificationStatus.VERIFIED,
                message="Container runtime setup is verified.",
                evidence={
                    "phase": "verify",
                    "classification": outcome.state.value,
                    "node": outcome.node.name,
                    "role": outcome.node.role.value,
                },
            )
        status = (
            VerificationStatus.FAILED_TO_APPLY
            if errors[0] == "docker_install_failed"
            else VerificationStatus.FAILED_TO_VERIFY
        )
        return VerificationResult(
            target_id=f"platform:container-docker-install:{outcome.node.name}",
            status=status,
            message="Container runtime setup is not verified.",
            evidence={
                "phase": "verify",
                "classification": errors[0],
                "node": outcome.node.name,
                "role": outcome.node.role.value,
                "install_state": outcome.state.value,
            },
        )

    def verify_swarm_manager_bootstrap(
        self,
        outcome: SwarmManagerBootstrapOutcome,
    ) -> VerificationResult:
        errors = outcome.bootstrap_errors()
        if not errors:
            return VerificationResult(
                target_id=f"platform:swarm-manager:{outcome.node.name}",
                status=VerificationStatus.VERIFIED,
                message="Swarm manager bootstrap is verified.",
                evidence={
                    "phase": "verify",
                    "classification": outcome.state.value,
                    "node": outcome.node.name,
                    "role": outcome.node.role.value,
                },
            )
        return VerificationResult(
            target_id=f"platform:swarm-manager:{outcome.node.name}",
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Swarm manager bootstrap is not verified.",
            evidence={
                "phase": "verify",
                "classification": errors[0],
                "node": outcome.node.name,
                "role": outcome.node.role.value,
                "manager_state": outcome.state.value,
            },
        )

    def verify_swarm_worker_join(
        self,
        outcome: SwarmWorkerJoinOutcome,
    ) -> VerificationResult:
        errors = outcome.join_errors()
        if not errors:
            return VerificationResult(
                target_id=f"platform:swarm-worker:{outcome.node.name}",
                status=VerificationStatus.VERIFIED,
                message="Swarm worker join is verified.",
                evidence={
                    "phase": "verify",
                    "classification": outcome.state.value,
                    "node": outcome.node.name,
                    "role": outcome.node.role.value,
                },
            )
        return VerificationResult(
            target_id=f"platform:swarm-worker:{outcome.node.name}",
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Swarm worker join is not verified.",
            evidence={
                "phase": "verify",
                "classification": errors[0],
                "node": outcome.node.name,
                "role": outcome.node.role.value,
                "join_state": outcome.state.value,
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
