import asyncio
import json
import os
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from tiny_swarm_world.application.services.artifacts import ArtifactWorkflowResult
from tiny_swarm_world.application.services.deployment import DeploymentWorkflowResult
from tiny_swarm_world.application.services.platform.workflow_taxonomy import (
    PLATFORM_WORKFLOW_TAXONOMY,
    PlatformWorkflowKind,
    PlatformWorkflowResult,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.domain.preflight import (
    LIVE_CONSENT_ENVIRONMENT_VARIABLE,
    LIVE_CONSENT_PHRASE,
    LiveConsent,
)
from tiny_swarm_world.infrastructure.composition import (
    ApplicationServices,
    ArtifactServices,
    DeploymentServices,
    build_application_services,
    build_artifact_services,
    build_deployment_services,
    build_preflight_service,
)
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory

WorkflowResult = PlatformWorkflowResult | ArtifactWorkflowResult | DeploymentWorkflowResult


@dataclass(frozen=True)
class CliWorkflow:
    namespace: str
    action: str
    mutating: bool
    destructive: bool
    platform_kind: PlatformWorkflowKind | None = None
    confirmation_phrase: str | None = None

    @property
    def name(self) -> str:
        return f"{self.namespace} {self.action}"

    @property
    def implemented(self) -> bool:
        return self.platform_kind is not None or self.namespace in {"artifacts", "deployment"}


PLATFORM_WORKFLOW_ORDER = (
    PlatformWorkflowKind.INIT,
    PlatformWorkflowKind.RECONCILE,
    PlatformWorkflowKind.VERIFY,
    PlatformWorkflowKind.RESET,
    PlatformWorkflowKind.DESTROY,
)

CLI_WORKFLOWS = (
    *(
        CliWorkflow(
            namespace="platform",
            action=kind.value,
            mutating=PLATFORM_WORKFLOW_TAXONOMY[kind].mutating,
            destructive=PLATFORM_WORKFLOW_TAXONOMY[kind].destructive,
            platform_kind=kind,
            confirmation_phrase=PLATFORM_WORKFLOW_TAXONOMY[kind].confirmation_phrase,
        )
        for kind in PLATFORM_WORKFLOW_ORDER
    ),
    CliWorkflow(namespace="artifacts", action="prepare", mutating=True, destructive=False),
    CliWorkflow(namespace="artifacts", action="verify", mutating=False, destructive=False),
    CliWorkflow(namespace="deployment", action="apply", mutating=True, destructive=False),
    CliWorkflow(namespace="deployment", action="verify", mutating=False, destructive=False),
)
CLI_WORKFLOWS_BY_KEY = {(workflow.namespace, workflow.action): workflow for workflow in CLI_WORKFLOWS}


def parse_args(argv: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser(description="Tiny Swarm World automation entrypoint.")
    parser.add_argument(
        "--list-workflows",
        action="store_true",
        help="List workflow-level commands without building application services.",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run static preflight validation without executing live infrastructure commands.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Allow live infrastructure execution after the required consent checks pass.",
    )
    parser.add_argument(
        "--confirm",
        help="Exact confirmation phrase required by destructive workflows.",
    )
    parser.add_argument("workflow_namespace", nargs="?", help="Workflow namespace.")
    parser.add_argument("workflow_action", nargs="?", help="Workflow action.")
    args = parser.parse_args(argv)

    if (args.workflow_namespace is None) != (args.workflow_action is None):
        parser.error("workflow command requires both namespace and action")

    args.workflow = None
    if args.workflow_namespace is not None and args.workflow_action is not None:
        args.workflow = CLI_WORKFLOWS_BY_KEY.get((args.workflow_namespace, args.workflow_action))
        if args.workflow is None:
            parser.error(f"unsupported workflow command: {args.workflow_namespace} {args.workflow_action}")

    return args


async def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    logger = LoggerFactory.get_logger("application")
    logger.info("Starting application")

    if args.list_workflows:
        for workflow in CLI_WORKFLOWS:
            print(f"{workflow.name}\tmutating={workflow.mutating}\tdestructive={workflow.destructive}")
        return

    if args.preflight:
        preflight = build_preflight_service()
        live_consent = _live_consent_from_args(args) if args.live else None
        result = await preflight.run(live_consent)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        if not result.passed:
            raise SystemExit(1)
        return

    workflow = args.workflow
    if workflow is None:
        print("No workflow selected. Use --list-workflows to inspect available workflows.")
        return

    if workflow.confirmation_phrase is not None and args.confirm != workflow.confirmation_phrase:
        print(f"REFUSED_WORKFLOW_CONFIRMATION_MISSING: {workflow.name}")
        print(f"Expected --confirm {workflow.confirmation_phrase}")
        raise SystemExit(2)

    if not workflow.implemented:
        print(
            json.dumps(
                _blocked_workflow_result(workflow),
                indent=2,
                sort_keys=True,
            )
        )
        raise SystemExit(1)

    if workflow.mutating:
        live_consent = _live_consent_from_args(args)
        if not live_consent.accepted:
            print("REFUSED_LIVE_CONSENT_MISSING")
            for reason in live_consent.missing_reasons:
                print(f"- {reason}")
            raise SystemExit(2)

    logger.info("Running workflow: %s", workflow.name)
    result = await run_cli_workflow(workflow, args.confirm)
    print(json.dumps(_workflow_result_to_dict(result), indent=2, sort_keys=True))
    if _workflow_status_value(result) != PlatformWorkflowStatus.COMPLETED.value:
        raise SystemExit(1)

    logger.info("Done")


async def run_cli_workflow(
    workflow: CliWorkflow,
    confirmation: str | None,
) -> WorkflowResult:
    if workflow.platform_kind is not None:
        services = build_application_services()
        return await run_platform_workflow(services, workflow.platform_kind, confirmation)
    if workflow.namespace == "artifacts":
        services = build_artifact_services()
        return await run_artifact_workflow(services, workflow.action)
    if workflow.namespace == "deployment":
        services = build_deployment_services()
        return await run_deployment_workflow(services, workflow.action)
    raise ValueError(f"Unsupported workflow: {workflow.name}")


async def run_platform_workflow(
    services: ApplicationServices,
    kind: PlatformWorkflowKind | None,
    confirmation: str | None,
) -> PlatformWorkflowResult:
    workflows = services.platform.workflows
    match kind:
        case PlatformWorkflowKind.INIT:
            return await workflows.init.run()
        case PlatformWorkflowKind.RECONCILE:
            return await workflows.reconcile.run()
        case PlatformWorkflowKind.VERIFY:
            return await workflows.verify.run()
        case PlatformWorkflowKind.RESET:
            return await workflows.reset.run(confirmation)
        case PlatformWorkflowKind.DESTROY:
            return await workflows.destroy.run(confirmation)
        case _:
            raise ValueError(f"Unsupported platform workflow: {kind}")


async def run_artifact_workflow(
    services: ArtifactServices,
    action: str,
) -> ArtifactWorkflowResult:
    workflows = services.workflows
    match action:
        case "prepare":
            return await workflows.prepare.run()
        case "verify":
            return await workflows.verify.run()
        case _:
            raise ValueError(f"Unsupported artifacts workflow: {action}")


async def run_deployment_workflow(
    services: DeploymentServices,
    action: str,
) -> DeploymentWorkflowResult:
    workflows = services.workflows
    match action:
        case "apply":
            return await workflows.apply.run()
        case "verify":
            return await workflows.verify.run()
        case _:
            raise ValueError(f"Unsupported deployment workflow: {action}")


def _workflow_result_to_dict(result: WorkflowResult) -> dict[str, object]:
    if isinstance(result, ArtifactWorkflowResult | DeploymentWorkflowResult):
        return result.to_dict()
    return {
        "executed": result.executed,
        "message": result.message,
        "status": result.status.value,
        "workflow": f"platform {result.kind.value}",
    }


def _workflow_status_value(result: WorkflowResult) -> str:
    status = result.status
    if isinstance(status, Enum):
        return str(status.value)
    return str(status)


def _blocked_workflow_result(workflow: CliWorkflow) -> dict[str, object]:
    return {
        "executed": False,
        "message": f"{workflow.name} is declared but not wired in this workflow slice.",
        "status": "blocked",
        "workflow": workflow.name,
    }


def _live_consent_from_args(args: Namespace) -> LiveConsent:
    typed_phrase = None
    if args.live:
        try:
            typed_phrase = input(f"Type '{LIVE_CONSENT_PHRASE}' to continue: ")
        except EOFError:
            typed_phrase = None
    return LiveConsent(
        live_flag=args.live,
        environment_value=os.environ.get(LIVE_CONSENT_ENVIRONMENT_VARIABLE),
        typed_phrase=typed_phrase,
    )


if __name__ == "__main__":
    asyncio.run(main())
