from __future__ import annotations

import asyncio
from dataclasses import replace

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure, OperationOutcome, OperationResult
from tiny_swarm_world.application.services.shared.operation_results import aggregate_operation, failure_from_exception
from collections.abc import Mapping
from typing import Protocol

from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.application.ports.update import (
    PortUpdateStateStore,
    PortUpdateRuntimeObserver,
    UpdateObservationError,
    UpdateObservationChanged,
)
from tiny_swarm_world.application.services.deployment.workflows import (
    DeploymentApplyWorkflow,
    DeploymentWorkflowStatus,
)
from tiny_swarm_world.application.services.platform.workflow.results import (
    PlatformWorkflowResult,
)
from tiny_swarm_world.application.services.platform.workflow.semantics import (
    PLATFORM_WORKFLOW_TAXONOMY,
)
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.deployment import ComposeServiceDefinition
from tiny_swarm_world.domain.inventory import (
    VerificationEvidenceScope,
    VerificationResult,
    VerificationStatus,
)
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.domain.update import ClassicUpdatePlan, UpdateRuntimeObservation


class _DeploymentWorkflowFactory(Protocol):
    def __call__(self, plan: ClassicUpdatePlan) -> DeploymentApplyWorkflow: ...


class ClassicUpdateWorkflow:
    """Validate and execute one explicit, reversible Classic update."""

    semantics = PLATFORM_WORKFLOW_TAXONOMY[PlatformWorkflowKind.UPDATE]

    def __init__(
        self,
        compose_repository: PortComposeFileRepository,
        deployment_workflow_factory: _DeploymentWorkflowFactory,
        state_store: PortUpdateStateStore,
        runtime_observer: PortUpdateRuntimeObserver | None = None,
        *,
        verification_attempts: int = 30,
        poll_interval_seconds: float = 2.0,
        observation_timeout_seconds: float = 10.0,
    ):
        if (
            verification_attempts < 1
            or poll_interval_seconds < 0
            or observation_timeout_seconds <= 0
        ):
            raise ValueError(
                "Update observation bounds must be positive (poll interval may be zero)."
            )
        self.compose_repository = compose_repository
        self.deployment_workflow_factory = deployment_workflow_factory
        self.state_store = state_store
        self.runtime_observer = runtime_observer
        self.verification_attempts = verification_attempts
        self.poll_interval_seconds = poll_interval_seconds
        self.observation_timeout_seconds = observation_timeout_seconds

    async def run(
        self,
        plan: ClassicUpdatePlan,
        *,
        preview: bool,
        live_consent: LiveConsent | None,
    ) -> PlatformWorkflowResult:
        return await self._run(
            plan, preview=preview, live_consent=live_consent, recovery=False
        )

    async def _run(
        self,
        plan: ClassicUpdatePlan,
        *,
        preview: bool,
        live_consent: LiveConsent | None,
        recovery: bool,
    ) -> PlatformWorkflowResult:
        current = self._current_service(plan, recovery=recovery)
        if isinstance(current, PlatformWorkflowResult):
            return current
        preview_result = self._verification(
            plan,
            status=VerificationStatus.VERIFIED,
            message="Static update preview; runtime qualification is required before apply.",
            evidence={
                "phase": "pre_apply",
                "current_image": current.image_ref,
                "from_image": plan.source_image,
                "to_image": plan.target_image,
                "mutation": "planned",
                "runtime_observed": "false",
            },
        )
        if preview:
            return PlatformWorkflowResult.completed(
                self.semantics,
                executed=False,
                verification_results=(preview_result,),
                operation_result=OperationResult(OperationOutcome.SUCCESS, completed_operations=("platform.recover.preview" if recovery else "platform.update.preview",)),
            )
        if live_consent is None or not live_consent.accepted:
            return PlatformWorkflowResult(
                kind=self.semantics.kind,
                status=PlatformWorkflowStatus.REFUSED,
                operation_result=aggregate_operation(OperationOutcome.REFUSED, pending=(_request_id(recovery),), failures=(OperationFailure.for_cause(_request_id(recovery), "platform", "refused"),)),
                message="platform update refused because live infrastructure consent is incomplete.",
                executed=False,
                verification_results=(
                    self._verification(
                        plan,
                        status=VerificationStatus.REFUSED,
                        message="Live consent is required before an update can mutate infrastructure.",
                        evidence={
                            "phase": "pre_apply",
                            "reason": "live_consent_missing",
                        },
                    ),
                ),
            )

        try:
            observed = await self._observe(plan)
        except UpdateObservationError as error:
            return self._blocked(
                plan,
                "Runtime observation is unavailable; no mutation was started.",
                {"reason": "runtime_observation_unavailable"},
                recovery=recovery, failures=(error.failure,),
            )
        if observed.converged(plan.target_image, allow_completed_rollback=recovery):
            return self._runtime_completed(
                plan, observed, executed=False, recovery=recovery
            )
        qualified = (
            observed.belongs_to_transition(plan.source_image, plan.target_image)
            if recovery
            else observed.converged(plan.source_image)
        )
        if not qualified:
            return self._blocked(
                plan,
                "Runtime image or rollout does not qualify for this transition; no mutation was started.",
                {"reason": "runtime_source_mismatch", **observed.to_evidence()},
                recovery=recovery,
            )
        if not recovery:
            try:
                previous = self.state_store.load(plan.stack_name, plan.service_name)
                if previous is not None and previous.plan != plan:
                    if not (
                        observed.converged(previous.plan.source_image)
                        or observed.converged(previous.plan.target_image)
                    ):
                        return self._blocked(
                            plan,
                            "Unresolved recovery state belongs to another transition.",
                            {"reason": "unresolved_recovery_state"},
                        )
                if previous is None or previous.plan != plan:
                    self.state_store.save(plan)
            except (OSError, ValueError) as error:
                return self._blocked(
                    plan,
                    "Recovery state could not be preserved; no mutation was started.",
                    {"reason": "state_unavailable"},
                    failures=(failure_from_exception(error, "platform.update.state", "platform"),),
                )
        return await self._apply_and_verify(plan, observed, recovery=recovery)

    async def _apply_and_verify(
        self,
        plan: ClassicUpdatePlan,
        before: UpdateRuntimeObservation,
        *,
        recovery: bool,
    ) -> PlatformWorkflowResult:
        try:
            deployment_result = await self.deployment_workflow_factory(plan).run()
        except (OSError, ValueError, RuntimeError) as error:
            return self._runtime_failure(
                plan, "deployment_failed", PlatformWorkflowStatus.FAILED_TO_APPLY,
                recovery=recovery, failures=(failure_from_exception(error, _request_id(recovery), "platform"),),
            )
        child = getattr(deployment_result, "operation_result", None)
        completed = child.completed_operations if isinstance(child, OperationResult) else ()
        if deployment_result.status != DeploymentWorkflowStatus.COMPLETED or (isinstance(child, OperationResult) and child.outcome != OperationOutcome.SUCCESS):
            status = {
                DeploymentWorkflowStatus.BLOCKED: PlatformWorkflowStatus.BLOCKED,
                DeploymentWorkflowStatus.FAILED_TO_APPLY: PlatformWorkflowStatus.FAILED_TO_APPLY,
                DeploymentWorkflowStatus.FAILED_TO_PREPARE: PlatformWorkflowStatus.FAILED_TO_APPLY,
                DeploymentWorkflowStatus.FAILED_TO_VERIFY: PlatformWorkflowStatus.FAILED_TO_VERIFY,
            }.get(
                deployment_result.status,
                PlatformWorkflowStatus.FAILED_TO_VERIFY,
            )
            return PlatformWorkflowResult(
                kind=self.semantics.kind,
                status=status,
                message="platform update did not complete its deployment verification.",
                executed=True,
                verification_results=deployment_result.verification_results,
                operation_result=aggregate_operation(
                    OperationOutcome.BLOCKED if status == PlatformWorkflowStatus.BLOCKED else OperationOutcome.FAILED,
                    completed=completed,
                    pending=(*child.pending_operations, _request_id(recovery) + ".verify") if isinstance(child, OperationResult) else (_request_id(recovery) + ".verify",),
                    uncertain=child.uncertain_operations if isinstance(child, OperationResult) else (() if status == PlatformWorkflowStatus.BLOCKED else (_request_id(recovery) + ".apply",)),
                    failures=child.failures if isinstance(child, OperationResult) and child.failures else (OperationFailure.for_cause(_request_id(recovery), "platform", "verification_failed"),),
                ),
            )
        for attempt in range(self.verification_attempts):
            try:
                observed = await self._observe(plan)
            except UpdateObservationChanged as error:
                if attempt + 1 == self.verification_attempts:
                    return self._runtime_failure(plan, "runtime_snapshot_unstable", failures=(error.failure,), recovery=recovery, completed=completed)
                await asyncio.sleep(self.poll_interval_seconds)
                continue
            except UpdateObservationError as error:
                return self._runtime_failure(plan, "runtime_observation_unavailable", failures=(error.failure,), recovery=recovery, completed=completed)
            if observed.service_id != before.service_id:
                return self._runtime_failure(
                    plan, "service_identity_changed", observation=observed, recovery=recovery, completed=completed
                )
            if observed.converged(plan.target_image, allow_completed_rollback=recovery):
                return self._runtime_completed(
                    plan,
                    observed,
                    executed=True,
                    recovery=recovery,
                    deployment_evidence=deployment_result.verification_results,
                    observed_source_image=before.desired_image,
                    observation_attempts=attempt + 1,
                    completed=completed,
                )
            if observed.rollout_failed:
                return self._runtime_failure(
                    plan, "rollout_failed", observation=observed, recovery=recovery, completed=completed
                )
            if attempt + 1 < self.verification_attempts:
                await asyncio.sleep(self.poll_interval_seconds)
        return self._runtime_failure(plan, "target_not_converged", observation=observed, recovery=recovery, completed=completed)

    async def _observe(self, plan: ClassicUpdatePlan) -> UpdateRuntimeObservation:
        if self.runtime_observer is None:
            raise UpdateObservationError("runtime_observer_missing")
        try:
            observed = await asyncio.wait_for(
                self.runtime_observer.observe(plan.stack_name, plan.service_name),
                timeout=self.observation_timeout_seconds,
            )
        except UpdateObservationError:
            raise
        except OperationError as error:
            raise UpdateObservationError("runtime_observation_unavailable", failure=error.failure) from None
        except TimeoutError:
            raise UpdateObservationError("runtime_observation_unavailable", failure=OperationFailure.for_cause("update.observe", "runtime_observer", "process_timeout")) from None
        except (OSError, ValueError) as error:
            raise UpdateObservationError("runtime_observation_unavailable", failure=failure_from_exception(error, "update.observe", "runtime_observer")) from None
        if (
            not isinstance(observed, UpdateRuntimeObservation)
            or observed.stack_name != plan.stack_name
            or observed.service_name != plan.service_name
            or not observed.service_id
        ):
            raise UpdateObservationError("runtime_identity_mismatch")
        return observed

    def _runtime_completed(
        self,
        plan: ClassicUpdatePlan,
        observed: UpdateRuntimeObservation,
        *,
        executed: bool,
        recovery: bool,
        deployment_evidence: tuple[VerificationResult, ...] = (),
        observed_source_image: str | None = None,
        observation_attempts: int = 1,
        completed: tuple[str, ...] = (),
    ) -> PlatformWorkflowResult:
        return PlatformWorkflowResult.completed(
            self.semantics,
            executed=executed,
            operation_result=aggregate_operation(
                OperationOutcome.ROLLED_BACK if recovery else OperationOutcome.SUCCESS,
                completed=(*completed, _request_id(recovery) + ".verify"), rollback_verified=recovery,
            ),
            verification_results=(
                self._verification(
                    plan,
                    status=VerificationStatus.VERIFIED,
                    message="Selected service and running tasks converged to the requested image.",
                    evidence={
                        **observed.to_evidence(),
                        "observation_attempts": str(observation_attempts),
                        "phase": "recovery" if recovery else "apply",
                        "from_image": plan.source_image,
                        "to_image": plan.target_image,
                        "mutation": "applied" if executed else "not_needed",
                        "applied": "true" if executed else "false",
                        "observed_source_image": observed_source_image
                        or observed.desired_image,
                        "rollback_state": "original_preserved"
                        if recovery
                        else "unchanged"
                        if not executed
                        else "recorded",
                    },
                    evidence_scope=VerificationEvidenceScope.LIVE,
                ),
                *deployment_evidence,
            ),
        )

    def _runtime_failure(
        self,
        plan: ClassicUpdatePlan,
        reason: str,
        status: PlatformWorkflowStatus = PlatformWorkflowStatus.FAILED_TO_VERIFY,
        *,
        observation: UpdateRuntimeObservation | None = None,
        recovery: bool = False,
        completed: tuple[str, ...] = (),
        failures: tuple[OperationFailure, ...] = (),
    ) -> PlatformWorkflowResult:
        message = "Update did not establish target convergence; original recovery state is retained."
        return PlatformWorkflowResult(
            kind=self.semantics.kind,
            status=status,
            message=message,
            executed=True,
            operation_result=aggregate_operation(
                OperationOutcome.FAILED, completed=completed,
                pending=(_request_id(recovery) + ".verify",),
                uncertain=(_request_id(recovery) + ".apply",),
                failures=failures or (OperationFailure.for_cause(_request_id(recovery), "platform", "verification_failed"),),
            ),
            verification_results=(
                self._verification(
                    plan,
                    status=(
                        VerificationStatus.FAILED_TO_APPLY
                        if status is PlatformWorkflowStatus.FAILED_TO_APPLY
                        else VerificationStatus.FAILED_TO_VERIFY
                    ),
                    message=message,
                    evidence={
                        "phase": "post_apply",
                        "reason": reason,
                        "rollback_state": "retained",
                        **(observation.to_evidence() if observation else {}),
                    },
                    evidence_scope=VerificationEvidenceScope.LIVE,
                ),
            ),
        )

    async def recover(
        self,
        stack_name: str,
        service_name: str,
        *,
        preview: bool,
        live_consent: LiveConsent | None,
    ) -> PlatformWorkflowResult:
        failures: tuple[OperationFailure, ...] = ()
        try:
            state = self.state_store.load(stack_name, service_name)
        except (OSError, ValueError) as error:
            state = None
            failures = (failure_from_exception(error, "platform.recover.state", "platform"),)
        if state is None:
            message = (
                "no rollback state is available for the selected stack/service; "
                "no mutation was started"
            )
            target_id = f"update:{stack_name}:{service_name}:recovery"
            return replace(PlatformWorkflowResult.blocked(
                self.semantics,
                message,
                (
                    self._verification_for_target(
                        target_id,
                        status=VerificationStatus.BLOCKED,
                        message=message,
                        evidence={"phase": "recovery", "reason": "state_not_found"},
                    ),
                ),
            ), operation_result=aggregate_operation(
                OperationOutcome.BLOCKED, pending=("platform.recover",),
                failures=failures or (OperationFailure.for_cause("platform.recover", "platform", "blocked"),),
            ))
        if (
            state.plan.stack_name != stack_name
            or state.plan.service_name != service_name
        ):
            return self._blocked(
                state.plan,
                "Recovery state belongs to another service.",
                {"reason": "state_identity_mismatch"},
                recovery=True,
            )
        return await self._run(
            state.plan.rollback_plan,
            preview=preview,
            live_consent=live_consent,
            recovery=True,
        )

    def _current_service(
        self,
        plan: ClassicUpdatePlan,
        *, recovery: bool = False,
    ) -> ComposeServiceDefinition | PlatformWorkflowResult:
        try:
            services = self.compose_repository.get_services_of(plan.stack_name)
        except (OSError, ValueError) as exc:
            return self._blocked(
                plan,
                "update preview could not inspect the selected stack; no mutation was started",
                {"reason": exc.__class__.__name__},
                recovery=recovery, failures=(failure_from_exception(exc, _request_id(recovery), "platform"),),
            )
        service = next(
            (item for item in services if item.name == plan.service_name), None
        )
        if service is None:
            return self._blocked(
                plan,
                "selected service is not part of the selected stack; no mutation was started",
                {"reason": "service_not_found"},
                recovery=recovery,
            )
        return service

    def _blocked(
        self,
        plan: ClassicUpdatePlan,
        message: str,
        evidence: Mapping[str, str],
        *, recovery: bool = False,
        failures: tuple[OperationFailure, ...] = (),
    ) -> PlatformWorkflowResult:
        return replace(PlatformWorkflowResult.blocked(
            self.semantics,
            message,
            (
                self._verification(
                    plan,
                    status=VerificationStatus.BLOCKED,
                    message=message,
                    evidence=evidence,
                ),
            ),
        ), operation_result=aggregate_operation(
            OperationOutcome.BLOCKED, pending=(_request_id(recovery),),
            failures=failures or (OperationFailure.for_cause(_request_id(recovery), "platform", "blocked"),),
        ))

    @staticmethod
    def _verification(
        plan: ClassicUpdatePlan,
        *,
        status: VerificationStatus,
        message: str,
        evidence: Mapping[str, str],
        evidence_scope: VerificationEvidenceScope = VerificationEvidenceScope.STATIC,
    ) -> VerificationResult:
        return ClassicUpdateWorkflow._verification_for_target(
            plan.target_id,
            status=status,
            message=message,
            evidence=evidence,
            evidence_scope=evidence_scope,
        )

    @staticmethod
    def _verification_for_target(
        target_id: str,
        *,
        status: VerificationStatus,
        message: str,
        evidence: Mapping[str, str],
        evidence_scope: VerificationEvidenceScope = VerificationEvidenceScope.STATIC,
    ) -> VerificationResult:
        return VerificationResult(
            target_id=target_id,
            status=status,
            message=message,
            evidence=evidence,
            evidence_scope=evidence_scope,
        )


def _request_id(recovery: bool) -> str:
    return "platform.recover" if recovery else "platform.update"
