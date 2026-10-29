"""Domain-only v1 migration preview and hostile-input tests."""
from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest
from unittest.mock import patch

from tiny_swarm_world.domain.lifecycle import manifest_v2
from tiny_swarm_world.domain.lifecycle.models import (
    ComponentCatalog, ComponentState, ConfigurationReference, CredentialReference,
    InstallationManifest, ProductIdentity, ResourceRequirements, ServiceDefinition,
    VersionIdentity,
)


def component(name: str) -> ComponentState:
    return ComponentState(component_id=name, service_id=name, desired=VersionIdentity())


def service(name: str, kind: str, *, dependencies: tuple[str, ...] = (),
            presets: tuple[str, ...] = ("default", "service-access")) -> ServiceDefinition:
    return ServiceDefinition.model_validate({
        "service_id": name, "kind": kind, "mandatory": name in {"incus", "portainer"},
        "dependencies": dependencies, "capabilities": (), "components": (component(name),),
        "resources": ResourceRequirements(), "native_asset": None, "presets": presets,
        "lifecycle_owner": ("host-operator" if name == "incus"
                            else "portainer-adapter" if name == "portainer" else "stack-update"),
        "backup_policy": "not-applicable",
    }, strict=True)


def fixtures(selected: tuple[str, ...] = ()) -> tuple[InstallationManifest, ComponentCatalog]:
    services = (
        service("incus", "host-prerequisite"),
        service("portainer", "managed-foundation", dependencies=("incus",)),
        service("nexus", "stack", dependencies=("portainer",)),
        service("swagger", "stack", dependencies=("portainer",)),
        service("jenkins", "stack", dependencies=("portainer",)),
    )
    resolved = ("incus", "portainer") + selected
    catalog = ComponentCatalog(services=services)
    manifest = InstallationManifest(
        installation_id="12345678-1234-1234-1234-123456789abc",
        host="native-linux", service_preset="default",
        product=ProductIdentity(release="0.2.0", revision="a" * 40, dependency_lock="sha256:" + "b" * 64),
        requested_services=("incus",), resolved_services=resolved,
        selection_reasons={name: ("incus",) for name in resolved if name != "incus"},
        components=tuple(component(name) for name in resolved),
        credential_references=(CredentialReference(key="TSW_PORTAINER_PASSWORD", source="external_user_secret"),),
        configuration_references=(ConfigurationReference(key="route", source="operator_override", reference="local"),),
        operation_reference="operation-1", checkpoint_reference="checkpoint-1",
    )
    return manifest, catalog


class ManifestPreviewTests(unittest.TestCase):
    def test_minimal_selection_preserves_every_value_without_adding_swagger(self) -> None:
        manifest, catalog = fixtures()
        before = manifest.model_dump(mode="python")
        preview = manifest_v2.preview_migration(manifest, catalog)
        self.assertEqual(preview.v1_snapshot, before)
        self.assertEqual(preview.stack_policies, ())
        self.assertIs(preview.swagger_exposure, manifest_v2.SwaggerExposure.NOT_APPLICABLE)
        resolved = preview.v1_snapshot["resolved_services"]
        assert isinstance(resolved, tuple)
        self.assertNotIn("swagger", resolved)
        for identity in (preview.project, preview.profile, preview.route, preview.owner):
            self.assertIs(identity, manifest_v2.UnknownIdentity.UNKNOWN)
        self.assertEqual(manifest.model_dump(mode="python"), before)

    def test_selected_stack_defaults_are_sorted_and_swagger_explicit(self) -> None:
        for selected, expected in (
            (("nexus",), (("nexus", "swarm"),)),
            (("swagger", "nexus", "jenkins"), (("jenkins", "swarm"), ("nexus", "swarm"), ("swagger", "swarm"))),
        ):
            with self.subTest(selected=selected):
                manifest, catalog = fixtures(selected)
                preview = manifest_v2.preview_migration(manifest, catalog)
                self.assertEqual(preview.stack_policies, expected)
                exposure = (manifest_v2.SwaggerExposure.PUBLISHED if "swagger" in selected
                            else manifest_v2.SwaggerExposure.NOT_APPLICABLE)
                self.assertIs(preview.swagger_exposure, exposure)

    def test_deep_detachment_and_immutable_preview(self) -> None:
        manifest, catalog = fixtures(("nexus",))
        preview = manifest_v2.preview_migration(manifest, catalog)
        with self.assertRaises(TypeError):
            preview.v1_snapshot["host"] = "wsl2"  # type: ignore[index]
        reasons = preview.v1_snapshot["selection_reasons"]
        self.assertIsNot(reasons, manifest.selection_reasons)
        with self.assertRaises(TypeError):
            reasons["portainer"] = ("nexus",)  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError):
            preview.project = manifest_v2.UnknownIdentity.UNKNOWN  # type: ignore[misc]
        manifest.selection_reasons["portainer"] = ("nexus",)
        self.assertEqual(reasons["portainer"], ("incus",))  # type: ignore[index]
        self.assertEqual(preview.v1_snapshot["credential_references"][0]["key"], "TSW_PORTAINER_PASSWORD")  # type: ignore[index]
        self.assertEqual(preview.v1_snapshot["configuration_references"][0]["reference"], "local")  # type: ignore[index]

    def test_duplicate_and_ambiguous_catalogs_fail_closed(self) -> None:
        manifest, catalog = fixtures(("nexus",))
        services = catalog.services
        duplicate_component = services[3].model_copy(update={"components": (component("nexus"),)})
        wrong_owner = services[3].model_copy(update={"components": (component("jenkins"),)})
        for invalid in (
            catalog.model_copy(update={"services": services + (services[0],)}),
            catalog.model_copy(update={"services": services[:3] + (duplicate_component,) + services[4:]}),
            catalog.model_copy(update={"services": services[:3] + (wrong_owner,) + services[4:]}),
        ):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, r"^Invalid v1 migration input\.$"):
                manifest_v2.preview_migration(manifest, invalid)

    def test_catalog_unknown_dependencies_and_cycles_fail_even_when_unselected(self) -> None:
        manifest, catalog = fixtures()
        for changes in (
            {"swagger": ("swagger",)},
            {"swagger": ("nexus",), "nexus": ("swagger",)},
            {"swagger": ("not-in-catalog",)},
        ):
            with self.subTest(changes=changes):
                services = tuple(item.model_copy(update={"dependencies": changes[item.service_id]})
                                 if item.service_id in changes else item for item in catalog.services)
                with self.assertRaisesRegex(ValueError, r"^Invalid v1 migration input\.$"):
                    manifest_v2.preview_migration(manifest, catalog.model_copy(update={"services": services}))

    def test_foundations_and_selected_swagger_classifications_are_required(self) -> None:
        manifest, catalog = fixtures(("swagger",))
        services = catalog.services
        for index, kind in ((0, "stack"), (1, "stack"), (3, "host-prerequisite")):
            with self.subTest(index=index):
                replacement = services[index].model_copy(update={"kind": kind})
                bad = catalog.model_copy(update={"services": services[:index] + (replacement,) + services[index + 1:]})
                with self.assertRaises(ValueError):
                    manifest_v2.preview_migration(manifest, bad)

    def test_selection_preset_dependency_and_component_bundle_are_validated(self) -> None:
        manifest, catalog = fixtures(("nexus",))
        unknown = manifest.model_copy(update={
            "resolved_services": manifest.resolved_services + ("unknown",),
            "selection_reasons": dict(manifest.selection_reasons, unknown=("incus",)),
        })
        missing_component = manifest.model_copy(update={"components": manifest.components[:-1]})
        missing_dependency = catalog.model_copy(update={"services": tuple(
            item.model_copy(update={"dependencies": ("jenkins",)}) if item.service_id == "nexus" else item
            for item in catalog.services)})
        invalid_preset = catalog.model_copy(update={"services": tuple(
            item.model_copy(update={"presets": ("service-access",)}) if item.service_id == "nexus" else item
            for item in catalog.services)})
        for bad_manifest, bad_catalog in ((unknown, catalog), (missing_component, catalog),
                                          (manifest, missing_dependency), (manifest, invalid_preset)):
            with self.subTest(bad_manifest=bad_manifest, bad_catalog=bad_catalog), self.assertRaises(ValueError):
                manifest_v2.preview_migration(bad_manifest, bad_catalog)

    def test_forged_models_nested_updates_and_versions_are_revalidated(self) -> None:
        manifest, catalog = fixtures()
        bad_product = manifest.product.model_copy(update={"revision": "secret"})
        bad_component = manifest.components[0].model_copy(update={"desired": VersionIdentity.model_construct(
            image_tag="tag", image_repository=None)})
        bad_service = catalog.services[0].model_copy(update={"mandatory": "yes"})
        cases: tuple[tuple[object, object], ...] = (
            (None, catalog), (manifest, object()), ({}, catalog),
            (manifest.model_copy(update={"schema_version": True}), catalog),
            (manifest.model_copy(update={"catalog_version": 2}), catalog),
            (manifest.model_copy(update={"product": bad_product}), catalog),
            (manifest.model_copy(update={"components": (bad_component,) + manifest.components[1:]}), catalog),
            (InstallationManifest.model_construct(**dict(manifest.model_dump(), host="bad")), catalog),
            (manifest, catalog.model_copy(update={"schema_version": True})),
            (manifest, catalog.model_copy(update={"catalog_version": 2})),
            (manifest, catalog.model_copy(update={"services": (bad_service,) + catalog.services[1:]})),
            (manifest, ComponentCatalog.model_construct(schema_version=1, catalog_version=1, services=("bad",))),
        )
        for bad_manifest, bad_catalog in cases:
            with self.subTest(bad_manifest=bad_manifest, bad_catalog=bad_catalog):
                with self.assertRaises(ValueError) as caught:
                    manifest_v2.preview_migration(bad_manifest, bad_catalog)
                self.assertNotIn("secret", str(caught.exception))

    def test_domain_imports_and_preview_have_no_host_io(self) -> None:
        tree = ast.parse(inspect.getsource(manifest_v2))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
                imports.add(node.module or "")
        self.assertEqual(imports, {"dataclasses", "enum", "types", "typing",
                                   "tiny_swarm_world.domain.lifecycle.models",
                                   "tiny_swarm_world.domain.lifecycle.selection"})
        manifest, catalog = fixtures()
        with patch("builtins.open", side_effect=AssertionError("filesystem")), \
                patch("os.system", side_effect=AssertionError("command")), \
                patch("subprocess.Popen", side_effect=AssertionError("process")), \
                patch("socket.socket", side_effect=AssertionError("network")):
            self.assertEqual(manifest_v2.preview_migration(manifest, catalog).stack_policies, ())


if __name__ == "__main__":
    unittest.main()
