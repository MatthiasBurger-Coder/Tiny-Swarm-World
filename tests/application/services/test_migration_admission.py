"""Fail-closed migration admission with read-only ports."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from types import SimpleNamespace
from typing import cast
import unittest
from unittest.mock import Mock, patch

from tests.domain.lifecycle.test_scoped_route_policy import make_fixture
from tiny_swarm_world.application.ports.lifecycle import ManifestSnapshot
from tiny_swarm_world.application.ports.lifecycle.migration_admission import (
    MigrationAdmissionRequest, MigrationAdmissionResult, MigrationAdmissionStatus,
)
from tiny_swarm_world.application.services import migration_admission as admission
from tiny_swarm_world.domain.lifecycle import incus_capability
from tiny_swarm_world.domain.lifecycle.incus_capability import CapabilityResult, IntentKind
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode


class MigrationAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest, self.catalog_value = make_fixture()
        self.manifests = Mock()
        self.catalog = Mock()
        self.manifests.load.return_value = ManifestSnapshot(self.manifest, "SECRET_TOKEN", ("SECRET_DIAGNOSTIC",))
        self.catalog.load.return_value = self.catalog_value
        self.service = admission.MigrationAdmissionService(self.manifests, self.catalog)
        self.request = MigrationAdmissionRequest("6.0.5", SwaggerMode.NOT_APPLICABLE, "127.0.0.1")

    def test_valid_scoped_versions_always_block_unsupported_and_do_not_write(self) -> None:
        before = self.manifest.model_dump(mode="python")
        for version in ("0.0.0", "6.0.5", "1" * 28 + ".0.0"):
            with self.subTest(version=version):
                self.manifests.reset_mock()
                self.catalog.reset_mock()
                result = self.service.evaluate(MigrationAdmissionRequest(version, SwaggerMode.NOT_APPLICABLE,
                                                                          "127.0.0.1"))
                self.assertIs(result.status, MigrationAdmissionStatus.BLOCKED_UNSUPPORTED)
                self.assertFalse(result.applied)
                self.assertFalse(result.qualified)
                self.assertNotIn("SECRET", repr(result))
                self.manifests.load.assert_called_once_with()
                self.catalog.load.assert_called_once_with()
                self.manifests.save.assert_not_called()
        self.assertEqual(self.manifest.model_dump(mode="python"), before)
        self.assertEqual([item.name for item in fields(MigrationAdmissionResult)], ["status", "applied", "qualified"])
        with self.assertRaises(FrozenInstanceError):
            result.applied = True  # type: ignore[misc]

    def test_missing_invalid_token_or_forged_snapshot_is_unknown_before_plan(self) -> None:
        invalid = (ManifestSnapshot(None, "token"), ManifestSnapshot(self.manifest, None),
                   ManifestSnapshot(self.manifest, ""), ManifestSnapshot(self.manifest, cast(str, True)),
                   ManifestSnapshot(self.manifest, cast(str, 123)),
                   ManifestSnapshot(self.manifest, "token", cast(tuple[str, ...], ["SECRET"])),
                   SimpleNamespace(manifest=self.manifest, token="token", diagnostics=()))
        for snapshot in invalid:
            with self.subTest(snapshot=snapshot):
                self.manifests.reset_mock()
                self.catalog.reset_mock()
                self.manifests.load.return_value = snapshot
                with patch.object(admission, "plan_desired_manifest_v2") as planner:
                    result = self.service.evaluate(self.request)
                self.assertIs(result.status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)
                self.assertNotIn("SECRET", repr(result))
                self.manifests.load.assert_called_once_with()
                self.catalog.load.assert_called_once_with()
                self.manifests.save.assert_not_called()
                planner.assert_not_called()

    def test_invalid_requests_versions_and_domain_gaps_return_unknown(self) -> None:
        bad_requests: tuple[object, ...] = (
            None, {"version": "6.0.5"}, MigrationAdmissionRequest("", SwaggerMode.NOT_APPLICABLE, "127.0.0.1"),
            MigrationAdmissionRequest("6.0.5-rc", SwaggerMode.NOT_APPLICABLE, "127.0.0.1"),
            MigrationAdmissionRequest(cast(str, True), SwaggerMode.NOT_APPLICABLE, "127.0.0.1"),
            MigrationAdmissionRequest("6.0.5", cast(SwaggerMode, "published"), "127.0.0.1"),
            MigrationAdmissionRequest("6.0.5", SwaggerMode.NOT_APPLICABLE, " 127.0.0.1"),
        )
        for request in bad_requests:
            with self.subTest(request=request):
                self.assertIs(self.service.evaluate(request).status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)
        manifest, catalog = make_fixture(("swagger",))
        self.manifests.load.return_value = ManifestSnapshot(manifest, "token")
        self.catalog.load.return_value = catalog
        self.assertIs(self.service.evaluate(MigrationAdmissionRequest("6.0.5", SwaggerMode.INTERNAL, "127.0.0.1")).status,
                      MigrationAdmissionStatus.BLOCKED_UNKNOWN)
        manifest, catalog = make_fixture(("infisical",), "service-access")
        self.manifests.load.return_value = ManifestSnapshot(manifest, "token")
        self.catalog.load.return_value = catalog
        self.assertIs(self.service.evaluate(self.request).status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)
        self.manifests.save.assert_not_called()

    def test_load_failures_and_forged_plans_are_redacted(self) -> None:
        for name in ("manifests", "catalog"):
            with self.subTest(port=name):
                self.setUp()
                port = self.manifests if name == "manifests" else self.catalog
                port.load.side_effect = PermissionError("SECRET /private/path")
                result = self.service.evaluate(self.request)
                self.assertIs(result.status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)
                self.assertNotIn("SECRET", repr(result))
                self.manifests.save.assert_not_called()
        self.setUp()
        with patch.object(admission, "plan_desired_manifest_v2",
                          return_value=SimpleNamespace(status="DESIRED", desired="SECRET")):
            result = self.service.evaluate(self.request)
        self.assertIs(result.status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)
        self.assertNotIn("SECRET", repr(result))

    def test_different_manifest_plan_is_not_accepted(self) -> None:
        other = self.manifest.model_copy(update={"installation_id": "00000000-0000-0000-0000-000000000000"})
        other_plan = admission.plan_desired_manifest_v2(other, self.catalog_value,
                                                       exposure=SwaggerMode.NOT_APPLICABLE,
                                                       listen_address="127.0.0.1")
        with patch.object(admission, "plan_desired_manifest_v2", return_value=other_plan):
            result = self.service.evaluate(self.request)
        self.assertIs(result.status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)

    def test_same_manifest_different_listen_plan_is_rejected(self) -> None:
        other = admission.plan_desired_manifest_v2(self.manifest, self.catalog_value,
                                                   exposure=SwaggerMode.NOT_APPLICABLE,
                                                   listen_address="0.0.0.0")
        with patch.object(admission, "plan_desired_manifest_v2", return_value=other), \
                patch.object(incus_capability, "classify_incus_capability") as classifier:
            result = self.service.evaluate(self.request)
        self.assertIs(result.status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)
        classifier.assert_not_called()

    def test_forged_profile_routes_stack_exposure_and_types_are_rejected(self) -> None:
        self.assertIs(self.service.evaluate(self.request).status, MigrationAdmissionStatus.BLOCKED_UNSUPPORTED)
        for field_name in ("profile", "routes", "flag", "stack", "exposure", "schema", "snapshot"):
            with self.subTest(field_name=field_name):
                plan = admission.plan_desired_manifest_v2(self.manifest, self.catalog_value,
                                                         exposure=SwaggerMode.NOT_APPLICABLE,
                                                         listen_address="127.0.0.1")
                desired = plan.desired
                assert desired is not None
                if field_name == "profile":
                    object.__setattr__(desired, "desired_profile_name", "tsw-profile-" + "0" * 32)
                elif field_name == "routes":
                    object.__setattr__(desired, "desired_routes", ())
                elif field_name == "flag":
                    route = replace(desired.desired_routes[0], nat=cast(bool, 0))
                    object.__setattr__(desired, "desired_routes", (route,))
                elif field_name == "stack":
                    object.__setattr__(desired, "stack_policies", (("nexus", "swarm"),))
                elif field_name == "exposure":
                    from tiny_swarm_world.domain.lifecycle.manifest_v2 import SwaggerExposure
                    object.__setattr__(desired, "swagger_exposure", SwaggerExposure.PUBLISHED)
                elif field_name == "schema":
                    object.__setattr__(desired, "desired_schema_version", 2.0)
                else:
                    snapshot = dict(desired.v1_snapshot)
                    snapshot["schema_version"] = True
                    object.__setattr__(desired, "v1_snapshot", snapshot)
                with patch.object(admission, "plan_desired_manifest_v2", return_value=plan), \
                        patch.object(incus_capability, "classify_incus_capability") as classifier:
                    result = self.service.evaluate(self.request)
                self.assertIs(result.status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)
                classifier.assert_not_called()

    def test_unexpected_classifier_and_mutated_registry_are_unknown(self) -> None:
        for value in (CapabilityResult.LEGACY_CLASSIC, CapabilityResult.INVALID_VERSION, "SUPPORTED", None):
            with self.subTest(value=value), patch.object(incus_capability, "classify_incus_capability",
                                                         return_value=value) as classifier:
                result = self.service.evaluate(self.request)
                self.assertIs(result.status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)
                classifier.assert_called_once_with(IntentKind.INSTALLATION_SCOPED, "6.0.5")
        with patch.object(incus_capability, "SUPPORTED_VERSIONS", frozenset({"6.0.5"})):
            self.assertIs(self.service.evaluate(self.request).status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)
        with patch.object(incus_capability, "SUPPORTED_VERSIONS", set()):
            self.assertIs(self.service.evaluate(self.request).status, MigrationAdmissionStatus.BLOCKED_UNKNOWN)

    def test_no_classifier_injection_and_no_host_io(self) -> None:
        with self.assertRaises(TypeError):
            admission.MigrationAdmissionService(self.manifests, self.catalog, classifier=Mock())  # type: ignore[call-arg]
        with patch("os.getenv", side_effect=AssertionError("environment")), \
                patch("builtins.open", side_effect=AssertionError("filesystem")), \
                patch("os.system", side_effect=AssertionError("command")), \
                patch("subprocess.Popen", side_effect=AssertionError("process")), \
                patch("socket.socket", side_effect=AssertionError("network")):
            self.assertIs(self.service.evaluate(self.request).status, MigrationAdmissionStatus.BLOCKED_UNSUPPORTED)
        self.manifests.save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
