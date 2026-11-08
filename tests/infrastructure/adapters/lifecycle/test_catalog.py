from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.artifacts.container_image_contract import DEFAULT_CONTAINER_IMAGE_CONTRACTS
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog

ROOT = Path(__file__).resolve().parents[4]


class NativeCatalogTests(unittest.TestCase):
    def test_catalog_covers_native_images_bundles_foundations_and_policies(self):
        catalog = NativeComponentCatalog(ROOT).load()
        services = {item.service_id: item for item in catalog.services}
        self.assertEqual(set(services), {"incus", "portainer", "traefik", "nexus", "jenkins", "pulsar", "sonarqube", "swagger", "infisical", "service-access"})
        self.assertEqual({name for name, item in services.items() if item.mandatory}, {"incus", "portainer"})
        components = {item.component_id: item for service in catalog.services for item in service.components}
        self.assertEqual(set(components) - {"incus"}, {item.build_context for item in DEFAULT_CONTAINER_IMAGE_CONTRACTS})
        self.assertIsNone(components["incus"].desired.image_repository)
        self.assertIsNone(components["jenkins"].desired.upstream_version)
        self.assertEqual(components["jenkins"].desired.build_identity, "0.2.0")
        self.assertIsNotNone(components["swagger-api"].desired.image_digest)
        self.assertIsNone(components["swagger-api"].desired.image_tag)
        self.assertEqual(components["pulsar-manager-bootstrap"].service_id, "pulsar")
        self.assertIn("nexus", services["jenkins"].dependencies)
        self.assertIn("infisical", services["service-access"].dependencies)
        self.assertTrue(all(item.migration_policy == ("explicit-transitions" if item.service_id in {"portainer", "swagger", "traefik"} else "no-qualified-transition") for item in catalog.services))
        self.assertTrue(all(item.resources.qualification == "native-declarations-only" for item in catalog.services))

    def test_injected_preview_text_reader_matches_legacy_catalog(self):
        captured = []
        def read(relative):
            captured.append(relative)
            return (ROOT / relative).read_text(encoding="utf-8")
        self.assertEqual(NativeComponentCatalog(ROOT, text_reader=read).load(), NativeComponentCatalog(ROOT).load())
        self.assertEqual(len(captured), 9)
        self.assertEqual(len(set(captured)), 9)

    def test_injected_reader_failure_is_sanitized(self):
        def read(_relative):
            raise PermissionError("SECRET /private")
        with self.assertRaises(LifecycleStateError) as caught:
            NativeComponentCatalog(ROOT, text_reader=read).load()
        self.assertNotIn("SECRET", str(caught.exception))

    def test_mismatched_native_image_blocks_without_echoing_configuration(self):
        with patch("tiny_swarm_world.infrastructure.adapters.lifecycle.catalog.yaml.safe_load", return_value={"services": {"portainer": {"image": "SECRET_SENTINEL"}, "agent": {"image": "SECRET_SENTINEL"}}}):
            with self.assertRaises(LifecycleStateError) as caught:
                NativeComponentCatalog(ROOT).load()
            self.assertNotIn("SECRET_SENTINEL", str(caught.exception))

    def test_malformed_yaml_shapes_are_sanitized(self):
        for payload in ([], None, {"services": []}, {"services": {"portainer": None}},
                        {"services": {"portainer": {"deploy": None}}},
                        {"services": {"portainer": {"deploy": {"resources": []}}}}):
            with self.subTest(payload=payload), patch("tiny_swarm_world.infrastructure.adapters.lifecycle.catalog.yaml.safe_load", return_value=payload), self.assertRaises(LifecycleStateError):
                NativeComponentCatalog(ROOT).load()

    def test_missing_assets_block(self):
        with TemporaryDirectory() as directory, self.assertRaises(LifecycleStateError):
            NativeComponentCatalog(Path(directory)).load()
