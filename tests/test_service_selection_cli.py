import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tiny_swarm_world.__main__ import main
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.composition import build_installation_lifecycle_service
from tests.application.services.test_lifecycle import adoption_fixture


class SelectionCliTests(unittest.IsolatedAsyncioTestCase):
    async def preview(self, options, service, config_root=None):
        with patch("tiny_swarm_world.infrastructure.adapters.cli.selection.Path.cwd", return_value=config_root or Path.cwd()), patch("tiny_swarm_world.infrastructure.adapters.cli.selection.build_installation_lifecycle_service", return_value=service), patch("tiny_swarm_world.infrastructure.adapters.cli.dispatcher.ensure_common_executable_paths") as paths, patch("tiny_swarm_world.infrastructure.adapters.cli.dispatcher.build_application_logger") as logger, contextlib.redirect_stdout(io.StringIO()) as output:
            await main(options + ["--json"])
        paths.assert_not_called()
        logger.assert_not_called()
        return json.loads(output.getvalue())

    async def test_minimal_and_config_cli_precedence_preview_without_writes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = build_installation_lifecycle_service(Path(__file__).resolve().parents[1])
            service.manifests = JsonManifestRepository(root / "state" / "manifest.json")
            result = await self.preview(["setup", "run", "--minimal", "--preview"], service)
            self.assertEqual(set(result["plan"]["resolved_services"]), {"incus", "portainer"})
            self.assertEqual(list(root.iterdir()), [])
            config = root / "selection.yml"
            config.write_text("services:\n  - jenkins\n")
            result = await self.preview(["setup", "run", "--selection-config", str(config), "--preview"], service, root)
            self.assertIn("nexus", result["plan"]["resolved_services"])
            result = await self.preview(["setup", "run", "--services", "swagger", "--selection-config", str(root / "absent"), "--preview"], service)
            self.assertNotIn("jenkins", result["plan"]["resolved_services"])
            self.assertFalse((root / "state").exists())

    def test_invalid_selection_modes_and_consent_flags_fail_before_composition(self):
        commands = [
            ["setup", "run", "--services", "jenkins"],
            ["setup", "run", "--minimal", "--preview", "--services", "jenkins"],
            ["setup", "run", "--minimal", "--preview", "--service-profile", "default"],
            ["setup", "run", "--services", "jenkins", "--preview", "--live"],
            ["setup", "run", "--services", "jenkins", "--preview", "--approve-live"],
            ["setup", "run", "--services", "jenkins,", "--preview"],
            ["setup", "run", "--services", "jenkins,jenkins", "--preview"],
            ["services", "remove", "--services", "jenkins", "--live"],
            ["services", "add", "--preview"],
            ["services", "list", "--services", "jenkins"],
        ]
        for command in commands:
            with self.subTest(command=command), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                parse_args(command)
            self.assertEqual(caught.exception.code, 2)

    async def test_unknown_and_foundation_removal_are_argument_errors_without_writes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            service = build_installation_lifecycle_service(Path(__file__).resolve().parents[1])
            service.manifests = JsonManifestRepository(root / "state.json")
            for command in (["setup", "run", "--services", "unknown", "--preview"], ["services", "remove", "--services", "portainer", "--preview"]):
                with self.subTest(command=command), self.assertRaises(SystemExit) as caught:
                    await self.preview(command, service)
                self.assertEqual(caught.exception.code, 2)
            self.assertEqual(list(root.iterdir()), [])

    async def test_optional_removal_preview_reports_impact_without_runtime_or_manifest_writes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "state.json"
            service = build_installation_lifecycle_service(Path(__file__).resolve().parents[1])
            service.manifests = JsonManifestRepository(manifest_path)
            selection = ServiceSelectionService(service.manifests, service.catalog)
            service.manifests.save(adoption_fixture(service.catalog.load()), expected_token=None)
            selection.persist(selection.preview(("jenkins",), add=True), approved=True)
            before_bytes = manifest_path.read_bytes()
            before_mtime = manifest_path.stat().st_mtime_ns

            result = await self.preview(
                ["services", "remove", "--services", "nexus", "--preview"],
                service,
            )

            self.assertEqual(result["status"], "selection_preview")
            self.assertEqual(result["execution"], "not performed (read-only preview)")
            self.assertEqual(result["data_policy"], "deployments and persistent data are retained")
            self.assertEqual(result["plan"]["removals"], ["nexus"])
            self.assertEqual(result["plan"]["removal_impact"], {"nexus": ["jenkins"]})
            self.assertTrue(result["plan"]["retained_data"])
            self.assertEqual(manifest_path.read_bytes(), before_bytes)
            self.assertEqual(manifest_path.stat().st_mtime_ns, before_mtime)

    def test_help_is_readonly_and_tracks_explicit_preset(self):
        for command in (["setup", "run"], ["services", "add"], ["services", "remove"]):
            with contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as caught:
                parse_args(command + ["--help"])
            self.assertEqual(caught.exception.code, 0)
            self.assertIn("--services", output.getvalue())
        self.assertFalse(parse_args(["setup", "run"]).service_profile_explicit)
        self.assertTrue(parse_args(["setup", "run", "--service-profile", "default"]).service_profile_explicit)

    def test_selection_config_rejects_escape_and_symlinks_before_read(self):
        from tiny_swarm_world.infrastructure.adapters.cli.selection import _configured_services
        with TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = root / "checkout"
            checkout.mkdir()
            outside = root / "outside.yml"
            outside.write_text("services: [jenkins]\n")
            link = checkout / "link.yml"
            link.symlink_to(outside)
            for path in (str(outside), str(checkout / ".." / "outside.yml"), str(link)):
                with self.subTest(path=path), patch("tiny_swarm_world.infrastructure.adapters.cli.selection.Path.cwd", return_value=checkout), patch("tiny_swarm_world.infrastructure.adapters.cli.selection.Path.read_text") as read:
                    with self.assertRaisesRegex(ValueError, "within the current working directory"):
                        _configured_services(path)
                    read.assert_not_called()
            inside = checkout / "selection.yml"
            inside.write_text("services: [jenkins]\n")
            with patch("tiny_swarm_world.infrastructure.adapters.cli.selection.Path.cwd", return_value=checkout):
                self.assertEqual(_configured_services(str(inside)), ("jenkins",))

    def test_selection_config_symlink_loop_is_sanitized_before_read(self):
        from tiny_swarm_world.infrastructure.adapters.cli.selection import _configured_services
        with patch("tiny_swarm_world.infrastructure.adapters.cli.selection.Path.resolve", side_effect=RuntimeError("loop")), patch("tiny_swarm_world.infrastructure.adapters.cli.selection.Path.read_text") as read:
            with self.assertRaisesRegex(ValueError, "Cannot read selection config"):
                _configured_services("loop.yml")
            read.assert_not_called()
