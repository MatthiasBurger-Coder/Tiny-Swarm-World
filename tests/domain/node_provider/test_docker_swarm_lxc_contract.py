import unittest

from tiny_swarm_world.domain.node_provider import (
    ContainerDockerInstallOutcome,
    ContainerDockerReadiness,
    DockerEngineState,
    DockerInstallState,
    DockerSwarmInLxcProfileContract,
    DockerSwarmLxcRiskLabel,
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    REQUIRED_DOCKER_SWARM_LXC_RISK_LABELS,
    SwarmManagerBootstrapOutcome,
    SwarmManagerState,
    SwarmNodeReadinessEvidence,
    SwarmNodeState,
    SwarmWorkerJoinCredential,
    SwarmWorkerJoinOutcome,
    WorkerJoinState,
)


class TestDockerSwarmLxcContract(unittest.TestCase):
    def test_default_profile_contract_is_explicit_and_valid_for_node_creation(self):
        profile = DockerSwarmInLxcProfileContract.default_docker_swarm()

        self.assertTrue(profile.valid_for_node_creation)
        self.assertEqual("docker-swarm", profile.profile_name)
        self.assertEqual(
            {ManagedLxcBackend.INCUS},
            set(profile.backend_support),
        )
        self.assertTrue(profile.nesting_required)
        self.assertTrue(profile.syscall_interception_required)
        self.assertTrue(profile.intercept_mknod_required)
        self.assertTrue(profile.intercept_setxattr_required)
        self.assertEqual("v2_required", profile.cgroup_policy)
        self.assertFalse(profile.privileged_default)
        self.assertFalse(profile.host_network)
        self.assertEqual((), profile.host_mounts)
        self.assertEqual((), profile.capability_additions)
        self.assertEqual(
            set(REQUIRED_DOCKER_SWARM_LXC_RISK_LABELS),
            set(profile.risk_labels),
        )

    def test_profile_contract_requires_nesting_and_syscall_interception(self):
        profile = DockerSwarmInLxcProfileContract(
            nesting_required=False,
            intercept_mknod_required=False,
            intercept_setxattr_required=False,
        )

        self.assertFalse(profile.valid_for_node_creation)
        self.assertIn("nesting_not_required", profile.validation_errors())
        self.assertIn("mknod_interception_not_required", profile.validation_errors())
        self.assertIn("setxattr_interception_not_required", profile.validation_errors())

    def test_profile_contract_rejects_silent_privileged_or_host_access_defaults(self):
        profile = DockerSwarmInLxcProfileContract(
            privileged_default=True,
            host_network=True,
            host_mounts=("/mnt/host",),
            capability_additions=("sys_admin",),
        )

        self.assertIn("privileged_default_forbidden", profile.validation_errors())
        self.assertIn("host_network_forbidden", profile.validation_errors())
        self.assertIn("host_mounts_forbidden", profile.validation_errors())
        self.assertIn("capability_additions_forbidden_default", profile.validation_errors())

    def test_profile_contract_rejects_unconfined_apparmor_or_seccomp(self):
        profile = DockerSwarmInLxcProfileContract(
            apparmor_policy="unconfined",
            seccomp_policy="unconfined",
        )

        self.assertIn("apparmor_policy_not_provider_default", profile.validation_errors())
        self.assertIn("seccomp_policy_not_provider_default", profile.validation_errors())

    def test_profile_contract_requires_visible_risk_labels(self):
        profile = DockerSwarmInLxcProfileContract(
            risk_labels=(
                DockerSwarmLxcRiskLabel.DOCKER_IN_CONTAINER_REQUIRES_NESTING,
            )
        )

        self.assertFalse(profile.valid_for_node_creation)
        self.assertIn("risk_labels_incomplete", profile.validation_errors())

    def test_swarm_readiness_requires_observed_docker_and_swarm_state(self):
        readiness = SwarmNodeReadinessEvidence(
            node=_manager_node(),
            docker_engine_observed=True,
            docker_engine_ready=True,
            swarm_state_observed=True,
            swarm_state=SwarmNodeState.ACTIVE,
            observed_role=NodeRole.MANAGER,
            manager_count=1,
            expected_node_count=3,
            observed_node_count=3,
        )

        self.assertTrue(readiness.ready)
        self.assertEqual((), readiness.readiness_errors())

    def test_swarm_readiness_does_not_claim_health_without_observed_state(self):
        readiness = SwarmNodeReadinessEvidence(
            node=_manager_node(),
            docker_engine_observed=False,
            docker_engine_ready=True,
            swarm_state_observed=False,
            swarm_state=SwarmNodeState.ACTIVE,
        )

        self.assertFalse(readiness.ready)
        self.assertEqual(("observed_state_missing",), readiness.readiness_errors())

    def test_swarm_readiness_requires_observed_role(self):
        readiness = SwarmNodeReadinessEvidence(
            node=_manager_node(),
            docker_engine_observed=True,
            docker_engine_ready=True,
            swarm_state_observed=True,
            swarm_state=SwarmNodeState.ACTIVE,
            manager_count=1,
        )

        self.assertFalse(readiness.ready)
        self.assertIn("node_role_missing", readiness.readiness_errors())

    def test_swarm_readiness_reports_role_quorum_and_count_mismatches(self):
        readiness = SwarmNodeReadinessEvidence(
            node=_manager_node(),
            docker_engine_observed=True,
            docker_engine_ready=False,
            swarm_state_observed=True,
            swarm_state=SwarmNodeState.PENDING,
            observed_role=NodeRole.WORKER,
            manager_count=0,
            expected_node_count=3,
            observed_node_count=2,
        )

        self.assertFalse(readiness.ready)
        self.assertEqual(
            (
                "docker_engine_not_ready",
                "swarm_state_not_active",
                "node_role_mismatch",
                "manager_quorum_missing",
                "swarm_node_count_incomplete",
            ),
            readiness.readiness_errors(),
        )

    def test_container_docker_readiness_requires_observed_ready_engine(self):
        readiness = ContainerDockerReadiness(
            node=_manager_node(),
            observed=True,
            engine_state=DockerEngineState.READY,
        )

        self.assertTrue(readiness.ready)
        self.assertEqual((), readiness.readiness_errors())

        missing = ContainerDockerReadiness(
            node=_manager_node(),
            observed=False,
            engine_state=DockerEngineState.READY,
        )

        self.assertFalse(missing.ready)
        self.assertEqual(
            ("docker_observed_state_missing",),
            missing.readiness_errors(),
        )

    def test_container_docker_install_outcome_requires_verified_non_failed_state(self):
        installed = ContainerDockerInstallOutcome(
            node=_manager_node(),
            state=DockerInstallState.INSTALLED,
            verified=True,
        )

        self.assertTrue(installed.successful)
        self.assertEqual((), installed.install_errors())

        failed = ContainerDockerInstallOutcome(
            node=_manager_node(),
            state=DockerInstallState.FAILED,
            verified=False,
        )

        self.assertFalse(failed.successful)
        self.assertEqual(("docker_install_failed",), failed.install_errors())

    def test_swarm_manager_bootstrap_requires_manager_role_and_active_state(self):
        active = SwarmManagerBootstrapOutcome(
            node=_manager_node(),
            state=SwarmManagerState.ACTIVE,
            manager_count=1,
        )

        self.assertTrue(active.active)
        self.assertEqual((), active.bootstrap_errors())

        wrong_role = SwarmManagerBootstrapOutcome(
            node=_worker_node(),
            state=SwarmManagerState.ACTIVE,
            manager_count=1,
        )

        self.assertFalse(wrong_role.active)
        self.assertIn("manager_node_role_required", wrong_role.bootstrap_errors())

    def test_worker_join_outcome_requires_worker_role_joined_state_and_verification(self):
        joined = SwarmWorkerJoinOutcome(
            node=_worker_node(),
            state=WorkerJoinState.JOINED,
            verified=True,
        )

        self.assertTrue(joined.joined)
        self.assertEqual((), joined.join_errors())

        failed = SwarmWorkerJoinOutcome(
            node=_manager_node(),
            state=WorkerJoinState.FAILED,
            verified=False,
        )

        self.assertFalse(failed.joined)
        self.assertEqual(
            (
                "worker_node_role_required",
                "worker_join_failed",
                "worker_join_not_verified",
            ),
            failed.join_errors(),
        )

    def test_worker_join_credential_redacts_repr_and_string(self):
        credential = SwarmWorkerJoinCredential("sensitive-value")

        self.assertNotIn("sensitive-value", repr(credential))
        self.assertNotIn("sensitive-value", str(credential))

        with self.assertRaises(ValueError):
            SwarmWorkerJoinCredential("")


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
