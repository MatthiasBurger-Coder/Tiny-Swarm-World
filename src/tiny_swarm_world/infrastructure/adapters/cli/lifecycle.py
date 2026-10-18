"""Read-only lifecycle CLI, intentionally preceding all runtime composition."""
from argparse import Namespace
import json

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.composition import build_installation_lifecycle_service


async def run_lifecycle_inspection(args: Namespace) -> None:
    if args.component_update_command:
        from tiny_swarm_world.infrastructure.adapters.cli.component_updates import run_component_updates

        await run_component_updates(args)
        return
    try:
        result = build_installation_lifecycle_service().inspect()
    except LifecycleStateError as error:
        print(json.dumps({"status": "blocked", "diagnostics": [str(error)]}))
        raise SystemExit(1) from None
    if args.workflow_namespace == "product":
        result.pop("catalog")
    else:
        manifest = result["manifest"]
        selected = set() if manifest is None else set(manifest["resolved_services"])
        for service in result["catalog"]["services"]:
            service["installation_state"] = ("unknown" if manifest is None else
                                             "installed" if service["service_id"] in selected else "uninstalled")
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
