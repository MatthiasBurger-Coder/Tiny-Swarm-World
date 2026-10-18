import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tiny_swarm_world.__main__ import main
from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args
from tiny_swarm_world.infrastructure.composition import build_installation_lifecycle_service


class LifecycleCliTests(unittest.IsolatedAsyncioTestCase):
    async def test_inspection_avoids_logging_runtime_and_all_writes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            # Native catalog assets are read from the real repo; instance state is isolated.
            service = build_installation_lifecycle_service(Path(__file__).resolve().parents[1])
            from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
            service.manifests = JsonManifestRepository(root / "state" / "manifest.json")
            for command in (["product", "version", "--json"], ["services", "list", "--json"]):
                output = io.StringIO()
                with patch("tiny_swarm_world.infrastructure.adapters.cli.lifecycle.build_installation_lifecycle_service", return_value=service), patch("tiny_swarm_world.infrastructure.adapters.cli.dispatcher.ensure_common_executable_paths") as paths, patch("tiny_swarm_world.infrastructure.adapters.cli.dispatcher.build_application_logger") as logger, contextlib.redirect_stdout(output):
                    await main(command)
                result = json.loads(output.getvalue())
                self.assertEqual(result["status"], "adoption_required")
                if command[0] == "services":
                    self.assertTrue(all(item["installation_state"] == "unknown" for item in result["catalog"]["services"]))
                paths.assert_not_called()
                logger.assert_not_called()
                self.assertEqual(list(root.iterdir()), [])

    async def test_corrupt_state_returns_sanitized_failure(self):
        from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
        with patch("tiny_swarm_world.infrastructure.adapters.cli.lifecycle.build_installation_lifecycle_service", side_effect=LifecycleStateError("Invalid installation manifest")), contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as caught:
                await main(["product", "version", "--json"])
            self.assertEqual(caught.exception.code, 1)
            self.assertEqual(json.loads(output.getvalue())["status"], "blocked")

    def test_mutation_update_and_unsupported_options_rejected(self):
        for options in (["--live"], ["--approve-live"], ["--preview"], ["--recover"], ["--preflight"], ["--service", "jenkins"]):
            with self.subTest(options=options), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                parse_args(["services", "list", *options])
            self.assertEqual(caught.exception.code, 2)

    def test_help_lists_readonly_commands(self):
        from tiny_swarm_world.infrastructure.adapters.cli.registry import CLI_WORKFLOWS_BY_KEY
        self.assertFalse(CLI_WORKFLOWS_BY_KEY[("product", "version")].mutating)
        self.assertFalse(CLI_WORKFLOWS_BY_KEY[("services", "list")].mutating)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as caught:
            parse_args(["product", "version", "--help"])
        self.assertEqual(caught.exception.code, 0)
