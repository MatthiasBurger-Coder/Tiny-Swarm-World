"""CLI option parsing and transport request construction."""

from argparse import ArgumentParser, Namespace
from collections.abc import Sequence

from tiny_swarm_world.application.services.platform.workflow.types import (
    PlatformWorkflowKind,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend, NodeProviderKind
from tiny_swarm_world.domain.update import ClassicUpdatePlan
from tiny_swarm_world.infrastructure.adapters.cli.registry import CLI_WORKFLOWS_BY_KEY
from tiny_swarm_world.infrastructure.composition import (
    DEFAULT_SETUP_SERVICE_PROFILE,
    NodeProviderSelectionRequest,
)


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
