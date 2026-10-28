"""Execute selection-aware verification using the staged target's actual code."""
import os
from pathlib import Path
import sys

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_migration import verify_product_infra

TARGET_VERIFICATION = '''
import asyncio, sys
from tiny_swarm_world.domain.lifecycle.models import InstallationManifest
from tiny_swarm_world.infrastructure.composition import build_platform_services, build_deployment_services_for_provider
manifest = InstallationManifest.model_validate_json(sys.stdin.read())
async def verify():
    options = dict(service_profile=manifest.service_preset, resolved_services=manifest.resolved_services)
    platform = build_platform_services(**options)
    deployment = build_deployment_services_for_provider(**options)
    for workflow in (platform.workflows.cluster.verify, platform.workflows.verify, deployment.workflows.verify):
        result = await workflow.run()
        if getattr(result.status, 'value', result.status) != 'completed':
            raise SystemExit(1)
asyncio.run(verify())
print('target-runtime-verified')
'''


def verify_target_runtime(installation, plan):
    verify_product_infra(installation, plan)
    code = installation.directory(plan)
    _verify_selection(installation, plan.manifest, code, code / '.venv/bin/python',
                      installation.state / 'infra' / plan.target.product.revision)


def verify_bound_runtime(installation, plan, manifest):
    """Run this controller's full verifier with isolated child configuration."""
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_configuration_source import runtime_source

    expected = plan.manifest.model_copy(update={'product': plan.target.product})
    if manifest not in (plan.manifest, expected):
        raise LifecycleStateError('Runtime verification differs from the admitted installation selection.')
    infra = runtime_source(installation, plan)
    controller = Path(__file__).resolve().parents[4].parent
    _verify_selection(installation, manifest, controller, Path(sys.executable), infra)
    return infra


def _verify_selection(installation, manifest, code, python, infra):
    environment = {**os.environ, 'PYTHONPATH': str(code / 'src'),
                   'TSW_REPOSITORY_ROOT': str(installation.root),
                   'TSW_INFRA_ROOT': str(infra)}
    result = installation._command((str(python), '-c', TARGET_VERIFICATION),
        cwd=code, env=environment, input=manifest.model_dump_json(), timeout=600)
    if not result.endswith('target-runtime-verified'):
        raise LifecycleStateError('Prepared runtime could not verify the complete installed selection.')
