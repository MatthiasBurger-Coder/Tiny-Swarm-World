import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from tests.domain.lifecycle.test_update_planning import update_fixture
from tiny_swarm_world.__main__ import main
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository


class ComponentUpdateCliTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "manifest.json"
        self.catalog, manifest = update_fixture()
        self.repository = JsonManifestRepository(self.path)
        self.repository.save(manifest, expected_token=None)
        catalogs = Mock()
        catalogs.load.return_value = self.catalog
        self.lifecycle = InstallationLifecycleService(self.repository, catalogs)

    async def run_command(self, command, expected_exit=0):
        before = {item.name: (item.read_bytes(), item.stat().st_mtime_ns) for item in self.path.parent.iterdir()}
        output = io.StringIO()
        with patch("tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_installation_lifecycle_service", return_value=self.lifecycle), patch("tiny_swarm_world.infrastructure.adapters.cli.dispatcher.ensure_common_executable_paths") as paths, patch("tiny_swarm_world.infrastructure.adapters.cli.dispatcher.build_application_logger") as logger, patch("subprocess.run") as subprocess, contextlib.redirect_stdout(output):
            if expected_exit:
                with self.assertRaises(SystemExit) as caught:
                    await main(command)
                self.assertEqual(caught.exception.code, expected_exit)
            else:
                await main(command)
        paths.assert_not_called()
        logger.assert_not_called()
        subprocess.assert_not_called()
        self.assertEqual(before, {item.name: (item.read_bytes(), item.stat().st_mtime_ns) for item in self.path.parent.iterdir()})
        return json.loads(output.getvalue())

    async def test_readonly_discovery_default_and_selected(self):
        result = await self.run_command(["services", "updates", "--json"])
        self.assertEqual({item["service_id"] for item in result["services"]}, {"incus", "portainer", "jenkins", "nexus"})
        result = await self.run_command(["services", "updates", "--services", "jenkins", "--json"])
        self.assertEqual([item["service_id"] for item in result["services"]], ["jenkins"])

    async def test_preview_batch_and_single(self):
        result = await self.run_command(["services", "update", "--services", "jenkins,nexus", "--preview", "--json"])
        self.assertEqual(result["dependency_order"], ["nexus", "jenkins"])
        self.assertEqual(result["execution"], "not performed (read-only preview)")
        result = await self.run_command(["services", "update", "--services", "jenkins", "--to", "test-next", "--preview"])
        self.assertEqual(result["services"][0]["target"]["target_id"], "test-next")

    async def test_failures_uninstalled_unknown_unsupported_and_dedicated(self):
        for command, code in ((["services", "updates", "--services", "swagger"], 1),
                              (["services", "updates", "--services", "unknown"], 2),
                              (["services", "update", "--services", "nexus", "--to", "unknown", "--preview"], 1),
                              (["services", "update", "--services", "portainer,incus", "--preview"], 1)):
            with self.subTest(command=command):
                await self.run_command(command, expected_exit=code)

    def test_invalid_conflicting_arguments_and_live_refusal(self):
        cases = [
            ["services", "update"], ["services", "update", "--services", "nexus"],
            ["services", "update", "--services", "jenkins,nexus", "--to", "test-next", "--preview"],
            ["services", "updates", "--to", "test-next"], ["services", "updates", "--preview"],
            ["services", "list", "--to", "test-next"],
        ]
        for service_ids in ("", "nexus,nexus", "nexus,", "*", "Nexus"):
            cases.append(["services", "updates", "--services", service_ids])
        for options in (["--live"], ["--approve-live"], ["--confirm", "yes"], ["--preflight"],
                        ["--recover", "--to", "test-next"], ["--minimal"], ["--selection-config", "config.yaml"],
                        ["--service-profile", "default"], ["--stack", "nexus"], ["--service", "nexus"]):
            cases.append(["services", "update", "--services", "nexus", "--preview", *options])
        for command in cases:
            with self.subTest(command=command), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                parse_args(command)
            self.assertEqual(caught.exception.code, 2)

    def test_help_and_registry_are_readonly(self):
        from tiny_swarm_world.infrastructure.adapters.cli.registry import CLI_WORKFLOWS_BY_KEY
        for action in ("updates", "update"):
            self.assertEqual(CLI_WORKFLOWS_BY_KEY[("services", action)].mutating, action == "update")
            with contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as caught:
                parse_args(["services", action, "--help"])
            self.assertEqual(caught.exception.code, 0)
            self.assertIn("--to", output.getvalue())

    async def test_execution_requires_existing_live_consent_before_runtime_construction(self):
        output = io.StringIO()
        with patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_installation_lifecycle_service', return_value=self.lifecycle), patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_component_update_execution') as build, patch('builtins.input', side_effect=EOFError), contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as caught:
                await main(['services', 'update', '--services', 'nexus', '--live', '--json'])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(json.loads(output.getvalue())['status'], 'refused')
        build.assert_not_called()

    async def test_live_dispatch_preserves_selection_recovery_and_exit_status(self):
        from unittest.mock import AsyncMock
        executor = Mock()
        executor.run = AsyncMock(return_value={'status': 'partial'})
        output = io.StringIO()
        with patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_installation_lifecycle_service', return_value=self.lifecycle), patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_component_update_execution', return_value=executor), contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as caught:
                await main(['services', 'update', '--services', 'nexus,jenkins', '--live', '--approve-live', '--recover', '--json'])
        self.assertEqual(caught.exception.code, 1)
        self.assertEqual(executor.run.await_args.args[0], ('nexus', 'jenkins'))
        self.assertTrue(executor.run.await_args.kwargs['consent'].accepted)
        self.assertTrue(executor.run.await_args.kwargs['recovery'])

    async def test_blocked_production_plan_never_constructs_runtime(self):
        catalogs = Mock()
        catalogs.load.return_value = update_fixture(qualified=False)[0]
        lifecycle = InstallationLifecycleService(self.repository, catalogs)
        with patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_installation_lifecycle_service', return_value=lifecycle), patch('tiny_swarm_world.infrastructure.adapters.cli.component_updates.build_component_update_execution') as build, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                await main(['services', 'update', '--services', 'nexus', '--live', '--approve-live'])
        self.assertEqual(caught.exception.code, 1)
        build.assert_not_called()
