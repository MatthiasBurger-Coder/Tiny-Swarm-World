"""Desired-only conversion tests: no adoption, persistence or host evidence."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from typing import cast
import unittest
from unittest.mock import patch

from tests.domain.lifecycle.test_scoped_route_policy import make_fixture
from tiny_swarm_world.domain.lifecycle import desired_manifest_v2 as conversion
from tiny_swarm_world.domain.lifecycle.manifest_v2 import SwaggerExposure, UnknownIdentity
from tiny_swarm_world.domain.lifecycle import scoped_route_policy
from tiny_swarm_world.domain.lifecycle.models import InstallationManifest
from tiny_swarm_world.domain.preflight.setup_manifest import SetupProfile, default_setup_manifest
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode, scoped_route_reference


def convert(manifest: object, catalog: object, *, exposure: object = SwaggerMode.NOT_APPLICABLE,
            listen: object = "127.0.0.1", **extra: object) -> conversion.ConversionPlan:
    return conversion.plan_desired_manifest_v2(manifest, catalog, exposure=exposure, listen_address=listen, **extra)


class DesiredManifestV2Tests(unittest.TestCase):
    def test_minimal_preserves_all_v1_values_and_actual_state_unknown(self) -> None:
        manifest, catalog = make_fixture()
        before = manifest.model_dump(mode="python")
        plan = convert(manifest, catalog)
        self.assertIs(plan.status, conversion.ConversionStatus.DESIRED)
        desired = plan.desired
        assert desired is not None
        self.assertEqual(desired.v1_snapshot, before)
        self.assertEqual(manifest.model_dump(mode="python"), before)
        self.assertEqual(desired.desired_project, "default")
        self.assertEqual([route.listen_port for route in desired.desired_routes], [10001])
        self.assertEqual(desired.stack_policies, ())
        self.assertIs(desired.swagger_exposure, SwaggerExposure.NOT_APPLICABLE)
        for value in (desired.actual_project, desired.actual_profile, desired.actual_route,
                      desired.actual_owner, desired.actual_host, desired.runtime_source):
            self.assertIs(value, UnknownIdentity.UNKNOWN)
        self.assertIs(desired.applied, False)
        self.assertIs(desired.qualified, False)

    def test_routes_stack_policy_and_selected_swagger_are_derived(self) -> None:
        manifest, catalog = make_fixture(("nexus", "pulsar", "swagger"))
        plan = convert(manifest, catalog, exposure=SwaggerMode.PUBLISHED)
        self.assertIs(plan.status, conversion.ConversionStatus.DESIRED)
        desired = plan.desired
        assert desired is not None
        self.assertEqual(desired.stack_policies, (("nexus", "swarm"), ("pulsar", "swarm"), ("swagger", "swarm")))
        self.assertIs(desired.swagger_exposure, SwaggerExposure.PUBLISHED)
        self.assertTrue({10001, 13501, 7750, 16080, 16081} <=
                        {route.listen_port for route in desired.desired_routes})
        self.assertEqual(desired.v1_snapshot, manifest.model_dump(mode="python"))
        self.assertEqual(plan, convert(manifest, catalog, exposure=SwaggerMode.PUBLISHED))

    def test_reuses_same_detached_validated_inputs_for_preview_and_p0(self) -> None:
        manifest, catalog = make_fixture()
        with patch.object(conversion, "preview_migration", wraps=conversion.preview_migration) as preview, \
                patch.object(conversion, "scoped_route_reference", wraps=conversion.scoped_route_reference) as p0:
            plan = convert(manifest, catalog)
        self.assertIs(plan.status, conversion.ConversionStatus.DESIRED)
        first_manifest, first_catalog = preview.call_args.args
        second_manifest, second_catalog = p0.call_args.args
        self.assertIs(first_manifest, second_manifest)
        self.assertIs(first_catalog, second_catalog)
        self.assertIsNot(first_manifest, manifest)
        self.assertIsNot(first_catalog, catalog)

    def test_uuid_vectors_preserve_original_text(self) -> None:
        manifest, catalog = make_fixture()
        vectors = (
            ("00000000-0000-0000-0000-000000000000", "tsw-profile-61b337b53d63c58eab10669c47a35a0b"),
            ("123E4567-E89B-12D3-A456-426614174000", "tsw-profile-e175d6395024f2dc3b44dca4aa283506"),
            ("123e4567-e89b-12d3-a456-426614174000", "tsw-profile-e175d6395024f2dc3b44dca4aa283506"),
        )
        for uuid_text, profile in vectors:
            with self.subTest(uuid_text=uuid_text):
                plan = convert(manifest.model_copy(update={"installation_id": uuid_text}), catalog)
                assert plan.desired is not None
                self.assertEqual(plan.desired.v1_snapshot["installation_id"], uuid_text)
                self.assertEqual(plan.desired.desired_profile_name, profile)

    def test_gaps_and_unsolicited_bindings_never_produce_partial_desired(self) -> None:
        for selected, preset, mode in (
            (("traefik",), "default", SwaggerMode.NOT_APPLICABLE),
            (("swagger",), "default", SwaggerMode.INTERNAL),
        ):
            manifest, catalog = make_fixture(selected, preset)
            plan = convert(manifest, catalog, exposure=mode)
            self.assertIs(plan.status, conversion.ConversionStatus.AUTHORITY_GAP)
            self.assertIsNone(plan.desired)
        manifest, catalog = make_fixture()
        for extra in ({"p0": scoped_route_reference}, {"profile_name": "SECRET"},
                      {"project": "default"}, {"runtime_source": "REVIEWED"}, {"owner": "SECRET"}):
            with self.subTest(extra=extra):
                plan = convert(manifest, catalog, **extra)
                self.assertIs(plan.status, conversion.ConversionStatus.AUTHORITY_GAP)
                self.assertNotIn("SECRET", repr(plan))

    def test_scoped_v2_8086_desired_values_are_exact_and_unadopted(self) -> None:
        for selected, expected_8086 in ((("infisical",), False),
                                        (("service-access", "nexus", "infisical", "traefik"), True)):
            with self.subTest(selected=selected):
                manifest, catalog = make_fixture(selected, "service-access")
                plan = convert(manifest, catalog)
                self.assertIs(plan.status, conversion.ConversionStatus.DESIRED)
                desired = plan.desired
                assert desired is not None
                routes = [route for route in desired.desired_routes if route.listen_port == 8086]
                self.assertEqual(bool(routes), expected_8086)
                if routes:
                    self.assertEqual(len(routes), 1)
                    self.assertEqual(routes[0].service_id, "service-access")
                self.assertIn(17080, [route.listen_port for route in desired.desired_routes])
                self.assertIs(desired.runtime_source, UnknownIdentity.UNKNOWN)
                self.assertFalse(desired.applied)
        manifest, catalog = make_fixture()
        original = scoped_route_reference(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                          listen_address="127.0.0.1")
        with patch.object(conversion, "scoped_route_reference",
                          return_value=replace(original, policy_version="scoped-route-policy-v1")):
            self.assertIs(convert(manifest, catalog).status, conversion.ConversionStatus.AUTHORITY_GAP)

    def test_forged_invalid_nested_unknown_fields_and_types_fail_closed(self) -> None:
        manifest, catalog = make_fixture()
        bad_product = manifest.product.model_copy(update={"unexpected_alias": "SECRET"})
        bad_nested = catalog.services[0].model_copy(update={"forged": "SECRET"})
        cases: tuple[tuple[object, object], ...] = (
            (manifest.model_copy(update={"schema_version": True}), catalog),
            (manifest.model_copy(update={"unknown": "SECRET"}), catalog),
            (manifest.model_copy(update={"product": bad_product}), catalog),
            (manifest.model_copy(update={"installation_id": "invalid"}), catalog),
            (InstallationManifest.model_construct(**dict(manifest.model_dump(), host="invalid")), catalog),
            (manifest.model_copy(update={"requested_services": ("incus", "incus")}), catalog),
            (manifest, catalog.model_copy(update={"schema_version": 2})),
            (manifest, catalog.model_copy(update={"services": (bad_nested,) + catalog.services[1:]})),
            (manifest, catalog.model_copy(update={"services": catalog.services + (catalog.services[0],)})),
            (object(), catalog), (manifest, object()),
        )
        for bad_manifest, bad_catalog in cases:
            with self.subTest(manifest=bad_manifest, catalog=bad_catalog):
                plan = convert(bad_manifest, bad_catalog)
                self.assertIs(plan.status, conversion.ConversionStatus.AUTHORITY_GAP)
                self.assertIsNone(plan.desired)
                self.assertNotIn("SECRET", repr(plan))

    def test_p0_setup_source_drift_blocks_conversion(self) -> None:
        manifest, catalog = make_fixture()
        setup = default_setup_manifest(profile=SetupProfile.FULL, service_profile="default",
                                       resolved_services=manifest.resolved_services)
        parent = setup.services[0]
        changed = replace(setup, services=(replace(parent, ports=()),))
        with patch.object(scoped_route_policy, "default_setup_manifest", return_value=changed):
            plan = convert(manifest, catalog)
        self.assertIs(plan.status, conversion.ConversionStatus.AUTHORITY_GAP)
        self.assertIsNone(plan.desired)

    def test_wrong_p0_version_identity_and_claims_are_rejected(self) -> None:
        manifest, catalog = make_fixture()
        original = scoped_route_reference(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                          listen_address="127.0.0.1")
        for forged in (replace(original, policy_version="other"),
                       replace(original, profile_algorithm="other"),
                       replace(original, installation_id="SECRET"),
                       replace(original, profile_name="tsw-profile-" + "0" * 32),
                       replace(original, routes=(replace(original.routes[0], listen_port=5),)),
                       replace(original, routes=()),
                       replace(original, runtime_source=cast(UnknownIdentity, "REVIEWED")),
                       replace(original, applied=True),
                       replace(original, qualified=True)):
            with self.subTest(forged=forged), patch.object(conversion, "scoped_route_reference", return_value=forged):
                plan = convert(manifest, catalog)
                self.assertIs(plan.status, conversion.ConversionStatus.AUTHORITY_GAP)
                self.assertIsNone(plan.desired)

    def test_forged_route_builtin_types_do_not_use_coercive_equality(self) -> None:
        class TextSubclass(str):
            pass

        class IntegerSubclass(int):
            pass

        manifest, catalog = make_fixture()
        original = scoped_route_reference(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                          listen_address="127.0.0.1")
        route = original.routes[0]
        variants = (
            replace(route, nat=cast(bool, 0)), replace(route, proxy_protocol=cast(bool, 0)),
            replace(route, nat=cast(bool, 1)), replace(route, proxy_protocol=cast(bool, 1)),
            replace(route, listen_port=True), replace(route, connect_port=IntegerSubclass(route.connect_port)),
            replace(route, service_id=TextSubclass(route.service_id)),
            replace(route, device_name=TextSubclass(route.device_name)),
            replace(route, protocol=TextSubclass(route.protocol)),
            replace(route, listen_address=TextSubclass(route.listen_address)),
            replace(route, connect_address=TextSubclass(route.connect_address)),
            replace(route, bind=TextSubclass(route.bind)),
        )
        for forged_route in variants:
            forged = replace(original, routes=(forged_route,))
            with self.subTest(forged_route=forged_route), patch.object(
                    conversion, "scoped_route_reference", return_value=forged):
                plan = convert(manifest, catalog)
                self.assertIs(plan.status, conversion.ConversionStatus.AUTHORITY_GAP)
                self.assertIsNone(plan.desired)

    def test_public_construction_and_inconsistent_status_are_rejected(self) -> None:
        manifest, catalog = make_fixture()
        desired = convert(manifest, catalog).desired
        assert desired is not None
        with self.assertRaises(TypeError):
            conversion.DesiredManifestV2()
        with self.assertRaises(TypeError):
            conversion.DesiredManifestV2(v1_snapshot={"selection_reasons": {}},  # type: ignore[call-arg]
                                         desired_profile_name="forged", desired_routes=[])
        with self.assertRaises(ValueError):
            conversion.ConversionPlan(conversion.ConversionStatus.DESIRED)
        with self.assertRaises(ValueError):
            conversion.ConversionPlan(conversion.ConversionStatus.AUTHORITY_GAP, desired)
        with self.assertRaises(ValueError):
            conversion.ConversionPlan("DESIRED", desired)  # type: ignore[arg-type]

    def test_deep_detachment_and_no_shared_mutable_state(self) -> None:
        manifest, catalog = make_fixture(("nexus",))
        plan = convert(manifest, catalog)
        desired = plan.desired
        assert desired is not None
        reasons = desired.v1_snapshot["selection_reasons"]
        self.assertIsNot(reasons, manifest.selection_reasons)
        with self.assertRaises(TypeError):
            reasons["portainer"] = ("nexus",)  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError):
            desired.desired_routes[0].listen_port = 1  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            desired.applied = True  # type: ignore[misc]
        manifest.selection_reasons["portainer"] = ("nexus",)
        self.assertEqual(reasons["portainer"], ("incus",))  # type: ignore[index]

    def test_no_environment_or_io(self) -> None:
        manifest, catalog = make_fixture()
        with patch("os.getenv", side_effect=AssertionError("environment")), \
                patch("builtins.open", side_effect=AssertionError("filesystem")), \
                patch("os.system", side_effect=AssertionError("command")), \
                patch("subprocess.Popen", side_effect=AssertionError("process")), \
                patch("socket.socket", side_effect=AssertionError("network")):
            self.assertIs(convert(manifest, catalog).status, conversion.ConversionStatus.DESIRED)


if __name__ == "__main__":
    unittest.main()
