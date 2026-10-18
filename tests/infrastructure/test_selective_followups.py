"""Selection boundaries across WSL bridge, credentials and public direct access."""
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import yaml

from tiny_swarm_world.infrastructure.adapters.host.selected_port_registry import SelectedPortRegistryRunner
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml
from tiny_swarm_world.infrastructure.composition_runtime import _with_infisical_post_apply_steps, _deployment_stack_environment

ROOT = Path(__file__).resolve().parents[2]


class SelectiveFollowupTests(TestCase):
    def test_wsl_bridge_receives_only_selected_ports_and_original_is_unchanged(self):
        original = ROOT / "infra/config/ports.yaml"
        before = original.read_bytes()
        seen = []

        def run(action, **kwargs):
            path = kwargs["port_registry_path"]
            seen.append(path)
            content = path.read_text()
            # Existing PowerShell protocol exits the ports block at a non-indented line.
            port_lines = content.split("ports:\n", 1)[1].splitlines()
            self.assertTrue(port_lines[0].startswith("  - id:"))
            payload = yaml.safe_load(content)
            self.assertEqual({item["id"] for item in payload["ports"]}, {"portainer-http"})
            self.assertEqual(action, "verify")
            return SimpleNamespace(return_code=0)

        delegate = Mock()
        delegate.run.side_effect = run
        runner = SelectedPortRegistryRunner(delegate, ("portainer-http",))
        result = runner.run("verify", script_path=Path("bridge"), config_path=Path("config"),
                            port_registry_path=original, timeout_seconds=5)
        self.assertEqual(result.return_code, 0)
        self.assertEqual(original.read_bytes(), before)
        self.assertTrue(all(not path.exists() for path in seen))

    def test_infisical_synchronizes_before_jenkins_without_dashboard(self):
        infisical = SimpleNamespace(service_stack=SimpleNamespace(stack_name="infisical"))
        jenkins = SimpleNamespace(service_stack=SimpleNamespace(stack_name="jenkins"))
        sync = object()
        self.assertEqual(_with_infisical_post_apply_steps((infisical, jenkins), (sync,)),
                         (infisical, sync, jenkins))

    def test_minimal_ignores_invalid_unselected_image_override_and_has_direct_access(self):
        with patch.dict("os.environ", {"TSW_JENKINS_IMAGE": "invalid image reference"}):
            repository = ComposeFileRepositoryYaml(resolved_services=("incus", "portainer"), write_logs=False)
            inventory = repository.get_image_inventory()
            self.assertEqual({item.service_name.split(":")[0] for item in inventory.requirements}, {"portainer"})
            access = repository.get_effective_access_model().to_dict()
            self.assertEqual(access["routes"], [])
            self.assertEqual(access["gateway_public_ingress_ports"], [])
            self.assertEqual(access["service_access_links"][0]["url"], "http://localhost:10001")

    def test_minimal_does_not_validate_an_unused_registry_configuration(self):
        from tiny_swarm_world.domain.deployment import ServiceStackProfile

        with patch("tiny_swarm_world.infrastructure.composition_runtime._swarm_registry_endpoint", side_effect=ValueError("unselected registry")) as endpoint:
            environment = _deployment_stack_environment(ServiceStackProfile.DEFAULT, ("incus", "portainer"))
        endpoint.assert_not_called()
        self.assertNotIn("jenkins", environment)
