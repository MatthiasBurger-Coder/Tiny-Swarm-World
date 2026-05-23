import unittest
from unittest.mock import MagicMock

from tiny_swarm_world.application.services.deployment.ensure_nexus_stack import EnsureNexusStack
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition


class TestEnsureNexusStack(unittest.TestCase):
    def test_creates_stack_when_missing(self):
        stack_definition = StackDefinition(name="nexus", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        portainer_client = MagicMock()
        portainer_client.get_endpoint_id_by_name.return_value = 1
        portainer_client.find_stack_id_by_name.return_value = None

        service = EnsureNexusStack(compose_repository, portainer_client, "nexus", "local")
        service.run()

        compose_repository.get_compose_of.assert_called_once_with("nexus")
        portainer_client.get_endpoint_id_by_name.assert_called_once_with("local")
        portainer_client.find_stack_id_by_name.assert_called_once_with("nexus")
        portainer_client.create_stack.assert_called_once_with(stack_definition, 1)
        portainer_client.update_stack.assert_not_called()

    def test_updates_stack_when_present(self):
        stack_definition = StackDefinition(name="nexus", compose_content="services: {}")
        compose_repository = MagicMock()
        compose_repository.get_compose_of.return_value = stack_definition
        portainer_client = MagicMock()
        portainer_client.get_endpoint_id_by_name.return_value = 1
        portainer_client.find_stack_id_by_name.return_value = 7

        service = EnsureNexusStack(compose_repository, portainer_client, "nexus", "local")
        service.run()

        compose_repository.get_compose_of.assert_called_once_with("nexus")
        portainer_client.get_endpoint_id_by_name.assert_called_once_with("local")
        portainer_client.find_stack_id_by_name.assert_called_once_with("nexus")
        portainer_client.update_stack.assert_called_once_with(7, stack_definition, 1)
        portainer_client.create_stack.assert_not_called()
