import asyncio
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from dataclasses import dataclass

from tiny_swarm_world.cli_presentation import (
    _host_detection_payload as _host_detection_payload,
    _print_host_environment_summary as _print_host_environment_summary,
    _workflow_result_to_dict as _workflow_result_to_dict,
    _emit_workflow_result as _emit_workflow_result,
    _emit_json_payload as _emit_json_payload,
    _workflow_status_value as _workflow_status_value,
    _should_emit_json as _should_emit_json,
    _print_blocked_workflow_summary as _print_blocked_workflow_summary,
    _print_workflow_summary as _print_workflow_summary,
    _format_workflow_summary as _format_workflow_summary,
    _format_operation_summary as _format_operation_summary,
    _format_verification_summary as _format_verification_summary,
    _workflow_name as _workflow_name,
    _print_preflight_summary as _print_preflight_summary,
    _print_setup_installation_summary as _print_setup_installation_summary,
    _format_setup_installation_summary as _format_setup_installation_summary,
    _format_setup_phase_diagnostics as _format_setup_phase_diagnostics,
    _print_setup_nested_workflow_diagnostics as _print_setup_nested_workflow_diagnostics,
    _format_setup_nested_workflow_diagnostics as _format_setup_nested_workflow_diagnostics,
    _format_phase_status_counts as _format_phase_status_counts,
    _format_status_counts as _format_status_counts,
    _console_enum as _console_enum,
    _console_text as _console_text,
    _safe_console_value as _safe_console_value,
    render_setup_installation_plan as _render_setup_installation_plan,
)
from tiny_swarm_world.application.services.artifacts import ArtifactWorkflowResult
from tiny_swarm_world.application.services.deployment import DeploymentWorkflowResult
from tiny_swarm_world.application.services.setup import SetupWorkflowResult
from tiny_swarm_world.application.services.setup.installation_plan import build_setup_installation_plan
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
from tiny_swarm_world.application.services.platform.host.prepare_with_preflight import (
    PrepareHostWithPreflight,
)
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend, NodeProviderKind
from tiny_swarm_world.domain.preflight import (
    LIVE_CONSENT_PROMPT,
    LIVE_CONSENT_YES_VALUES,
    LiveConsent,
)
from tiny_swarm_world.infrastructure.composition import (
    DEFAULT_SETUP_SERVICE_PROFILE,
    NodeProviderSelectionRequest,
    build_application_services,
    execute_cli_workflow,
    build_classic_update_workflow,
    build_artifact_services_for_provider,
    build_compose_file_repository,
    build_deployment_services_for_provider,
    build_host_detection_service,
    build_host_preparation_service,
    build_read_only_hang_diagnostics,
    build_network_doctor_service,
    build_network_repair_options,
    build_network_repair_service,
    build_preflight_service,
    build_application_logger,
    run_setup_with_terminal_status,
)
from tiny_swarm_world.infrastructure.composition import ensure_common_executable_paths
from tiny_swarm_world.domain.update import ClassicUpdatePlan

WorkflowResult = (
    PlatformWorkflowResult
    | ArtifactWorkflowResult
    | DeploymentWorkflowResult
    | SetupWorkflowResult
)


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
        return self.platform_kind is not None or self.namespace in {
            "artifacts",
            "deployment",
            "host",
            "setup",
        }


PLATFORM_WORKFLOW_ORDER = (
    PlatformWorkflowKind.INIT,
    PlatformWorkflowKind.RECONCILE,
    PlatformWorkflowKind.UPDATE,
    PlatformWorkflowKind.EXPOSE,
    PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT,
    PlatformWorkflowKind.VERIFY,
    PlatformWorkflowKind.RESET,
    PlatformWorkflowKind.DESTROY,
)

CLI_WORKFLOWS = (
    CliWorkflow(namespace="host", action="detect", mutating=False, destructive=False),
    CliWorkflow(namespace="host", action="preflight", mutating=False, destructive=False),
    CliWorkflow(namespace="host", action="prepare", mutating=True, destructive=False),
    CliWorkflow(namespace="host", action="verify", mutating=False, destructive=False),
    CliWorkflow(namespace="host", action="cleanup", mutating=True, destructive=True),
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
    CliWorkflow(namespace="deployment", action="bootstrap", mutating=True, destructive=False),
    CliWorkflow(namespace="deployment", action="apply", mutating=True, destructive=False),
    CliWorkflow(namespace="deployment", action="verify", mutating=False, destructive=False),
    CliWorkflow(namespace="setup", action="run", mutating=True, destructive=False),
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
        "--approve-live",
        action="store_true",
        help=(
            "Explicit non-interactive approval for --live infrastructure changes. "
            "Without this flag, --live asks for interactive confirmation."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON workflow results instead of the default human-readable summary.",
    )
    parser.add_argument(
        "--confirm",
        help="Exact confirmation phrase required by destructive workflows.",
    )
    parser.add_argument(
        "--service-profile",
        choices=[profile.value for profile in ServiceStackProfile],
        default=DEFAULT_SETUP_SERVICE_PROFILE.value,
        help=(
            "Service stack profile for setup, deployment and preflight. "
            "The default full installation includes service-access."
        ),
    )
    parser.add_argument(
        "--allow-wsl-windows-filesystem",
        action="store_true",
        help=(
            "Allow a confirmed Windows-mounted WSL2 repository for live work; "
            "the applied override is recorded in protected local evidence."
        ),
    )
    parser.add_argument(
        "--node-provider",
        choices=[NodeProviderKind.LXC_NATIVE.value],
        default=NodeProviderKind.LXC_NATIVE.value,
        help="Node provider for platform setup; default is lxc_native.",
    )
    parser.add_argument(
        "--lxc-backend",
        choices=[ManagedLxcBackend.INCUS.value],
        help="Preferred managed LXC backend when --node-provider lxc_native is selected.",
    )
    parser.add_argument(
        "--runtime",
        choices=["wsl2-nat"],
        help="Runtime target for 'network repair'.",
    )
    parser.add_argument(
        "--linux-forwarding",
        action="store_true",
        help="Plan or apply Incus bridge forwarding repair for 'network repair'.",
    )
    parser.add_argument(
        "--incus",
        action="store_true",
        help="Plan or apply guarded Incus bridge repair for 'network repair'.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the selected 'network repair' target; omitted means dry-run.",
    )
    parser.add_argument(
        "--stack",
        help="Existing Classic stack for 'platform update'.",
    )
    parser.add_argument(
        "--service",
        help="Service within the selected stack for 'platform update'.",
    )
    parser.add_argument(
        "--from-image",
        dest="from_image",
        help="Currently configured image reference for 'platform update'.",
    )
    parser.add_argument(
        "--to-image",
        dest="to_image",
        help="Target image reference for 'platform update'.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Validate and print the update plan without mutating infrastructure.",
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="Reverse the last recorded update for the selected stack/service.",
    )
    parser.add_argument("workflow_namespace", nargs="?", help="Workflow namespace.")
    parser.add_argument("workflow_action", nargs="?", help="Workflow action.")
    args = parser.parse_args(argv)

    _validate_provider_args(parser, args)
    _assign_network_command(parser, args)
    _assign_workflow(parser, args)
    return args


def _validate_provider_args(parser: ArgumentParser, args: Namespace) -> None:
    if args.lxc_backend is not None and args.node_provider != NodeProviderKind.LXC_NATIVE.value:
        parser.error("--lxc-backend requires --node-provider lxc_native")


def _assign_network_command(parser: ArgumentParser, args: Namespace) -> None:
    if (args.workflow_namespace is None) != (args.workflow_action is None):
        parser.error("workflow command requires both namespace and action")

    args.network_command = _network_command(args.workflow_namespace, args.workflow_action)
    network_options_present = bool(args.runtime or args.linux_forwarding or args.incus or args.apply)
    if args.network_command != "network_repair" and network_options_present:
        parser.error("network repair options require command: network repair")
    if args.network_command == "network_repair" and not _has_network_repair_target(args):
        parser.error("network repair requires --runtime, --linux-forwarding, or --incus")


def _network_command(namespace: str | None, action: str | None) -> str | None:
    if namespace == "doctor" and action == "network":
        return "doctor_network"
    if namespace == "network" and action == "repair":
        return "network_repair"
    return None


def _has_network_repair_target(args: Namespace) -> bool:
    return bool(args.runtime or args.linux_forwarding or args.incus)


def _assign_workflow(parser: ArgumentParser, args: Namespace) -> None:
    args.workflow = None
    if args.workflow_namespace is None or args.workflow_action is None or args.network_command is not None:
        return
    args.workflow = CLI_WORKFLOWS_BY_KEY.get((args.workflow_namespace, args.workflow_action))
    if args.workflow is None:
        parser.error(f"unsupported workflow command: {args.workflow_namespace} {args.workflow_action}")
    is_update = args.workflow_namespace == "platform" and args.workflow_action == "update"
    update_options_present = any(
        value is not None
        for value in (args.stack, args.service, args.from_image, args.to_image)
    ) or args.preview or args.recover
    if not is_update and update_options_present:
        parser.error("update options require command: platform update")
    if is_update:
        if args.recover:
            if not args.stack or not args.service:
                parser.error("platform update --recover requires --stack and --service")
            if args.from_image or args.to_image:
                parser.error("platform update --recover cannot use --from-image or --to-image")
            return
        missing = [
            name
            for name, value in (
                ("--stack", args.stack),
                ("--service", args.service),
                ("--from-image", args.from_image),
                ("--to-image", args.to_image),
            )
            if not value
        ]
        if missing:
            parser.error("platform update requires " + ", ".join(missing))


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


def cli(argv: Sequence[str] | None = None) -> None:
    asyncio.run(main(argv))


def _print_workflow_list() -> None:
    for workflow in CLI_WORKFLOWS:
        print(f"{workflow.name}\tmutating={workflow.mutating}\tdestructive={workflow.destructive}")


def _run_host_detect_command(args: Namespace) -> None:
    report = build_host_detection_service().run()
    if _should_emit_json(args):
        _emit_json_payload(_host_detection_payload(report))
    else:
        _print_host_environment_summary(report)
    if not report.supported:
        raise SystemExit(1)


def _run_host_verify_command(args: Namespace) -> None:
    report = build_read_only_hang_diagnostics().collect()
    payload = {
        "read_only": report.read_only,
        "commands": [
            {
                "name": item.name,
                "status": item.status,
                "timed_out": item.timed_out,
                "classification": getattr(item, "classification", "unknown"),
                "output": item.output,
            }
            for item in report.commands
        ],
    }
    if _should_emit_json(args):
        _emit_json_payload(payload)
        return
    print("Host diagnostics (read-only)")
    for item in report.commands:
        print(f"{item.name}: {item.status}")


async def _run_host_preparation_command(args: Namespace) -> None:
    workflow = args.workflow
    live_consent = _live_consent_for_workflow(workflow, args)
    use_case = PrepareHostWithPreflight(
        build_preflight_service(
            service_profile=args.service_profile,
            node_provider_request=_node_provider_request_from_args(args),
            allow_wsl_windows_filesystem=args.allow_wsl_windows_filesystem,
            include_secret_checks=False,
            include_port_checks=False,
        ),
        lambda: build_host_preparation_service(live_consent),
    )
    outcome = await use_case.run(workflow.action, live_consent)
    if outcome.preparation is None:
        if _should_emit_json(args):
            _emit_json_payload(
                {"preflight": outcome.preflight.to_dict(), "host_preparation": None}
            )
        else:
            _print_preflight_summary(outcome.preflight, live=True)
        raise SystemExit(1)

    result = outcome.preparation
    if _should_emit_json(args):
        _emit_json_payload(
            {"preflight": outcome.preflight.to_dict(), "host_preparation": result.to_dict()}
        )
    else:
        print(f"Host preparation: {result.operation}")
        print(f"Status: {result.status.value}")
        print(_console_text(result.message))
        if result.evidence:
            print("Evidence:")
            for key, value in sorted(result.evidence.items()):
                print(f"- {key}: {_safe_console_value(value)}")
    if not result.succeeded:
        raise SystemExit(1)






async def _run_preflight_command(args: Namespace) -> None:
    node_provider_request = _node_provider_request_from_args(args)
    preflight = build_preflight_service(
        service_profile=args.service_profile,
        node_provider_request=node_provider_request,
        allow_wsl_windows_filesystem=args.allow_wsl_windows_filesystem,
    )
    live_consent = _live_consent_from_args(args) if args.live else None
    result = await preflight.run(live_consent)
    if _should_emit_json(args):
        _emit_json_payload(result.to_dict())
    else:
        _print_preflight_summary(result, live=args.live)
    if not result.passed:
        raise SystemExit(1)


async def _run_network_doctor_command(args: Namespace) -> None:
    report = await build_network_doctor_service().run()
    if _should_emit_json(args):
        _emit_json_payload(report.to_dict())
    else:
        print(report.render())
    if not report.passed:
        raise SystemExit(1)


async def _run_network_repair_command(args: Namespace) -> None:
    options = build_network_repair_options(
        runtime=args.runtime,
        linux_forwarding=bool(args.linux_forwarding),
        incus=bool(args.incus),
        apply=bool(args.apply),
    )
    report = await build_network_repair_service().run(options)
    if _should_emit_json(args):
        _emit_json_payload(report.to_dict())
    else:
        print(report.render())
    if not report.succeeded:
        raise SystemExit(1)


def _selected_workflow(args: Namespace) -> CliWorkflow | None:
    workflow = args.workflow
    if workflow is None:
        print("No workflow selected. Use --list-workflows to inspect available workflows.")
    return workflow


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




def _update_plan_from_args(args: Namespace) -> ClassicUpdatePlan | None:
    if (
        args.workflow is None
        or args.workflow.platform_kind is not PlatformWorkflowKind.UPDATE
        or args.recover
    ):
        return None
    return ClassicUpdatePlan(
        stack_name=args.stack,
        service_name=args.service,
        source_image=args.from_image,
        target_image=args.to_image,
    )










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


def _node_provider_request_from_args(args: Namespace) -> NodeProviderSelectionRequest | None:
    if args.node_provider == NodeProviderKind.LXC_NATIVE.value and args.lxc_backend is None:
        return None
    return NodeProviderSelectionRequest(
        requested_provider=NodeProviderKind(args.node_provider),
        preferred_backend=(
            None
            if args.lxc_backend is None
            else ManagedLxcBackend(args.lxc_backend)
        ),
    )




def _print_setup_installation_plan(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    compose_repository: PortComposeFileRepository | None = None,
) -> None:
    plan = build_setup_installation_plan(
        service_profile,
        compose_repository or build_compose_file_repository(),
    )
    _render_setup_installation_plan(
        plan,
        requested_provider=(node_provider_request or NodeProviderSelectionRequest()).requested_provider.value,
        preferred_backend=(node_provider_request or NodeProviderSelectionRequest()).preferred_backend,
    )


if __name__ == "__main__":
    cli()
