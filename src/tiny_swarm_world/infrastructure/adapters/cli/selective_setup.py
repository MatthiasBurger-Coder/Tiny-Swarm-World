"""Selection transport into the existing guarded Classic setup workflow."""
from __future__ import annotations

from argparse import Namespace
from dataclasses import replace
import json

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease, installation_operation
from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure, OperationOutcome, OperationResult
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.application.services.setup.workflow import SetupWorkflowKind, SetupWorkflowResult, SetupWorkflowStatus
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.cli.parser import _node_provider_request_from_args
from tiny_swarm_world.infrastructure.adapters.cli.selection import _configured_services


async def run_selective_setup(args: Namespace, consent: LiveConsent | None) -> SetupWorkflowResult | None:
    if consent is None or not consent.accepted:
        raise ValueError('Selective setup requires accepted live consent')
    lifecycle = composition.build_installation_lifecycle_service()
    with installation_operation(lifecycle.operation_lock, 'profile-recovery' if getattr(args, 'recover', False) else 'setup') as admitted:
        return await _run_selective_setup(args, consent, lifecycle, admitted)


async def _run_selective_setup(args: Namespace, consent: LiveConsent | None, lifecycle,
                               operation_lease: InstallationLease) -> SetupWorkflowResult | None:
    if consent is None or not consent.accepted:
        raise ValueError("Selective setup requires accepted live consent")
    try:
        if legacy_full_request(args) and composition.legacy_full_setup_available(lifecycle):
            return None
        plan, request, state = await _prepare_selection(args, consent, lifecycle, operation_lease)
        from tiny_swarm_world.application.services.profile_completion import CreationCompletionOperation
        if isinstance(state.profile_operation, CreationCompletionOperation):
            await state.profile_operation.commit_installation()
            return SetupWorkflowResult(SetupWorkflowKind.RUN, SetupWorkflowStatus.COMPLETED,
                'Original creation checkpoint completion recovered; runtime and manifest preserved.',
                'creation_completion_recovered', executed=False)
    except (LifecycleStateError, ValueError) as error:
        return SetupWorkflowResult(SetupWorkflowKind.RUN, SetupWorkflowStatus.BLOCKED, str(error), "selection_admission_blocked")
    if not args.json:
        print(json.dumps({"resolved_services": plan.resolved_services, "resources": plan.resources.model_dump(mode="json"),
                          "resource_policy": "fixed Classic node topology and compatibility host floors; selected native demand remains unknown where undeclared"}, sort_keys=True))
    result = await composition.run_setup_with_terminal_status(
        consent, "run", service_profile=plan.service_preset, node_provider_request=request,
        allow_wsl_windows_filesystem=args.allow_wsl_windows_filesystem, selection_plan=plan, operation_lease=operation_lease,
        **({"profile_operation": state.profile_operation} if state.profile_operation is not None else {}),
    )
    if result.status is not SetupWorkflowStatus.COMPLETED:
        return result
    try:
        await composition.complete_setup_selection_state(state, request)
    except (LifecycleStateError, OperationError, TimeoutError):
        return replace(result, status=SetupWorkflowStatus.FAILED_TO_VERIFY,
                       message="Runtime setup completed but source observations failed. Preserve runtime/data and inspect pinned images/tasks before retrying.",
                       reason="selection_observation_failed", operation_result=OperationResult(
                           OperationOutcome.PARTIAL,
                           failures=(OperationFailure.for_cause("selection.observe", "runtime_observer", "observation_unavailable"),),
                           completed_operations=("setup.runtime",), pending_operations=("selection.persist",),
                       ))
    try:
        if state.profile_operation is not None:
            await state.profile_operation.verify_effective_routes()
        state.commit()
        if state.profile_operation is not None:
            await state.profile_operation.commit_installation()
    except LifecycleStateError:
        return replace(result, status=SetupWorkflowStatus.FAILED_TO_VERIFY,
                       message="Runtime setup completed but selection persistence failed. Preserve data, inspect manifest/runtime drift and adopt or preview before retrying.",
                       reason="selection_persistence_failed", operation_result=OperationResult(
                           OperationOutcome.PARTIAL,
                           failures=(OperationFailure.for_cause("selection.persist", "manifest", "state_invalid"),),
                           completed_operations=("setup.runtime",), pending_operations=("selection.persist",),
                       ))
    return result


def legacy_full_request(args):
    return ((args.workflow_namespace, args.workflow_action) == ('setup', 'run')
        and args.services is None and not args.minimal and args.selection_config is None
        and getattr(args, 'swagger_exposure', None) != 'internal'
        and getattr(args, 'stack_owner', None) != 'portainer' and not getattr(args, 'recover', False))


async def _prepare_selection(args, consent, lifecycle, operation_lease):
    plan = ServiceSelectionService(lifecycle.manifests, lifecycle.catalog).preview(
        stack_owner=getattr(args, "stack_owner", None),
        requested=getattr(args, "selected_services", None),
        configured=None if args.services is not None else _configured_services(args.selection_config),
        minimal=args.minimal,
        preset=args.service_profile if args.service_profile_explicit else None,
        add=(args.workflow_namespace, args.workflow_action) == ("services", "add"),
        service_exposure=({"swagger": args.swagger_exposure} if getattr(args, "swagger_exposure", None) is not None else None),
    )
    request = _node_provider_request_from_args(args)
    state = await composition.prepare_setup_selection_state(lifecycle, plan, request, operation_lease=operation_lease,
        consent=consent, recovery=bool(getattr(args, 'recover', False)))
    return plan, request, state
