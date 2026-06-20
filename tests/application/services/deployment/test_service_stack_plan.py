import unittest
from typing import cast

from tiny_swarm_world.application.ports.clients.port_deployment_gateway import (
    DeploymentStackRequest,
    PortDeploymentGateway,
)
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.application.services.deployment.service_stack_plan import (
    build_default_service_stack_steps,
    build_service_stack_steps,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestServiceStackPlan(unittest.IsolatedAsyncioTestCase):
    def test_builds_default_service_stack_steps_without_concrete_adapters(self):
        compose_repository = _compose_repository_stub()
        deployment_gateway = _deployment_gateway_stub()

        steps = build_default_service_stack_steps(compose_repository, deployment_gateway)

        self.assertEqual(6, len(steps))
        self.assertEqual(
            [
                "deployment:traefik-stack",
                "deployment:nexus-stack",
                "deployment:jenkins-stack",
                "deployment:pulsar-stack",
                "deployment:sonarqube-stack",
                "deployment:swagger-stack",
            ],
            [step.verification_target_id for step in steps],
        )
        self.assertTrue(all(step.compose_repository is compose_repository for step in steps))
        self.assertTrue(all(step.deployment_gateway is deployment_gateway for step in steps))

    def test_default_service_stack_steps_do_not_include_portainer_bootstrap_cycle(self):
        steps = build_default_service_stack_steps(
            _compose_repository_stub(),
            _deployment_gateway_stub(),
        )

        self.assertNotIn("portainer", [step.service_stack.stack_name for step in steps])

    def test_service_access_profile_steps_include_selected_stack(self):
        compose_repository = _compose_repository_stub()
        deployment_gateway = _deployment_gateway_stub()

        steps = build_service_stack_steps(
            compose_repository,
            deployment_gateway,
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
        )

        self.assertEqual(
            (
                "traefik",
                "nexus",
                "jenkins",
                "pulsar",
                "sonarqube",
                "swagger",
                "infisical",
                "service-access",
            ),
            tuple(step.service_stack.stack_name for step in steps),
        )
        self.assertNotIn("portainer", tuple(step.service_stack.stack_name for step in steps))
        self.assertTrue(all(step.compose_repository is compose_repository for step in steps))
        self.assertTrue(all(step.deployment_gateway is deployment_gateway for step in steps))
        self.assertEqual(
            {
                "traefik": "network-routing",
                "nexus": "artifacts",
                "jenkins": "cicd",
                "pulsar": "messaging",
                "sonarqube": "quality",
                "swagger": "docs",
                "infisical": "secrets",
                "service-access": "control",
            },
            {step.service_stack.stack_name: step.service_stack.phase_id for step in steps},
        )
        self.assertEqual(
            ("pulsar-broker", "pulsar-admin-api"),
            next(
                step.service_stack.port_ids
                for step in steps
                if step.service_stack.stack_name == "pulsar"
            ),
        )

    def test_service_stack_steps_can_exclude_bootstrap_owned_stacks(self):
        steps = build_service_stack_steps(
            _compose_repository_stub(),
            _deployment_gateway_stub(),
            service_profile=ServiceStackProfile.SERVICE_ACCESS,
            excluded_stack_names=("nexus",),
        )

        self.assertEqual(
            ("traefik", "jenkins", "pulsar", "sonarqube", "swagger", "infisical", "service-access"),
            tuple(step.service_stack.stack_name for step in steps),
        )

    def test_service_stack_steps_attach_stack_specific_environment(self):
        steps = build_service_stack_steps(
            _compose_repository_stub(),
            _deployment_gateway_stub(),
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
        deployment_gateway = _FakeDeploymentGateway()

        steps = build_default_service_stack_steps(
            cast(PortComposeFileRepository, compose_repository),
            cast(PortDeploymentGateway, deployment_gateway),
        )
        verification_results = [await step.verify() for step in steps]

        self.assertEqual(
            [
                "deployment:traefik-stack",
                "deployment:nexus-stack",
                "deployment:jenkins-stack",
                "deployment:pulsar-stack",
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
        self.assertTrue(
            all(
                verification.evidence["registration_scope"] == "deployment_gateway_stack"
                for verification in verification_results
            )
        )
        self.assertEqual([], compose_repository.requested_stacks)


class _FakeComposeRepository:
    def __init__(self) -> None:
        self.requested_stacks: list[str] = []

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        self.requested_stacks.append(stack_name)
        return StackDefinition(name=stack_name, compose_content="services: {}")


class _FakeDeploymentGateway:
    def __init__(self) -> None:
        self.applied_requests: list[DeploymentStackRequest] = []

    def apply_stack(self, request: DeploymentStackRequest) -> None:
        self.applied_requests.append(request)

    def stack_registered(self, stack_name: str) -> bool:
        return True


def _compose_repository_stub() -> PortComposeFileRepository:
    return cast(PortComposeFileRepository, object())


def _deployment_gateway_stub() -> PortDeploymentGateway:
    return cast(PortDeploymentGateway, object())
