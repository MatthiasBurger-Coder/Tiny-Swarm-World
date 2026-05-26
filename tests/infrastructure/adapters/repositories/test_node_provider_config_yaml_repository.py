import tempfile
import unittest
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderConfigError,
    NodeProviderConfigYamlRepository,
)


class TestNodeProviderConfigYamlRepository(unittest.TestCase):
    def test_loads_committed_provider_config_with_lxc_native_default(self):
        config = NodeProviderConfigYamlRepository().load()

        self.assertEqual("1", config.schema_version)
        self.assertEqual(NodeProviderKind.LXC_NATIVE, config.default_provider)
        self.assertIsNone(config.preferred_backend)
        self.assertEqual(
            (ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
            config.backend_candidates,
        )
        self.assertEqual(
            ("swarm-manager", "swarm-worker-1", "swarm-worker-2"),
            tuple(node.spec.name for node in config.nodes),
        )
        self.assertEqual(NodeRole.MANAGER, config.nodes[0].spec.role)

    def test_committed_config_declares_multipass_legacy_only_as_explicit_fallback(self):
        config = NodeProviderConfigYamlRepository().load()

        fallback = config.legacy_fallbacks[0]

        self.assertEqual(NodeProviderKind.MULTIPASS_LEGACY, fallback.provider)
        self.assertEqual("explicit_only", fallback.selection_policy)
        self.assertFalse(fallback.automatic)

    def test_committed_config_declares_incus_and_lxd_profiles(self):
        config = NodeProviderConfigYamlRepository().load()
        profile = config.profiles[0]

        self.assertEqual("docker-swarm", profile.name)
        self.assertEqual((ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD), profile.backend_support)
        self.assertFalse(profile.privileged_default)
        self.assertTrue(profile.nesting_required)
        self.assertTrue(profile.syscall_interception_required)
        self.assertTrue(profile.live_mutation_consent_required)
        self.assertTrue(profile.blocks_mutation_when_missing)
        self.assertIn("docker_in_container_requires_nesting", profile.risk_labels)
        self.assertIn("privileged_profile_forbidden_default", profile.risk_labels)
        self.assertEqual((), profile.host_mounts)
        self.assertFalse(profile.host_network)

    def test_provider_config_load_is_deterministic(self):
        repository = NodeProviderConfigYamlRepository()

        self.assertEqual(repository.load(), repository.load())

    def test_missing_provider_config_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory) / "missing.yaml"

            with self.assertRaises(NodeProviderConfigError):
                NodeProviderConfigYamlRepository(missing_path).load()

    def test_invalid_yaml_raises_repository_validation_error(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "provider_config.yaml"
            config_path.write_text("schema_version: [\n", encoding="utf-8")

            with self.assertRaises(NodeProviderConfigError):
                NodeProviderConfigYamlRepository(config_path).load()

    def test_rejects_non_mapping_yaml_root(self):
        with self.assertRaises(NodeProviderConfigError):
            _repository_for(["not", "a", "mapping"]).load()

    def test_rejects_missing_schema_version(self):
        data = _valid_config()
        data.pop("schema_version")

        with self.assertRaises(NodeProviderConfigError):
            _repository_for(data).load()

    def test_rejects_unknown_root_field(self):
        data = _valid_config()
        data["surprise"] = "unsupported"

        with self.assertRaises(NodeProviderConfigError):
            _repository_for(data).load()

    def test_rejects_invalid_provider_and_backend_values(self):
        for mutation in (_with_default_provider("docker"), _with_backend_candidate("raw_lxc")):
            with self.subTest(mutation=mutation):
                with self.assertRaises(NodeProviderConfigError):
                    _repository_for(mutation).load()

    def test_rejects_duplicate_node_names(self):
        data = _valid_config()
        data["nodes"][1]["name"] = "swarm-manager"

        with self.assertRaises(NodeProviderConfigError):
            _repository_for(data).load()

    def test_rejects_automatic_multipass_fallback(self):
        data = _valid_config()
        data["legacy_fallbacks"][0]["automatic"] = True

        with self.assertRaises(NodeProviderConfigError):
            _repository_for(data).load()

    def test_rejects_privileged_default_profile(self):
        data = _valid_config()
        data["profiles"]["docker-swarm"]["privileged_default"] = True

        with self.assertRaises(NodeProviderConfigError):
            _repository_for(data).load()

    def test_rejects_missing_profile_risk_labels(self):
        data = _valid_config()
        data["profiles"]["docker-swarm"]["risk_labels"] = []

        with self.assertRaises(NodeProviderConfigError):
            _repository_for(data).load()

    def test_rejects_host_network_or_mounts(self):
        for key, value in (("host_network", True), ("host_mounts", ["workspace"])):
            data = _valid_config()
            data["profiles"]["docker-swarm"][key] = value

            with self.subTest(key=key):
                with self.assertRaises(NodeProviderConfigError):
                    _repository_for(data).load()

    def test_rejects_raw_evidence_policy(self):
        data = _valid_config()
        data["verification_metadata"]["evidence_policy"]["store_raw_output"] = True

        with self.assertRaises(NodeProviderConfigError):
            _repository_for(data).load()

    def test_rejects_host_specific_values_or_secrets(self):
        cases = (
            ("external_ip", "10.0.0.10"),
            ("username", "operator"),
            ("credential", "value"),
            ("notes", "/home/operator/workspace"),
            ("notes", "incus launch ubuntu:24.04 node"),
            ("notes", "token=hidden"),
            ("notes", "C:\\Users\\operator"),
        )

        for key, value in cases:
            data = _valid_config()
            data["nodes"][0][key] = value

            with self.subTest(key=key, value=value):
                with self.assertRaises(NodeProviderConfigError):
                    _repository_for(data).load()

    def test_committed_provider_config_contains_no_host_specific_values_or_secrets(self):
        rendered = repr(_load_committed_config_data()).casefold()

        forbidden_fragments = (
            "password",
            "secret",
            "token",
            "api_key",
            "credential",
            "authorization",
            "username",
            "host_user",
            "host_ip",
            "ip_address",
            "external_ip",
            "gateway",
            "local_path",
            "/home/",
            "/mnt/",
            "/users/",
            "/var/run/docker.sock",
            "/var/lib/docker",
            "privileged: true",
            "security.privileged",
        )
        self.assertNotRegex(rendered, r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, rendered)


def _repository_for(data: object) -> NodeProviderConfigYamlRepository:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
        path = Path(handle.name)
        YAML().dump(data, handle)
    return NodeProviderConfigYamlRepository(path)


def _valid_config() -> dict[str, Any]:
    return {
        "schema_version": "1",
        "default_provider": "lxc_native",
        "backend_selection": {
            "preferred_backend": None,
            "candidates": ["incus", "lxd"],
        },
        "legacy_fallbacks": [
            {
                "provider": "multipass_legacy",
                "selection_policy": "explicit_only",
                "automatic": False,
            }
        ],
        "nodes": [
            {
                "name": "swarm-manager",
                "role": "manager",
                "provider": "lxc_native",
                "backend": None,
                "profile": "docker-swarm",
                "image_alias": "ubuntu-24.04",
                "resources": {"cpu": "2", "memory": "4G", "disk": "20G"},
                "networks": ["control"],
            },
            {
                "name": "swarm-worker-1",
                "role": "worker",
                "provider": "lxc_native",
                "backend": None,
                "profile": "docker-swarm",
                "image_alias": "ubuntu-24.04",
                "resources": {"cpu": "2", "memory": "8G", "disk": "50G"},
                "networks": ["control"],
            },
        ],
        "profiles": {
            "docker-swarm": {
                "backend_support": ["incus", "lxd"],
                "risk_labels": [
                    "docker_in_container_requires_nesting",
                    "provider_profile_mutation_requires_live_consent",
                    "privileged_profile_forbidden_default",
                ],
                "privileged_default": False,
                "nesting_required": True,
                "syscall_interception_required": True,
                "cgroup_policy": "v2_required",
                "apparmor_policy": "provider_default",
                "seccomp_policy": "provider_default",
                "capability_additions": [],
                "host_network": False,
                "host_mounts": [],
                "live_mutation_consent_required": True,
                "blocks_mutation_when_missing": True,
            }
        },
        "verification_metadata": {
            "readiness_timeout_seconds": 5,
            "evidence_policy": {
                "summary_only": True,
                "store_raw_output": False,
            },
            "checks": ["backend_readiness", "profile_requirements"],
        },
    }


def _with_default_provider(provider: str) -> dict[str, Any]:
    data = _valid_config()
    data["default_provider"] = provider
    return data


def _with_backend_candidate(backend: str) -> dict[str, Any]:
    data = _valid_config()
    data["backend_selection"]["candidates"] = [backend, "lxd"]
    return data


def _load_committed_config_data() -> object:
    config_path = Path(__file__).resolve().parents[4] / "infra" / "config" / "node-providers" / "provider_config.yaml"
    return YAML(typ="safe").load(config_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
