"""Explicit product target, read-only preview and existing live consent transport."""
from argparse import ArgumentParser, Namespace
import json

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure import composition


def validate_product_args(parser: ArgumentParser, args: Namespace):
    args.product_upgrade_command = (args.workflow_namespace, args.workflow_action) == ('product', 'upgrade')
    if not args.product_upgrade_command:
        if args.adoption_manifest is not None:
            parser.error('--adoption-manifest requires product upgrade')
        return
    if args.to != '0.5.0' or args.preview == args.live:
        parser.error('product upgrade requires --to 0.5.0 and exactly one of --preview or --live')
    if (args.preview and args.approve_live) or args.confirm or args.preflight or args.service_profile_explicit:
        parser.error('product upgrade cannot combine preview/approval, confirmation, preflight or preset overrides')
    if args.services or args.minimal or args.selection_config or args.runtime or args.apply or args.incus or args.linux_forwarding:
        parser.error('product upgrade uses the complete installed selection and cannot use selection/network options')
    if any(item is not None for item in (args.stack, args.service, args.from_image, args.to_image, args.lxc_backend)):
        parser.error('product upgrade uses the recorded Classic runtime, not platform/component overrides')
    if args.recover and args.adoption_manifest:
        parser.error('product recovery uses its pinned inventory; omit --adoption-manifest')


async def run_product_upgrade(args):
    from tiny_swarm_world.infrastructure.adapters.cli.consent import _live_consent_from_args

    service = None
    try:
        consent = None if args.preview else _live_consent_from_args(args)
        if consent is not None and not consent.accepted:
            result = {'status': 'refused', 'diagnostics': list(consent.missing_reasons)}
        else:
            service = composition.build_product_upgrade(adoption_file=args.adoption_manifest)
            if args.preview:
                result = await service.preview(args.to, recovery=args.recover)
            else:
                result = await service.run(args.to, consent=consent, recovery=args.recover)
    except LifecycleStateError as error:
        result = {'status': 'blocked', 'diagnostics': [str(error)],
                  'recovery': 'preserve source/checkpoint; use product upgrade --to 0.5.0 --recover --preview from management checkout'}
        if service is not None:
            try:
                checkpoint = service.journal.load()
                if checkpoint is not None and checkpoint.stage != 'completed':
                    result.update(status='failed', stage=checkpoint.stage)
            except LifecycleStateError:
                result.update(status='failed', stage='unknown; checkpoint unavailable')
    except ValueError:
        # Technical details/configuration/credentials never enter operator evidence.
        result = {'status': 'blocked', 'diagnostics': ['Product operation blocked; preserve source and checkpoint. Inspect release, inventory, host/resources and --recover --preview.']}
    except OSError:
        result = {'status': 'failed', 'diagnostics': ['Product storage unavailable; preserve staged state and inspect recovery.']}
    print(json.dumps(result, sort_keys=True, indent=None if args.json else 2))
    if result['status'] not in {'preview', 'verification_required', 'completed', 'no_op'}:
        raise SystemExit(2 if result['status'] == 'refused' else 1)
