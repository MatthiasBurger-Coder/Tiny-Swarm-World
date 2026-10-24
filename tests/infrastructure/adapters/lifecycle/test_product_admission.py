"""Source admission and lazy composition safety, using real local manifest state."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests.application.services.test_product_upgrade import product_plan
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_installation import PreparedProductInstallation
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_source import OFFICIAL_REPOSITORY


class ProductAdmissionTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.fixture = product_plan()
        lock = b'example==1.0\n'
        source = self.fixture.source.model_copy(update={'product': self.fixture.source.product.model_copy(
            update={'dependency_lock': 'sha256:' + hashlib.sha256(lock).hexdigest()})})
        self.manifest = self.fixture.manifest.model_copy(update={'product': source.product})
        self.revision = source.product.revision
        self.origin = OFFICIAL_REPOSITORY
        self.top_level = str(self.root)
        (self.root / 'pyproject.toml').write_text('[project]\nversion="0.2.0"\n')
        (self.root / 'requirements.lock').write_bytes(lock)
        self.manifests = JsonManifestRepository(self.root / '.tiny-swarm-world/installation/manifest.json')
        self.manifests.save(self.manifest, expected_token=None)
        self.source = Mock()
        self.source.resolve.return_value = (self.fixture.target, ())
        self.catalog = Mock()
        self.installation = PreparedProductInstallation(self.root, self.manifests, self.catalog, self.source, Mock())
        self.installation._command = Mock(side_effect=self.command)
        self.installation._host_and_resources = Mock()

    def command(self, args, **kwargs):
        if tuple(args[:2]) == ('git', 'status'):
            return ''
        if tuple(args) == ('git', 'rev-parse', '--show-toplevel'):
            return self.top_level
        if tuple(args[:2]) == ('git', 'rev-parse'):
            return self.revision
        if tuple(args[:2]) == ('git', 'remote'):
            return self.origin
        raise AssertionError('Unexpected admission command')

    def test_valid_preview_revalidates_source_target_inventory_without_writing(self):
        before = self.manifests.path.read_bytes()
        plan = self.installation.plan('0.5.0')
        self.assertEqual(plan.manifest, self.manifest)
        self.assertFalse(plan.adoption)
        self.assertEqual(plan.source.product, self.manifest.product)
        self.assertEqual(plan.target, self.fixture.target)
        self.assertEqual(self.manifests.path.read_bytes(), before)
        self.catalog.load.return_value.validate_manifest.assert_called_once_with(self.manifest)
        self.installation._host_and_resources.assert_called_once_with(plan)

    def test_missing_inventory_blocks_before_release_or_runtime_access(self):
        self.manifests.path.unlink()
        with self.assertRaises(LifecycleStateError):
            self.installation.plan('0.5.0')
        self.source.resolve.assert_not_called()

    def test_explicit_legacy_inventory_is_validated_but_not_persisted_by_preview(self):
        self.manifests.path.unlink()
        inventory = self.root / 'inventory.json'
        inventory.write_text(self.manifest.model_dump_json())
        self.installation.adoption_file = inventory
        plan = self.installation.plan('0.5.0')
        self.assertTrue(plan.adoption)
        self.assertIsNone(plan.manifest_token)
        self.assertFalse(self.manifests.path.exists())
        self.assertEqual(plan.manifest.credential_references, self.manifest.credential_references)

    def test_unreadable_legacy_inventory_is_safe_refusal(self):
        self.manifests.path.unlink()
        self.installation.adoption_file = self.root / 'missing.json'
        with self.assertRaises(LifecycleStateError):
            self.installation.plan('0.5.0')
        self.source.resolve.assert_not_called()

    def test_interrupted_manifest_blocks_without_promoting_temporary_data(self):
        interrupted = self.manifests.path.parent / '.installation-manifest-retained.tmp'
        interrupted.write_text('unverified')
        with self.assertRaises(LifecycleStateError):
            self.installation.plan('0.5.0')
        self.assertEqual(interrupted.read_text(), 'unverified')
        self.source.resolve.assert_not_called()

    def test_inventory_source_mismatch_blocks_before_target_access(self):
        snapshot = self.manifests.load()
        changed = self.manifest.model_copy(update={'product': self.manifest.product.model_copy(
            update={'revision': 'f' * 40})})
        self.manifests.save(changed, expected_token=snapshot.token)
        with self.assertRaises(LifecycleStateError):
            self.installation.plan('0.5.0')
        self.source.resolve.assert_not_called()

    def test_moved_target_during_admission_blocks(self):
        moved = self.fixture.target.model_copy(update={'product': self.fixture.target.product.model_copy(
            update={'revision': 'f' * 40})})
        self.source.resolve.side_effect = [(self.fixture.target, ()), (moved, ())]
        with self.assertRaises(LifecycleStateError):
            self.installation.plan('0.5.0')

    def test_stale_manifest_token_cannot_resume_over_new_state(self):
        plan = self.installation.plan('0.5.0')
        self.manifests.save(self.manifest.model_copy(update={'checkpoint_reference': 'other-operation'}),
                            expected_token=plan.manifest_token)
        with self.assertRaises(LifecycleStateError):
            self.installation.validate(plan)

    def test_source_change_after_preview_is_rejected(self):
        plan = self.installation.plan('0.5.0')
        self.revision = 'f' * 40
        with self.assertRaises(LifecycleStateError):
            self.installation.validate(plan)

    def test_already_committed_matching_target_is_valid_recovery_state(self):
        plan = self.installation.plan('0.5.0')
        self.manifests.save(self.manifest.model_copy(update={'product': plan.target.product}),
                            expected_token=plan.manifest_token)
        self.installation.validate(plan)

    def test_foreign_origin_or_wrong_checkout_root_is_rejected(self):
        for origin, root in (('https://example.invalid/other.git', str(self.root)),
                             (OFFICIAL_REPOSITORY, str(self.root.parent))):
            self.origin, self.top_level = origin, root
            with self.assertRaises(LifecycleStateError):
                self.installation._clean_source()
        self.source.resolve.assert_not_called()

    def test_missing_source_lock_is_not_an_installed_product_identity(self):
        (self.root / 'requirements.lock').unlink()
        with self.assertRaises(LifecycleStateError):
            self.installation._source_identity()


class ProductCompositionTests(unittest.TestCase):
    def test_controller_construction_is_lazy_and_uses_bounded_incus_gateway(self):
        from tiny_swarm_world.infrastructure import composition
        from tiny_swarm_world.infrastructure import composition_runtime
        from tiny_swarm_world.domain.node_provider import ManagedLxcBackend

        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        lifecycle = SimpleNamespace(manifests=JsonManifestRepository(root / 'installation/manifest.json'),
                                    catalog=Mock(root=root))
        with (patch('tiny_swarm_world.infrastructure.composition_lifecycle.build_installation_lifecycle_service', return_value=lifecycle),
              patch.object(composition_runtime, '_required_operator_secret_value', return_value='fixture-only') as secret,
              patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway.LxcManagerShellGateway') as shell,
              patch('tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client.LxcPortainerHttpClient') as client):
            service = composition.build_product_upgrade(adoption_file='inventory.json')
            self.assertEqual(service.installation.adoption_file, 'inventory.json')
            self.assertEqual(service.installation.root, root)
            secret.assert_not_called()
            shell.assert_not_called()
            client.assert_not_called()
            self.assertEqual(list(root.iterdir()), [])
            service.runtime.shell_factory()
            self.assertEqual(shell.call_args.kwargs['backend'], ManagedLxcBackend.INCUS)
            self.assertEqual(shell.call_args.kwargs['timeout_seconds'], 30)
            service.runtime.api_factory()
            secret.assert_called_once_with('TSW_PORTAINER_ADMIN_PASSWORD')
            client.return_value._client.assert_called_once_with()
