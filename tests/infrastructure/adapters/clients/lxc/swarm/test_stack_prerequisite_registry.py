import subprocess
import unittest
from unittest.mock import Mock

from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.stack_prerequisite_registry import (
    StackPrerequisiteRegistry,
)


class TestStackPrerequisiteRegistry(unittest.TestCase):
    def test_registry_applies_network_and_sonarqube_strategies_in_order(self):
        run_manager_shell = Mock(
            side_effect=[
                subprocess.CompletedProcess([], 1),
                subprocess.CompletedProcess([], 0),
                subprocess.CompletedProcess([], 0),
            ]
        )
        ensure_network = Mock()
        ensure_tls = Mock()
        registry = StackPrerequisiteRegistry()
        definition = StackDefinition(
            name="sonarqube",
            compose_content=(
                "networks:\n"
                "  shared:\n"
                "    name: shared_overlay\n"
                "    external: true\n"
            ),
        )

        registry.ensure(
            "sonarqube",
            definition,
            ensure_external_overlay_network=ensure_network,
            ensure_traefik_tls_secrets=ensure_tls,
            run_manager_shell=run_manager_shell,
        )

        ensure_network.assert_called_once_with("shared_overlay")
        ensure_tls.assert_not_called()
        run_manager_shell.assert_called_once_with(
            "sysctl -w vm.max_map_count=524288 fs.file-max=131072 >/dev/null"
        )

    def test_traefik_tls_strategy_is_idempotent_when_secrets_exist(self):
        run_manager_shell = Mock()
        registry = StackPrerequisiteRegistry()

        registry.ensure_traefik_tls_secrets(
            "cert",
            "key",
            external_secret_exists=Mock(return_value=True),
            run_manager_shell=run_manager_shell,
        )

        run_manager_shell.assert_not_called()
