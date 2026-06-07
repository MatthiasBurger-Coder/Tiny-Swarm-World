import unittest
from typing import cast

from tiny_swarm_world.application.ports.clients.port_portainer_client import PortPortainerClient
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.application.services.deployment.service_stack_plan import (
    DEFAULT_PORTAINER_ENDPOINT_NAME,
    build_default_service_stack_steps,
    build_service_stack_steps,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestServiceStackPlan(unittest.IsolatedAsyncioTestCase):
    def test_builds_default_service_stack_steps_without_concrete_adapters(self):
        compose_repository = _compose_repository_stub()
        portainer_client = _portainer_client_stub()

        steps = build_default_service_stack_steps(compose_repository, portainer_client, "local")

        self.assertEqual(5, len(steps))
        self.assertEqual(
            [
                "deployment:nexus-stack",
                "deployment:jenkins-stack",
                "deployment:rabbitmq-stack",
                "deployment:sonarqube-stack",
                "deployment:swagger-stack",
            ],
            [step.verification_target_id for step in steps],
        )
        self.assertTrue(all(step.compose_repository is compose_repository for step in steps))
        self.assertTrue(all(step.portainer_client is portainer_client for step in steps))
        self.assertTrue(all(step.endpoint_name == "local" for step in steps))

    def test_default_service_stack_steps_do_not_include_portainer_bootstrap_cycle(self):
        steps = build_default_service_stack_steps(
            _compose_repository_stub(),
            _portainer_client_stub(),
            "local",
        )

        self.assertNotIn("portainer", [step.service_stack.stack_name for step in steps])

    def test_default_service_stack_steps_use_named_portainer_endpoint_default(self):
        steps = build_default_service_stack_steps(
            _compose_repository_stub(),
            _portainer_client_stub(),
        )

        self.assertEqual("local", DEFAULT_PORTAINER_ENDPOINT_NAME)
        self.assertTrue(
            all(step.endpoint_name == DEFAULT_PORTAINER_ENDPOINT_NAME for step in steps)
        )

    def test_service_stack_steps_use_named_portainer_endpoint_default(self):
        steps = build_service_stack_steps(
            _compose_repository_stub(),
            _portainer_client_stub(),
        )

        self.assertTrue(
            all(step.endpoint_name == DEFAULT_PORTAINER_ENDPOINT_NAME for step in steps)
        )

    def test_service_access_profile_steps_include_selected_stack(self):
        compose_repository = _compose_repository_stub()
        portainer_client = _portainer_client_stub()

        steps = build_service_stack_steps(
            compose_repository,
            portainer_client,
            "local",
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
        )

        self.assertEqual(
            ("nexus", "jenkins", "rabbitmq", "sonarqube", "swagger", "infisical", "service-access"),
            tuple(step.service_stack.stack_name for step in steps),
        )
        self.assertNotIn("portainer", tuple(step.service_stack.stack_name for step in steps))
        self.assertTrue(all(step.compose_repository is compose_repository for step in steps))
        self.assertTrue(all(step.portainer_client is portainer_client for step in steps))
        self.assertTrue(all(step.endpoint_name == "local" for step in steps))

    def test_service_stack_steps_can_exclude_bootstrap_owned_stacks(self):
        steps = build_service_stack_steps(
            _compose_repository_stub(),
            _portainer_client_stub(),
            "local",
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
            excluded_stack_names=("nexus",),
        )

        self.assertEqual(
            ("jenkins", "rabbitmq", "sonarqube", "swagger", "infisical", "service-access"),
            tuple(step.service_stack.stack_name for step in steps),
        )

    def test_service_stack_steps_attach_stack_specific_environment(self):
        steps = build_service_stack_steps(
            _compose_repository_stub(),
            _portainer_client_stub(),
            "local",
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
            stack_environments={
                "infisical": {
                    "TSW_INFISICAL_AUTH_SECRET": "operator_defined",
                }
            },
        )

        infisical_step = next(
            step
            for step in steps
            if step.service_stack.stack_name == "infisical"
        )

        self.assertEqual(
            {"TSW_INFISICAL_AUTH_SECRET": "operator_defined"},
            infisical_step.stack_environment,
        )

    async def test_default_service_stack_steps_verify_stack_registration_without_readiness_claim(self):
        compose_repository = _FakeComposeRepository()
        portainer_client = _FakePortainerClient()

        steps = build_default_service_stack_steps(
            cast(PortComposeFileRepository, compose_repository),
            cast(PortPortainerClient, portainer_client),
            "local",
        )
        verification_results = [await step.verify() for step in steps]

        self.assertEqual(
            [
                "deployment:nexus-stack",
                "deployment:jenkins-stack",
                "deployment:rabbitmq-stack",
                "deployment:sonarqube-stack",
                "deployment:swagger-stack",
            ],
            [verification.target_id for verification in verification_results],
        )
        self.assertTrue(
            all(verification.status == VerificationStatus.VERIFIED for verification in verification_results)
        )
        self.assertTrue(
            all(verification.evidence["readiness_observed"] == "false" for verification in verification_results)
        )
        self.assertEqual([], compose_repository.requested_stacks)


class _FakeComposeRepository:
    def __init__(self) -> None:
        self.requested_stacks: list[str] = []

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        self.requested_stacks.append(stack_name)
        return StackDefinition(name=stack_name, compose_content="services: {}")


class _FakePortainerClient:
    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        return 7

    def find_stack_id_by_name(self, stack_name: str) -> int | None:
        return 42


def _compose_repository_stub() -> PortComposeFileRepository:
    return cast(PortComposeFileRepository, object())


def _portainer_client_stub() -> PortPortainerClient:
    return cast(PortPortainerClient, object())
