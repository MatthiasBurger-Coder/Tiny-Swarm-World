from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from tiny_swarm_world.application.ports.method_trace import (
    NullMethodTrace,
    PortMethodTrace,
)
from tiny_swarm_world.application.ports.progress import (
    NullWorkflowProgress,
    PortWorkflowProgress,
    WorkflowProgressEvent,
)
from tiny_swarm_world.application.services.artifacts import ArtifactWorkflowResult
from tiny_swarm_world.application.services.deployment import DeploymentWorkflowResult
from tiny_swarm_world.application.services.platform.workflow_taxonomy import PlatformWorkflowResult
from tiny_swarm_world.application.services.shared import MethodTraceWrapper
from tiny_swarm_world.domain.preflight import InstallationPlan, LiveConsent, PreflightResult


class SetupWorkflowKind(str, Enum):
    RUN = "run"


class SetupWorkflowStatus(str, Enum):
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    FAILED_TO_APPLY = "failed_to_apply"
    FAILED_TO_PREPARE = "failed_to_prepare"
    FAILED_TO_VERIFY = "failed_to_verify"
    REFUSED = "refused"
    RESOURCE_GATED = "resource_gated"


RUN_SETUP_WORKFLOW_TASK = "Run setup workflow"


class SetupPhase(Protocol):
    name: str

    async def run(self) -> object:
        # Protocol declaration; concrete setup phases perform the work.
        pass


@dataclass(frozen=True)
class SetupWorkflowPhase:
    name: str
    runner: Callable[[], object]
    method_trace: PortMethodTrace | None = None
    trace_correlation_id: str | None = None

    async def run(self) -> object:
        return await MethodTraceWrapper(
            self.method_trace,
            component="setup",
            workflow="setup run",
            correlation_id=self.trace_correlation_id,
        ).wrap_async(self._run, method_name="run")()

    async def _run(self) -> object:
        result = self.runner()
        if inspect.isawaitable(result):
            return await result
        return result


@dataclass(frozen=True)
class SetupPhaseResult:
    name: str
    status: str
    result: object

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "result": _result_to_dict(self.result),
            "status": self.status,
        }


@dataclass(frozen=True)
class SetupWorkflowResult:
    kind: SetupWorkflowKind
    status: SetupWorkflowStatus
    message: str
    reason: str
    executed: bool = False
    phase_results: tuple[SetupPhaseResult, ...] = ()

    @property
    def workflow_name(self) -> str:
        return f"setup {self.kind.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "executed": self.executed,
            "message": self.message,
            "phase_results": [phase.to_dict() for phase in self.phase_results],
            "reason": self.reason,
            "status": self.status.value,
            "workflow": self.workflow_name,
        }


class SetupWorkflow:
    def __init__(
        self,
        phases: Sequence[SetupWorkflowPhase] = (),
        live_consent: LiveConsent | None = None,
        progress: PortWorkflowProgress | None = None,
        method_trace: PortMethodTrace | None = None,
        trace_correlation_id: str | None = None,
        installation_plan: InstallationPlan | None = None,
    ):
        self.phases = tuple(phases)
        self.live_consent = live_consent
        self.progress = progress or NullWorkflowProgress()
        self.method_trace = method_trace or NullMethodTrace()
        self.trace_correlation_id = trace_correlation_id
        self.installation_plan = installation_plan

    async def run(self) -> SetupWorkflowResult:
        return await MethodTraceWrapper(
            self.method_trace,
            component="setup",
            workflow=f"setup {SetupWorkflowKind.RUN.value}",
            correlation_id=self.trace_correlation_id,
        ).wrap_async(
            self._run,
            method_name="run",
            result_classifier=_setup_trace_result,
        )()

    async def _run(self) -> SetupWorkflowResult:
        if self.live_consent is None or not self.live_consent.accepted:
            self._report_progress(
                phase="setup",
                target="setup",
                task=RUN_SETUP_WORKFLOW_TASK,
                step="live consent",
                status=SetupWorkflowStatus.REFUSED.value,
                result=SetupWorkflowStatus.REFUSED.value,
                safe_message="Setup run refused because live consent is incomplete.",
                recovery_hint="Run with live consent before retrying.",
            )
            return SetupWorkflowResult(
                kind=SetupWorkflowKind.RUN,
                status=SetupWorkflowStatus.REFUSED,
                message="setup run refused because live infrastructure consent is incomplete.",
                reason="live consent is required before setup orchestration can run",
            )

        try:
            phases = self._ordered_phases()
        except ValueError as exc:
            self._report_progress(
                phase="setup",
                target="setup",
                task=RUN_SETUP_WORKFLOW_TASK,
                step="phase configuration",
                status=SetupWorkflowStatus.BLOCKED.value,
                result=SetupWorkflowStatus.BLOCKED.value,
                safe_message="Setup run is blocked by the installation phase plan.",
                recovery_hint="Repair the installation phase plan before retrying.",
            )
            return SetupWorkflowResult(
                kind=SetupWorkflowKind.RUN,
                status=SetupWorkflowStatus.BLOCKED,
                message="setup run is blocked by the installation phase plan.",
                reason=str(exc),
            )

        if not phases:
            self._report_progress(
                phase="setup",
                target="setup",
                task=RUN_SETUP_WORKFLOW_TASK,
                step="phase configuration",
                status=SetupWorkflowStatus.BLOCKED.value,
                result=SetupWorkflowStatus.BLOCKED.value,
                safe_message="Setup run is blocked until setup phases are configured.",
                recovery_hint="Configure setup phases before retrying.",
            )
            return SetupWorkflowResult(
                kind=SetupWorkflowKind.RUN,
                status=SetupWorkflowStatus.BLOCKED,
                message="setup run is blocked until setup phases are configured.",
                reason="setup orchestration phases are missing",
            )

        phase_results: list[SetupPhaseResult] = []
        for phase in phases:
            _print_phase_progress(phase.name, "START")
            self._report_phase_progress(
                phase_name=phase.name,
                status="started",
                result="pending",
                safe_message="Setup phase started.",
            )
            try:
                phase_output = await phase.run()
            except Exception as exc:
                _print_phase_progress(phase.name, "FAILED", exc.__class__.__name__)
                failed_phase = SetupPhaseResult(
                    name=phase.name,
                    status=SetupWorkflowStatus.FAILED.value,
                    result={
                        "status": SetupWorkflowStatus.FAILED.value,
                        "reason": "setup phase failed",
                    },
                )
                phase_results.append(failed_phase)
                not_run_phase_results = _not_run_phase_results(
                    phases[len(phase_results) :]
                )
                self._report_phase_progress(
                    phase_name=phase.name,
                    status=SetupWorkflowStatus.FAILED.value,
                    result=SetupWorkflowStatus.FAILED.value,
                    safe_message=f"Setup phase failed with {exc.__class__.__name__}.",
                    recovery_hint="Inspect the failed phase evidence before retrying.",
                )
                self._report_not_run_phase_progress(not_run_phase_results)
                self._report_stopped_progress(SetupWorkflowStatus.FAILED.value)
                return SetupWorkflowResult(
                    kind=SetupWorkflowKind.RUN,
                    status=SetupWorkflowStatus.FAILED,
                    message=f"setup run failed during phase '{phase.name}'.",
                    reason=f"phase '{phase.name}' failed with {exc.__class__.__name__}",
                    executed=True,
                    phase_results=(
                        *phase_results,
                        *not_run_phase_results,
                    ),
                )

            try:
                _result_to_dict(phase_output)
            except ValueError:
                _print_phase_progress(phase.name, "FAILED", "unsafe result payload")
                failed_phase = SetupPhaseResult(
                    name=phase.name,
                    status=SetupWorkflowStatus.FAILED.value,
                    result={
                        "status": SetupWorkflowStatus.FAILED.value,
                        "reason": "unsafe phase result payload",
                    },
                )
                phase_results.append(failed_phase)
                not_run_phase_results = _not_run_phase_results(
                    phases[len(phase_results) :]
                )
                self._report_phase_progress(
                    phase_name=phase.name,
                    status=SetupWorkflowStatus.FAILED.value,
                    result=SetupWorkflowStatus.FAILED.value,
                    safe_message="Setup phase result was unsafe.",
                    recovery_hint="Inspect the phase result contract before retrying.",
                )
                self._report_not_run_phase_progress(not_run_phase_results)
                self._report_stopped_progress(SetupWorkflowStatus.FAILED.value)
                return SetupWorkflowResult(
                    kind=SetupWorkflowKind.RUN,
                    status=SetupWorkflowStatus.FAILED,
                    message=f"setup run failed during phase '{phase.name}'.",
                    reason=f"phase '{phase.name}' returned unsafe result payload",
                    executed=True,
                    phase_results=(
                        *phase_results,
                        *not_run_phase_results,
                    ),
                )

            phase_status = _result_status_value(phase_output)
            _print_phase_progress(phase.name, phase_status.upper())
            phase_result = SetupPhaseResult(
                name=phase.name,
                status=phase_status,
                result=phase_output,
            )
            phase_results.append(phase_result)
            self._report_phase_progress(
                phase_name=phase.name,
                status=phase_status,
                result=phase_status,
                safe_message=f"Setup phase {phase_status}.",
            )
            if _is_success_status(phase_status):
                continue

            setup_status = _setup_status_for_phase_status(phase_status)
            not_run_phase_results = _not_run_phase_results(
                phases[len(phase_results) :]
            )
            self._report_not_run_phase_progress(not_run_phase_results)
            self._report_stopped_progress(setup_status.value)
            return SetupWorkflowResult(
                kind=SetupWorkflowKind.RUN,
                status=setup_status,
                message=f"setup run stopped during phase '{phase.name}'.",
                reason=f"phase '{phase.name}' returned {phase_status}",
                executed=True,
                phase_results=(
                    *phase_results,
                    *not_run_phase_results,
                ),
            )

        self._report_progress(
            phase="setup",
            target="setup",
            task=RUN_SETUP_WORKFLOW_TASK,
            step="workflow completed",
            status=SetupWorkflowStatus.COMPLETED.value,
            result=SetupWorkflowStatus.COMPLETED.value,
            safe_message="Setup run completed all configured phases.",
        )
        return SetupWorkflowResult(
            kind=SetupWorkflowKind.RUN,
            status=SetupWorkflowStatus.COMPLETED,
            message="setup run completed all configured phases.",
            reason="preflight, platform, artifacts, deployment, and verification phases completed",
            executed=True,
            phase_results=tuple(phase_results),
        )

    def _ordered_phases(self) -> tuple[SetupWorkflowPhase, ...]:
        if self.installation_plan is None:
            return self.phases
        return self.installation_plan.arrange_workflow_phases(self.phases)

    def _report_phase_progress(
        self,
        *,
        phase_name: str,
        status: str,
        result: str,
        safe_message: str,
        recovery_hint: str | None = None,
    ) -> None:
        self._report_progress(
            phase=phase_name,
            target=phase_name,
            task="Run setup phase",
            step="phase progress",
            status=status,
            result=result,
            safe_message=safe_message,
            recovery_hint=recovery_hint,
        )

    def _report_not_run_phase_progress(
        self,
        phase_results: Sequence[SetupPhaseResult],
    ) -> None:
        for phase_result in phase_results:
            self._report_phase_progress(
                phase_name=phase_result.name,
                status="not_run",
                result="not_run",
                safe_message="Setup phase did not run.",
                recovery_hint="Resolve the earlier stopped phase before retrying.",
            )

    def _report_stopped_progress(self, result: str) -> None:
        self._report_progress(
            phase="setup",
            target="setup",
            task=RUN_SETUP_WORKFLOW_TASK,
            step="workflow stopped",
            status="stopped",
            result=result,
            safe_message="Setup run stopped after a non-success phase.",
            recovery_hint="Resolve the stopped phase before retrying.",
        )

    def _report_progress(
        self,
        *,
        phase: str,
        target: str,
        task: str,
        step: str,
        status: str,
        result: str,
        safe_message: str,
        recovery_hint: str | None = None,
    ) -> None:
        self.progress.report(
            WorkflowProgressEvent(
                workflow=f"setup {SetupWorkflowKind.RUN.value}",
                phase=phase,
                target=target,
                task=task,
                step=step,
                status=status,
                result=result,
                safe_message=safe_message,
                recovery_hint=recovery_hint,
            )
        )


def _print_phase_progress(phase_name: str, status: str, detail: str | None = None) -> None:
    message = f"[setup] {phase_name}: {status}"
    if detail:
        message = f"{message} ({detail})"
    print(message, flush=True)


def _result_status_value(result: object) -> str:
    if isinstance(result, Mapping):
        return str(result.get("status", "unknown")).lower()
    status = getattr(result, "status", None)
    if isinstance(status, Enum):
        return str(status.value)
    if isinstance(status, str):
        return status.lower()
    return "unknown"


def _setup_trace_result(result: SetupWorkflowResult) -> str:
    return result.status.value


def _result_to_dict(result: object) -> dict[str, object]:
    if isinstance(result, Mapping):
        return _safe_mapping_to_dict(result)
    if isinstance(
        result,
        ArtifactWorkflowResult | DeploymentWorkflowResult | PlatformWorkflowResult | PreflightResult,
    ):
        return result.to_dict()
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        raise ValueError("setup phase result type is not allowed")
    return {"status": _result_status_value(result)}


def _safe_mapping_to_dict(result: Mapping[object, object]) -> dict[str, object]:
    payload = {str(key): value for key, value in result.items()}
    _reject_unsafe_payload_keys(payload)
    return payload


def _reject_unsafe_payload_keys(payload: object) -> None:
    forbidden_parts = (
        "command",
        "environment",
        "password",
        "raw",
        "secret",
        "stderr",
        "stdout",
        "token",
    )
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            normalized_key = str(key).lower()
            if any(part in normalized_key for part in forbidden_parts):
                raise ValueError("setup phase result payload contains unsafe keys")
            _reject_unsafe_payload_keys(value)
    if isinstance(payload, list | tuple):
        for item in payload:
            _reject_unsafe_payload_keys(item)


def _is_success_status(status: str) -> bool:
    return status.lower() in {"completed", "passed", "verified"}


def _setup_status_for_phase_status(status: str) -> SetupWorkflowStatus:
    normalized_status = status.lower()
    if normalized_status == "refused":
        return SetupWorkflowStatus.REFUSED
    if normalized_status == "resource_gated":
        return SetupWorkflowStatus.RESOURCE_GATED
    if normalized_status == "blocked":
        return SetupWorkflowStatus.BLOCKED
    if normalized_status == "failed_to_apply":
        return SetupWorkflowStatus.FAILED_TO_APPLY
    if normalized_status == "failed_to_prepare":
        return SetupWorkflowStatus.FAILED_TO_PREPARE
    if normalized_status == "failed_to_verify":
        return SetupWorkflowStatus.FAILED_TO_VERIFY
    return SetupWorkflowStatus.FAILED


def _not_run_phase_results(phases: Sequence[SetupWorkflowPhase]) -> tuple[SetupPhaseResult, ...]:
    return tuple(
        SetupPhaseResult(
            name=phase.name,
            status="not_run",
            result={"status": "not_run", "reason": "previous phase stopped setup run"},
        )
        for phase in phases
    )
