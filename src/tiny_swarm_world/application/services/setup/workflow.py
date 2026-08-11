from __future__ import annotations

import asyncio
from contextlib import suppress
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
from tiny_swarm_world.application.services.platform.workflow.results import PlatformWorkflowResult
from tiny_swarm_world.application.services.shared import MethodTraceWrapper
from tiny_swarm_world.domain.preflight import (
    HostPreparationResult,
    InstallationPlan,
    LiveConsent,
    PreflightResult,
)


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
    TIMED_OUT = "timed_out"


RUN_SETUP_WORKFLOW_TASK = "Run setup workflow"
DEFAULT_SETUP_MAX_CONCURRENCY = 2


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
class _SetupPhaseGroup:
    group_id: str
    phases: tuple[SetupWorkflowPhase, ...]
    maximum_concurrency: int


@dataclass(frozen=True)
class _SetupPhaseExecution:
    phase_result: "SetupPhaseResult"
    terminal_reason: str | None = None
    completion_message: str = "Setup phase completed."


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
class SetupPhaseGroupResult:
    group_id: str
    phase_names: tuple[str, ...]
    status: str
    maximum_concurrency: int
    duration_seconds: float

    def to_dict(self) -> dict[str, object]:
        return {
            "duration_seconds": self.duration_seconds,
            "group_id": self.group_id,
            "maximum_concurrency": self.maximum_concurrency,
            "phase_names": list(self.phase_names),
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
    phase_group_results: tuple[SetupPhaseGroupResult, ...] = ()

    @property
    def workflow_name(self) -> str:
        return f"setup {self.kind.value}"

    def to_dict(self) -> dict[str, object]:
        return {
            "executed": self.executed,
            "message": self.message,
            "phase_group_results": [
                group.to_dict() for group in self.phase_group_results
            ],
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
        timeout_seconds: float | None = None,
        heartbeat_interval_seconds: float | None = None,
        max_concurrency: int = DEFAULT_SETUP_MAX_CONCURRENCY,
    ):
        self.phases = tuple(phases)
        self.live_consent = live_consent
        self.progress = progress or NullWorkflowProgress()
        self.method_trace = method_trace or NullMethodTrace()
        self.trace_correlation_id = trace_correlation_id
        self.installation_plan = installation_plan
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ValueError("Setup workflow timeout must be positive.")
        self.timeout_seconds = timeout_seconds
        if heartbeat_interval_seconds is not None and heartbeat_interval_seconds <= 0:
            raise ValueError("Setup workflow heartbeat interval must be positive.")
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        if not isinstance(max_concurrency, int) or max_concurrency <= 0:
            raise ValueError("Setup workflow maximum concurrency must be positive.")
        self.max_concurrency = max_concurrency

    async def run(self) -> SetupWorkflowResult:
        runner = MethodTraceWrapper(
            self.method_trace,
            component="setup",
            workflow=f"setup {SetupWorkflowKind.RUN.value}",
            correlation_id=self.trace_correlation_id,
        ).wrap_async(self._run, method_name="run", result_classifier=_setup_trace_result)
        try:
            if self.timeout_seconds is None:
                return await runner()
            return await asyncio.wait_for(runner(), timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            self._report_progress(
                phase="setup",
                target="setup",
                task=RUN_SETUP_WORKFLOW_TASK,
                step="outer timeout",
                status=SetupWorkflowStatus.TIMED_OUT.value,
                result=SetupWorkflowStatus.TIMED_OUT.value,
                safe_message="Setup workflow exceeded its configured outer timeout.",
                recovery_hint="Inspect read-only process diagnostics before retrying.",
            )
            return SetupWorkflowResult(
                kind=SetupWorkflowKind.RUN,
                status=SetupWorkflowStatus.TIMED_OUT,
                message="setup workflow timed out.",
                reason=f"outer timeout exceeded after {self.timeout_seconds:g} seconds",
                executed=True,
            )

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

        phase_groups = self._ordered_phase_groups()
        phase_results: list[SetupPhaseResult] = []
        phase_group_results: list[SetupPhaseGroupResult] = []
        for group_index, group in enumerate(phase_groups):
            executions, group_result = await self._run_phase_group(group)
            phase_group_results.append(group_result)
            phase_results.extend(execution.phase_result for execution in executions)
            failed_execution = next(
                (
                    execution
                    for execution in executions
                    if not _is_success_status(execution.phase_result.status)
                ),
                None,
            )
            if failed_execution is None:
                continue

            failed_phase = failed_execution.phase_result
            setup_status = _setup_status_for_phase_status(failed_phase.status)
            remaining_phases = tuple(
                phase
                for later_group in phase_groups[group_index + 1 :]
                for phase in later_group.phases
            )
            not_run_phase_results = _not_run_phase_results(
                remaining_phases,
                reason=f"dependency group '{group.group_id}' did not complete",
            )
            self._report_not_run_phase_progress(not_run_phase_results)
            self._report_stopped_progress(setup_status.value)
            return SetupWorkflowResult(
                kind=SetupWorkflowKind.RUN,
                status=setup_status,
                message=f"setup run stopped during phase '{failed_phase.name}'.",
                reason=failed_execution.terminal_reason or (
                    f"phase '{failed_phase.name}' returned {failed_phase.status}"
                ),
                executed=True,
                phase_results=(*phase_results, *not_run_phase_results),
                phase_group_results=tuple(phase_group_results),
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
            phase_group_results=tuple(phase_group_results),
        )

    async def _run_phase_with_heartbeat(self, phase: SetupWorkflowPhase) -> object:
        if self.heartbeat_interval_seconds is None:
            return await phase.run()
        phase_task = asyncio.create_task(phase.run())
        elapsed_seconds = 0.0
        try:
            while True:
                try:
                    return await asyncio.wait_for(
                        asyncio.shield(phase_task),
                        timeout=self.heartbeat_interval_seconds,
                    )
                except asyncio.TimeoutError:
                    elapsed_seconds += self.heartbeat_interval_seconds
                    self._report_phase_progress(
                        phase_name=phase.name,
                        status="running",
                        result="running",
                        step="heartbeat",
                        safe_message=(
                            f"Setup phase heartbeat after {elapsed_seconds:g} seconds."
                        ),
                    )
        finally:
            if not phase_task.done():
                phase_task.cancel()
            with suppress(asyncio.CancelledError):
                await phase_task

    async def _run_phase_group(
        self,
        group: "_SetupPhaseGroup",
    ) -> tuple[tuple[_SetupPhaseExecution, ...], SetupPhaseGroupResult]:
        started_at = asyncio.get_running_loop().time()
        if len(group.phases) > 1:
            self._report_progress(
                phase="setup",
                target=group.group_id,
                task="Run setup phase group",
                step="phase group started",
                status="running",
                result="pending",
                safe_message="Setup phase group started.",
            )
        for phase in group.phases:
            self._report_phase_progress(
                phase_name=phase.name,
                status="started",
                result="pending",
                safe_message="Setup phase started.",
            )
        semaphore = asyncio.Semaphore(group.maximum_concurrency)

        async def run_bounded(phase: SetupWorkflowPhase) -> _SetupPhaseExecution:
            async with semaphore:
                return await self._execute_phase(phase)

        executions = tuple(
            await asyncio.gather(*(run_bounded(phase) for phase in group.phases))
        )
        for execution in executions:
            phase_result = execution.phase_result
            self._report_phase_progress(
                phase_name=phase_result.name,
                status=phase_result.status,
                result=phase_result.status,
                safe_message=execution.completion_message,
                recovery_hint=(
                    "Inspect the failed phase evidence before retrying."
                    if not _is_success_status(phase_result.status)
                    else None
                ),
            )
        failed_execution = next(
            (
                execution
                for execution in executions
                if not _is_success_status(execution.phase_result.status)
            ),
            None,
        )
        group_status = (
            "completed"
            if failed_execution is None
            else _setup_status_for_phase_status(
                failed_execution.phase_result.status
            ).value
        )
        group_result = SetupPhaseGroupResult(
            group_id=group.group_id,
            phase_names=tuple(phase.name for phase in group.phases),
            status=group_status,
            maximum_concurrency=group.maximum_concurrency,
            duration_seconds=max(
                0.0,
                asyncio.get_running_loop().time() - started_at,
            ),
        )
        if len(group.phases) > 1:
            self._report_progress(
                phase="setup",
                target=group.group_id,
                task="Run setup phase group",
                step="phase group completed",
                status=group_status,
                result=group_status,
                safe_message="Setup phase group completed.",
            )
        return executions, group_result

    async def _execute_phase(self, phase: SetupWorkflowPhase) -> _SetupPhaseExecution:
        try:
            phase_output = await self._run_phase_with_heartbeat(phase)
        except Exception as exc:
            return _SetupPhaseExecution(
                phase_result=SetupPhaseResult(
                    name=phase.name,
                    status=SetupWorkflowStatus.FAILED.value,
                    result={
                        "status": SetupWorkflowStatus.FAILED.value,
                        "reason": "setup phase failed",
                    },
                ),
                terminal_reason=f"phase '{phase.name}' failed with {exc.__class__.__name__}",
                completion_message=f"Setup phase failed with {exc.__class__.__name__}.",
            )

        try:
            _result_to_dict(phase_output)
        except ValueError:
            return _SetupPhaseExecution(
                phase_result=SetupPhaseResult(
                    name=phase.name,
                    status=SetupWorkflowStatus.FAILED.value,
                    result={
                        "status": SetupWorkflowStatus.FAILED.value,
                        "reason": "unsafe phase result payload",
                    },
                ),
                terminal_reason=f"phase '{phase.name}' returned unsafe result payload",
                completion_message="Setup phase result was unsafe.",
            )

        phase_status = _result_status_value(phase_output)
        return _SetupPhaseExecution(
            phase_result=SetupPhaseResult(
                name=phase.name,
                status=phase_status,
                result=phase_output,
            ),
            terminal_reason=(
                f"phase '{phase.name}' returned {phase_status}"
                if not _is_success_status(phase_status)
                else None
            ),
            completion_message=f"Setup phase {phase_status}.",
        )

    def _ordered_phases(self) -> tuple[SetupWorkflowPhase, ...]:
        return tuple(
            phase
            for group in self._ordered_phase_groups()
            for phase in group.phases
        )

    def _ordered_phase_groups(self) -> tuple["_SetupPhaseGroup", ...]:
        if self.installation_plan is None:
            return tuple(
                _SetupPhaseGroup(phase.name, (phase,), 1)
                for phase in self.phases
            )
        self.installation_plan.arrange_workflow_phases(self.phases)
        by_name = {phase.name: phase for phase in self.phases}
        by_plan_phase_id = {
            phase.phase_id: phase
            for phase in self.installation_plan.ordered_phases()
        }
        groups: list[_SetupPhaseGroup] = []
        for plan_group in self.installation_plan.phase_groups(self.max_concurrency):
            runnable_phases = tuple(
                by_name[name]
                for phase_id in plan_group.phase_ids
                for name in by_plan_phase_id[phase_id].workflow_phase_names
                if name in by_name
            )
            if runnable_phases:
                groups.append(
                    _SetupPhaseGroup(
                        plan_group.group_id,
                        runnable_phases,
                        plan_group.maximum_concurrency,
                    )
                )
        return tuple(groups)

    def _report_phase_progress(
        self,
        *,
        phase_name: str,
        status: str,
        result: str,
        step: str = "phase progress",
        safe_message: str,
        recovery_hint: str | None = None,
    ) -> None:
        self._report_progress(
            phase=phase_name,
            target=phase_name,
            task="Run setup phase",
            step=step,
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
        ArtifactWorkflowResult
        | DeploymentWorkflowResult
        | HostPreparationResult
        | PlatformWorkflowResult
        | PreflightResult,
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
    return status.lower() in {"completed", "passed", "success", "verified"}


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


def _not_run_phase_results(
    phases: Sequence[SetupWorkflowPhase],
    *,
    reason: str = "previous phase stopped setup run",
) -> tuple[SetupPhaseResult, ...]:
    return tuple(
        SetupPhaseResult(
            name=phase.name,
            status="not_run",
            result={"status": "not_run", "reason": reason},
        )
        for phase in phases
    )
