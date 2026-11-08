"""Component transport; preview and discovery never initialize runtime services."""
from argparse import ArgumentParser, Namespace
import json
import re

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.component_updates import ComponentUpdateService
from tiny_swarm_world.domain.lifecycle.update_planning import UninstalledServiceError
from tiny_swarm_world.infrastructure.adapters.cli.selection import parse_service_ids
from tiny_swarm_world.infrastructure.composition import build_installation_lifecycle_service, build_component_update_execution, build_component_update_journal, build_portainer_upgrade, build_portainer_upgrade_journal


def validate_component_args(parser: ArgumentParser, args: Namespace) -> None:
    from tiny_swarm_world.infrastructure.adapters.cli.product_upgrade import validate_product_args

    validate_product_args(parser, args)
    command = (args.workflow_namespace, args.workflow_action)
    args.component_update_command = command in {("services", "updates"), ("services", "update")}
    if not args.component_update_command:
        if args.to is not None and not args.product_upgrade_command:
            parser.error("--to requires services update --services <id> --preview")
        return
    update = command == ("services", "update")
    if (args.minimal or args.selection_config or args.service_profile_explicit or args.confirm or args.preflight
            or any(value is not None for value in (args.stack, args.service, args.from_image, args.to_image))):
        parser.error("component updates cannot use setup selection or platform update options")
    if update:
        if args.services is None or args.preview == args.live:
            parser.error("services update requires --services and exactly one of --preview or --live")
        if args.preview and args.approve_live:
            parser.error("preview cannot use live approval")
        if args.recover and args.to is not None:
            parser.error("recovery uses the original journal; omit --to")
    elif args.preview or args.to is not None or args.live or args.approve_live or args.recover:
        parser.error("services updates is read-only discovery")
    try:
        args.selected_services = None if args.services is None else parse_service_ids(args.services)
    except ValueError as error:
        parser.error(str(error))
    if args.to is not None:
        if len(args.selected_services) != 1 or re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,99}", args.to) is None:
            parser.error("--to requires one selected service and a canonical catalog target ID")


async def run_component_updates(args: Namespace) -> None:
    try:
        lifecycle = build_installation_lifecycle_service()
        service = ComponentUpdateService(lifecycle.manifests, lifecycle.catalog)
        if args.workflow_action == "updates":
            result = service.discover(args.selected_services)
        elif args.selected_services == ('portainer',):
            result = await _run_portainer(args, lifecycle)
        elif args.preview:
            if args.recover:
                from tiny_swarm_world.application.services.component_execution import component_recovery_preview

                result = component_recovery_preview(build_component_update_journal(lifecycle),
                                                    args.selected_services)
            else:
                result = service.preview(args.selected_services, args.to).model_dump(mode="json")
        else:
            from tiny_swarm_world.infrastructure.adapters.cli.consent import _live_consent_from_args
            from tiny_swarm_world.infrastructure.adapters.cli.parser import _node_provider_request_from_args

            consent = _live_consent_from_args(args)
            if not consent.accepted:
                print(json.dumps({'status': 'refused', 'diagnostics': list(consent.missing_reasons)}))
                raise SystemExit(2)
            # Admission remains local. No runtime adapter is built for blocked plans.
            if not args.recover:
                plan = service.preview(args.selected_services, args.to)
                # Interrupted commits must resume from the original journal even when
                # recorded observations now differ from the original preview.
                if plan.status == 'blocked':
                    journal = build_component_update_journal(lifecycle).load()
                    if journal is None:
                        raise LifecycleStateError('Update plan blocked; inspect supported transitions and restrictions.')
            executor = build_component_update_execution(lifecycle, _node_provider_request_from_args(args))
            result = await executor.run(args.selected_services, args.to, consent=consent, recovery=args.recover)
    except (LifecycleStateError, UninstalledServiceError) as error:
        print(json.dumps({"status": "blocked", "diagnostics": [str(error)]}))
        raise SystemExit(1) from None
    except ValueError as error:
        print(json.dumps({"status": "invalid_selection", "diagnostics": [str(error)]}))
        raise SystemExit(2) from None
    print(json.dumps(result, sort_keys=True, indent=None if args.json else 2))
    if result["status"] not in {"discovered", "preview", "no_op", "completed", "recovered"}:
        raise SystemExit(2 if result['status'] == 'refused' else 1)


async def _run_portainer(args, lifecycle):
    from tiny_swarm_world.infrastructure.adapters.cli.portainer_upgrade import portainer_preview, require_no_component_batch
    from tiny_swarm_world.infrastructure.adapters.cli.consent import _live_consent_from_args
    from tiny_swarm_world.infrastructure.adapters.cli.parser import _node_provider_request_from_args

    preview = portainer_preview(lifecycle, target=args.to, recovery=args.recover)
    if args.preview:
        return preview
    consent = _live_consent_from_args(args)
    if not consent.accepted:
        return {'status': 'refused', 'diagnostics': list(consent.missing_reasons)}
    require_no_component_batch(lifecycle)
    executor = build_portainer_upgrade(lifecycle, _node_provider_request_from_args(args))
    try:
        return await executor.run(target=args.to, consent=consent, recovery=args.recover)
    except LifecycleStateError as error:
        checkpoint = build_portainer_upgrade_journal(lifecycle).load()
        return {'status': 'failed' if checkpoint is not None and not checkpoint.settled else 'blocked',
                'stage': None if checkpoint is None else checkpoint.stage,
                'diagnostics': [str(error)], 'recovery': 'preserve checkpoint/backup; inspect services update --services portainer --recover --preview'}
