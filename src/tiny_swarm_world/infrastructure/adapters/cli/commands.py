"""Host and network command adapter invocation."""

from argparse import Namespace

from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import (
    PortComposeFileRepository,
)
from tiny_swarm_world.application.services.platform.host.prepare_with_preflight import (
    PrepareHostWithPreflight,
)
from tiny_swarm_world.application.services.setup.installation_plan import (
    build_setup_installation_plan,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.infrastructure.adapters.cli.consent import (
    _live_consent_for_workflow,
    _live_consent_from_args,
)
from tiny_swarm_world.infrastructure.adapters.cli.parser import (
    _node_provider_request_from_args,
)
from tiny_swarm_world.infrastructure.adapters.cli.presentation import (
    _console_text,
    _emit_json_payload,
    _host_detection_payload,
    _print_host_environment_summary,
    _print_preflight_summary,
    _safe_console_value,
    _should_emit_json,
)
from tiny_swarm_world.infrastructure.adapters.cli.presentation import (
    render_setup_installation_plan as _render_setup_installation_plan,
)
from tiny_swarm_world.infrastructure.adapters.cli.registry import CLI_WORKFLOWS
from tiny_swarm_world.infrastructure.composition import (
    DEFAULT_SETUP_SERVICE_PROFILE,
    NodeProviderSelectionRequest,
    build_compose_file_repository,
    build_host_detection_service,
    build_host_preparation_service,
    build_network_doctor_service,
    build_network_repair_options,
    build_network_repair_service,
    build_preflight_service,
    build_read_only_hang_diagnostics,
)


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
