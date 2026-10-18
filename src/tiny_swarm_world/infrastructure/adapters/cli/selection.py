"""Read-only selection transport; never compose the infrastructure runtime."""
from argparse import ArgumentParser, Namespace
import json
from pathlib import Path
import re

import yaml

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.infrastructure.composition import build_installation_lifecycle_service


def parse_service_ids(value: str) -> tuple[str, ...]:
    services = tuple(value.split(","))
    if any(re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,99}", name) is None for name in services):
        raise ValueError("Use comma-separated canonical lowercase service IDs without empty entries or wildcards.")
    if len(set(services)) != len(services):
        raise ValueError("Duplicate service IDs are not allowed.")
    return services


def _configured_services(path: str | None) -> tuple[str, ...] | None:
    if path is None:
        return None
    try:
        root = Path.cwd().resolve(strict=True)
        selected = Path(path).resolve(strict=True)
        if not selected.is_relative_to(root) or not selected.is_file():
            raise ValueError("Selection config must be a regular file within the current working directory.")
        payload = yaml.safe_load(selected.read_text(encoding="utf-8"))
    except (OSError, RuntimeError, UnicodeError, yaml.YAMLError):
        raise ValueError("Cannot read selection config; supply a readable YAML/JSON services list.") from None
    if not isinstance(payload, dict) or set(payload) != {"services"}:
        raise ValueError("Selection config must contain only a services list.")
    services = payload["services"]
    if not isinstance(services, list) or not services or any(not isinstance(name, str) or "," in name for name in services):
        raise ValueError("Selection config requires a nonempty list of canonical service IDs; use --minimal for foundations.")
    return parse_service_ids(",".join(services))


def run_selection_preview(args: Namespace) -> None:
    try:
        lifecycle = build_installation_lifecycle_service()
        service = ServiceSelectionService(lifecycle.manifests, lifecycle.catalog)
        removal = args.workflow_namespace == "services" and args.workflow_action == "remove"
        # Explicit CLI selection wins without reading an unused config file.
        configured = None if args.services is not None else _configured_services(args.selection_config)
        plan = service.preview(
            requested=None if removal else args.selected_services,
            configured=configured,
            minimal=args.minimal,
            preset=args.service_profile if args.service_profile_explicit else None,
            remove=args.selected_services if removal else (),
            add=args.workflow_namespace == "services" and args.workflow_action == "add",
        )
    except LifecycleStateError as error:
        print(json.dumps({"status": "blocked", "diagnostics": [str(error)]}))
        raise SystemExit(1) from None
    except ValueError as error:
        print(json.dumps({"status": "invalid_selection", "diagnostics": [str(error)]}))
        raise SystemExit(2) from None
    print(json.dumps({"status": "selection_preview", "plan": plan.model_dump(mode="json"),
                      "execution": "not performed (read-only preview)",
                      "data_policy": "deployments and persistent data are retained"},
                     sort_keys=True, indent=None if args.json else 2))

def validate_selection_args(parser: ArgumentParser, args: Namespace) -> None:
    if args.component_update_command:
        args.selection_preview = False
        return
    command = (args.workflow_namespace, args.workflow_action)
    selection_options = args.services is not None or args.minimal or args.selection_config is not None
    selection_command = command in {("services", "add"), ("services", "remove")}
    args.selection_preview = args.preview and (selection_command or command == ("setup", "run"))
    if selection_options and not (selection_command or command == ("setup", "run")):
        parser.error("selection options require setup run or services add/remove")
    if selection_command or args.selection_preview or selection_options:
        if args.preview and (args.live or args.approve_live or args.confirm or args.preflight):
            parser.error("selection preview requires --preview without live/consent/preflight flags")
        if command == ("services", "remove") and not args.preview:
            parser.error("service removal is preview-only; deployments and data are retained")
        if not args.preview and (args.preflight or not args.live):
            parser.error("selection apply requires --live and existing live consent; use --preview to inspect")
        if args.minimal and (args.services is not None or args.selection_config or args.service_profile_explicit):
            parser.error("--minimal conflicts with --services, --selection-config and explicit --service-profile")
        if selection_command and (args.services is None or args.minimal or args.selection_config or args.service_profile_explicit):
            parser.error("services add/remove requires --services and forbids presets/config/minimal")
        if args.recover or any(value is not None for value in (args.stack, args.service, args.from_image, args.to_image)):
            parser.error("selection cannot use platform update options")
        if args.services is not None:
            try:
                args.selected_services = parse_service_ids(args.services)
            except ValueError as error:
                parser.error(str(error))
        else:
            args.selected_services = None
