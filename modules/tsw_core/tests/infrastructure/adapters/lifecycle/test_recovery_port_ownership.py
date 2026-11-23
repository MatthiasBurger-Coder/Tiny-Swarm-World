"""Scoped recovery proof with synthetic authority and read-only runtime frames."""

from dataclasses import replace
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from modules.tsw_core.tests.domain.lifecycle.test_models import manifest_fixture
from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import admitted_fixture, intent_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestSnapshot
from tiny_swarm_world.application.ports.lifecycle.installation_profile import ProfileObservation
from tiny_swarm_world.application.services.profile_setup import proxy_routes_from_setup_manifest
from tiny_swarm_world.domain.lifecycle.models import installation_profile_name
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, ProfileLifecycleCheckpoint, installation_manifest_sha256
from tiny_swarm_world.domain.preflight import HostEnvironmentKind
from tiny_swarm_world.domain.preflight.setup_manifest import default_setup_manifest
from tiny_swarm_world.infrastructure.adapters.lifecycle import recovery_port_ownership as recovery


_MANAGER_UUID = "11111111-1111-1111-1111-111111111111"
_INSTALLATION_UUID = "22222222-2222-2222-2222-222222222222"
_REVISION = "c" * 40
_PRESET = "default"


def _checkpoint() -> ProfileLifecycleCheckpoint:
    original = intent_fixture()
    manifest = manifest_fixture()
    manifest = manifest.model_copy(update={
        "installation_id": _INSTALLATION_UUID,
        "product": manifest.product.model_copy(update={"revision": _REVISION}),
    })
    profile = original.profile
    assert profile.profile is not None
    setup = default_setup_manifest(service_profile=_PRESET, resolved_services=manifest.resolved_services)
    routes = proxy_routes_from_setup_manifest(setup, "127.0.0.1")
    binding = profile.profile.model_copy(update={
        "profile_name": installation_profile_name(_INSTALLATION_UUID),
        "routes": routes,
    })
    intent = ManagerCreateIntent.model_validate_json(original.model_copy(update={
        "initial_manifest": manifest,
        "catalog_ports": tuple(sorted({route.listen_port for route in routes})),
        "profile": profile.model_copy(update={
            "installation_id": _INSTALLATION_UUID,
            "controller_revision": _REVISION,
            "product_source_revision": _REVISION,
            "profile": binding,
        }),
    }).model_dump_json())
    return ProfileLifecycleCheckpoint(
        intent=intent,
        stage="recoverable",
        previous_stage="routes-verified",
        generation=7,
        pending_action="instance-start",
        instance_uuid=_MANAGER_UUID,
        observation_sha256="9" * 64,
    )


class TestRecoveryPortOwnership(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.checkpoint = _checkpoint()
        self.intent = self.checkpoint.intent
        self.journal = Mock()
        self.journal.load.return_value = self.checkpoint
        self.change = Mock()
        self.change.load.return_value = None
        self.lifecycle = Mock()
        self.lifecycle.manifests.load.return_value = ManifestSnapshot(manifest=None, token=None)
        self.environment = SimpleNamespace(environment=HostEnvironmentKind.NATIVE_LINUX)
        self.plan = SimpleNamespace(
            service_preset=_PRESET,
            requested_services=self.intent.profile.requested_services,
            resolved_services=self.intent.profile.resolved_services,
            service_exposure=self.intent.profile.service_exposure,
            stack_owners=self.intent.planned_stack_owners,
            manifest_token=None,
            removals=(),
        )
        self.observation = ProfileObservation(
            client_version="6.0.5",
            server_version="6.0.5",
            preservation_sha256=self.intent.preservation_sha256,
            base_profiles_sha256=self.intent.base_profiles_sha256,
            profile_state="exact",
            instance_state="running",
            effective_routes_match=True,
            forbidden_listener=False,
            listeners_match=True,
            listeners_clear=False,
            observation_sha256="8" * 64,
            instance_uuid=_MANAGER_UUID,
        )
        self.reader = Mock()
        self.reader.inspect = AsyncMock(return_value=self.observation)
        self.reader.clean_source_revision = AsyncMock(return_value=_REVISION)
        self.runtime = Mock()
        self.runtime.for_observation.return_value = self.reader
        self.listen_address = Mock(return_value="127.0.0.1")
        replacements = {
            "HostEnvironmentDetector": Mock(return_value=Mock(**{"detect.return_value": self.environment})),
            "build_installation_lifecycle_service": Mock(return_value=self.lifecycle),
            "JsonProfileLifecycleJournal": Mock(return_value=self.journal),
            "JsonProfileChangeJournal": Mock(return_value=self.change),
            "ServiceSelectionService": Mock(return_value=Mock(**{"preview.return_value": self.plan})),
            "IncusProfileCapabilityRepository": Mock(return_value=Mock(**{"load.return_value": admitted_fixture()})),
            "IncusProfileLifecycleRuntime": Mock(return_value=self.runtime),
            "selected_listen_address": self.listen_address,
        }
        self.enterContext(patch.multiple(recovery, **replacements))

    async def test_exact_pending_start_exposes_only_observed_route_ports_without_writes(self):
        proof = await recovery.observe_recovery_ports(self.root, _PRESET)

        self.assertIsNotNone(proof)
        assert proof is not None
        self.assertEqual(proof.ports, frozenset({10001}))
        self.assertEqual(proof.observation_sha256, self.observation.observation_sha256)
        self.runtime.for_observation.assert_called_once_with(self.intent)
        self.runtime.for_operation.assert_not_called()
        self.assertEqual(self.reader.inspect.await_count, 2)
        self.journal.exclusive.assert_not_called()
        self.journal.save.assert_not_called()
        self.lifecycle.manifests.save.assert_not_called()
        self.assertEqual(self.lifecycle.operation_lock.mock_calls, [])
        self.assertEqual(list(self.root.iterdir()), [])

    async def test_foreign_or_incomplete_listener_frames_block_recovery(self):
        for changes in (
            {"forbidden_listener": True},
            {"listeners_match": False},
            {"effective_routes_match": False},
            {"instance_uuid": "33333333-3333-3333-3333-333333333333"},
            {"preservation_sha256": "f" * 63 + "0"},
            {"base_profiles_sha256": "b" * 63 + "0"},
            {"server_version": "6.0.6"},
        ):
            with self.subTest(changes=changes):
                self.reader.inspect.return_value = replace(self.observation, **changes)
                self.assertIsNone(await recovery.observe_recovery_ports(self.root, _PRESET))

    async def test_observation_source_and_journal_drift_block_recovery(self):
        self.reader.inspect.side_effect = [self.observation, replace(self.observation, observation_sha256="7" * 64)]
        self.assertIsNone(await recovery.observe_recovery_ports(self.root, _PRESET))
        self.reader.inspect.side_effect = None
        self.reader.clean_source_revision.side_effect = [_REVISION, "d" * 40]
        self.assertIsNone(await recovery.observe_recovery_ports(self.root, _PRESET))
        self.reader.clean_source_revision.side_effect = None
        self.journal.load.side_effect = [self.checkpoint, self.checkpoint.model_copy(update={"generation": 8})]
        self.assertIsNone(await recovery.observe_recovery_ports(self.root, _PRESET))

    async def test_unknown_ownership_or_changed_intent_produces_no_proof(self):
        self.reader.inspect.side_effect = LifecycleStateError("trusted listener readback unavailable")
        self.assertIsNone(await recovery.observe_recovery_ports(self.root, _PRESET))
        self.reader.inspect.side_effect = None
        self.reader.inspect.reset_mock()
        self.lifecycle.manifests.load.return_value = ManifestSnapshot(manifest=None, token="d" * 64)
        self.assertIsNone(await recovery.observe_recovery_ports(self.root, _PRESET))
        self.lifecycle.manifests.load.return_value = ManifestSnapshot(manifest=None, token=None)
        self.plan.requested_services = ("incus", "portainer", "nexus")
        self.assertIsNone(await recovery.observe_recovery_ports(self.root, _PRESET))
        self.reader.inspect.assert_not_awaited()

    def test_matching_installed_manifest_keeps_existing_completion_admission(self):
        manifest = self.intent.initial_manifest
        assert manifest is not None
        self.journal.load.return_value = self.checkpoint.model_copy(update={
            "stage": "completed", "previous_stage": "completed", "pending_action": None,
            "installation_manifest_sha256": installation_manifest_sha256(manifest),
        })
        self.lifecycle.manifests.load.return_value = ManifestSnapshot(manifest=manifest, token="f" * 64)
        self.assertFalse(recovery.pending_creation_applies(self.root))

        altered = manifest.model_copy(
            update={"host": "wsl2"},
        )
        self.lifecycle.manifests.load.return_value = ManifestSnapshot(manifest=altered, token="a" * 64)
        self.assertTrue(recovery.pending_creation_applies(self.root))

    async def test_listener_binding_drift_and_missing_pending_start_are_refused_before_probe(self):
        self.listen_address.return_value = "0.0.0.0"
        self.assertIsNone(await recovery.observe_recovery_ports(self.root, _PRESET))
        self.listen_address.return_value = "127.0.0.1"
        self.journal.load.return_value = self.checkpoint.model_copy(update={"pending_action": None})
        self.assertIsNone(await recovery.observe_recovery_ports(self.root, _PRESET))
        self.reader.inspect.assert_not_awaited()
