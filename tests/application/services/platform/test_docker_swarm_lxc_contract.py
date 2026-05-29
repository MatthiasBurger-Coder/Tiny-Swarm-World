import unittest
from tests.support.sonar_safe_literals import ipv4_address

from tiny_swarm_world.application.services.platform import DockerSwarmInLxcContractService
from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.domain.network import ContainerNetworkPlan, ContainerNetworkPurpose
from tiny_swarm_world.domain.node_provider import (
    ContainerDockerInstallOutcome,
    ContainerDockerReadiness,
    DockerEngineState,
    DockerInstallState,
    DockerSwarmInLxcProfileContract,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    SwarmManagerBootstrapOutcome,
    SwarmManagerState,
    SwarmNodeReadinessEvidence,
    SwarmNodeState,
    SwarmWorkerJoinOutcome,
    WorkerJoinState,
)


class TestDockerSwarmInLxcContractService(unittest.TestCase):
    def test_valid_profile_contract_is_verified_with_summary_evidence(self):
        result = DockerSwarmInLxcContractService().validate_profile_contract(
            DockerSwarmInLxcProfileContract.default_docker_swarm()
        )

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("profile_contract_valid", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    def test_invalid_profile_contract_blocks_node_creation(self):
        result = DockerSwarmInLxcContractService().validate_profile_contract(
            DockerSwarmInLxcProfileContract(privileged_default=True)
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("privileged_default_forbidden", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    def test_swarm_node_readiness_requires_observed_active_state(self):
        result = DockerSwarmInLxcContractService().verify_swarm_node_readiness(
            SwarmNodeReadinessEvidence(
                node=_manager_node(),
                docker_engine_observed=True,
                docker_engine_ready=True,
                swarm_state_observed=True,
                swarm_state=SwarmNodeState.ACTIVE,
                observed_role=NodeRole.MANAGER,
                manager_count=1,
                expected_node_count=1,
                observed_node_count=1,
            )
        )

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("swarm_node_ready", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    def test_swarm_node_without_observed_state_blocks_health_claim(self):
        result = DockerSwarmInLxcContractService().verify_swarm_node_readiness(
            SwarmNodeReadinessEvidence(
                node=_manager_node(),
                docker_engine_observed=False,
                docker_engine_ready=True,
                swarm_state_observed=False,
                swarm_state=SwarmNodeState.ACTIVE,
            )
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("observed_state_missing", result.evidence["classification"])

    def test_observed_but_inactive_swarm_node_fails_verify(self):
        result = DockerSwarmInLxcContractService().verify_swarm_node_readiness(
            SwarmNodeReadinessEvidence(
                node=_manager_node(),
                docker_engine_observed=True,
                docker_engine_ready=True,
                swarm_state_observed=True,
                swarm_state=SwarmNodeState.PENDING,
                observed_role=NodeRole.MANAGER,
                manager_count=1,
            )
        )

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual("swarm_state_not_active", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    def test_safe_container_network_plan_is_verified(self):
        result = DockerSwarmInLxcContractService().validate_network_plan(
            ContainerNetworkPlan.provider_managed_control()
        )

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("container_network_plan_valid", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    def test_container_docker_readiness_maps_to_summary_verification(self):
        result = DockerSwarmInLxcContractService().verify_container_docker_readiness(
            ContainerDockerReadiness(
                node=_manager_node(),
                observed=True,
                engine_state=DockerEngineState.READY,
            )
        )

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("container_docker_ready", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    def test_missing_container_docker_observation_blocks_readiness_claim(self):
        result = DockerSwarmInLxcContractService().verify_container_docker_readiness(
            ContainerDockerReadiness(
                node=_manager_node(),
                observed=False,
                engine_state=DockerEngineState.READY,
            )
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("docker_observed_state_missing", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    def test_container_docker_install_failure_maps_to_failed_apply(self):
        result = DockerSwarmInLxcContractService().verify_container_docker_install(
            ContainerDockerInstallOutcome(
                node=_manager_node(),
                state=DockerInstallState.FAILED,
                verified=False,
            )
        )

        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual("docker_install_failed", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    def test_swarm_manager_and_worker_outcomes_map_to_summary_verification(self):
        service = DockerSwarmInLxcContractService()

        manager_result = service.verify_swarm_manager_bootstrap(
            SwarmManagerBootstrapOutcome(
                node=_manager_node(),
                state=SwarmManagerState.INITIALIZED,
                manager_count=1,
            )
        )
        worker_result = service.verify_swarm_worker_join(
            SwarmWorkerJoinOutcome(
                node=_worker_node(),
                state=WorkerJoinState.ALREADY_JOINED,
                verified=True,
            )
        )

        self.assertEqual(VerificationStatus.VERIFIED, manager_result.status)
        self.assertEqual("initialized", manager_result.evidence["classification"])
        self.assertEqual(VerificationStatus.VERIFIED, worker_result.status)
        self.assertEqual("already_joined", worker_result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(manager_result)
        self.assertEvidenceIsSummaryOnly(worker_result)

    def test_host_specific_network_plan_blocks_static_config(self):
        result = DockerSwarmInLxcContractService().validate_network_plan(
            ContainerNetworkPlan(
                name="control",
                purpose=ContainerNetworkPurpose.CONTROL,
                host_addresses=(ipv4_address(10, 0, 0, 2),),
            )
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("host_address_forbidden", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    def assertEvidenceIsSummaryOnly(self, result):
        rendered = repr(result.to_dict()).casefold()
        for fragment in (
            "stdout",
            "stderr",
            "token",
            "secret",
            "join-token",
            "10.0.0.",
            "/mnt/",
            "docker swarm",
            "lxc ",
            "incus ",
        ):
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, rendered)


def _manager_node() -> NodeSpec:
    return NodeSpec(
        name="swarm-manager",
        role=NodeRole.MANAGER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


def _worker_node() -> NodeSpec:
    return NodeSpec(
        name="swarm-worker-1",
        role=NodeRole.WORKER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


if __name__ == "__main__":
    unittest.main()
