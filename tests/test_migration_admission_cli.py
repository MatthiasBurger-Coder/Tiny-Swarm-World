"""Non-admitting migration-check CLI grammar and read-only tests."""
from __future__ import annotations

from contextlib import contextmanager, nullcontext, redirect_stderr, redirect_stdout
from collections.abc import Iterator
from io import StringIO
from itertools import permutations
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests.domain.lifecycle.test_manifest_v2 import fixtures
from tiny_swarm_world.application.ports.lifecycle.migration_admission import (
    MigrationAdmissionRequest, MigrationAdmissionResult, MigrationAdmissionStatus,
)
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode
from tiny_swarm_world.infrastructure.adapters.cli import dispatcher
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog

ROOT = Path(__file__).resolve().parents[1]
ACTION = ["services", "migration-check"]
BLOCKED_UNKNOWN = {"status": "BLOCKED_UNKNOWN", "source": "operator_local_unverified",
                   "applied": False, "qualified": False}
BLOCKED_UNSUPPORTED = dict(BLOCKED_UNKNOWN, status="BLOCKED_UNSUPPORTED")


class MigrationCheckCliTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_option_orders_and_equals_are_early_non_admitting(self) -> None:
        choices = (("--version", "6.0.5"), ("--exposure", "not_applicable"),
                   ("--listen-address", "127.0.0.1"))
        for ordered in permutations(choices):
            for equals in (False, True):
                with self.subTest(ordered=ordered, equals=equals):
                    arguments = [name + "=" + value for name, value in ordered] if equals else [
                        part for pair in ordered for part in pair]
                    service = Mock()
                    service.evaluate.return_value = MigrationAdmissionResult(MigrationAdmissionStatus.BLOCKED_UNSUPPORTED)
                    out, err = StringIO(), StringIO()
                    with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service",
                               return_value=nullcontext(service)), \
                            patch.object(dispatcher, "ensure_common_executable_paths") as paths, \
                            patch.object(dispatcher, "build_application_logger") as logger, \
                            patch.object(dispatcher, "run_cli_workflow") as runtime, \
                            redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit) as stopped:
                        await dispatcher.main(ACTION + arguments)
                    self.assertEqual(stopped.exception.code, 2)
                    self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNSUPPORTED)
                    self.assertEqual(err.getvalue(), "")
                    service.evaluate.assert_called_once_with(
                        MigrationAdmissionRequest("6.0.5", SwaggerMode.NOT_APPLICABLE, "127.0.0.1"))
                    paths.assert_not_called()
                    logger.assert_not_called()
                    runtime.assert_not_called()

    async def test_mixed_equals_and_separate_options_are_accepted(self) -> None:
        cases = (
            ["--version=6.0.5", "--exposure", "not_applicable", "--listen-address=127.0.0.1"],
            ["--listen-address", "127.0.0.1", "--version=6.0.5", "--exposure=not_applicable"],
            ["--exposure=not_applicable", "--version", "6.0.5", "--listen-address", "127.0.0.1"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                service = Mock()
                service.evaluate.return_value = MigrationAdmissionResult(MigrationAdmissionStatus.BLOCKED_UNSUPPORTED)
                out, err = StringIO(), StringIO()
                with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service",
                           return_value=nullcontext(service)), redirect_stdout(out), redirect_stderr(err), \
                        self.assertRaises(SystemExit) as stopped:
                    await dispatcher.main(ACTION + arguments)
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNSUPPORTED)
                self.assertEqual(err.getvalue(), "")
                service.evaluate.assert_called_once_with(
                    MigrationAdmissionRequest("6.0.5", SwaggerMode.NOT_APPLICABLE, "127.0.0.1"))

    async def test_invalid_grammar_is_redacted_before_load_or_runtime(self) -> None:
        good = ["--version", "6.0.5", "--exposure", "published", "--listen-address", "127.0.0.1"]
        cases = (ACTION, ACTION + good[:-2], ACTION + good + ["--version", "SECRET"],
                 ACTION + good + ["--live"], ACTION + good + ["--unknown", "SECRET"],
                 ACTION + good + ["SECRET"], ACTION + ["--vers", "SECRET"] + good[2:],
                 ["--live"] + ACTION + good, ACTION + ["--"] + good,
                 ACTION + ["--version=", "--exposure", "published", "--listen-address", "127.0.0.1"],
                 ACTION + ["--version", "6.0.5", "--exposure", "SECRET", "--listen-address", "127.0.0.1"],
                 ACTION + ["--version", "6.0.5", "--exposure", "unknown", "--listen-address", "127.0.0.1"],
                 ACTION + ["--version", "6.0.5", "--exposure", "published", "--listen-address", "SECRET"],
                 ["services", "--unknown", "SECRET", "migration-check=SECRET"],
                 ["services", "migration-checkSECRET"], ["services", "migration-che"],
                 ["services", "migration-"])
        for arguments in cases:
            with self.subTest(arguments=arguments):
                out, err = StringIO(), StringIO()
                with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service") as build, \
                        patch.object(dispatcher, "build_application_logger") as logger, \
                        redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit) as stopped:
                    await dispatcher.main(arguments)
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNKNOWN)
                self.assertEqual(err.getvalue(), "")
                self.assertNotIn("SECRET", out.getvalue())
                build.assert_not_called()
                logger.assert_not_called()

    async def test_both_fixed_outcomes_and_context_cleanup_failure_are_redacted(self) -> None:
        args = ACTION + ["--version", "SECRET", "--exposure", "not_applicable", "--listen-address", "0.0.0.0"]
        for status in (MigrationAdmissionStatus.BLOCKED_UNKNOWN, MigrationAdmissionStatus.BLOCKED_UNSUPPORTED):
            service = Mock()
            service.evaluate.return_value = MigrationAdmissionResult(status)
            out, err = StringIO(), StringIO()
            with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service",
                       return_value=nullcontext(service)), redirect_stdout(out), redirect_stderr(err), \
                    self.assertRaises(SystemExit) as stopped:
                await dispatcher.main(args)
            self.assertEqual(stopped.exception.code, 2)
            self.assertEqual(json.loads(out.getvalue())["status"], status.value)
            self.assertNotIn("SECRET", out.getvalue() + err.getvalue())
            self.assertEqual(err.getvalue(), "")

        @contextmanager
        def failing_cleanup() -> Iterator[Mock]:
            yield Mock(evaluate=Mock(return_value=MigrationAdmissionResult(MigrationAdmissionStatus.BLOCKED_UNSUPPORTED)))
            raise OSError("SECRET /private/path")

        out, err = StringIO(), StringIO()
        with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service",
                   side_effect=failing_cleanup), redirect_stdout(out), redirect_stderr(err), \
                self.assertRaises(SystemExit):
            await dispatcher.main(args)
        self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNKNOWN)
        self.assertEqual(err.getvalue(), "")

    async def test_legacy_action_and_values_are_not_hijacked(self) -> None:
        from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args

        preview = parse_args(["services", "migration-preview"])
        self.assertEqual(preview.workflow.action, "migration-preview")
        legacy = parse_args(["--confirm", "migration-check", "platform", "destroy"])
        self.assertEqual(legacy.confirm, "migration-check")
        legacy = parse_args(["--selection-config=migration-check", "setup", "run", "--preview"])
        self.assertEqual(legacy.selection_config, "migration-check")

    async def test_action_words_in_new_option_values_are_not_commands(self) -> None:
        for value in ("migration-check", "migration-preview"):
            service = Mock()
            service.evaluate.return_value = MigrationAdmissionResult(MigrationAdmissionStatus.BLOCKED_UNKNOWN)
            out, err = StringIO(), StringIO()
            args = ACTION + ["--version", value, "--exposure", "not_applicable", "--listen-address", "127.0.0.1"]
            with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service",
                       return_value=nullcontext(service)), redirect_stdout(out), redirect_stderr(err), \
                    self.assertRaises(SystemExit):
                await dispatcher.main(args)
            self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNKNOWN)
            self.assertEqual(service.evaluate.call_args.args[0].version, value)

    async def test_argv_none_unknown_status_and_exceptions_are_fixed(self) -> None:
        args = ACTION + ["--version", "6.0.5", "--exposure", "not_applicable", "--listen-address", "127.0.0.1"]
        out, err = StringIO(), StringIO()
        with patch.object(sys, "argv", ["tsw"] + args + ["SECRET"]), \
                redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit):
            await dispatcher.main(None)
        self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNKNOWN)
        self.assertEqual(err.getvalue(), "")
        service = Mock()
        service.evaluate.return_value = "SECRET"
        out, err = StringIO(), StringIO()
        with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service",
                   return_value=nullcontext(service)), redirect_stdout(out), redirect_stderr(err), \
                self.assertRaises(SystemExit):
            await dispatcher.main(args)
        self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNKNOWN)
        self.assertEqual(err.getvalue(), "")
        out, err = StringIO(), StringIO()
        with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service",
                   side_effect=PermissionError("SECRET /private")), redirect_stdout(out), redirect_stderr(err), \
                self.assertRaises(SystemExit):
            await dispatcher.main(args)
        self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNKNOWN)
        self.assertEqual(err.getvalue(), "")

    async def test_actual_g2d_invalid_version_empty_token_and_internal_gap_block(self) -> None:
        from tests.domain.lifecycle.test_scoped_route_policy import make_fixture
        from tiny_swarm_world.application.ports.lifecycle import ManifestSnapshot
        from tiny_swarm_world.application.services.migration_admission import MigrationAdmissionService

        for case in ("bad_version", "empty_token", "internal"):
            with self.subTest(case=case):
                manifest, catalog = make_fixture(("swagger",) if case == "internal" else ())
                manifests, catalog_port = Mock(), Mock()
                manifests.load.return_value = ManifestSnapshot(manifest, "" if case == "empty_token" else "SECRET_TOKEN")
                catalog_port.load.return_value = catalog
                service = MigrationAdmissionService(manifests, catalog_port)
                version = "SECRET" if case == "bad_version" else "6.0.5"
                exposure = "internal" if case == "internal" else "not_applicable"
                args = ACTION + ["--version", version, "--exposure", exposure, "--listen-address", "127.0.0.1"]
                out, err = StringIO(), StringIO()
                with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service",
                           return_value=nullcontext(service)), redirect_stdout(out), redirect_stderr(err), \
                        self.assertRaises(SystemExit):
                    await dispatcher.main(args)
                self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNKNOWN)
                self.assertNotIn("SECRET", out.getvalue() + err.getvalue())
                manifests.save.assert_not_called()

    async def test_scoped_8086_cases_stay_fixed_unsupported_without_host_effects(self) -> None:
        from tests.domain.lifecycle.test_scoped_route_policy import make_fixture
        from tiny_swarm_world.application.ports.lifecycle import ManifestSnapshot
        from tiny_swarm_world.application.services.migration_admission import MigrationAdmissionService

        for selected in (("infisical",), ("service-access", "nexus", "infisical", "traefik")):
            with self.subTest(selected=selected):
                manifest, catalog = make_fixture(selected, "service-access")
                manifests, catalog_port = Mock(), Mock()
                manifests.load.return_value = ManifestSnapshot(manifest, "SECRET_TOKEN")
                catalog_port.load.return_value = catalog
                service = MigrationAdmissionService(manifests, catalog_port)
                args = ACTION + ["--version", "6.0.5", "--exposure", "not_applicable",
                                 "--listen-address", "127.0.0.1"]
                out, err = StringIO(), StringIO()
                with patch("tiny_swarm_world.infrastructure.adapters.cli.migration_admission.build_migration_admission_service",
                           return_value=nullcontext(service)), \
                        patch.object(dispatcher, "build_application_logger") as logger, \
                        patch.object(dispatcher, "run_cli_workflow") as runtime, \
                        patch("os.system", side_effect=AssertionError("host command")), \
                        patch("subprocess.Popen", side_effect=AssertionError("host process")), \
                        patch("socket.socket", side_effect=AssertionError("network")), \
                        redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit) as stopped:
                    await dispatcher.main(args)
                self.assertEqual(stopped.exception.code, 2)
                self.assertEqual(out.getvalue(),
                                 '{"status":"BLOCKED_UNSUPPORTED","source":"operator_local_unverified",'
                                 '"applied":false,"qualified":false}\n')
                self.assertEqual(err.getvalue(), "")
                self.assertNotIn("SECRET", out.getvalue() + err.getvalue())
                manifests.save.assert_not_called()
                logger.assert_not_called()
                runtime.assert_not_called()

    async def test_real_bounded_local_load_yields_unsupported_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
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
            before = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            out, err = StringIO(), StringIO()
            args = ACTION + ["--version", "6.0.5", "--exposure", "not_applicable", "--listen-address", "127.0.0.1"]
            with patch.dict(os.environ, {"TSW_REPOSITORY_ROOT": str(root), "TSW_INFRA_ROOT": "/private/ignored"}), \
                    patch.object(Path, "mkdir", side_effect=AssertionError("write")), \
                    redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit):
                await dispatcher.main(args)
            self.assertEqual(json.loads(out.getvalue()), BLOCKED_UNSUPPORTED)
            self.assertEqual(err.getvalue(), "")
            after = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(before, after)

    def test_user_guide_documents_exact_invocation_and_limit(self) -> None:
        guide = (ROOT / "documentation/user_guide/selective-setup.md").read_text(encoding="utf-8")
        self.assertIn("services migration-check --version 6.0.5 --exposure published --listen-address 127.0.0.1", guide)
        self.assertIn("not a detected host version", " ".join(guide.split()))
        self.assertIn("operator_local_unverified", guide)


if __name__ == "__main__":
    unittest.main()
