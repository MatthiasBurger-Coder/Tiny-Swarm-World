import unittest

from tiny_swarm_world.domain.node_provider import (
    DockerSwarmInLxcProfileContract,
    DockerSwarmLxcRiskLabel,
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    REQUIRED_DOCKER_SWARM_LXC_RISK_LABELS,
    SwarmNodeReadinessEvidence,
    SwarmNodeState,
)


class TestDockerSwarmLxcContract(unittest.TestCase):
    def test_default_profile_contract_is_explicit_and_valid_for_node_creation(self):
        profile = DockerSwarmInLxcProfileContract.default_docker_swarm()

        self.assertTrue(profile.valid_for_node_creation)
        self.assertEqual("docker-swarm", profile.profile_name)
        self.assertEqual(
            {ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD},
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


def _manager_node() -> NodeSpec:
    return NodeSpec(
        name="swarm-manager",
        role=NodeRole.MANAGER,
        provider=NodeProviderKind.LXC_NATIVE,
    )


if __name__ == "__main__":
    unittest.main()
