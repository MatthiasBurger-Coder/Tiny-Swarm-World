"""CLI fallback preserves full Classic setup while scoped versions remain empty."""
import contextlib
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tiny_swarm_world.__main__ import main
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.application.services.setup.workflow import SetupWorkflowKind, SetupWorkflowResult, SetupWorkflowStatus
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tests.infrastructure.adapters.lifecycle.test_installation_operation_lock import FakeInstallationLock

_ROOT = Path(__file__).resolve().parents[1]


class FullClassicCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_parse_dispatch_full_classic_reaches_legacy_runner_but_new_requests_do_not_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / 'infra/config/incus-profile-capabilities.json'
            asset.parent.mkdir(parents=True)
            asset.write_text('{"schema_version":1,"capability":"installation-scoped-incus-manager-profile","admitted_versions":[]}')
            catalog = SimpleNamespace(root=root, load=NativeComponentCatalog(_ROOT).load)
            lifecycle = InstallationLifecycleService(JsonManifestRepository(root / '.tiny-swarm-world/installation/manifest.json'),
                catalog, operation_lock=FakeInstallationLock(root))
            completed = SetupWorkflowResult(SetupWorkflowKind.RUN, SetupWorkflowStatus.COMPLETED, 'legacy full fixture', 'fixture', executed=True)
            with patch('tiny_swarm_world.infrastructure.adapters.cli.selective_setup.composition.build_installation_lifecycle_service', return_value=lifecycle), \
                    patch('tiny_swarm_world.infrastructure.adapters.cli.selective_setup.composition.prepare_setup_selection_state', new_callable=AsyncMock,
                          side_effect=LifecycleStateError('No version is admitted for scoped setup.')) as scoped, \
                    patch('tiny_swarm_world.infrastructure.adapters.cli.dispatcher.run_cli_workflow', new_callable=AsyncMock, return_value=completed) as legacy, \
                    patch('tiny_swarm_world.infrastructure.adapters.cli.dispatcher.ensure_common_executable_paths'), \
                    patch('tiny_swarm_world.infrastructure.adapters.cli.dispatcher.build_application_logger', return_value=Mock()), \
                    patch('tiny_swarm_world.infrastructure.adapters.cli.dispatcher._print_setup_installation_plan'), \
                    contextlib.redirect_stdout(io.StringIO()):
                await main(['setup', 'run', '--live', '--approve-live', '--json'])
                legacy.assert_awaited_once()
                scoped.assert_not_awaited()
                legacy.reset_mock()
                requests = (['--minimal'], ['--services', 'swagger'], ['--swagger-exposure', 'internal'],
                            ['--stack-owner', 'portainer'], ['--recover'])
                for options in requests:
                    with self.subTest(options=options), self.assertRaises(SystemExit) as error:
                        await main(['setup', 'run', *options, '--live', '--approve-live', '--json'])
                    self.assertEqual(error.exception.code, 1)
                    legacy.assert_not_awaited()
                self.assertEqual(scoped.await_count, len(requests))
            from tests.domain.lifecycle.test_profile_lifecycle import admitted_fixture
            from tiny_swarm_world.infrastructure.composition import legacy_full_setup_available
            asset.write_text(admitted_fixture().model_dump_json())
            self.assertFalse(legacy_full_setup_available(lifecycle))
