"""Mocked repeat-run and failure contracts for deployment prerequisites."""

import subprocess
import unittest
from unittest.mock import Mock

from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client import (
    LxcPortainerHttpClient,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import (
    LxcSwarmStackRuntime,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.stack_prerequisite_registry import (
    StackPrerequisiteRegistry,
)


class TestRecoverySemantics(unittest.TestCase):
    def test_main_swarm_network_prerequisite_requires_proven_absence(self):
        registry = StackPrerequisiteRegistry()
        commands: list[str] = []

        def failing_inventory(script: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            commands.append(script)
            return subprocess.CompletedProcess([], 1, stdout="")

        with self.assertRaisesRegex(RuntimeError, "state could not be established"):
            registry.ensure_external_overlay_network(
                "shared", run_manager_shell=failing_inventory,
            )
        self.assertEqual(2, len(commands))
        self.assertFalse(any("network create" in command for command in commands))

    def test_network_creation_is_noop_on_repeat_and_failure_stops_stack_apply(self):
        client = LxcPortainerHttpClient(
            backend=ManagedLxcBackend.LXD, username="admin", password="test-value",
        )
        observed = False
        scripts: list[str] = []

        def manager_shell(script: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            nonlocal observed
            scripts.append(script)
            if "network inspect" in script:
                return subprocess.CompletedProcess([], 0 if observed else 1)
            if "network ls" in script:
                return subprocess.CompletedProcess([], 0, stdout="shared\n" if observed else "")
            if "network create" in script:
                observed = True
                return subprocess.CompletedProcess([], 0)
            raise AssertionError("unexpected manager command")

        client._run_manager_shell = manager_shell
        stack = StackDefinition(
            name="example", compose_content="networks:\n  shared:\n    external: true\n",
        )
        client._ensure_external_overlay_networks(stack)
        client._ensure_external_overlay_networks(stack)
        self.assertEqual(2, sum("network inspect" in script for script in scripts))
        self.assertEqual(1, sum("network create" in script for script in scripts))

        def failing_shell(script: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            if "network inspect" in script:
                return subprocess.CompletedProcess([], 1)
            if "network ls" in script:
                return subprocess.CompletedProcess([], 0, stdout="")
            raise RuntimeError("network creation failed")

        client._run_manager_shell = failing_shell
        client._cached_client = Mock()
        with self.assertRaisesRegex(RuntimeError, "network creation failed"):
            client.create_stack(stack, 1)
        client._cached_client.create_stack.assert_not_called()

        client._run_manager_shell = lambda script, **_kwargs: subprocess.CompletedProcess(
            [], 1 if "network inspect" in script else 0, stdout="shared\n",
        )
        with self.assertRaisesRegex(RuntimeError, "state could not be established"):
            client.create_stack(stack, 1)
        client._cached_client.create_stack.assert_not_called()

        client._run_manager_shell = lambda script, **_kwargs: subprocess.CompletedProcess(
            [], 1, stdout="",
        )
        with self.assertRaisesRegex(RuntimeError, "state could not be established"):
            client.create_stack(stack, 1)
        client._cached_client.create_stack.assert_not_called()

    def test_secret_creation_is_noop_on_repeat_and_failure_is_visible(self):
        present = False
        creates: list[str] = []

        def manager_shell(script: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            nonlocal present
            if "secret inspect" in script:
                return subprocess.CompletedProcess([], 0 if present else 1)
            if "secret ls" in script:
                return subprocess.CompletedProcess([], 0, stdout="example_key\n" if present else "")
            if "secret create" in script:
                creates.append(script)
                present = True
                return subprocess.CompletedProcess([], 0)
            raise AssertionError("unexpected manager command")

        runtime = LxcSwarmStackRuntime(
            remote_stack_root="/remote/stacks", service_list_timeout_seconds=30,
            run_manager_shell=manager_shell, run_node_shell=Mock(),
            prepare_stack_assets=Mock(), ensure_stack_prerequisites=Mock(),
        )
        runtime.ensure_external_secret("example_key", "test-value")
        runtime.ensure_external_secret("example_key", "test-value")
        self.assertEqual(1, len(creates))
        self.assertNotIn("test-value", creates[0])

        def failing_shell(script: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            if "secret inspect" in script:
                return subprocess.CompletedProcess([], 1)
            if "secret ls" in script:
                return subprocess.CompletedProcess([], 0, stdout="")
            raise RuntimeError("secret creation failed")

        runtime._run_manager_shell = failing_shell
        with self.assertRaisesRegex(RuntimeError, "secret creation failed"):
            runtime.ensure_external_secret("other_key", "test-value")

        runtime._run_manager_shell = lambda script, **_kwargs: subprocess.CompletedProcess(
            [], 1 if "secret inspect" in script else 0, stdout="other_key\n",
        )
        with self.assertRaisesRegex(RuntimeError, "state could not be established"):
            runtime.ensure_external_secret("other_key", "test-value")

    def test_failed_swarm_observations_never_look_like_absent_resources(self):
        commands: list[str] = []

        def unavailable(script: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
            commands.append(script)
            return subprocess.CompletedProcess([], 1, stdout="")

        runtime = LxcSwarmStackRuntime(
            remote_stack_root="/remote/stacks", service_list_timeout_seconds=30,
            run_manager_shell=unavailable, run_node_shell=Mock(),
            prepare_stack_assets=Mock(), ensure_stack_prerequisites=Mock(),
        )
        with self.assertRaisesRegex(RuntimeError, "stack inventory"):
            runtime.stack_exists("example")
        with self.assertRaisesRegex(RuntimeError, "service inventory"):
            runtime.list_stack_services("example")
        with self.assertRaisesRegex(RuntimeError, "published ports"):
            runtime.published_ports("example_web")
        with self.assertRaisesRegex(RuntimeError, "published ports"):
            runtime.reconcile_host_published_ports(StackDefinition(
                name="example",
                compose_content=(
                    "services:\n  web:\n    image: nginx:stable\n    ports:\n"
                    "      - target: 80\n        published: 8080\n        mode: host\n"
                ),
            ))
        self.assertFalse(any("service update" in script for script in commands))

        runtime._run_manager_shell = lambda script, **_kwargs: subprocess.CompletedProcess(
            [], 1, stdout="",
        )
        with self.assertRaisesRegex(RuntimeError, "state could not be established"):
            runtime.ensure_external_secret("other_key", "test-value")
