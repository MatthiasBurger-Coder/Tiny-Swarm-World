import tempfile
import unittest
from pathlib import Path

from tiny_swarm_world.domain.network import PortExposureClass
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)


class TestPortRegistryYamlRepository(unittest.TestCase):
    def test_loads_committed_default_port_registry(self):
        registry = PortRegistryYamlRepository().load()

        self.assertEqual(len(registry.ranges), 11)
        self.assertEqual(len(registry.mappings), 24)
        self.assertEqual(tuple(port.external_port for port in registry.preflight_ports), (80, 443))
        self.assertEqual(
            PortExposureClass.PUBLIC_INGRESS,
            registry.mapping_for_port_id("traefik-http").exposure,
        )
        self.assertEqual(
            registry.mapping_for_port_id("service-access-legacy-http").external_port,
            8086,
        )

    def test_missing_port_registry_defaults_to_empty_registry(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            registry = PortRegistryYamlRepository(
                Path(temporary_directory) / "missing.yaml"
            ).load()

        self.assertEqual(registry.ranges, ())
        self.assertEqual(registry.mappings, ())

    def test_rejects_duplicate_external_ports(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            registry_file = Path(temporary_directory) / "ports.yaml"
            registry_file.write_text(
                """
ranges:
  - id: diagnostic
    start: 10000
    end: 19999
ports:
  - id: first
    service_id: first
    internal_port: 8080
    external_port: 10080
    exposure: diagnostic
    range_id: diagnostic
  - id: second
    service_id: second
    internal_port: 8080
    external_port: 10080
    exposure: diagnostic
    range_id: diagnostic
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "duplicate external ports"):
                PortRegistryYamlRepository(registry_file).load()

    def test_rejects_unsafe_metadata(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            registry_file = Path(temporary_directory) / "ports.yaml"
            registry_file.write_text(
                """
metadata:
  dashboard_url: "https://user:pass@example.test"
ranges: []
ports: []
""",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "secret|credential"):
                PortRegistryYamlRepository(registry_file).load()

    def test_rejects_non_mapping_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            registry_file = Path(temporary_directory) / "ports.yaml"
            registry_file.write_text("- invalid\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "root must be a mapping"):
                PortRegistryYamlRepository(registry_file).load()


class TestPortRegistryBoundary(unittest.TestCase):
    def test_invalid_yaml_shapes_and_scalars_are_rejected_safely(self):
        import traceback
        base = "ranges: []\nports: [{id: one, service_id: one, internal_port: 80, exposure: diagnostic, required_for_preflight: false}]"
        for text in (
            "ports: [boundary-marker-secret",
            "ports: []\nports: [boundary-marker-secret]",
            "ports: &loop [*loop]",
            base.replace("internal_port: 80", "internal_port: true"),
            base.replace("required_for_preflight: false", "required_for_preflight: 'false'"),
            base.replace("exposure: diagnostic", "exposure: boundary-marker-secret"),
            base + "\nmetadata: {note: [boundary-marker-secret]}",
            base + "\nmetadata: {1: boundary-marker-secret}",
        ):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "ports.yaml"
                path.write_text(text, encoding="utf-8")
                try:
                    PortRegistryYamlRepository(path).load()
                except ValueError as error:
                    self.assertNotIn("boundary-marker-secret", str(error))
                    self.assertNotIn("boundary-marker-secret", "".join(traceback.format_exception(error)))
                else:
                    self.fail("Malformed port registry accepted")

    def test_empty_documents_default_and_metadata_is_preserved(self):
        for text in ("", "null", "ranges: []\nports: []", "ranges: []\nports: []\nmetadata: {release: 2, owner: platform}"):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "ports.yaml"
                path.write_text(text, encoding="utf-8")
                registry = PortRegistryYamlRepository(path).load()
                self.assertEqual(registry.ranges, ())
                self.assertEqual(registry.mappings, ())
                if "metadata" in text:
                    self.assertEqual(dict(registry.metadata), {"release": "2", "owner": "platform"})


    def test_missing_null_or_misspelled_collections_are_rejected(self):
        for text in (
            "{}",
            "ranges: []",
            "ports: []",
            "ranges: null\nports: []",
            "ranges: []\nports: null",
            "ranges: null\nports: null",
            "range: []\nports: []",
            "ranges: []\nport: []",
        ):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "ports.yaml"
                path.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "must be a list"):
                    PortRegistryYamlRepository(path).load()
