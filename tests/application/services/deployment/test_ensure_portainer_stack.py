import unittest
from unittest.mock import MagicMock

from tiny_swarm_world.application.ports.clients.port_deployment_gateway import (
    DeploymentStackRequest,
)
from tiny_swarm_world.application.services.deployment.ensure_portainer_stack import (
    EnsurePortainerStack,
)
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition


class TestEnsurePortainerStack(unittest.IsolatedAsyncioTestCase):
    async def test_creates_stack_when_portainer_stack_is_missing(self):
        stack_definition = StackDefinition(name="portainer", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        deployment_gateway = _FakeDeploymentGateway()

        service = EnsurePortainerStack(compose_repository, deployment_gateway, "portainer")
        await service.run()

        compose_repository.get_compose_of.assert_called_once_with("portainer")
        request = _single_applied_request(deployment_gateway)
        self.assertEqual("portainer", request.target_stack)
        self.assertEqual(stack_definition, request.stack_definition)

    async def test_updates_stack_when_portainer_stack_exists(self):
        stack_definition = StackDefinition(name="portainer", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        deployment_gateway = _FakeDeploymentGateway()

        service = EnsurePortainerStack(compose_repository, deployment_gateway, "portainer")
        await service.run()

        request = _single_applied_request(deployment_gateway)
        self.assertEqual(stack_definition, request.stack_definition)

    async def test_compose_lookup_failure_does_not_deploy_stack(self):
        compose_repository = MagicMock()
        compose_repository.get_compose_of.side_effect = FileNotFoundError("missing")
        deployment_gateway = _FakeDeploymentGateway()

        service = EnsurePortainerStack(compose_repository, deployment_gateway, "portainer")

        with self.assertRaises(FileNotFoundError):
            await service.run()

        self.assertEqual([], deployment_gateway.applied_requests)

    async def test_gateway_failure_is_propagated(self):
        stack_definition = StackDefinition(name="portainer", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        deployment_gateway = _FakeDeploymentGateway(RuntimeError("deployment gateway failed"))

        service = EnsurePortainerStack(compose_repository, deployment_gateway, "portainer")

        with self.assertRaises(RuntimeError):
            await service.run()

        self.assertEqual(1, len(deployment_gateway.applied_requests))


class _FakeDeploymentGateway:
    def __init__(self, apply_exception: Exception | None = None) -> None:
        self.apply_exception = apply_exception
        self.applied_requests: list[DeploymentStackRequest] = []

    def apply_stack(self, request: DeploymentStackRequest) -> None:
        self.applied_requests.append(request)
        if self.apply_exception is not None:
            raise self.apply_exception

    def stack_registered(self, stack_name: str) -> bool:
        return bool(self.applied_requests)


def _single_applied_request(
    deployment_gateway: _FakeDeploymentGateway,
) -> DeploymentStackRequest:
    (request,) = deployment_gateway.applied_requests
    return request


if __name__ == "__main__":
    unittest.main()
