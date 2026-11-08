import unittest
from unittest.mock import MagicMock

from tiny_swarm_world.application.ports.clients.port_deployment_gateway import (
    DeploymentStackRequest,
)
from tiny_swarm_world.application.services.deployment.ensure_nexus_stack import EnsureNexusStack
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition


class TestEnsureNexusStack(unittest.TestCase):
    def test_creates_stack_when_missing(self):
        stack_definition = StackDefinition(name="nexus", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        deployment_gateway = _FakeDeploymentGateway()

        service = EnsureNexusStack(compose_repository, deployment_gateway, "nexus")
        service.run()

        compose_repository.get_compose_of.assert_called_once_with("nexus")
        self.assertEqual(len(deployment_gateway.applied_requests), 1)
        request = deployment_gateway.applied_requests[0]
        self.assertEqual(request.target_stack, "nexus")
        self.assertEqual(stack_definition, request.stack_definition)

    def test_updates_stack_when_present(self):
        stack_definition = StackDefinition(name="nexus", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        deployment_gateway = _FakeDeploymentGateway()

        service = EnsureNexusStack(compose_repository, deployment_gateway, "nexus")
        service.run()

        compose_repository.get_compose_of.assert_called_once_with("nexus")
        self.assertEqual(stack_definition, deployment_gateway.applied_requests[0].stack_definition)


class _FakeDeploymentGateway:
    def __init__(self) -> None:
        self.applied_requests: list[DeploymentStackRequest] = []

    def apply_stack(self, request: DeploymentStackRequest) -> None:
        self.applied_requests.append(request)

    def stack_registered(self, stack_name: str) -> bool:
        return bool(self.applied_requests)
