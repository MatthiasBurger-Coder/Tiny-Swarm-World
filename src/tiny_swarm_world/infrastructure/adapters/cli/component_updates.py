"""Read-only component transport; intentionally never initializes runtime services."""
from argparse import ArgumentParser, Namespace
import json
import re

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.component_updates import ComponentUpdateService
from tiny_swarm_world.domain.lifecycle.update_planning import UninstalledServiceError
from tiny_swarm_world.infrastructure.adapters.cli.selection import parse_service_ids
from tiny_swarm_world.infrastructure.composition import build_installation_lifecycle_service


def validate_component_args(parser: ArgumentParser, args: Namespace) -> None:
    command = (args.workflow_namespace, args.workflow_action)
    args.component_update_command = command in {("services", "updates"), ("services", "update")}
    if not args.component_update_command:
        if args.to is not None:
            parser.error("--to requires services update --services <id> --preview")
        return
    if args.live or args.approve_live or args.confirm or args.preflight:
        parser.error("component discovery/planning is read-only; live execution belongs to W06/W07")
    if (args.minimal or args.selection_config or args.service_profile_explicit or args.recover
            or any(value is not None for value in (args.stack, args.service, args.from_image, args.to_image))):
        parser.error("component discovery/planning cannot use setup selection or platform update options")
    preview = command == ("services", "update")
    if preview and (not args.preview or args.services is None):
        parser.error("services update requires explicit --services and --preview; execution is not available")
    if not preview and (args.preview or args.to is not None):
        parser.error("services updates is discovery; use services update for --to/--preview")
    try:
        args.selected_services = None if args.services is None else parse_service_ids(args.services)
    except ValueError as error:
        parser.error(str(error))
    if args.to is not None:
        if len(args.selected_services) != 1 or re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,99}", args.to) is None:
            parser.error("--to requires one selected service and a canonical catalog target ID")


def run_component_updates(args: Namespace) -> None:
    try:
        lifecycle = build_installation_lifecycle_service()
        service = ComponentUpdateService(lifecycle.manifests, lifecycle.catalog)
        if args.workflow_action == "updates":
            result = service.discover(args.selected_services)
        else:
            result = service.preview(args.selected_services, args.to).model_dump(mode="json")
    except (LifecycleStateError, UninstalledServiceError) as error:
        print(json.dumps({"status": "blocked", "diagnostics": [str(error)]}))
        raise SystemExit(1) from None
    except ValueError as error:
        print(json.dumps({"status": "invalid_selection", "diagnostics": [str(error)]}))
        raise SystemExit(2) from None
    print(json.dumps(result, sort_keys=True, indent=None if args.json else 2))
    if result["status"] == "blocked":
        raise SystemExit(1)
