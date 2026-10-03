"""CLI confirmation and explicit live-consent safeguards."""

from argparse import Namespace

from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
)
from tiny_swarm_world.domain.preflight import (
    LIVE_CONSENT_PROMPT,
    LIVE_CONSENT_YES_VALUES,
    LiveConsent,
)
from tiny_swarm_world.infrastructure.adapters.cli.presentation import (
    _emit_json_payload,
    _print_blocked_workflow_summary,
    _should_emit_json,
)
from tiny_swarm_world.infrastructure.adapters.cli.registry import CliWorkflow


def _enforce_workflow_confirmation(workflow: CliWorkflow, confirmation: str | None) -> None:
    if workflow.confirmation_phrase is None or confirmation == workflow.confirmation_phrase:
        return
    print(f"REFUSED_WORKFLOW_CONFIRMATION_MISSING: {workflow.name}")
    print(f"Expected --confirm {workflow.confirmation_phrase}")
    raise SystemExit(2)


def _enforce_workflow_implementation(workflow: CliWorkflow, args: Namespace) -> None:
    if workflow.implemented:
        return
    payload = _blocked_workflow_result(workflow)
    if _should_emit_json(args):
        _emit_json_payload(payload)
    else:
        _print_blocked_workflow_summary(payload)
    raise SystemExit(1)


def _live_consent_for_workflow(
    workflow: CliWorkflow,
    args: Namespace,
) -> LiveConsent | None:
    if not workflow.mutating:
        return None
    if workflow.platform_kind is PlatformWorkflowKind.UPDATE and args.preview:
        return None
    live_consent = _live_consent_from_args(args)
    if live_consent.accepted:
        return live_consent
    print("REFUSED_LIVE_CONSENT_MISSING")
    for reason in live_consent.missing_reasons:
        print(f"- {reason}")
    raise SystemExit(2)


def _blocked_workflow_result(workflow: CliWorkflow) -> dict[str, object]:
    return {
        "executed": False,
        "message": f"{workflow.name} is declared but not wired in this workflow slice.",
        "status": "blocked",
        "workflow": workflow.name,
    }


def _live_consent_from_args(args: Namespace) -> LiveConsent:
    confirmed = bool(args.approve_live)
    if args.live and not confirmed:
        try:
            answer = input(f"{LIVE_CONSENT_PROMPT} ")
            confirmed = answer.strip().lower() in LIVE_CONSENT_YES_VALUES
        except EOFError:
            confirmed = False
    return LiveConsent(live_flag=args.live, confirmed=confirmed)
