"""Boundary regressions; all probes and persistence are in-memory fakes."""
from dataclasses import replace
import unittest
from unittest.mock import Mock

from tests.application.services.platform.test_preflight_service import (
    _fake_probe, _wsl2_environment, _ResourceInspector,
    _ProjectFilesystemService, _filesystem_assessment,
    _SecretStorageProbe, _secret_storage_inspection,
)
from tiny_swarm_world.application.services.platform.preflight_service import PreflightService
from tiny_swarm_world.domain.preflight import LiveConsent, PreflightResult
from tiny_swarm_world.domain.preflight.completeness import (
    PreflightConstruction, SummaryPersistence,
)
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind
from tiny_swarm_world.domain.preflight.artifact_sources import (
    ArtifactSourceReadiness, ArtifactSourceAttempt, ArtifactSourceStatus,
)


LIVE = LiveConsent(live_flag=True, confirmed=True)


class TestPreflightCompleteness(unittest.IsolatedAsyncioTestCase):
    async def test_custom_omissions_do_not_claim_qualification(self):
        result = await PreflightService(_fake_probe(host_environment=_wsl2_environment())).run()
        self.assertTrue(result.passed)
        self.assertTrue(result.executed_checks_passed)
        self.assertFalse(result.qualified)
        self.assertFalse(result.completeness.collaborators_complete)
        self.assertEqual({"resource_inspector", "project_filesystem", "filesystem_authorizer",
                          "secret_storage", "artifact_source", "evidence_writer"},
                         set(result.completeness.missing_collaborators))
        self.assertEqual(("project_filesystem", "resource_inspector"),
                         result.completeness.applicable_collaborators)
        self.assertEqual(SummaryPersistence.NOT_REQUESTED, result.completeness.summary_persistence)
        self.assertFalse(result.completeness.evidence_complete)

    async def test_standard_omissions_fail_and_keep_probe_failures(self):
        result = await PreflightService(
            _fake_probe(python_version_value="3.11.9"),
            construction=PreflightConstruction.STANDARD_SETUP,
        ).run()
        self.assertFalse(result.passed)
        self.assertEqual({"PYTHON", "PREFLIGHT-COLLABORATORS"},
                         {check.check_id for check in result.failed_checks})
        self.assertFalse(result.executed_checks_passed)

    async def test_missing_live_writer_is_explicit_without_breaking_custom_status(self):
        result = await PreflightService(_fake_probe()).run(LIVE)
        self.assertTrue(result.passed)
        self.assertFalse(result.qualified)
        self.assertEqual("LIVE", result.completeness.scope)
        self.assertEqual(SummaryPersistence.MISSING_WRITER, result.completeness.summary_persistence)
        self.assertFalse(result.completeness.evidence_complete)

    async def test_noncallable_writer_is_missing(self):
        result = await PreflightService(_fake_probe(), evidence_writer=object()).run(LIVE)
        self.assertEqual(SummaryPersistence.MISSING_WRITER, result.completeness.summary_persistence)

    async def test_summary_failures_preserve_existing_failure_and_write_once(self):
        for error in (OSError("private path"), ValueError("private value")):
            with self.subTest(error=type(error).__name__):
                writer = Mock()
                writer.write.side_effect = error
                result = await PreflightService(
                    _fake_probe(python_version_value="3.11.9"), evidence_writer=writer,
                ).run(LIVE)
                self.assertEqual({"PYTHON", "PREFLIGHT-EVIDENCE"},
                                 {check.check_id for check in result.failed_checks})
                self.assertFalse(result.executed_checks_passed)
                self.assertEqual(SummaryPersistence.FAILED, result.completeness.summary_persistence)
                self.assertFalse(result.completeness.evidence_complete)
                self.assertNotIn("private", repr(result.to_dict()))
                writer.write.assert_called_once()

    async def test_evidence_failure_separates_executed_success(self):
        writer = Mock()
        writer.write.side_effect = OSError("unavailable")
        result = await PreflightService(_fake_probe(), evidence_writer=writer).run(LIVE)
        self.assertFalse(result.passed)
        self.assertTrue(result.executed_checks_passed)
        self.assertFalse(result.completeness.evidence_complete)

    async def test_stored_partial_summary_is_not_complete_evidence(self):
        writer = Mock()
        result = await PreflightService(_fake_probe(), evidence_writer=writer).run(LIVE)
        self.assertEqual(SummaryPersistence.STORED, result.completeness.summary_persistence)
        self.assertFalse(result.completeness.evidence_complete)
        payload = writer.write.call_args.args[0]
        self.assertEqual("STORED", payload["completeness"]["summary_persistence"])
        self.assertEqual("NOT_EVALUATED", payload["completeness"]["release_evidence_acceptance"])
        self.assertEqual(result.to_dict()["completeness"], result.to_evidence()["completeness"])

    async def test_malformed_inspector_reports_and_missing_methods_fail(self):
        for inspector in (object(), Mock(inspect=Mock(return_value={}),
                                         memory_pressure=Mock(return_value=None))):
            with self.subTest(inspector=type(inspector).__name__):
                result = await PreflightService(
                    _fake_probe(host_environment=_wsl2_environment()), resource_inspector=inspector,
                ).run()
                failures = {check.check_id: check for check in result.failed_checks}
                self.assertEqual({"RESOURCE-STRUCTURED", "RESOURCE-MEMORY-PRESSURE"}, set(failures))
                self.assertTrue(all(check.evidence["classification"] == "malformed_inspector_output"
                                    for check in failures.values()))
                self.assertFalse(result.completeness.qualification_complete)

    async def test_resource_inspection_is_not_applicable_to_native_linux(self):
        inspector = Mock()
        result = await PreflightService(_fake_probe(), resource_inspector=inspector).run()
        self.assertNotIn("resource_inspector", result.completeness.applicable_collaborators)
        inspector.inspect.assert_not_called()
        inspector.memory_pressure.assert_not_called()

    async def test_missing_authorizer_blocks_live_override_before_runtime(self):
        probe = _fake_probe(host_environment=_wsl2_environment())
        probe.runtime_readiness = Mock(side_effect=AssertionError("must not run"))
        evaluator = _ProjectFilesystemService(_filesystem_assessment(
            ProjectFilesystemKind.WINDOWS_MOUNTED, "/mnt/d/private/project", allow_override=True,
        ))
        result = await PreflightService(
            probe, project_filesystem_evaluator=evaluator, project_path="/mnt/d/private/project",
            allow_wsl_windows_filesystem=True,
        ).run(LIVE)
        self.assertFalse(result.passed)
        self.assertEqual("HOST-FILESYSTEM-AUTHORIZER", result.failed_checks[0].check_id)
        self.assertFalse(any(check.check_id.startswith("RUNTIME-") for check in result.checks))
        self.assertEqual([], evaluator.calls)

    async def test_missing_authorizer_does_not_block_static_override_evaluation(self):
        evaluator = _ProjectFilesystemService(_filesystem_assessment(
            ProjectFilesystemKind.WINDOWS_MOUNTED, "/mnt/d/private/project", allow_override=True,
        ))
        result = await PreflightService(
            _fake_probe(host_environment=_wsl2_environment()),
            project_filesystem_evaluator=evaluator, project_path="/mnt/d/private/project",
            allow_wsl_windows_filesystem=True,
        ).run()
        self.assertTrue(result.passed)
        self.assertIn("filesystem_authorizer", result.completeness.missing_collaborators)
        self.assertEqual(1, len(evaluator.calls))

    async def test_unexpected_writer_and_inspector_defects_propagate(self):
        writer = Mock()
        writer.write.side_effect = RuntimeError("defect")
        with self.assertRaises(RuntimeError):
            await PreflightService(_fake_probe(), evidence_writer=writer).run(LIVE)
        for method in ("inspect", "memory_pressure"):
            inspector = Mock(wraps=_ResourceInspector())
            getattr(inspector, method).side_effect = RuntimeError("defect")
            with self.subTest(method=method), self.assertRaises(RuntimeError):
                await PreflightService(_fake_probe(host_environment=_wsl2_environment()),
                                       resource_inspector=inspector).run()

    async def test_complete_standard_public_run_has_independent_evidence_state(self):
        filesystem = _ProjectFilesystemService(_filesystem_assessment(
            ProjectFilesystemKind.WSL_LINUX, "/project", allow_override=False,
        ))
        source = Mock()
        source.check.return_value = ArtifactSourceReadiness("direct", "fixture", (
            ArtifactSourceAttempt("fixture", "packages", ArtifactSourceStatus.READY, "reachable"),
        ))
        writer = Mock()
        result = await PreflightService(
            _fake_probe(host_environment=_wsl2_environment()),
            resource_inspector=_ResourceInspector(),
            project_filesystem_evaluator=filesystem, project_filesystem_authorizer=filesystem,
            project_path="/project", secret_storage_probe=_SecretStorageProbe(
                _secret_storage_inspection(ProjectFilesystemKind.WSL_LINUX)),
            secret_storage_path="/secret", artifact_source_readiness=source,
            evidence_writer=writer, construction=PreflightConstruction.STANDARD_SETUP,
        ).run(LIVE)
        self.assertTrue(result.passed)
        self.assertTrue(result.executed_checks_passed)
        self.assertTrue(result.qualified)
        self.assertTrue(result.completeness.evidence_complete)
        self.assertEqual((), result.completeness.missing_collaborators)
        self.assertEqual("LIVE", result.completeness.scope)
        self.assertEqual("NOT_EVALUATED", result.to_dict()["completeness"]["release_evidence_acceptance"])
        writer.write.assert_called_once()
        source.check.assert_called_once()

    async def test_full_coverage_can_store_failed_checks_without_claiming_release_success(self):
        # Use the result helper to isolate persistence from external probe execution.
        service = PreflightService(
            _fake_probe(), resource_inspector=_ResourceInspector(),
            project_filesystem_evaluator=Mock(), project_filesystem_authorizer=Mock(),
            project_path="/project", secret_storage_probe=Mock(), secret_storage_path="/secret",
            artifact_source_readiness=Mock(), evidence_writer=Mock(),
            construction=PreflightConstruction.STANDARD_SETUP,
        )
        failed = await PreflightService(_fake_probe(python_version_value="3.11.9")).run()
        result = service._result(failed.checks, write_evidence=True)
        self.assertFalse(result.passed)
        self.assertTrue(result.completeness.collaborators_complete)
        self.assertTrue(result.completeness.evidence_complete)
        self.assertEqual("NOT_EVALUATED", result.to_evidence()["completeness"]["release_evidence_acceptance"])
        malformed = replace(failed.checks[0], evidence={"classification": "malformed_inspector_output"})
        result = service._result((malformed,), write_evidence=True)
        self.assertFalse(result.completeness.evidence_complete)

    def test_unassessed_direct_result_never_claims_complete_qualification(self):
        result = PreflightResult(())
        self.assertTrue(result.passed)
        self.assertFalse(result.qualified)
        self.assertFalse(result.completeness.evidence_complete)
        with self.assertRaises(TypeError):
            result.completeness.collaborators["secret_storage"] = True
