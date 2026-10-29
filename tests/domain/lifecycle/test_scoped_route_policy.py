"""Pure code-bound route reference and deterministic profile identity tests."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from itertools import combinations
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tests.domain.lifecycle.test_legacy_route_candidate import make_fixture as legacy_fixture, render
from tiny_swarm_world.domain.lifecycle import scoped_route_policy as policy
from tiny_swarm_world.domain.lifecycle.manifest_v2 import UnknownIdentity, preview_migration
from tiny_swarm_world.domain.preflight.setup_manifest import SetupProfile, default_setup_manifest
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog


def make_fixture(selected: tuple[str, ...] = (), preset: str = "default"):
    manifest, catalog = legacy_fixture(selected, preset)
    both = ("default", "service-access")
    canonical = {
        "incus": ("host-prerequisite", True, (), both),
        "portainer": ("managed-foundation", True, ("incus",), both),
        "traefik": ("stack", False, ("portainer",), both),
        "nexus": ("stack", False, ("portainer",), both),
        "jenkins": ("stack", False, ("portainer", "nexus"), both),
        "pulsar": ("stack", False, ("portainer",), both),
        "sonarqube": ("stack", False, ("portainer",), both),
        "swagger": ("stack", False, ("portainer",), both),
        "infisical": ("stack", False, ("portainer",), ("service-access",)),
        "service-access": ("stack", False, ("portainer", "nexus", "infisical", "traefik"), ("service-access",)),
    }
    corrected = tuple(item.model_copy(update={
        "kind": canonical[item.service_id][0], "mandatory": canonical[item.service_id][1],
        "dependencies": canonical[item.service_id][2], "presets": canonical[item.service_id][3],
    }) for item in catalog.services)
    return manifest, catalog.model_copy(update={"services": corrected})


def reference(manifest: object, catalog: object, *, exposure: object = policy.SwaggerMode.NOT_APPLICABLE,
              listen: object = "127.0.0.1", **extra: object) -> policy.ScopedPolicyReference:
    return policy.scoped_route_reference(manifest, catalog, exposure=exposure, listen_address=listen, **extra)


class ScopedRoutePolicyTests(unittest.TestCase):
    def test_minimal_has_portainer_policy_and_unknown_runtime(self) -> None:
        manifest, catalog = make_fixture()
        result = reference(manifest, catalog)
        self.assertIs(result.status, policy.PolicyStatus.REFERENCE)
        self.assertEqual([(item.service_id, item.listen_port) for item in result.routes], [("portainer", 10001)])
        self.assertIs(result.runtime_source, UnknownIdentity.UNKNOWN)
        self.assertIs(result.host, UnknownIdentity.UNKNOWN)
        self.assertIs(result.project, UnknownIdentity.UNKNOWN)
        self.assertIs(result.ownership, UnknownIdentity.UNKNOWN)
        self.assertFalse(result.applied)
        self.assertFalse(result.qualified)
        self.assertEqual((result.routes[0].bind, result.routes[0].nat, result.routes[0].proxy_protocol),
                         ("host", False, False))

    def test_known_service_preset_combinations_are_total_or_explicitly_blocked(self) -> None:
        optional = ("nexus", "jenkins", "pulsar", "sonarqube", "swagger", "traefik")
        for preset in ("default", "service-access"):
            for count in range(len(optional) + 1):
                for selected in combinations(optional, count):
                    with self.subTest(preset=preset, selected=selected):
                        manifest, catalog = make_fixture(selected, preset)
                        mode = policy.SwaggerMode.PUBLISHED if "swagger" in selected else policy.SwaggerMode.NOT_APPLICABLE
                        result = reference(manifest, catalog, exposure=mode)
                        if ((preset == "default" and "traefik" in selected)
                                or ("jenkins" in selected and "nexus" not in selected)):
                            self.assertIs(result.status, policy.PolicyStatus.AUTHORITY_GAP)
                            continue
                        self.assertIs(result.status, policy.PolicyStatus.REFERENCE)
                        legacy = render(manifest, catalog)
                        self.assertEqual([route.listen_port for route in result.routes],
                                         [route.listen_port for route in legacy.routes])
                        for item in result.routes:
                            self.assertEqual(item.device_name, f"tsw-proxy-{item.listen_port}")
                            self.assertEqual((item.protocol, item.connect_address, item.connect_port),
                                             ("tcp", "127.0.0.1", item.listen_port))

    def test_required_ports_and_8086_conflict_do_not_get_silently_omitted(self) -> None:
        manifest, catalog = make_fixture(("nexus", "pulsar", "swagger"))
        result = reference(manifest, catalog, exposure=policy.SwaggerMode.PUBLISHED)
        ports = {route.listen_port for route in result.routes}
        self.assertTrue({10001, 13501, 7750, 16080, 16081} <= ports)
        for selected in (("infisical",), ("service-access", "nexus", "infisical", "traefik")):
            with self.subTest(selected=selected):
                manifest, catalog = make_fixture(selected, "service-access")
                preview_migration(manifest, catalog)
                self.assertIs(reference(manifest, catalog).status, policy.PolicyStatus.AUTHORITY_GAP)

    def test_selected_internal_and_untyped_exposure_or_self_attestation_block(self) -> None:
        manifest, catalog = make_fixture(("swagger",))
        for exposure in (policy.SwaggerMode.INTERNAL, policy.SwaggerMode.UNKNOWN,
                         policy.SwaggerMode.NOT_APPLICABLE, None, "published", True):
            with self.subTest(exposure=exposure):
                self.assertIs(reference(manifest, catalog, exposure=exposure).status,
                              policy.PolicyStatus.AUTHORITY_GAP)
        for extra in ({"trusted": True}, {"source": "stock"}, {"actual_applicability": False},
                      {"policy_version": "scoped-route-policy-v1"}):
            with self.subTest(extra=extra):
                self.assertIs(reference(manifest, catalog, exposure=policy.SwaggerMode.PUBLISHED, **extra).status,
                              policy.PolicyStatus.AUTHORITY_GAP)

    def test_explicit_listen_and_forged_inputs_fail_closed(self) -> None:
        manifest, catalog = make_fixture()
        for value in (None, True, " 127.0.0.1", "127.0.0.1 ", "::1", "127.0.0.2"):
            with self.subTest(listen=value):
                self.assertIs(reference(manifest, catalog, listen=value).status, policy.PolicyStatus.AUTHORITY_GAP)
        self.assertIs(reference(manifest, catalog, listen="0.0.0.0").status, policy.PolicyStatus.REFERENCE)
        for bad_manifest, bad_catalog in (
            (manifest.model_copy(update={"schema_version": True}), catalog),
            (manifest.model_copy(update={"service_preset": "secret"}), catalog),
            (manifest.model_copy(update={"resolved_services": ("incus",)}), catalog),
            (manifest, catalog.model_copy(update={"services": catalog.services + (catalog.services[0],)})),
            (object(), catalog), (manifest, object()),
        ):
            with self.subTest(manifest=bad_manifest, catalog=bad_catalog):
                self.assertIs(reference(bad_manifest, bad_catalog).status, policy.PolicyStatus.AUTHORITY_GAP)

    def test_caller_catalog_cannot_redefine_classic_service_policy(self) -> None:
        manifest, catalog = make_fixture(("jenkins", "nexus"))
        for change in ({"dependencies": ("portainer",)}, {"kind": "host-prerequisite"},
                       {"mandatory": True}, {"presets": ("default",)}):
            with self.subTest(change=change):
                altered = tuple(item.model_copy(update=change) if item.service_id == "jenkins" else item
                                for item in catalog.services)
                forged = catalog.model_copy(update={"services": altered})
                self.assertIs(reference(manifest, forged).status, policy.PolicyStatus.AUTHORITY_GAP)

    def test_pure_setup_source_drift_and_invalid_bool_or_duplicates_fail_closed(self) -> None:
        manifest, catalog = make_fixture()
        self.assertIs(reference(manifest, catalog).status, policy.PolicyStatus.REFERENCE)
        setup = default_setup_manifest(profile=SetupProfile.FULL, service_profile="default",
                                       resolved_services=manifest.resolved_services)
        parent = setup.services[0]
        port = parent.ports[0]
        variants = (
            replace(parent, ports=()),
            replace(parent, ports=(replace(port, port=True),)),
            replace(parent, ports=(replace(port, port=10002),)),
            replace(parent, ports=(port, port)),
            replace(parent, ports=(replace(port, service="secret"),)),
            replace(parent, name="Unknown"),
        )
        for group in variants:
            with self.subTest(group=group), patch.object(
                    policy, "default_setup_manifest", return_value=replace(setup, services=(group,))):
                self.assertIs(reference(manifest, catalog).status, policy.PolicyStatus.AUTHORITY_GAP)
        with patch.object(policy, "default_setup_manifest", return_value=replace(setup, services=(parent, parent))):
            self.assertIs(reference(manifest, catalog).status, policy.PolicyStatus.AUTHORITY_GAP)

    def test_real_catalog_semantics_align_and_dependency_closure_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = Path(__file__).resolve().parents[3] / "infra" / "config" / "compose"
            destination = root / "infra" / "config" / "compose"
            destination.parent.mkdir(parents=True)
            shutil.copytree(source, destination)
            catalog = NativeComponentCatalog(root).load()
            manifest, _ = legacy_fixture()
            selected = set(manifest.resolved_services)
            components = tuple(item for group in catalog.services if group.service_id in selected
                               for item in group.components)
            manifest = manifest.model_copy(update={"components": components})
            self.assertIs(reference(manifest, catalog).status, policy.PolicyStatus.REFERENCE)
            manifest_no_nexus, synthetic = make_fixture(("jenkins",))
            self.assertIs(reference(manifest_no_nexus, synthetic).status, policy.PolicyStatus.AUTHORITY_GAP)
            manifest_closed, synthetic = make_fixture(("jenkins", "nexus"))
            self.assertIs(reference(manifest_closed, synthetic).status, policy.PolicyStatus.REFERENCE)

    def test_same_port_and_label_moved_to_other_parent_is_drift(self) -> None:
        manifest, catalog = make_fixture(("nexus", "pulsar"))
        setup = default_setup_manifest(profile=SetupProfile.FULL, service_profile="default",
                                       resolved_services=manifest.resolved_services)
        nexus = next(group for group in setup.services if group.name == "Nexus")
        pulsar = next(group for group in setup.services if group.name == "Pulsar")
        transferred = nexus.ports[0]
        groups = tuple(replace(group, ports=group.ports[1:]) if group.name == "Nexus"
                       else replace(group, ports=group.ports + (transferred,)) if group.name == "Pulsar"
                       else group for group in setup.services)
        self.assertEqual(sorted((item.port, item.service) for item in setup.required_ports),
                         sorted((item.port, item.service) for group in groups for item in group.ports))
        self.assertTrue(pulsar.ports)
        with patch.object(policy, "default_setup_manifest", return_value=replace(setup, services=groups)):
            self.assertIs(reference(manifest, catalog).status, policy.PolicyStatus.AUTHORITY_GAP)

    def test_changed_policy_boolean_or_duplicate_service_fails_closed(self) -> None:
        manifest, catalog = make_fixture()
        for altered in ((("portainer", ((True, "Portainer"),)),),
                        (("portainer", ((10001, "Portainer"),)), ("portainer", ()))):
            with self.subTest(altered=altered), patch.object(policy, "_POLICY", altered):
                self.assertIs(reference(manifest, catalog).status, policy.PolicyStatus.AUTHORITY_GAP)

    def test_listener_collision_allows_distinct_listeners_to_share_target(self) -> None:
        manifest, catalog = make_fixture()
        route = reference(manifest, catalog).routes[0]
        same = replace(route)
        wildcard = replace(route, listen_address="0.0.0.0", device_name="another")
        distinct = replace(route, listen_port=10002, device_name="another")
        self.assertTrue(policy._listener_collision((route, same)))
        self.assertTrue(policy._listener_collision((route, wildcard)))
        self.assertFalse(policy._listener_collision((route, distinct)))
        self.assertEqual(route.connect_port, distinct.connect_port)

    def test_profile_name_vectors_equivalence_and_original_text(self) -> None:
        manifest, catalog = make_fixture()
        vectors = (
            ("00000000-0000-0000-0000-000000000000", "tsw-profile-61b337b53d63c58eab10669c47a35a0b"),
            ("123e4567-e89b-12d3-a456-426614174000", "tsw-profile-e175d6395024f2dc3b44dca4aa283506"),
            ("123E4567-E89B-12D3-A456-426614174000", "tsw-profile-e175d6395024f2dc3b44dca4aa283506"),
            ("{{" + "0" * 32 + "}}", "tsw-profile-61b337b53d63c58eab10669c47a35a0b"),
        )
        for original, expected in vectors:
            with self.subTest(original=original):
                instance = manifest.model_copy(update={"installation_id": original})
                result = reference(instance, catalog)
                self.assertIs(result.status, policy.PolicyStatus.REFERENCE)
                self.assertEqual(result.installation_id, original)
                self.assertEqual(result.profile_name, expected)

    def test_immutable_detached_policy_and_environment_independence(self) -> None:
        manifest, catalog = make_fixture()
        with patch.dict(os.environ, {"TSW_INFRA_ROOT": "/private-one"}):
            first = reference(manifest, catalog)
        with patch.dict(os.environ, {"TSW_INFRA_ROOT": "/private-two"}):
            second = reference(manifest, catalog)
        self.assertEqual(first, second)
        self.assertIs(first.runtime_source, UnknownIdentity.UNKNOWN)
        self.assertIs(type(policy._POLICY), tuple)
        self.assertFalse(hasattr(policy, "register"))
        with self.assertRaises(FrozenInstanceError):
            first.routes[0].listen_port = 2  # type: ignore[misc]
        manifest.selection_reasons["portainer"] = ("portainer",)
        self.assertEqual(first.routes[0].listen_port, 10001)

    def test_no_environment_or_host_io(self) -> None:
        manifest, catalog = make_fixture()
        with patch("os.getenv", side_effect=AssertionError("environment")), \
                patch("builtins.open", side_effect=AssertionError("filesystem")), \
                patch("os.system", side_effect=AssertionError("command")), \
                patch("subprocess.Popen", side_effect=AssertionError("process")), \
                patch("socket.socket", side_effect=AssertionError("network")):
            self.assertIs(reference(manifest, catalog).status, policy.PolicyStatus.REFERENCE)


if __name__ == "__main__":
    unittest.main()
