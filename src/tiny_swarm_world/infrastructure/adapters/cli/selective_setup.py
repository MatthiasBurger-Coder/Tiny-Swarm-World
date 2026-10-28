"""Selection transport into the existing guarded Classic setup workflow."""
from __future__ import annotations

from argparse import Namespace
from dataclasses import replace
import json

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure, OperationOutcome, OperationResult
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.application.services.setup.workflow import SetupWorkflowKind, SetupWorkflowResult, SetupWorkflowStatus
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.cli.parser import _node_provider_request_from_args
from tiny_swarm_world.infrastructure.adapters.cli.selection import _configured_services


async def run_selective_setup(args: Namespace, consent: LiveConsent | None) -> SetupWorkflowResult | None:
    if consent is None or not consent.accepted:
        raise ValueError("Selective setup requires accepted live consent")
    lifecycle = composition.build_installation_lifecycle_service()
    explicit = args.services is not None or args.minimal or args.selection_config is not None
    if not explicit and lifecycle.manifests.load().manifest is None:
        return None
    try:
        plan = ServiceSelectionService(lifecycle.manifests, lifecycle.catalog).preview(
            requested=getattr(args, "selected_services", None),
            configured=None if args.services is not None else _configured_services(args.selection_config),
            minimal=args.minimal,
            preset=args.service_profile if args.service_profile_explicit else None,
            add=(args.workflow_namespace, args.workflow_action) == ("services", "add"),
        )
        request = _node_provider_request_from_args(args)
        state = await composition.prepare_setup_selection_state(lifecycle, plan, request)
    except (LifecycleStateError, ValueError) as error:
        return SetupWorkflowResult(SetupWorkflowKind.RUN, SetupWorkflowStatus.BLOCKED, str(error), "selection_admission_blocked")
    if not args.json:
        print(json.dumps({"resolved_services": plan.resolved_services, "resources": plan.resources.model_dump(mode="json"),
                          "resource_policy": "fixed Classic node topology and compatibility host floors; selected native demand remains unknown where undeclared"}, sort_keys=True))
    result = await composition.run_setup_with_terminal_status(
        consent, "run", service_profile=plan.service_preset, node_provider_request=request,
        allow_wsl_windows_filesystem=args.allow_wsl_windows_filesystem, selection_plan=plan,
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
        state.commit()
    except LifecycleStateError:
        return replace(result, status=SetupWorkflowStatus.FAILED_TO_VERIFY,
                       message="Runtime setup completed but selection persistence failed. Preserve data, inspect manifest/runtime drift and adopt or preview before retrying.",
                       reason="selection_persistence_failed", operation_result=OperationResult(
                           OperationOutcome.PARTIAL,
                           failures=(OperationFailure.for_cause("selection.persist", "manifest", "state_invalid"),),
                           completed_operations=("setup.runtime",), pending_operations=("selection.persist",),
                       ))
    return result
