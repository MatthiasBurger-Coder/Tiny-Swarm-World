import unittest
from unittest.mock import MagicMock

from tiny_swarm_world.application.services.deployment.ensure_portainer_stack import (
    EnsurePortainerStack,
)
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition


class TestEnsurePortainerStack(unittest.IsolatedAsyncioTestCase):
    async def test_creates_stack_when_portainer_stack_is_missing(self):
        stack_definition = StackDefinition(name="portainer", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        portainer_client = MagicMock()
        portainer_client.get_endpoint_id_by_name.return_value = 7
        portainer_client.find_stack_id_by_name.return_value = None

        service = EnsurePortainerStack(compose_repository, portainer_client, "portainer", "local")
        await service.run()

        compose_repository.get_compose_of.assert_called_once_with("portainer")
        portainer_client.get_endpoint_id_by_name.assert_called_once_with("local")
        portainer_client.find_stack_id_by_name.assert_called_once_with("portainer")
        portainer_client.create_stack.assert_called_once_with(stack_definition, 7)
        portainer_client.update_stack.assert_not_called()

    async def test_updates_stack_when_portainer_stack_exists(self):
        stack_definition = StackDefinition(name="portainer", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        portainer_client = MagicMock()
        portainer_client.get_endpoint_id_by_name.return_value = 7
        portainer_client.find_stack_id_by_name.return_value = 42

        service = EnsurePortainerStack(compose_repository, portainer_client, "portainer", "local")
        await service.run()

        portainer_client.create_stack.assert_not_called()
        portainer_client.update_stack.assert_called_once_with(42, stack_definition, 7)

    async def test_compose_lookup_failure_does_not_deploy_stack(self):
        compose_repository = MagicMock()
        compose_repository.get_compose_of.side_effect = FileNotFoundError("missing")
        portainer_client = MagicMock()

        service = EnsurePortainerStack(compose_repository, portainer_client, "portainer", "local")

        with self.assertRaises(FileNotFoundError):
            await service.run()

        portainer_client.get_endpoint_id_by_name.assert_not_called()
        portainer_client.find_stack_id_by_name.assert_not_called()
        portainer_client.create_stack.assert_not_called()
        portainer_client.update_stack.assert_not_called()

    async def test_endpoint_lookup_failure_does_not_create_or_update_stack(self):
        stack_definition = StackDefinition(name="portainer", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        portainer_client = MagicMock()
        portainer_client.get_endpoint_id_by_name.side_effect = RuntimeError("endpoint missing")

        service = EnsurePortainerStack(compose_repository, portainer_client, "portainer", "local")

        with self.assertRaises(RuntimeError):
            await service.run()

        portainer_client.find_stack_id_by_name.assert_not_called()
        portainer_client.create_stack.assert_not_called()
        portainer_client.update_stack.assert_not_called()


if __name__ == "__main__":
    unittest.main()
