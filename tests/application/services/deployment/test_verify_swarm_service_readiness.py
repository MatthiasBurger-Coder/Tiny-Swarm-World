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

    async def test_verifies_service_access_when_all_required_services_are_ready(self):
        runtime = _FakeSwarmRuntime(
            (
                SwarmServiceStatus("service-access_service-access-dashboard", 1, 1),
                SwarmServiceStatus("service-access_infisical", 1, 1),
                SwarmServiceStatus("service-access_infisical-db", 1, 1),
                SwarmServiceStatus("service-access_infisical-redis", 1, 1),
                SwarmServiceStatus("service-access_service-access-nginx", 1, 1),
            )
        )
        service = VerifySwarmServiceReadiness(
            runtime,
            ServiceStackContract(
                "service-access",
                ("service-access-dashboard", "infisical", "infisical-db", "infisical-redis", "service-access-nginx"),
            ),
            max_attempts=1,
            wait_seconds=0,
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("deployment:service-access-service-readiness", verification.target_id)

    async def test_fails_service_access_when_required_service_is_missing(self):
        runtime = _FakeSwarmRuntime(
            (
                SwarmServiceStatus("service-access_service-access-dashboard", 1, 1),
                SwarmServiceStatus("service-access_service-access-nginx", 1, 1),
            )
        )
        service = VerifySwarmServiceReadiness(
            runtime,
            ServiceStackContract(
                "service-access",
                ("service-access-dashboard", "infisical", "infisical-db", "infisical-redis", "service-access-nginx"),
            ),
            max_attempts=1,
            wait_seconds=0,
        )

        verification = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertEqual(
            "infisical,infisical-db,infisical-redis",
            verification.evidence["missing_services"],
        )


class _FakeSwarmRuntime:
    def __init__(self, services: tuple[SwarmServiceStatus, ...]):
        self.services = services

    def deploy_stack(self, stack_definition, stack_environment=None):
        raise AssertionError("readiness verification must not deploy")

    def stack_exists(self, stack_name: str) -> bool:
        return bool(self.services)

    def list_stack_services(self, stack_name: str) -> tuple[SwarmServiceStatus, ...]:
        return self.services

    def external_secret_exists(self, name: str) -> bool:
        raise AssertionError("readiness verification must not inspect secrets")

    def ensure_external_secret(self, name: str, value: str) -> None:
        raise AssertionError("readiness verification must not create secrets")
