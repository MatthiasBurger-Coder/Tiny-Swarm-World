"""CLI command routing and delegation to composed application workflows."""

from argparse import Namespace
from collections.abc import Sequence

from tiny_swarm_world.application.services.artifacts import ArtifactWorkflowResult
from tiny_swarm_world.application.services.deployment import DeploymentWorkflowResult
from tiny_swarm_world.application.services.platform.workflow.results import (
    PlatformWorkflowResult,
)
from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowStatus,
)
from tiny_swarm_world.application.services.setup import SetupWorkflowResult
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.domain.update import ClassicUpdatePlan
from tiny_swarm_world.infrastructure.adapters.cli.commands import (
    _print_setup_installation_plan,
    _print_workflow_list,
    _run_host_detect_command,
    _run_host_preparation_command,
    _run_host_verify_command,
    _run_network_doctor_command,
    _run_network_repair_command,
    _run_preflight_command,
)
from tiny_swarm_world.infrastructure.adapters.cli.consent import (
    _enforce_workflow_confirmation,
    _enforce_workflow_implementation,
    _live_consent_for_workflow,
)
from tiny_swarm_world.infrastructure.adapters.cli.parser import (
    _node_provider_request_from_args,
    _update_plan_from_args,
    parse_args,
)
from tiny_swarm_world.infrastructure.adapters.cli.presentation import (
    _emit_workflow_result,
    _workflow_status_value,
)
from tiny_swarm_world.infrastructure.adapters.cli.registry import CliWorkflow
from tiny_swarm_world.infrastructure.composition import (
    DEFAULT_SETUP_SERVICE_PROFILE,
    NodeProviderSelectionRequest,
    build_application_logger,
    build_application_services,
    build_artifact_services_for_provider,
    build_classic_update_workflow,
    build_deployment_services_for_provider,
    ensure_common_executable_paths,
    execute_cli_workflow,
    run_setup_with_terminal_status,
)

WorkflowResult = (
    PlatformWorkflowResult
    | ArtifactWorkflowResult
    | DeploymentWorkflowResult
    | SetupWorkflowResult
)


async def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    if args.list_workflows:
        _print_workflow_list()
        return

    if args.workflow is not None and args.workflow.namespace == "host":
        if args.workflow.action == "detect":
            _run_host_detect_command(args)
        elif args.workflow.action == "preflight":
            await _run_preflight_command(args)
        elif args.workflow.action in {"prepare", "cleanup"}:
            await _run_host_preparation_command(args)
        else:
            _run_host_verify_command(args)
        return

    ensure_common_executable_paths()
    logger = build_application_logger()
    logger.info("Starting application")

    if args.network_command == "doctor_network":
        await _run_network_doctor_command(args)
        return

    if args.network_command == "network_repair":
        await _run_network_repair_command(args)
        return

    if args.preflight:
        await _run_preflight_command(args)
        return

    workflow = _selected_workflow(args)
    if workflow is None:
        return

    _enforce_workflow_confirmation(workflow, args.confirm)
    _enforce_workflow_implementation(workflow, args)
    live_consent = _live_consent_for_workflow(workflow, args)

    logger.info("Running workflow: %s", workflow.name)
    node_provider_request = _node_provider_request_from_args(args)
    if workflow.namespace == "setup" and workflow.action == "run":
        _print_setup_installation_plan(
            service_profile=args.service_profile,
            node_provider_request=node_provider_request,
        )
    result = await run_cli_workflow(
        workflow,
        args.confirm,
        live_consent,
        service_profile=args.service_profile,
        node_provider_request=node_provider_request,
        allow_wsl_windows_filesystem=args.allow_wsl_windows_filesystem,
        update_plan=_update_plan_from_args(args),
        update_preview=bool(args.preview),
        update_recover=bool(args.recover),
        update_stack_name=args.stack,
        update_service_name=args.service,
    )
    _emit_workflow_result(result, args)
    if _workflow_status_value(result) != PlatformWorkflowStatus.COMPLETED.value:
        raise SystemExit(1)

    logger.info("Done")


def _selected_workflow(args: Namespace) -> CliWorkflow | None:
    workflow = args.workflow
    if workflow is None:
        print("No workflow selected. Use --list-workflows to inspect available workflows.")
    return workflow


async def run_cli_workflow(
    workflow: CliWorkflow,
    confirmation: str | None,
    live_consent: LiveConsent | None = None,
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    allow_wsl_windows_filesystem: bool = False,
    update_plan: ClassicUpdatePlan | None = None,
    update_preview: bool = False,
    update_recover: bool = False,
    update_stack_name: str | None = None,
    update_service_name: str | None = None,
) -> WorkflowResult:
    return await execute_cli_workflow(
        namespace=workflow.namespace,
        action=workflow.action,
        platform_kind=workflow.platform_kind,
        confirmation=confirmation,
        live_consent=live_consent,
        service_profile=service_profile,
        node_provider_request=node_provider_request,
        allow_wsl_windows_filesystem=allow_wsl_windows_filesystem,
        update_plan=update_plan,
        update_preview=update_preview,
        update_recover=update_recover,
        update_stack_name=update_stack_name,
        update_service_name=update_service_name,
        build_classic_update_workflow=build_classic_update_workflow,
        build_application_services=build_application_services,
        build_artifact_services=build_artifact_services_for_provider,
        build_deployment_services=build_deployment_services_for_provider,
        run_setup_with_terminal_status=run_setup_with_terminal_status,
    )
