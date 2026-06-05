import unittest
from contextlib import redirect_stdout
from io import StringIO
from tests.support.sonar_safe_literals import sensitive_assignment

from tiny_swarm_world.application.ports.method_trace import (
    MethodTraceEvent,
    PortMethodTrace,
)
from tiny_swarm_world.application.ports.progress import (
    PortWorkflowProgress,
    WorkflowProgressEvent,
)
from tiny_swarm_world.application.services.artifacts import (
    ArtifactWorkflowKind,
    ArtifactWorkflowResult,
    ArtifactWorkflowStatus,
)
from tiny_swarm_world.application.services.deployment import (
    DeploymentWorkflowKind,
    DeploymentWorkflowResult,
    DeploymentWorkflowStatus,
)
from tiny_swarm_world.application.services.setup import (
    SetupWorkflow,
    SetupWorkflowKind,
    SetupWorkflowPhase,
    SetupWorkflowStatus,
)
from tiny_swarm_world.application.services.platform.workflow_taxonomy import (
    PlatformWorkflowKind,
    PlatformWorkflowResult,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.preflight import (
    LIVE_CONSENT_ENVIRONMENT_VALUE,
    LIVE_CONSENT_PHRASE,
    LiveConsent,
    PreflightCategory,
    PreflightCheck,
    PreflightResult,
    PreflightSeverity,
    PreflightStatus,
)


class TestSetupWorkflow(unittest.IsolatedAsyncioTestCase):
    async def test_blocks_when_no_phases_are_configured(self):
        result = await SetupWorkflow(live_consent=_accepted_live_consent()).run()

        self.assertEqual(SetupWorkflowKind.RUN, result.kind)
        self.assertEqual(SetupWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual("setup run", result.workflow_name)

    async def test_refuses_without_accepted_live_consent(self):
        calls: list[str] = []
        result = await SetupWorkflow(
            (SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),)
        ).run()

        self.assertEqual(SetupWorkflowStatus.REFUSED, result.status)
        self.assertFalse(result.executed)
        self.assertEqual([], calls)

    async def test_completes_all_configured_phases_in_order(self):
        calls: list[str] = []
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),
                SetupWorkflowPhase("platform init", lambda: _completed_result("platform init", calls)),
            ),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.COMPLETED, result.status)
        self.assertTrue(result.executed)
        self.assertEqual(["preflight", "platform init"], calls)
        self.assertEqual(["preflight", "platform init"], [phase.name for phase in result.phase_results])

    async def test_prints_progress_for_each_configured_phase(self):
        calls: list[str] = []
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),
                SetupWorkflowPhase("platform init", lambda: _completed_result("platform init", calls)),
            ),
            live_consent=_accepted_live_consent(),
        )
        output = StringIO()

        with redirect_stdout(output):
            await workflow.run()

        self.assertIn("[setup] preflight: START", output.getvalue())
        self.assertIn("[setup] preflight: COMPLETED", output.getvalue())
        self.assertIn("[setup] platform init: START", output.getvalue())
        self.assertIn("[setup] platform init: COMPLETED", output.getvalue())

    async def test_reports_progress_for_refused_setup(self):
        progress = _RecordingProgress()
        result = await SetupWorkflow(
            (SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", [])),),
            progress=progress,
        ).run()

        self.assertEqual(SetupWorkflowStatus.REFUSED, result.status)
        self.assertEqual(
            [("setup", "live consent", "refused", "refused")],
            progress.summary(),
        )

    async def test_reports_method_trace_for_workflow_and_phase_completion(self):
        trace = _RecordingMethodTrace()
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase(
                    "preflight",
                    lambda: _completed_result("preflight", []),
                    method_trace=trace,
                    trace_correlation_id="trace-setup",
                ),
            ),
            live_consent=_accepted_live_consent(),
            method_trace=trace,
            trace_correlation_id="trace-setup",
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(
            [
                ("SetupWorkflow", "run", "entered", "pending", None),
                ("SetupWorkflowPhase", "run", "entered", "pending", None),
                ("SetupWorkflowPhase", "run", "returned", "completed", None),
                ("SetupWorkflow", "run", "returned", "completed", None),
            ],
            trace.summary(),
        )
        self.assertEqual({"trace-setup"}, {event.correlation_id for event in trace.events})

    async def test_reports_method_trace_for_phase_exception_before_conversion(self):
        trace = _RecordingMethodTrace()
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase(
                    "preflight",
                    _raise_secret_error,
                    method_trace=trace,
                    trace_correlation_id="trace-setup",
                ),
            ),
            live_consent=_accepted_live_consent(),
            method_trace=trace,
            trace_correlation_id="trace-setup",
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.FAILED, result.status)
        self.assertIn(
            ("SetupWorkflowPhase", "run", "raised", "failed", "RuntimeError"),
            trace.summary(),
        )
        self.assertEqual(
            ("SetupWorkflow", "run", "returned", "failed", None),
            trace.summary()[-1],
        )
        self.assertNotIn(sensitive_assignment(), str(trace.events[-2].to_dict()))

    async def test_reports_progress_for_blocked_setup_without_phases(self):
        progress = _RecordingProgress()

        result = await SetupWorkflow(
            live_consent=_accepted_live_consent(),
            progress=progress,
        ).run()

        self.assertEqual(SetupWorkflowStatus.BLOCKED, result.status)
        self.assertEqual(
            [("setup", "phase configuration", "blocked", "blocked")],
            progress.summary(),
        )

    async def test_reports_progress_for_each_phase_and_final_completed(self):
        calls: list[str] = []
        progress = _RecordingProgress()
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),
                SetupWorkflowPhase("platform init", lambda: _completed_result("platform init", calls)),
            ),
            live_consent=_accepted_live_consent(),
            progress=progress,
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(
            [
                ("preflight", "phase progress", "started", "pending"),
                ("preflight", "phase progress", "completed", "completed"),
                ("platform init", "phase progress", "started", "pending"),
                ("platform init", "phase progress", "completed", "completed"),
                ("setup", "workflow completed", "completed", "completed"),
            ],
            progress.summary(),
        )

    async def test_stops_on_blocked_phase_without_running_later_phases(self):
        calls: list[str] = []
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),
                SetupWorkflowPhase("artifacts prepare", lambda: _blocked_result("artifacts prepare", calls)),
                SetupWorkflowPhase("deployment apply", lambda: _completed_result("deployment apply", calls)),
            ),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.BLOCKED, result.status)
        self.assertTrue(result.executed)
        self.assertEqual(["preflight", "artifacts prepare"], calls)
        self.assertEqual("phase 'artifacts prepare' returned blocked", result.reason)
        self.assertEqual(3, len(result.phase_results))
        self.assertEqual("not_run", result.phase_results[2].status)

    async def test_reports_stopped_and_downstream_not_run_progress(self):
        calls: list[str] = []
        progress = _RecordingProgress()
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),
                SetupWorkflowPhase("artifacts prepare", lambda: _blocked_result("artifacts prepare", calls)),
                SetupWorkflowPhase("deployment apply", lambda: _completed_result("deployment apply", calls)),
            ),
            live_consent=_accepted_live_consent(),
            progress=progress,
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.BLOCKED, result.status)
        self.assertEqual(
            [
                ("preflight", "phase progress", "started", "pending"),
                ("preflight", "phase progress", "completed", "completed"),
                ("artifacts prepare", "phase progress", "started", "pending"),
                ("artifacts prepare", "phase progress", "blocked", "blocked"),
                ("deployment apply", "phase progress", "not_run", "not_run"),
                ("setup", "workflow stopped", "stopped", "blocked"),
            ],
            progress.summary(),
        )

    async def test_failed_preflight_stops_before_platform_init_phase(self):
        calls: list[str] = []
        progress = _RecordingProgress()
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _failed_preflight_result(calls)),
                SetupWorkflowPhase("platform init", lambda: _completed_result("platform init", calls)),
            ),
            live_consent=_accepted_live_consent(),
            progress=progress,
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.FAILED, result.status)
        self.assertEqual(["preflight"], calls)
        self.assertEqual("phase 'preflight' returned failed", result.reason)
        self.assertEqual("not_run", result.phase_results[1].status)
        self.assertEqual(
            [
                ("preflight", "phase progress", "started", "pending"),
                ("preflight", "phase progress", "failed", "failed"),
                ("platform init", "phase progress", "not_run", "not_run"),
                ("setup", "workflow stopped", "stopped", "failed"),
            ],
            progress.summary(),
        )

    async def test_provider_blocked_platform_init_marks_downstream_phases_not_run(self):
        calls: list[str] = []
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),
                SetupWorkflowPhase("platform init", lambda: _provider_blocked_platform_init(calls)),
                SetupWorkflowPhase("platform reconcile", lambda: _completed_result("platform reconcile", calls)),
                SetupWorkflowPhase("deployment bootstrap", lambda: _completed_result("deployment bootstrap", calls)),
            ),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()
        payload = result.to_dict()

        self.assertEqual(SetupWorkflowStatus.BLOCKED, result.status)
        self.assertEqual(["preflight", "platform init"], calls)
        self.assertEqual("phase 'platform init' returned blocked", result.reason)
        self.assertEqual(
            ["completed", "blocked", "not_run", "not_run"],
            [phase["status"] for phase in payload["phase_results"]],
        )
        self.assertEqual(
            "provider_selection_blocked",
            payload["phase_results"][1]["result"]["verification_results"][0]["evidence"]["reason"],
        )
        self.assertNotIn("multipass_legacy", repr(payload))

    async def test_redacted_platform_init_failure_stops_before_downstream_phases(self):
        calls: list[str] = []
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),
                SetupWorkflowPhase("platform init", lambda: _failed_platform_init(calls)),
                SetupWorkflowPhase("deployment apply", lambda: _completed_result("deployment apply", calls)),
            ),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()
        payload = result.to_dict()

        self.assertEqual(SetupWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual(["preflight", "platform init"], calls)
        self.assertEqual("phase 'platform init' returned failed_to_apply", result.reason)
        self.assertEqual("not_run", result.phase_results[2].status)
        self.assertNotIn("stdout", str(payload).lower())
        self.assertNotIn("stderr", str(payload).lower())
        self.assertNotIn("cannot connect to the provider socket", str(payload).lower())

    async def test_sanitizes_phase_exceptions(self):
        progress = _RecordingProgress()
        workflow = SetupWorkflow(
            (SetupWorkflowPhase("deployment apply", _raise_secret_error),),
            live_consent=_accepted_live_consent(),
            progress=progress,
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.FAILED, result.status)
        self.assertEqual("phase 'deployment apply' failed with RuntimeError", result.reason)
        self.assertNotIn("secret", result.reason)
        self.assertEqual(
            [
                ("deployment apply", "phase progress", "started", "pending"),
                ("deployment apply", "phase progress", "failed", "failed"),
                ("setup", "workflow stopped", "stopped", "failed"),
            ],
            progress.summary(),
        )

    async def test_to_dict_preserves_phase_statuses(self):
        workflow = SetupWorkflow(
            (SetupWorkflowPhase("artifacts prepare", lambda: _blocked_result("artifacts prepare", [])),),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()

        payload = result.to_dict()
        self.assertEqual("setup run", payload["workflow"])
        self.assertEqual("blocked", payload["phase_results"][0]["status"])

    async def test_to_dict_preserves_platform_verification_results(self):
        verification = VerificationResult(
            target_id="platform:init:lxc-nodes",
            status=VerificationStatus.BLOCKED,
            message="Command-backed verification is not configured.",
            evidence={"reason": "command_backed_verification_missing"},
        )
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase(
                    "platform init",
                    lambda: PlatformWorkflowResult(
                        kind=PlatformWorkflowKind.INIT,
                        status=PlatformWorkflowStatus.BLOCKED,
                        message="init workflow blocked.",
                        executed=False,
                        verification_results=(verification,),
                    ),
                ),
            ),
            live_consent=_accepted_live_consent(),
        )

        payload = (await workflow.run()).to_dict()

        phase_payload = payload["phase_results"][0]["result"]
        self.assertEqual("platform init", phase_payload["workflow"])
        self.assertEqual("platform:init:lxc-nodes", phase_payload["verification_results"][0]["target_id"])

    async def test_preserves_failed_to_verify_as_distinct_terminal_status(self):
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase(
                    "deployment verify",
                    lambda: DeploymentWorkflowResult(
                        kind=DeploymentWorkflowKind.VERIFY,
                        status=DeploymentWorkflowStatus.FAILED_TO_VERIFY,
                        message="deployment verify failed.",
                        reason="observed service readiness failed",
                        executed=True,
                    ),
                ),
            ),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual("phase 'deployment verify' returned failed_to_verify", result.reason)

    async def test_stops_after_failed_bootstrap_verification_without_running_later_phases(self):
        calls: list[str] = []
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),
                SetupWorkflowPhase(
                    "deployment bootstrap",
                    lambda: _failed_deployment_bootstrap(calls),
                ),
                SetupWorkflowPhase("artifacts prepare", lambda: _completed_result("artifacts prepare", calls)),
            ),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual(["preflight", "deployment bootstrap"], calls)
        self.assertEqual("phase 'deployment bootstrap' returned failed_to_verify", result.reason)
        self.assertEqual("not_run", result.phase_results[2].status)

    async def test_preserves_deployment_apply_failure_as_failed_to_apply(self):
        calls: list[str] = []
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase("preflight", lambda: _completed_result("preflight", calls)),
                SetupWorkflowPhase("deployment apply", lambda: _failed_deployment_apply(calls)),
                SetupWorkflowPhase("deployment verify", lambda: _completed_result("deployment verify", calls)),
            ),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()

        self.assertEqual(SetupWorkflowStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual(["preflight", "deployment apply"], calls)
        self.assertEqual("phase 'deployment apply' returned failed_to_apply", result.reason)
        self.assertEqual("failed_to_apply", result.phase_results[1].status)
        self.assertEqual("not_run", result.phase_results[2].status)

    async def test_rejects_unknown_phase_payload_types_as_failed_status(self):
        class UnsafeResult:
            status = "completed"

            def to_dict(self) -> dict[str, object]:
                return {"status": "completed", "stdout": "secret"}

        workflow = SetupWorkflow(
            (SetupWorkflowPhase("unsafe", lambda: UnsafeResult()),),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()
        payload = result.to_dict()

        self.assertEqual(SetupWorkflowStatus.FAILED, result.status)
        self.assertEqual("phase 'unsafe' returned unsafe result payload", result.reason)
        self.assertNotIn("stdout", str(payload))

    async def test_rejects_unsafe_mapping_payload_keys_as_failed_status(self):
        workflow = SetupWorkflow(
            (
                SetupWorkflowPhase(
                    "unsafe",
                    lambda: {"status": "completed", "stdout": "secret"},
                ),
            ),
            live_consent=_accepted_live_consent(),
        )

        result = await workflow.run()
        payload = result.to_dict()

        self.assertEqual(SetupWorkflowStatus.FAILED, result.status)
        self.assertEqual("phase 'unsafe' returned unsafe result payload", result.reason)
        self.assertNotIn("stdout", str(payload))


def _completed_result(name: str, calls: list[str]) -> ArtifactWorkflowResult:
    calls.append(name)
    return ArtifactWorkflowResult(
        kind=ArtifactWorkflowKind.VERIFY,
        status=ArtifactWorkflowStatus.COMPLETED,
        message=f"{name} completed.",
        reason="completed",
        executed=True,
    )


def _blocked_result(name: str, calls: list[str]) -> ArtifactWorkflowResult:
    calls.append(name)
    return ArtifactWorkflowResult(
        kind=ArtifactWorkflowKind.PREPARE,
        status=ArtifactWorkflowStatus.BLOCKED,
        message=f"{name} blocked.",
        reason="blocked",
    )


def _failed_deployment_bootstrap(calls: list[str]) -> DeploymentWorkflowResult:
    calls.append("deployment bootstrap")
    return DeploymentWorkflowResult(
        kind=DeploymentWorkflowKind.BOOTSTRAP,
        status=DeploymentWorkflowStatus.FAILED_TO_VERIFY,
        message="deployment bootstrap failed.",
        reason="verification failed for deployment:portainer-admin-access",
        executed=True,
    )


def _failed_deployment_apply(calls: list[str]) -> DeploymentWorkflowResult:
    calls.append("deployment apply")
    return DeploymentWorkflowResult(
        kind=DeploymentWorkflowKind.APPLY,
        status=DeploymentWorkflowStatus.FAILED_TO_APPLY,
        message="deployment apply failed.",
        reason="apply failed with RuntimeError",
        executed=True,
    )


def _failed_preflight_result(calls: list[str]) -> PreflightResult:
    calls.append("preflight")
    return PreflightResult(
        (
            PreflightCheck(
                check_id="PROVIDER-LXC-DAEMON",
                category=PreflightCategory.DEPENDENCY,
                status=PreflightStatus.FAILED,
                severity=PreflightSeverity.MANDATORY,
                message="LXC provider daemon is not reachable.",
                remediation="Repair LXD/Incus daemon access and rerun setup.",
                evidence={"classification": "provider_daemon_unavailable"},
            ),
        )
    )


def _failed_platform_init(calls: list[str]) -> PlatformWorkflowResult:
    calls.append("platform init")
    return PlatformWorkflowResult(
        kind=PlatformWorkflowKind.INIT,
        status=PlatformWorkflowStatus.FAILED_TO_APPLY,
        message="init apply failed for platform:init:lxc-nodes.",
        executed=True,
        verification_results=(
            VerificationResult(
                target_id="platform:init:lxc-nodes",
                status=VerificationStatus.FAILED_TO_APPLY,
                message="Apply failed for platform:init:lxc-nodes: CommandExecutionFailed",
                evidence={"phase": "apply", "return_code": "2"},
            ),
        ),
    )


def _provider_blocked_platform_init(calls: list[str]) -> PlatformWorkflowResult:
    calls.append("platform init")
    return PlatformWorkflowResult(
        kind=PlatformWorkflowKind.INIT,
        status=PlatformWorkflowStatus.BLOCKED,
        message="init workflow blocked by provider selection before mutation.",
        executed=False,
        verification_results=(
            VerificationResult(
                target_id="platform:node-provider:lxc_native",
                status=VerificationStatus.BLOCKED,
                message="Provider selection blocked platform mutation.",
                evidence={
                    "phase": "pre_apply",
                    "reason": "provider_selection_blocked",
                    "requested_provider": "lxc_native",
                    "selected_provider": "lxc_native",
                    "selection_status": "blocked",
                    "backend_status": "missing",
                },
            ),
        ),
    )


def _raise_secret_error() -> object:
    raise RuntimeError(sensitive_assignment())


class _RecordingProgress(PortWorkflowProgress):
    def __init__(self) -> None:
        self.events: list[WorkflowProgressEvent] = []

    def report(self, event: WorkflowProgressEvent) -> None:
        self.events.append(event)

    def summary(self) -> list[tuple[str, str, str, str]]:
        return [
            (event.phase, event.step, event.status, event.result)
            for event in self.events
        ]


class _RecordingMethodTrace(PortMethodTrace):
    def __init__(self) -> None:
        self.events: list[MethodTraceEvent] = []

    def report(self, event: MethodTraceEvent) -> None:
        self.events.append(event)

    def summary(self) -> list[tuple[str, str, str, str | None, str | None]]:
        return [
            (
                event.class_name,
                event.method_name,
                event.status,
                event.safe_result,
                event.exception_type,
            )
            for event in self.events
        ]


def _accepted_live_consent() -> LiveConsent:
    return LiveConsent(
        live_flag=True,
        environment_value=LIVE_CONSENT_ENVIRONMENT_VALUE,
        typed_phrase=LIVE_CONSENT_PHRASE,
    )
