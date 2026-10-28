"""Selective CLI consent, dispatch and metadata failure regressions with fake runtime."""
import contextlib
import asyncio
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.application.services.setup.workflow import SetupWorkflowKind, SetupWorkflowResult, SetupWorkflowStatus
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure.adapters.cli.consent import _live_consent_for_workflow
from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args
from tiny_swarm_world.infrastructure.adapters.cli.selective_setup import run_selective_setup
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tests.application.services.test_lifecycle import adoption_fixture

MODULE = "tiny_swarm_world.infrastructure.adapters.cli.selective_setup"
ROOT = Path(__file__).resolve().parents[1]


class SelectiveCliTests(unittest.IsolatedAsyncioTestCase):
    def test_apply_argument_and_consent_boundaries(self):
        for command in (["setup", "run", "--minimal"], ["services", "add", "--services", "swagger"],
                        ["services", "remove", "--services", "swagger", "--live", "--approve-live"],
                        ["setup", "run", "--minimal", "--preview", "--live"],
                        ["setup", "run", "--services", "swagger,,jenkins", "--live"]):
            with self.subTest(command=command), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                parse_args(command)
            self.assertEqual(caught.exception.code, 2)
        for command in (["setup", "run", "--minimal", "--live"], ["services", "add", "--services", "swagger", "--live"]):
            args = parse_args(command)
            with patch("builtins.input", return_value="no"), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as caught:
                _live_consent_for_workflow(args.workflow, args)
            self.assertEqual(caught.exception.code, 2)
        args = parse_args(["services", "add", "--services", "swagger", "--live", "--approve-live"])
        self.assertTrue(_live_consent_for_workflow(args.workflow, args).accepted)

    async def test_add_uses_existing_setup_and_only_commits_after_success(self):
        for outcome in (SetupWorkflowStatus.COMPLETED, SetupWorkflowStatus.FAILED_TO_APPLY):
            with self.subTest(outcome=outcome):
                await self._exercise(outcome)

    async def test_failed_manifest_write_reports_partial_runtime_success(self):
        await self._exercise(SetupWorkflowStatus.COMPLETED, commit_error=True)

    async def _exercise(self, outcome, commit_error=False):
        with TemporaryDirectory() as directory:
            lifecycle = InstallationLifecycleService(JsonManifestRepository(Path(directory) / "state.json"), NativeComponentCatalog(ROOT))
            lifecycle.manifests.save(adoption_fixture(lifecycle.catalog.load()), expected_token=None)
            args = parse_args(["services", "add", "--services", "swagger", "--live", "--approve-live", "--json"])
            result = SetupWorkflowResult(SetupWorkflowKind.RUN, outcome, "fixture", "fixture", executed=True)
            with patch(MODULE + ".composition.build_installation_lifecycle_service", return_value=lifecycle), \
                 patch(MODULE + ".composition.prepare_setup_selection_state", new_callable=AsyncMock) as admission, \
                 patch(MODULE + ".composition.complete_setup_selection_state", new_callable=AsyncMock) as observation, \
                 patch(MODULE + ".composition.run_setup_with_terminal_status", new_callable=AsyncMock, return_value=result) as setup:
                state = Mock()
                events = Mock()
                events.attach_mock(setup, "runtime")
                events.attach_mock(observation, "observe")
                events.attach_mock(state.commit, "commit")
                admission.return_value = state
                if commit_error:
                    state.commit.side_effect = LifecycleStateError("fixture failure")
                actual = await run_selective_setup(args, LiveConsent(True, True))
                passed_plan = setup.call_args.kwargs["selection_plan"]
                self.assertIn("swagger", passed_plan.resolved_services)
                self.assertEqual(setup.call_args.args[1], "run")
                admission.assert_awaited_once()
                if outcome is SetupWorkflowStatus.COMPLETED:
                    observation.assert_awaited_once()
                    state.commit.assert_called_once()
                    self.assertEqual([call[0] for call in events.mock_calls], ["runtime", "observe", "commit"])
                else:
                    observation.assert_not_awaited()
                    state.commit.assert_not_called()
                if commit_error:
                    self.assertEqual(actual.reason, "selection_persistence_failed")
                    self.assertEqual(actual.operation_result.outcome.value, "partial")
                    self.assertEqual(actual.status, SetupWorkflowStatus.FAILED_TO_VERIFY)
                else:
                    self.assertIs(actual, result)

    async def test_observation_failure_reports_partial_runtime_without_commit_or_secret_leak(self):
        for failure in (LifecycleStateError("SECRET_SENTINEL"), TimeoutError("SECRET_SENTINEL")):
            with self.subTest(failure_type=type(failure).__name__), TemporaryDirectory() as directory:
                lifecycle = InstallationLifecycleService(JsonManifestRepository(Path(directory) / "state.json"), NativeComponentCatalog(ROOT))
                lifecycle.manifests.save(adoption_fixture(lifecycle.catalog.load()), expected_token=None)
                before = lifecycle.manifests.path.read_bytes()
                args = parse_args(["services", "add", "--services", "swagger", "--live", "--approve-live", "--json"])
                completed = SetupWorkflowResult(SetupWorkflowKind.RUN, SetupWorkflowStatus.COMPLETED, "verified runtime", "fixture", executed=True)
                state = Mock()
                with patch(MODULE + ".composition.build_installation_lifecycle_service", return_value=lifecycle), \
                     patch(MODULE + ".composition.prepare_setup_selection_state", new_callable=AsyncMock, return_value=state), \
                     patch(MODULE + ".composition.run_setup_with_terminal_status", new_callable=AsyncMock, return_value=completed), \
                     patch(MODULE + ".composition.complete_setup_selection_state", new_callable=AsyncMock, side_effect=failure):
                    result = await run_selective_setup(args, LiveConsent(True, True))
                self.assertEqual(result.status, SetupWorkflowStatus.FAILED_TO_VERIFY)
                self.assertEqual(result.reason, "selection_observation_failed")
                self.assertEqual(result.operation_result.outcome.value, "partial")
                self.assertEqual(result.operation_result.completed_operations, ("setup.runtime",))
                self.assertEqual(result.operation_result.pending_operations, ("selection.persist",))
                self.assertNotIn("SECRET_SENTINEL", str(result.to_dict()))
                self.assertEqual(lifecycle.manifests.path.read_bytes(), before)
                state.commit.assert_not_called()

    async def test_observation_cancellation_propagates_without_metadata_commit(self):
        with TemporaryDirectory() as directory:
            lifecycle = InstallationLifecycleService(JsonManifestRepository(Path(directory) / "state.json"), NativeComponentCatalog(ROOT))
            lifecycle.manifests.save(adoption_fixture(lifecycle.catalog.load()), expected_token=None)
            args = parse_args(["services", "add", "--services", "swagger", "--live", "--approve-live", "--json"])
            completed = SetupWorkflowResult(SetupWorkflowKind.RUN, SetupWorkflowStatus.COMPLETED, "verified runtime", "fixture", executed=True)
            state = Mock()
            with patch(MODULE + ".composition.build_installation_lifecycle_service", return_value=lifecycle), \
                 patch(MODULE + ".composition.prepare_setup_selection_state", new_callable=AsyncMock, return_value=state), \
                 patch(MODULE + ".composition.run_setup_with_terminal_status", new_callable=AsyncMock, return_value=completed), \
                 patch(MODULE + ".composition.complete_setup_selection_state", new_callable=AsyncMock, side_effect=asyncio.CancelledError()):
                with self.assertRaises(asyncio.CancelledError):
                    await run_selective_setup(args, LiveConsent(True, True))
            state.commit.assert_not_called()

    async def test_missing_consent_never_loads_state_or_builds_runtime(self):
        args = parse_args(["setup", "run", "--minimal", "--live"])
        with patch(MODULE + ".composition.build_installation_lifecycle_service") as load:
            with self.assertRaises(ValueError):
                await run_selective_setup(args, LiveConsent(True, False))
            load.assert_not_called()
