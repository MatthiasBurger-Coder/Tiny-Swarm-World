"""Execute selection-aware verification using the staged target's actual code."""
import os

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
    environment = {**os.environ, 'PYTHONPATH': str(code / 'src'),
                   'TSW_REPOSITORY_ROOT': str(installation.root),
                   'TSW_INFRA_ROOT': str(installation.state / 'infra' / plan.target.product.revision)}
    result = installation._command((str(code / '.venv/bin/python'), '-c', TARGET_VERIFICATION),
        cwd=code, env=environment, input=plan.manifest.model_dump_json(), timeout=600)
    if not result.endswith('target-runtime-verified'):
        raise LifecycleStateError('Staged target runtime could not verify the complete installed selection.')
