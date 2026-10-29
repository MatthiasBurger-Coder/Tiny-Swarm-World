"""Pure compatibility rendering tests; no host or runtime operations."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.domain.lifecycle.test_manifest_v2 import fixtures, service
from tiny_swarm_world.application.services.platform.incus.lxc_service_exposure import _plans_from_manifest
from tiny_swarm_world.domain.lifecycle import legacy_route_candidate as candidate
from tiny_swarm_world.domain.lifecycle.manifest_v2 import SwaggerExposure, UnknownIdentity
from tiny_swarm_world.domain.preflight.setup_manifest import SetupProfile, default_setup_manifest


def make_fixture(selected: tuple[str, ...] = (), preset: str = "default"):
    manifest, catalog = fixtures(selected)
    extra = tuple(service(name, "stack", dependencies=("portainer",))
                  for name in ("pulsar", "sonarqube", "traefik", "infisical", "service-access"))
    return (manifest.model_copy(update={"service_preset": preset}),
            catalog.model_copy(update={"services": catalog.services + extra}))


def render(manifest: object, catalog: object, *, source: object = candidate.SourceContext.STOCK_LEGACY,
           exposure: object = SwaggerExposure.PUBLISHED, inputs: object = candidate.RouteInputs(
               "127.0.0.1", "swarm-manager")) -> candidate.LegacyCandidate:
    return candidate.legacy_route_candidate(manifest, catalog, source=source, exposure=exposure, inputs=inputs)


class LegacyRouteCandidateTests(unittest.TestCase):
    def test_minimal_only_has_portainer_and_unverified_unknowns(self) -> None:
        manifest, catalog = make_fixture()
        result = render(manifest, catalog)
        self.assertIs(result.status, candidate.CandidateStatus.CANDIDATE)
        self.assertEqual([route.listen_port for route in result.routes], [10001])
        self.assertEqual(result.source, "legacy_setup_code_unverified_runtime")
        self.assertFalse(result.applied)
        self.assertFalse(result.qualified)
        for value in (result.host, result.project, result.profile, result.ownership,
                      result.routes[0].nat, result.routes[0].proxy_protocol):
            self.assertIs(value, UnknownIdentity.UNKNOWN)

    def test_exact_differential_matches_legacy_mapping_for_both_ingress_modes(self) -> None:
        for selected, preset in (
            ((), "default"),
            (("nexus", "pulsar", "swagger"), "default"),
            (("nexus", "pulsar", "swagger", "traefik"), "service-access"),
        ):
            with self.subTest(selected=selected, preset=preset):
                manifest, catalog = make_fixture(selected, preset)
                setup = default_setup_manifest(profile=SetupProfile.FULL, service_profile=preset,
                                               resolved_services=manifest.resolved_services)
                legacy = _plans_from_manifest(setup, gateway_node="swarm-manager", listen_address="127.0.0.1")
                result = render(manifest, catalog)
                self.assertIs(result.status, candidate.CandidateStatus.CANDIDATE)
                expected = sorted((p.service, p.listen_port, p.target_port, p.listen_address,
                                   p.target_address, p.gateway_node, p.device_name) for p in legacy)
                actual = sorted((p.service, p.listen_port, p.target_port, p.listen_address,
                                 p.target_address, p.gateway_node, p.device_name) for p in result.routes)
                self.assertEqual(actual, expected)
                self.assertEqual([r.listen_port for r in result.routes],
                                 sorted(r.listen_port for r in result.routes))
                if "pulsar" in selected:
                    self.assertIn(7750, [r.listen_port for r in result.routes])
                    self.assertIn(13501, [r.listen_port for r in result.routes])
                    self.assertIn(16080, [r.listen_port for r in result.routes])
                    self.assertIn(16081, [r.listen_port for r in result.routes])
                if preset == "service-access":
                    self.assertTrue(any(not p.host_preflight_required for p in setup.required_ports))
                    self.assertEqual(len(result.routes), len(setup.required_ports))

    def test_unselected_swagger_never_appears(self) -> None:
        manifest, catalog = make_fixture(("nexus",))
        result = render(manifest, catalog)
        self.assertIs(result.status, candidate.CandidateStatus.CANDIDATE)
        self.assertNotIn(16080, [route.listen_port for route in result.routes])
        self.assertNotIn(16081, [route.listen_port for route in result.routes])

    def test_source_policy_and_inputs_must_be_explicit_and_canonical(self) -> None:
        manifest, catalog = make_fixture()
        for source_value in (None, "stock_legacy", candidate.SourceContext.UNKNOWN,
                             candidate.SourceContext.CUSTOM_OVERRIDE, candidate.SourceContext.ALTERNATE_INFRA):
            with self.subTest(source=source_value):
                self.assertIs(render(manifest, catalog, source=source_value).status, candidate.CandidateStatus.AUTHORITY_GAP)
        for exposure_value in (None, "published", "internal", SwaggerExposure.NOT_APPLICABLE, True):
            with self.subTest(exposure=exposure_value):
                self.assertIs(render(manifest, catalog, exposure=exposure_value).status, candidate.CandidateStatus.AUTHORITY_GAP)
        for input_value in (None, ("127.0.0.1", "swarm-manager"), candidate.RouteInputs(" 127.0.0.1", "swarm-manager"),
                            candidate.RouteInputs("::1", "swarm-manager"), candidate.RouteInputs("0.0.0.0", " host"),
                            candidate.RouteInputs("0.0.0.0", ""), candidate.RouteInputs("0.0.0.0", True)):  # type: ignore[arg-type]
            with self.subTest(inputs=input_value):
                self.assertIs(render(manifest, catalog, inputs=input_value).status, candidate.CandidateStatus.AUTHORITY_GAP)
        self.assertIs(render(manifest, catalog, inputs=candidate.RouteInputs("0.0.0.0", "node-1")).status,
                      candidate.CandidateStatus.CANDIDATE)

    def test_invalid_and_constructed_bypassing_validation_fail_closed(self) -> None:
        manifest, catalog = make_fixture()
        cases = ((manifest.model_copy(update={"service_preset": "secret"}), catalog),
                 (manifest.model_copy(update={"schema_version": True}), catalog),
                 (manifest.model_copy(update={"resolved_services": ("incus",)}), catalog),
                 (manifest, catalog.model_copy(update={"services": catalog.services + (catalog.services[0],)})),
                 (manifest, catalog.model_copy(update={"catalog_version": 2})),
                 (object(), catalog), (manifest, object()))
        for bad_manifest, bad_catalog in cases:
            with self.subTest(manifest=bad_manifest, catalog=bad_catalog):
                result = render(bad_manifest, bad_catalog)
                self.assertIs(result.status, candidate.CandidateStatus.AUTHORITY_GAP)
                self.assertNotIn("secret", repr(result))

    def test_unknown_selected_service_is_not_silently_dropped(self) -> None:
        manifest, catalog = make_fixture(("unexpected",))
        catalog = catalog.model_copy(update={
            "services": catalog.services + (service("unexpected", "stack", dependencies=("portainer",)),)})
        self.assertIs(render(manifest, catalog).status, candidate.CandidateStatus.AUTHORITY_GAP)

    def test_bad_boolean_duplicate_or_unknown_port_and_service_are_rejected(self) -> None:
        manifest, catalog = make_fixture()
        for requirements in (
            (SimpleNamespace(port=True, service="Portainer"),),
            (SimpleNamespace(port=10001, service="Unknown"),),
            (SimpleNamespace(port=9999, service="Portainer"),),
            (SimpleNamespace(port=10001, service="Portainer"), SimpleNamespace(port=10001, service="Portainer")),
        ):
            with self.subTest(requirements=requirements), \
                    patch.object(candidate, "default_setup_manifest",
                                 return_value=SimpleNamespace(required_ports=requirements)):
                self.assertIs(render(manifest, catalog).status, candidate.CandidateStatus.AUTHORITY_GAP)

    def test_uuid_casing_and_mutable_input_detachment(self) -> None:
        manifest, catalog = make_fixture()
        manifest = manifest.model_copy(update={"installation_id": "ABCDEF12-1234-1234-1234-123456789ABC"})
        result = render(manifest, catalog)
        self.assertEqual(result.installation_id, "ABCDEF12-1234-1234-1234-123456789ABC")
        with self.assertRaises(FrozenInstanceError):
            result.routes[0].listen_port = 42  # type: ignore[misc]
        manifest.selection_reasons["portainer"] = ("portainer",)
        self.assertEqual(result.routes[0].listen_port, 10001)

    def test_no_io_or_host_operation(self) -> None:
        manifest, catalog = make_fixture()
        with patch("builtins.open", side_effect=AssertionError("filesystem")), \
                patch("os.system", side_effect=AssertionError("command")), \
                patch("subprocess.Popen", side_effect=AssertionError("process")), \
                patch("socket.socket", side_effect=AssertionError("network")):
            self.assertIs(render(manifest, catalog).status, candidate.CandidateStatus.CANDIDATE)


if __name__ == "__main__":
    unittest.main()
