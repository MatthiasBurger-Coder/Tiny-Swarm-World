import asyncio
import json
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from tiny_swarm_world.application.services.artifacts import ArtifactWorkflowResult
from tiny_swarm_world.application.services.deployment import DeploymentWorkflowResult
from tiny_swarm_world.application.services.setup import SetupWorkflowResult
from tiny_swarm_world.application.services.platform.workflow_taxonomy import (
    PLATFORM_WORKFLOW_TAXONOMY,
    PlatformWorkflowKind,
    PlatformWorkflowResult,
    PlatformWorkflowStatus,
)
from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.deployment.stack_definition import ComposeServiceDefinition
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend, NodeProviderKind
from tiny_swarm_world.domain.preflight import (
    LIVE_CONSENT_PROMPT,
    LIVE_CONSENT_YES_VALUES,
    LiveConsent,
    PreflightResult,
    default_preflight_configuration,
)
from tiny_swarm_world.infrastructure.composition import (
    ApplicationServices,
    ArtifactServices,
    DeploymentServices,
    DEFAULT_SETUP_SERVICE_PROFILE,
    NodeProviderSelectionRequest,
    SetupServices,
    build_application_services,
    build_artifact_services_for_provider,
    build_compose_file_repository,
    build_deployment_services_for_provider,
    build_preflight_service,
    build_application_logger,
    run_setup_with_terminal_status,
)
from tiny_swarm_world.infrastructure.adapters.preflight import ensure_common_executable_paths

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
        return self.platform_kind is not None or self.namespace in {"artifacts", "deployment", "setup"}


PLATFORM_WORKFLOW_ORDER = (
    PlatformWorkflowKind.INIT,
    PlatformWorkflowKind.RECONCILE,
    PlatformWorkflowKind.EXPOSE,
    PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT,
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
        "--node-provider",
        choices=[NodeProviderKind.LXC_NATIVE.value],
        default=NodeProviderKind.LXC_NATIVE.value,
        help="Node provider for platform setup; default is lxc_native.",
    )
    parser.add_argument(
        "--lxc-backend",
        choices=[backend.value for backend in ManagedLxcBackend],
        help="Preferred managed LXC backend when --node-provider lxc_native is selected.",
    )
    parser.add_argument("workflow_namespace", nargs="?", help="Workflow namespace.")
    parser.add_argument("workflow_action", nargs="?", help="Workflow action.")
    args = parser.parse_args(argv)

    if args.lxc_backend is not None and args.node_provider != NodeProviderKind.LXC_NATIVE.value:
        parser.error("--lxc-backend requires --node-provider lxc_native")

    if (args.workflow_namespace is None) != (args.workflow_action is None):
        parser.error("workflow command requires both namespace and action")

    args.workflow = None
    if args.workflow_namespace is not None and args.workflow_action is not None:
        args.workflow = CLI_WORKFLOWS_BY_KEY.get((args.workflow_namespace, args.workflow_action))
        if args.workflow is None:
            parser.error(f"unsupported workflow command: {args.workflow_namespace} {args.workflow_action}")

    return args


async def main(argv: Sequence[str] | None = None) -> None:
    ensure_common_executable_paths()
    args = parse_args(argv)

    logger = build_application_logger()
    logger.info("Starting application")

    if args.list_workflows:
        _print_workflow_list()
        return

    if args.preflight:
        await _run_preflight_command(args)
        return

    workflow = _selected_workflow(args)
    if workflow is None:
        return

    _enforce_workflow_confirmation(workflow, args.confirm)
    _enforce_workflow_implementation(workflow)
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
    )
    if isinstance(result, SetupWorkflowResult):
        _print_setup_installation_summary(result)
    print(json.dumps(_workflow_result_to_dict(result), indent=2, sort_keys=True))
    if _workflow_status_value(result) != PlatformWorkflowStatus.COMPLETED.value:
        raise SystemExit(1)

    logger.info("Done")


def cli(argv: Sequence[str] | None = None) -> None:
    asyncio.run(main(argv))


def _print_workflow_list() -> None:
    for workflow in CLI_WORKFLOWS:
        print(f"{workflow.name}\tmutating={workflow.mutating}\tdestructive={workflow.destructive}")


async def _run_preflight_command(args: Namespace) -> None:
    node_provider_request = _node_provider_request_from_args(args)
    preflight = build_preflight_service(
        service_profile=args.service_profile,
        node_provider_request=node_provider_request,
    )
    live_consent = _live_consent_from_args(args) if args.live else None
    result = await preflight.run(live_consent)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    _print_preflight_summary(result, live=args.live)
    if not result.passed:
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


def _enforce_workflow_implementation(workflow: CliWorkflow) -> None:
    if workflow.implemented:
        return
    print(
        json.dumps(
            _blocked_workflow_result(workflow),
            indent=2,
            sort_keys=True,
        )
    )
    raise SystemExit(1)


def _live_consent_for_workflow(
    workflow: CliWorkflow,
    args: Namespace,
) -> LiveConsent | None:
    if not workflow.mutating:
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
) -> WorkflowResult:
    if workflow.platform_kind is not None:
        services = build_application_services(
            live_consent=live_consent,
            service_profile=service_profile,
            node_provider_request=node_provider_request,
        )
        return await run_platform_workflow(
            services,
            workflow.platform_kind,
            confirmation,
        )
    if workflow.namespace == "artifacts":
        services = build_artifact_services_for_provider(
            node_provider_request=node_provider_request,
        )
        return await run_artifact_workflow(services, workflow.action)
    if workflow.namespace == "deployment":
        services = build_deployment_services_for_provider(
            service_profile=service_profile,
            node_provider_request=node_provider_request,
        )
        return await run_deployment_workflow(services, workflow.action)
    if workflow.namespace == "setup":
        if live_consent is None or not live_consent.accepted:
            raise ValueError("setup run requires accepted live consent")
        return await run_setup_with_terminal_status(
            live_consent,
            workflow.action,
            service_profile=service_profile,
            node_provider_request=node_provider_request,
        )
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
        case PlatformWorkflowKind.EXPOSE:
            return await workflows.expose.run()
        case PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT:
            return await workflows.repair_lxc_proxy_drift.run()
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
        case "bootstrap":
            return await workflows.bootstrap.run()
        case "apply":
            return await workflows.apply.run()
        case "verify":
            return await workflows.verify.run()
        case _:
            raise ValueError(f"Unsupported deployment workflow: {action}")


async def run_setup_workflow(
    services: SetupServices,
    action: str,
) -> SetupWorkflowResult:
    match action:
        case "run":
            return await services.workflows.run.run()
        case _:
            raise ValueError(f"Unsupported setup workflow: {action}")


def _workflow_result_to_dict(result: WorkflowResult) -> dict[str, object]:
    if isinstance(result, ArtifactWorkflowResult | DeploymentWorkflowResult | SetupWorkflowResult):
        return result.to_dict()
    return result.to_dict()


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
    confirmed = bool(args.approve_live)
    if args.live:
        if not confirmed:
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


def _print_preflight_summary(result: PreflightResult, *, live: bool = False) -> None:
    print()
    print(f"Preflight summary: {result.status}")
    if result.passed:
        if live:
            print("Preflight checks passed; provider readiness is checked by the platform guard.")
        else:
            print("Static checks passed; this does not claim live provider readiness.")
        return

    if result.resource_gated:
        print("Only resource-gated checks failed. Use a larger host or a smaller setup profile.")
    else:
        print("Fix the mandatory blockers before live setup.")

    for check in result.failed_checks:
        print(f"- {check.check_id}: {check.message}")
        if check.remediation and check.remediation != "None":
            print(f"  Action: {check.remediation}")


def _print_setup_installation_plan(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    compose_repository: PortComposeFileRepository | None = None,
) -> None:
    selected_service_profile = ServiceStackProfile(service_profile)
    configuration = default_preflight_configuration(service_profile=selected_service_profile)
    manifest = configuration.setup_manifest
    provider_request = node_provider_request or NodeProviderSelectionRequest()
    print()
    print("Tiny Swarm World guided installation")
    print("Target: local Linux/WSL LXC-native Docker Swarm")
    print(f"Default node provider: {provider_request.requested_provider.value}")
    if provider_request.preferred_backend is None:
        print("Managed backend: auto-detect Incus or LXD")
    else:
        print(f"Managed backend: {provider_request.preferred_backend.value}")
    print("Provider readiness: checked before platform mutation")
    print(f"Service profile: {selected_service_profile.value}")
    print("Platform:")
    print("- swarm-manager: Docker Swarm manager")
    print("- swarm-worker-1: Docker Swarm worker")
    print("- swarm-worker-2: Docker Swarm worker")
    print("Installation phases:")
    for phase in (
        "preflight",
        "platform init",
        "platform reconcile",
        "platform expose",
        "deployment bootstrap",
        "artifacts prepare",
        "artifacts verify",
        "deployment apply",
        "deployment verify",
        "platform verify",
    ):
        print(f"- {phase}")
    print("Services:")
    stack_names = {
        "Jenkins": "jenkins",
        "Infisical": "infisical",
        "Nexus": "nexus",
        "Portainer": "portainer",
        "RabbitMQ": "rabbitmq",
        "Service Access": "service-access",
        "SonarQube": "sonarqube",
        "Swagger/NGINX": "swagger",
        "Traefik Ingress": "traefik",
    }
    repository = compose_repository or build_compose_file_repository()
    for service in manifest.services:
        stack_name = stack_names.get(service.name, "infra")
        compose_services = _compose_services_for_plan(repository, stack_name)
        compose_service_names = _format_compose_service_names(compose_services)
        ports = _format_compose_published_ports(compose_services)
        print(
            f"- {service.name}: stack {stack_name}, "
            f"source infra/config/compose/{stack_name}/docker-compose.yml, "
            f"compose service(s) {compose_service_names}, published port(s) {ports}"
        )
    print()


def _compose_services_for_plan(
    repository: PortComposeFileRepository,
    stack_name: str,
) -> tuple[ComposeServiceDefinition, ...]:
    try:
        return repository.get_services_of(stack_name)
    except FileNotFoundError:
        return ()


def _format_compose_service_names(
    services: tuple[ComposeServiceDefinition, ...],
) -> str:
    return ", ".join(service.name for service in services) or "not declared"


def _format_compose_published_ports(
    services: tuple[ComposeServiceDefinition, ...],
) -> str:
    published_ports = tuple(
        dict.fromkeys(
            port
            for service in services
            for port in service.published_ports
        )
    )
    return ", ".join(str(port) for port in published_ports) or "no published port"


def _print_setup_installation_summary(result: SetupWorkflowResult) -> None:
    print()
    print("Setup phase summary:")
    for phase in result.phase_results:
        print(f"- {phase.name}: {phase.status}")
    print(f"Final setup status: {result.status.value}")
    print()


if __name__ == "__main__":
    cli()
