import unittest

from tiny_swarm_world.application.services.deployment.service_stack_plan import (
    build_default_service_stack_steps,
)
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestServiceStackPlan(unittest.IsolatedAsyncioTestCase):
    def test_builds_default_service_stack_steps_without_concrete_adapters(self):
        compose_repository = object()
        portainer_client = object()

        steps = build_default_service_stack_steps(compose_repository, portainer_client, "local")

        self.assertEqual(5, len(steps))
        self.assertEqual(
            [
                "deployment:nexus-service-readiness",
                "deployment:jenkins-service-readiness",
                "deployment:rabbitmq-service-readiness",
                "deployment:sonarqube-service-readiness",
                "deployment:swagger-service-readiness",
            ],
            [step.verification_target_id for step in steps],
        )
        self.assertTrue(all(step.compose_repository is compose_repository for step in steps))
        self.assertTrue(all(step.portainer_client is portainer_client for step in steps))
        self.assertTrue(all(step.endpoint_name == "local" for step in steps))

    def test_default_service_stack_steps_do_not_include_portainer_bootstrap_cycle(self):
        steps = build_default_service_stack_steps(object(), object(), "local")

        self.assertNotIn("portainer", [step.service_stack.stack_name for step in steps])

    async def test_default_service_stack_steps_block_until_service_readiness_is_observed(self):
        compose_repository = _FakeComposeRepository()
        portainer_client = _FakePortainerClient()

        steps = build_default_service_stack_steps(compose_repository, portainer_client, "local")
        verification_results = [await step.verify() for step in steps]

        self.assertEqual(
            [
                "deployment:nexus-service-readiness",
                "deployment:jenkins-service-readiness",
                "deployment:rabbitmq-service-readiness",
                "deployment:sonarqube-service-readiness",
                "deployment:swagger-service-readiness",
            ],
            [verification.target_id for verification in verification_results],
        )
        self.assertTrue(
            all(verification.status == VerificationStatus.BLOCKED for verification in verification_results)
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
