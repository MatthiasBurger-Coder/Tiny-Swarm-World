import unittest
from unittest.mock import Mock

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    SwarmServiceStatus,
)
from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.infrastructure.adapters.clients.docker_swarm_runtime import (
    DockerSwarmRuntime,
)


class TestDockerSwarmRuntime(unittest.TestCase):
    def test_delegates_proven_operations_to_concrete_transport(self):
        delegate = Mock()
        services = (SwarmServiceStatus("demo_web", 1, 1),)
        delegate.list_stack_services.return_value = services
        runtime = DockerSwarmRuntime(delegate)
        definition = StackDefinition(name="demo", compose_content="services: {}")

        runtime.deploy_stack(definition, {"IMAGE": "demo:1"})
        self.assertIs(runtime.stack_exists("demo"), delegate.stack_exists.return_value)
        self.assertEqual(services, runtime.list_stack_services("demo"))
        self.assertIs(runtime.external_secret_exists("demo-secret"), delegate.external_secret_exists.return_value)
        runtime.ensure_external_secret("demo-secret", "value")

        delegate.deploy_stack.assert_called_once_with(definition, {"IMAGE": "demo:1"})
        delegate.stack_exists.assert_called_once_with("demo")
        delegate.list_stack_services.assert_called_once_with("demo")
        delegate.external_secret_exists.assert_called_once_with("demo-secret")
        delegate.ensure_external_secret.assert_called_once_with("demo-secret", "value")

    def test_preserves_runtime_failure_for_application_translation(self):
        delegate = Mock()
        delegate.deploy_stack.side_effect = RuntimeError("runtime operation failed")
        runtime = DockerSwarmRuntime(delegate)
        definition = StackDefinition(name="demo", compose_content="services: {}")

        with self.assertRaisesRegex(RuntimeError, "runtime operation failed"):
            runtime.deploy_stack(definition)
