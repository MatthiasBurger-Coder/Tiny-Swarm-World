"""Capability admission is an explicit reviewed asset, never a version guess."""
import json
from pathlib import Path
import tempfile
import unittest

from modules.tsw_core.tests.domain.lifecycle.test_profile_lifecycle import admitted_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository import IncusProfileCapabilityRepository


class CapabilityRepositoryTests(unittest.TestCase):
    def test_c_empty_k_populated_are_read_only_exact_pair_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'modules/tsw_core/infra/config/incus-profile-capabilities.json'
            path.parent.mkdir(parents=True)
            empty = {'schema_version': 1, 'capability': 'installation-scoped-incus-manager-profile', 'admitted_versions': []}
            for payload, expected in ((empty, False), (admitted_fixture().model_dump(mode='json'), True)):
                path.write_text(json.dumps(payload))
                before = path.read_bytes(), path.stat().st_mtime_ns
                matrix = IncusProfileCapabilityRepository(root).load()
                self.assertEqual(matrix.admits('6.0.5', '6.0.5'), expected)
                for client, server in (('6.0.5', '6.0.6'), ('6.0.6', '6.0.5'), ('6.0.5-8', '6.0.5'), ('unknown', 'unknown')):
                    self.assertFalse(matrix.admits(client, server))
                self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)

    def test_empty_asset_refuses_every_version_and_qualified_provenance_is_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'modules/tsw_core/infra/config/incus-profile-capabilities.json'
            path.parent.mkdir(parents=True)
            path.write_text('{"schema_version":1,"capability":"installation-scoped-incus-manager-profile","admitted_versions":[]}')
            repository = IncusProfileCapabilityRepository(root)
            self.assertFalse(repository.load().admits('6.0.5', '6.0.5'))
            path.write_text(admitted_fixture().model_dump_json())
            observed = repository.load()
            self.assertTrue(observed.admits('6.0.5', '6.0.5'))
            self.assertEqual(observed.admitted_versions[0].fixture_source_revision, 'c' * 40)

    def test_missing_unknown_duplicate_malformed_and_symlink_assets_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'modules/tsw_core/infra/config/incus-profile-capabilities.json'
            path.parent.mkdir(parents=True)
            repository = IncusProfileCapabilityRepository(root)
            with self.assertRaises(LifecycleStateError):
                repository.load()
            originals = admitted_fixture().model_dump(mode='json')
            malformed: tuple[object, ...] = (None, [], {**originals, 'unexpected': True},
                {**originals, 'schema_version': True}, {**originals, 'admitted_versions': [{'client_version': '6.0.5'}]})
            for value in malformed:
                path.write_text(json.dumps(value))
                with self.subTest(value=value), self.assertRaises(LifecycleStateError):
                    repository.load()
            path.write_text('{"schema_version":1,"schema_version":1}')
            with self.assertRaises(LifecycleStateError):
                repository.load()
            path.unlink()
            target = root / 'outside.json'
            target.write_text(admitted_fixture().model_dump_json())
            path.symlink_to(target)
            with self.assertRaises(LifecycleStateError):
                repository.load()
