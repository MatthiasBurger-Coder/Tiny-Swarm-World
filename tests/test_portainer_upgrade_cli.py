"""Portainer transport uses existing CLI help, preview and consent boundaries."""
import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tests.domain.lifecycle.test_update_planning import update_fixture
from tiny_swarm_world.__main__ import main
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository


class PortainerCliTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        catalog, manifest = update_fixture()
        repository = JsonManifestRepository(self.root / 'manifest.json')
        repository.save(manifest, expected_token=None)
        self.lifecycle = InstallationLifecycleService(repository, Mock(load=Mock(return_value=catalog)))

    async def invoke(self, options, *, exit_code=None):
        output = io.StringIO()
        with patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_installation_lifecycle_service', return_value=self.lifecycle), contextlib.redirect_stdout(output):
            if exit_code is None:
                await main(['services', 'update', '--services', 'portainer', '--json', *options])
            else:
                with self.assertRaises(SystemExit) as caught:
                    await main(['services', 'update', '--services', 'portainer', '--json', *options])
                self.assertEqual(caught.exception.code, exit_code)
        return json.loads(output.getvalue())

    async def test_preview_is_read_only_and_never_constructs_runtime(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        with patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_portainer_upgrade') as build, patch('subprocess.run') as run:
            result = await self.invoke(['--preview', '--to', 'portainer-ce-2.45.1'])
        self.assertEqual(result['status'], 'preview')
        self.assertTrue(result['backup_required'])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        build.assert_not_called()
        run.assert_not_called()

    async def test_unsupported_target_and_missing_recovery_block_without_runtime(self):
        with patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_portainer_upgrade') as build:
            await self.invoke(['--preview', '--to', 'latest'], exit_code=1)
            await self.invoke(['--preview', '--recover'], exit_code=1)
        build.assert_not_called()

    async def test_missing_live_consent_prevents_runtime_construction(self):
        with patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_portainer_upgrade') as build, patch('builtins.input', side_effect=EOFError):
            result = await self.invoke(['--live'], exit_code=2)
        self.assertEqual(result['status'], 'refused')
        build.assert_not_called()

    async def test_explicit_consent_dispatches_only_dedicated_adapter(self):
        executor = Mock(run=AsyncMock(return_value={'status': 'completed'}))
        with patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_portainer_upgrade', return_value=executor) as build, patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_component_update_execution') as generic:
            result = await self.invoke(['--live', '--approve-live'])
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(executor.run.call_args.kwargs['consent'].accepted)
        build.assert_called_once()
        generic.assert_not_called()

    def test_help_and_argument_conflicts(self):
        with contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaises(SystemExit) as caught:
            parse_args(['services', 'update', '--help'])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn('--recover', out.getvalue())
        for flags in (['--live', '--preview'], ['--recover', '--preview', '--to', 'portainer-ce-2.45.1'], ['--approve-live', '--preview']):
            with self.subTest(flags=flags), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                parse_args(['services', 'update', '--services', 'portainer', *flags])
            self.assertEqual(caught.exception.code, 2)
