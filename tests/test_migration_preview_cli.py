"""CLI routing, redaction and read-only loader regression tests."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests.domain.lifecycle.test_manifest_v2 import fixtures
from tiny_swarm_world.application.ports.lifecycle import ManifestSnapshot
from tiny_swarm_world.application.services.migration_preview import MigrationPreviewService
from tiny_swarm_world.infrastructure.adapters.cli import dispatcher
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.repositories.local_state_paths import local_state_file


BLOCKED = {"status": "BLOCKED_UNKNOWN", "source": "operator_local_unverified", "applied": False, "qualified": False}
ROOT = Path(__file__).resolve().parents[1]


class MigrationPreviewCliTests(unittest.IsolatedAsyncioTestCase):
    async def test_route_is_early_and_never_serializes_private_snapshot(self) -> None:
        manifest, catalog = fixtures(("swagger",))
        manifests, catalog_port = Mock(), Mock()
        manifests.load.return_value = ManifestSnapshot(manifest, "SECRET_TOKEN", ("SECRET_DIAGNOSTIC",))
        catalog_port.load.return_value = catalog
        service = MigrationPreviewService(manifests, catalog_port)
        out, err = StringIO(), StringIO()
        with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_preview.build_migration_preview_service",
                   return_value=nullcontext(service)), \
                patch.object(dispatcher, "ensure_common_executable_paths") as paths, \
                patch.object(dispatcher, "build_application_logger") as logger, \
                patch.object(dispatcher, "run_cli_workflow") as runtime, \
                redirect_stdout(out), redirect_stderr(err):
            await dispatcher.main(["services", "migration-preview"])
        result = json.loads(out.getvalue())
        self.assertEqual(result["status"], "PREVIEW")
        self.assertEqual(result["source"], "operator_local_unverified")
        self.assertEqual(result["swagger_exposure"], "published")
        self.assertNotIn("SECRET", out.getvalue() + err.getvalue())
        self.assertNotIn("12345678", out.getvalue() + err.getvalue())
        paths.assert_not_called()
        logger.assert_not_called()
        runtime.assert_not_called()
        manifests.save.assert_not_called()
        self.assertEqual(err.getvalue(), "")

    async def test_invalid_arguments_are_fixed_before_loader_and_runtime(self) -> None:
        flag = "migration-preview"
        cases = (["services", flag, "--live"], ["services", flag, "--approve-live"],
                 ["services", flag, "--recover"], ["services", flag, "--json"],
                 ["services", flag, "--help"], ["services", flag, "--confirm", "SECRET"],
                 ["services", flag, "SECRET"], ["services", flag, flag],
                 ["--live", "services", flag], ["services", flag + "=SECRET"],
                 ["--confirm=SECRET", "services", flag], ["services", flag, "--confirm=SECRET"],
                 ["services", "--", flag], ["--", "services", flag],
                 ["services", "--bogus", "SECRET", flag + "=SECRET"],
                 ["--bogus", "SECRET", "services", flag + "=SECRET"],
                 ["services", flag, "--infra-root", "SECRET"])
        for args in cases:
            with self.subTest(args=args), \
                    patch("tiny_swarm_world.infrastructure.adapters.cli.migration_preview.build_migration_preview_service") as build, \
                    patch.object(dispatcher, "build_application_logger") as logger:
                out, err = StringIO(), StringIO()
                with redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit) as stopped:
                    await dispatcher.main(args)
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(json.loads(out.getvalue()), BLOCKED)
                self.assertEqual(err.getvalue(), "")
                self.assertNotIn("SECRET", out.getvalue())
                build.assert_not_called()
                logger.assert_not_called()

    async def test_existing_service_list_parser_remains_available(self) -> None:
        from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args

        args = parse_args(["services", "list"])
        self.assertEqual((args.workflow.namespace, args.workflow.action), ("services", "list"))

    def test_scanner_value_option_inventory_matches_argparse(self) -> None:
        import argparse
        from tiny_swarm_world.infrastructure.adapters.cli import parser as cli_parser

        instances: list[argparse.ArgumentParser] = []

        class CaptureParser(argparse.ArgumentParser):
            def __init__(self, *args: object, **kwargs: object) -> None:
                super().__init__(*args, **kwargs)  # type: ignore[arg-type]
                instances.append(self)

        with patch.object(cli_parser, "ArgumentParser", CaptureParser):
            cli_parser.parse_args(["services", "list"])
        value_options = {option for action in instances[0]._actions
                         if isinstance(action, argparse._StoreAction)
                         for option in action.option_strings}
        from tiny_swarm_world.infrastructure.adapters.cli.migration_preview import _VALUE_OPTIONS

        self.assertEqual(_VALUE_OPTIONS, value_options)

    async def test_migration_preview_option_values_do_not_change_legacy_parsing(self) -> None:
        from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args

        for args, expected in (
            (["--confirm", "migration-preview", "platform", "destroy"], "migration-preview"),
            (["--confirm=migration-preview=secret", "platform", "destroy"], "migration-preview=secret"),
            (["--conf", "migration-preview", "platform", "destroy"], "migration-preview"),
        ):
            with self.subTest(args=args):
                parsed = parse_args(args)
                self.assertEqual(parsed.confirm, expected)
                self.assertEqual((parsed.workflow.namespace, parsed.workflow.action), ("platform", "destroy"))

    async def test_selection_config_value_is_not_a_preview_action(self) -> None:
        from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args

        for args in (["--selection-config", "migration-preview", "setup", "run", "--preview"],
                     ["--selection-config=migration-preview=secret", "setup", "run", "--preview"]):
            with self.subTest(args=args):
                parsed = parse_args(args)
                self.assertTrue(parsed.selection_preview)
                self.assertEqual((parsed.workflow.namespace, parsed.workflow.action), ("setup", "run"))
                self.assertTrue(parsed.selection_config.startswith("migration-preview"))

    async def test_argv_none_is_sanitized_before_host_work(self) -> None:
        import sys

        out, err = StringIO(), StringIO()
        with patch.object(sys, "argv", ["tsw", "services", "migration-preview", "--confirm=SECRET"]), \
                patch.object(dispatcher, "build_application_logger") as logger, \
                redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit) as stopped:
            await dispatcher.main(None)
        self.assertEqual(stopped.exception.code, 2)
        self.assertEqual(json.loads(out.getvalue()), BLOCKED)
        self.assertEqual(err.getvalue(), "")
        logger.assert_not_called()

    def test_documented_command_and_fixed_result_match_contract(self) -> None:
        guide = (ROOT / "documentation/user_guide/selective-setup.md").read_text(encoding="utf-8")
        self.assertIn("python3 -m tiny_swarm_world services migration-preview", guide)
        self.assertIn('{"status":"BLOCKED_UNKNOWN","source":"operator_local_unverified","applied":false,"qualified":false}', guide)

    async def test_descriptor_cleanup_failure_does_not_emit_partial_preview(self) -> None:
        from contextlib import contextmanager

        @contextmanager
        def broken_service() -> Iterator[Mock]:
            yield Mock(preview=Mock(return_value={"status": "PREVIEW", "secret": "SECRET"}))
            raise OSError("SECRET /private/path")

        out, err = StringIO(), StringIO()
        with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_preview.build_migration_preview_service",
                   side_effect=broken_service), \
                redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit) as stopped:
            await dispatcher.main(["services", "migration-preview"])
        self.assertEqual(stopped.exception.code, 2)
        self.assertEqual(json.loads(out.getvalue()), BLOCKED)
        self.assertEqual(err.getvalue(), "")

    async def test_unexpected_loader_failure_is_closed_and_redacted(self) -> None:
        out, err = StringIO(), StringIO()
        with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_preview.build_migration_preview_service",
                   side_effect=PermissionError("SECRET /private/path")), \
                redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit) as stopped:
            await dispatcher.main(["services", "migration-preview"])
        self.assertEqual(stopped.exception.code, 2)
        self.assertEqual(json.loads(out.getvalue()), BLOCKED)
        self.assertEqual(err.getvalue(), "")


class ReadOnlyLoaderTests(unittest.TestCase):
    def test_manifest_load_and_path_discovery_do_not_write_in_isolated_fixture(self) -> None:
        manifest, _ = fixtures()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(Path, "mkdir", side_effect=AssertionError("write")), \
                    patch("os.open", side_effect=AssertionError("write")):
                path = local_state_file(root=root, relative_path="installation/manifest.json")
                self.assertIsNone(JsonManifestRepository(path).load().manifest)
            self.assertEqual(list(root.iterdir()), [])
            path.parent.mkdir(parents=True)
            path.write_text(manifest.model_dump_json(), encoding="utf-8")
            before = path.read_bytes()
            with patch.object(Path, "mkdir", side_effect=AssertionError("write")), \
                    patch("os.open", side_effect=AssertionError("write")):
                self.assertEqual(JsonManifestRepository(path).load().manifest, manifest)
            self.assertEqual(path.read_bytes(), before)
            path.write_text("{bad", encoding="utf-8")
            before = path.read_bytes()
            with patch.object(Path, "mkdir", side_effect=AssertionError("write")), \
                    patch("os.open", side_effect=AssertionError("write")), \
                    self.assertRaises(ValueError):
                JsonManifestRepository(path).load()
            self.assertEqual(path.read_bytes(), before)
            with patch.object(Path, "read_bytes", side_effect=PermissionError("SECRET")), \
                    patch.object(Path, "mkdir", side_effect=AssertionError("write")), \
                    patch("os.open", side_effect=AssertionError("write")), \
                    self.assertRaises(ValueError):
                JsonManifestRepository(path).load()

    def test_locally_changed_valid_assets_are_explicitly_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "infra" / "config" / "compose"
            destination.parent.mkdir(parents=True)
            shutil.copytree(ROOT / "infra" / "config" / "compose", destination)
            asset = next(destination.rglob("docker-compose.yml"))
            original = asset.read_text(encoding="utf-8")
            asset.write_text(original + "\n# operator local change\n", encoding="utf-8")
            catalog = NativeComponentCatalog(root).load()
            manifest, _ = fixtures()
            components = tuple(component for service in catalog.services
                               if service.service_id in manifest.resolved_services
                               for component in service.components)
            manifest = manifest.model_copy(update={"components": components})
            manifests, catalog_port = Mock(), Mock()
            manifests.load.return_value = ManifestSnapshot(manifest, "SECRET", ())
            catalog_port.load.return_value = catalog
            result = MigrationPreviewService(manifests, catalog_port).preview()
            self.assertEqual(result["source"], "operator_local_unverified")
            self.assertIs(result["qualified"], False)
            self.assertNotIn("SECRET", json.dumps(result))
            self.assertEqual(asset.read_text(encoding="utf-8"), original + "\n# operator local change\n")

    def test_pinned_composition_ignores_alternate_infra_root(self) -> None:
        from tiny_swarm_world.infrastructure.composition_lifecycle import build_migration_preview_service

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            destination = root / "infra" / "config" / "compose"
            destination.parent.mkdir(parents=True)
            shutil.copytree(ROOT / "infra" / "config" / "compose", destination)
            catalog = NativeComponentCatalog(root).load()
            manifest, _ = fixtures()
            manifest = manifest.model_copy(update={"components": tuple(
                component for service in catalog.services if service.service_id in manifest.resolved_services
                for component in service.components)})
            state = root / ".tiny-swarm-world" / "installation" / "manifest.json"
            state.parent.mkdir(parents=True)
            state.write_text(manifest.model_dump_json(), encoding="utf-8")
            environment = {"TSW_REPOSITORY_ROOT": str(root), "TSW_INFRA_ROOT": str(root / "missing-alternate")}
            with patch.dict(os.environ, environment), patch.object(Path, "mkdir", side_effect=AssertionError("write")):
                with build_migration_preview_service() as service:
                    result = service.preview()
            self.assertEqual(result["source"], "operator_local_unverified")
            self.assertIs(result["qualified"], False)

    def test_missing_project_asset_blocks_even_with_alternate_tree(self) -> None:
        from tiny_swarm_world.infrastructure.composition_lifecycle import build_migration_preview_service

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            alternate = Path(directory) / "alternate"
            root.mkdir()
            shutil.copytree(ROOT / "infra", alternate)
            manifest, _ = fixtures()
            state = root / ".tiny-swarm-world" / "installation" / "manifest.json"
            state.parent.mkdir(parents=True)
            state.write_text(manifest.model_dump_json(), encoding="utf-8")
            with patch.dict(os.environ, {"TSW_REPOSITORY_ROOT": str(root), "TSW_INFRA_ROOT": str(alternate)}):
                with self.assertRaises(ValueError), build_migration_preview_service() as service:
                    service.preview()

    def test_preview_rejects_symlinked_compose_asset(self) -> None:
        from tiny_swarm_world.infrastructure.composition_lifecycle import build_migration_preview_service

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "infra" / "config" / "compose"
            destination.parent.mkdir(parents=True)
            shutil.copytree(ROOT / "infra" / "config" / "compose", destination)
            manifest, _ = fixtures()
            state = root / ".tiny-swarm-world" / "installation" / "manifest.json"
            state.parent.mkdir(parents=True)
            state.write_text(manifest.model_dump_json(), encoding="utf-8")
            asset = next(destination.rglob("docker-compose.yml"))
            asset.unlink()
            asset.symlink_to(state)
            with self.assertRaises(ValueError), build_migration_preview_service(root) as service:
                service.preview()

    def test_native_catalog_reads_assets_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "infra" / "config" / "compose"
            destination.parent.mkdir(parents=True)
            shutil.copytree(ROOT / "infra" / "config" / "compose", destination)
            before = {str(path.relative_to(root)): path.read_bytes()
                      for path in root.rglob("*") if path.is_file()}
            with patch.object(Path, "mkdir", side_effect=AssertionError("write")), \
                    patch("os.open", side_effect=AssertionError("write")):
                catalog = NativeComponentCatalog(root).load()
            self.assertTrue(catalog.services)
            after = {str(path.relative_to(root)): path.read_bytes()
                     for path in root.rglob("*") if path.is_file()}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
