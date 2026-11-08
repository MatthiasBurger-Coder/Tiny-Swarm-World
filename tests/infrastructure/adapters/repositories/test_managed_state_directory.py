"""Independent first writers retain canonical private root authority."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.domain.lifecycle.test_models import manifest_fixture
from tests.infrastructure.adapters.repositories.test_routing_evidence_local_repository import _evidence
from tests.infrastructure.adapters.repositories.test_project_filesystem_evidence_local_repository import _override_assessment, _TargetInspector
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.repositories.port_repository_failure import RepositoryStorageError
from tiny_swarm_world.application.ports.repositories.port_project_filesystem_evidence_repository import ProjectFilesystemEvidenceError
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind
from tiny_swarm_world.infrastructure.adapters.repositories.routing_evidence_local_repository import RoutingEvidenceLocalRepository
from tiny_swarm_world.infrastructure.adapters.repositories.project_filesystem_evidence_local_repository import ProjectFilesystemEvidenceLocalRepository
from tiny_swarm_world.domain.inventory import ObservedInventory, VerificationResult, VerificationStatus
from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.repositories.observed_inventory_local_repository import ObservedInventoryLocalRepository
from tiny_swarm_world.infrastructure.adapters.repositories.verification_evidence_local_repository import VerificationEvidenceLocalRepository


class ManagedStateFirstWriterTests(unittest.TestCase):
    @staticmethod
    def write(root, writer):
        if writer == 'observed':
            ObservedInventoryLocalRepository(root=root).save(ObservedInventory())
        elif writer == 'verification':
            VerificationEvidenceLocalRepository(root=root).append(VerificationResult(
                target_id='fixture', status=VerificationStatus.VERIFIED, message='actual fixture result'))
        elif writer == 'routing':
            RoutingEvidenceLocalRepository(root=root).write_effective_access_model(_evidence())
        elif writer == 'filesystem':
            ProjectFilesystemEvidenceLocalRepository(
                path=root / '.tiny-swarm-world/evidence/filesystem/decision.json',
                target_inspector=_TargetInspector(ProjectFilesystemKind.WSL_LINUX)).write(_override_assessment())
        else:
            JsonManifestRepository(root / '.tiny-swarm-world/installation/manifest.json').save(
                manifest_fixture(), expected_token=None)

    def test_first_writer_preserves_real_private_operation_authority(self):
        for writer in ('observed', 'verification', 'routing', 'filesystem', 'manifest'):
            with self.subTest(writer=writer), TemporaryDirectory() as directory:
                root = Path(directory)
                self.write(root, writer)
                self.assertEqual((root / '.tiny-swarm-world').stat().st_mode & 0o777, 0o700)
                with JsonInstallationOperationLock(root).exclusive('setup') as lease:
                    lease.require_active()

    def test_existing_unsafe_root_is_not_repaired_by_any_first_writer(self):
        errors = {'observed': OSError, 'verification': RepositoryStorageError, 'routing': RepositoryStorageError,
                  'filesystem': ProjectFilesystemEvidenceError, 'manifest': LifecycleStateError}
        for writer, error in errors.items():
            with self.subTest(writer=writer), TemporaryDirectory() as directory:
                root = Path(directory)
                state = root / '.tiny-swarm-world'
                state.mkdir(mode=0o755)
                state.chmod(0o755)
                with self.assertRaises(error):
                    self.write(root, writer)
                self.assertEqual(state.stat().st_mode & 0o777, 0o755)
                self.assertEqual(list(state.iterdir()), [])

    def test_resolved_repository_paths_do_not_hide_original_state_root_symlink(self):
        errors = {'observed': OSError, 'verification': RepositoryStorageError, 'routing': RepositoryStorageError}
        for writer, error in errors.items():
            with self.subTest(writer=writer), TemporaryDirectory() as directory:
                root = Path(directory)
                original = root / 'original'
                original.mkdir(mode=0o700)
                state = root / '.tiny-swarm-world'
                state.symlink_to(original, target_is_directory=True)
                with self.assertRaises(error):
                    self.write(root, writer)
                self.assertTrue(state.is_symlink())
                self.assertEqual(list(original.iterdir()), [])
