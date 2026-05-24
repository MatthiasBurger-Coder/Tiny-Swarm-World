import unittest

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    SwarmServiceStatus,
)
from tiny_swarm_world.application.services.deployment.verify_swarm_service_readiness import (
    VerifySwarmServiceReadiness,
)
from tiny_swarm_world.domain.deployment import ServiceStackContract
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestVerifySwarmServiceReadiness(unittest.IsolatedAsyncioTestCase):
    async def test_verifies_when_required_services_reach_desired_replicas(self):
        runtime = _FakeSwarmRuntime(
            (
                SwarmServiceStatus("sonarqube_sonarqube", 1, 1),
                SwarmServiceStatus("sonarqube_sonar_db", 1, 1),
            )
        )
        service = VerifySwarmServiceReadiness(
            runtime,
            ServiceStackContract("sonarqube", ("sonarqube", "sonar_db")),
            max_attempts=1,
            wait_seconds=0,
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("deployment:sonarqube-service-readiness", verification.target_id)
        self.assertEqual("sonarqube", verification.evidence["stack_name"])

    async def test_fails_when_required_service_does_not_converge(self):
        runtime = _FakeSwarmRuntime((SwarmServiceStatus("nexus_nexus", 0, 1),))
        service = VerifySwarmServiceReadiness(
            runtime,
            ServiceStackContract("nexus", ("nexus",)),
            max_attempts=1,
            wait_seconds=0,
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertIn("nexus=0/1", verification.evidence["replicas"])


class _FakeSwarmRuntime:
    def __init__(self, services: tuple[SwarmServiceStatus, ...]):
        self.services = services

    def deploy_stack(self, stack_definition):
        raise AssertionError("readiness verification must not deploy")

    def stack_exists(self, stack_name: str) -> bool:
        return bool(self.services)

    def list_stack_services(self, stack_name: str) -> tuple[SwarmServiceStatus, ...]:
        return self.services
