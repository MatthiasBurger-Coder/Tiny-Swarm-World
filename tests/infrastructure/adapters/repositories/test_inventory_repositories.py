import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.domain.deployment import service_stack_contracts_for_profile
from tiny_swarm_world.domain.inventory import (
    DesiredInventory,
    ObservedInventory,
    VerificationResult,
    VerificationStatus,
    VmObservedState,
)
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.repositories.desired_inventory_yaml_repository import (
    DesiredInventoryYamlRepository,
)
from tiny_swarm_world.infrastructure.adapters.repositories.local_state_paths import (
    LocalStatePathError,
    local_state_file,
)
from tiny_swarm_world.infrastructure.adapters.repositories.observed_inventory_local_repository import (
    ObservedInventoryLocalRepository,
)
from tiny_swarm_world.infrastructure.adapters.repositories.verification_evidence_local_repository import (
    VerificationEvidenceLocalRepository,
)


class TestDesiredInventoryYamlRepository(unittest.TestCase):
    def test_loads_desired_inventory_from_yaml(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            inventory_file = Path(temporary_directory) / "desired_inventory.yaml"
            inventory_file.write_text(
                """
schema_version: "1"
vms:
  - name: tsw-manager-1
    role: manager
    image: ubuntu:24.04
    memory: 4G
    disk: 20G
    networks:
      - control
    stacks:
      - portainer
expected_stacks:
  - portainer
expected_artifact_registries:
  - nexus
""",
                encoding="utf-8",
            )

            inventory = DesiredInventoryYamlRepository(inventory_file).load()

        self.assertEqual("tsw-manager-1", inventory.vms[0].name)
        self.assertEqual(("portainer",), inventory.expected_stacks)

    def test_missing_desired_inventory_defaults_to_empty_inventory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_file = Path(temporary_directory) / "missing.yaml"

            inventory = DesiredInventoryYamlRepository(missing_file).load()

        self.assertEqual(DesiredInventory(), inventory)

    def test_loads_committed_default_desired_inventory_without_host_specific_values(self):
        inventory = DesiredInventoryYamlRepository().load()

        self.assertEqual(
            ("swarm-manager", "swarm-worker-1", "swarm-worker-2"),
            tuple(vm.name for vm in inventory.vms),
        )
        self.assertEqual(
            (
                "portainer",
                "traefik",
                "nexus",
                "jenkins",
                "pulsar",
                "sonarqube",
                "swagger",
                "infisical",
                "service-access",
            ),
            inventory.expected_stacks,
        )
        self.assertTrue(all("service-access" in vm.stacks for vm in inventory.vms))
        self.assertEqual(("nexus",), inventory.expected_artifact_registries)
        self.assertFalse(_contains_forbidden_inventory_key(inventory.to_dict()))

    def test_committed_default_inventory_matches_default_setup_service_profile(self):
        inventory = DesiredInventoryYamlRepository().load()
        stack_names = tuple(
            contract.stack_name
            for contract in service_stack_contracts_for_profile(
                composition.DEFAULT_SETUP_SERVICE_PROFILE
            )
        )

        self.assertEqual(stack_names, inventory.expected_stacks)

    def test_rejects_non_mapping_yaml_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            inventory_file = Path(temporary_directory) / "desired_inventory.yaml"
            inventory_file.write_text("- not-a-mapping\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                DesiredInventoryYamlRepository(inventory_file).load()

    def test_rejects_host_specific_desired_inventory_fields(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            inventory_file = Path(temporary_directory) / "desired_inventory.yaml"
            inventory_file.write_text(
                """
schema_version: "1"
vms:
  - name: swarm-manager
    role: manager
    external_ip: 10.0.0.10
""",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                DesiredInventoryYamlRepository(inventory_file).load()


class TestObservedInventoryLocalRepository(unittest.TestCase):
    def test_round_trips_observed_inventory_under_ignored_local_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            repository = ObservedInventoryLocalRepository(root=root)
            inventory = ObservedInventory(
                vms=(
                    VmObservedState(
                        name="tsw-manager-1",
                        status="running",
                        verification=VerificationResult(
                            target_id="vm:tsw-manager-1",
                            status=VerificationStatus.VERIFIED,
                            evidence={"probe": "summary"},
                        ),
                    ),
                )
            )

            repository.save(inventory)
            loaded = repository.load()

        self.assertEqual(inventory, loaded)
        self.assertIn(".tiny-swarm-world", str(repository.path))
        self.assertNotIn("infra/config", str(repository.path).replace("\\", "/"))

    def test_rejects_absolute_local_state_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(LocalStatePathError):
                ObservedInventoryLocalRepository(
                    root=Path(temporary_directory),
                    relative_path=Path(temporary_directory) / "observed.json",
                )

    def test_rejects_local_state_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(LocalStatePathError):
                ObservedInventoryLocalRepository(
                    root=Path(temporary_directory),
                    relative_path="../infra/config/observed.json",
                )

    def test_rejects_repository_root_inside_infra_config(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "infra" / "config"
            root.mkdir(parents=True)

            with self.assertRaises(LocalStatePathError):
                ObservedInventoryLocalRepository(root=root)

    def test_missing_observed_inventory_defaults_to_empty_inventory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = ObservedInventoryLocalRepository(root=Path(temporary_directory))

            inventory = repository.load()

        self.assertEqual(ObservedInventory(), inventory)

    def test_rejects_contaminated_observed_inventory_before_persistence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = ObservedInventoryLocalRepository(root=Path(temporary_directory))

            with self.assertRaises(ValueError):
                repository.save(
                    ObservedInventory(
                        vms=(
                            VmObservedState(
                                name="manager",
                                status="docker swarm join --token hidden",
                            ),
                        )
                    )
                )

    def test_default_local_state_root_env_must_point_to_verified_repository_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.dict("os.environ", {"TSW_REPOSITORY_ROOT": temporary_directory}):
                with self.assertRaises(LocalStatePathError):
                    local_state_file(relative_path="observed.json")


class TestVerificationEvidenceLocalRepository(unittest.TestCase):
    def test_appends_verification_results_without_raw_payloads(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = VerificationEvidenceLocalRepository(root=Path(temporary_directory))
            result = VerificationResult(
                target_id="stack:portainer",
                status=VerificationStatus.VERIFIED,
                message="Stack exists.",
                evidence={"summary": "one running service"},
            )

            repository.append(result)
            loaded = repository.list_all()

        self.assertEqual((result,), loaded)
        self.assertIn(".tiny-swarm-world", str(repository.path))

    def test_rejects_raw_payload_before_persistence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = VerificationEvidenceLocalRepository(root=Path(temporary_directory))

            with self.assertRaises(ValueError):
                repository.append(VerificationResult("command:probe", evidence={"stderr": "raw"}))

    def test_rejects_sensitive_payload_values_before_persistence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = VerificationEvidenceLocalRepository(root=Path(temporary_directory))

            with self.assertRaises(ValueError):
                repository.append(
                    VerificationResult(
                        "command:probe",
                        evidence={"summary": "docker swarm join --token hidden"},
                    )
                )

    def test_rejects_raw_message_before_persistence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            VerificationEvidenceLocalRepository(root=Path(temporary_directory))

            with self.assertRaises(ValueError):
                VerificationResult(
                    "command:probe",
                    message="docker swarm join --token hidden",
                )


def _contains_forbidden_inventory_key(value: object) -> bool:
    forbidden_keys = {
        "external_ip",
        "gateway",
        "docker_bridge_ip",
        "docker_overlay_ip",
        "username",
        "password",
        "secret",
        "token",
    }
    if isinstance(value, dict):
        return any(
            str(key) in forbidden_keys or _contains_forbidden_inventory_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_inventory_key(item) for item in value)
    return False


if __name__ == "__main__":
    unittest.main()
