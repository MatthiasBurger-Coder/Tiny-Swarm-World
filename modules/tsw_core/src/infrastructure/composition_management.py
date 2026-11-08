"""Explicit operation-bound optional-stack management writer composition."""
from pathlib import Path
from collections.abc import Mapping
import logging

import yaml

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.deployment.managed_stack import ManagedStackOperation
from tiny_swarm_world.application.services.shared.settled_blocking import settled_blocking
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership
from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_api import GuardedPortainerStackApi, definition_fingerprint
from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_journal import JsonManagedStackJournal
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway import LxcManagerShellGateway
from tiny_swarm_world.infrastructure.adapters.update.lxc_runtime_observer import LxcUpdateRuntimeObserver


def _pinned_definition(definition: StackDefinition, images: Mapping[str, str]) -> StackDefinition:
    payload = yaml.safe_load(definition.compose_content)
    if not isinstance(payload, dict) or not isinstance(payload.get('services'), dict) or set(payload['services']) != set(images):
        raise LifecycleStateError('Managed definition differs from the admitted service inventory.')
    for name, image in images.items():
        payload['services'][name]['image'] = image
    return StackDefinition(name=definition.name, compose_content=yaml.safe_dump(payload, sort_keys=True))


class ManagedDeploymentWriter:
    def __init__(self, *, root: Path, profile_operation, client, runtime, compose_repository, backend):
        self.root, self.operation = root, profile_operation
        self.client, self.runtime, self.repository, self.backend = client, runtime, compose_repository, backend

    async def apply(self, definition: StackDefinition, environment: Mapping[str, str]) -> None:
        operation = self.operation
        if operation is None:
            raise LifecycleStateError('Managed deployment requires an explicitly bound installation operation.')
        operation.lease.require_active()
        intent = operation.intent
        name = definition.name
        if intent.planned_stack_owners.get(name) != 'portainer':
            raise LifecycleStateError('Managed writer differs from the durably planned management mode.')
        images = {item.name: item.image_ref for item in self.repository.get_services_of(name)}
        target = _pinned_definition(definition, images)
        gateway = LxcManagerShellGateway(backend=self.backend, manager_node='swarm-manager', timeout_seconds=15,
                                         logger=logging.getLogger('managed_stack_observer'))
        def swarm_identity():
            result = gateway.run_manager_shell("docker info --format '{{.Swarm.Cluster.ID}}'", check=False)
            value = result.stdout.strip()
            if result.returncode or not value or len(value) > 128:
                raise LifecycleStateError('Actual local Swarm identity unavailable.')
            return value
        api = GuardedPortainerStackApi(self.client._client(), swarm_identity)
        baseline = intent.profile.stack_ownership.get(name)
        owner = baseline if isinstance(baseline, PortainerOwnership) else None
        # A recovered setup uses verified journal ownership, never a same-name lookup.
        recorded = getattr(operation, 'verified_stack_ownership', {}).get(name)
        if recorded is not None:
            owner = recorded
        effective = dict(environment)
        if owner is not None:
            current = await settled_blocking(api.inspect, name, owner.endpoint_id, owner.stack_id)
            if current.ownership != owner:
                # An unsettled management journal may legitimately bind old and new definitions.
                previous = JsonManagedStackJournal(self.root / '.tiny-swarm-world/installation' / f'managed-stack-{name}.json', operation.lease).load()
                if previous is None or previous.source != owner:
                    raise LifecycleStateError('Managed ownership differs from the installation checkpoint.')
            if any(key not in current.environment or current.environment[key] != value
                   for key, value in environment.items() if not key.endswith('_IMAGE')):
                raise LifecycleStateError('Managed setup cannot replace existing effective environment/credentials.')
            effective = dict(current.environment)
        managed = ManagedStackOperation(api,
            JsonManagedStackJournal(self.root / '.tiny-swarm-world/installation' / f'managed-stack-{name}.json', operation.lease),
            LxcUpdateRuntimeObserver(gateway), installation_id=intent.profile.installation_id, lease=operation.lease)
        # Asset/network preparation is part of the already checkpointed operation;
        # it never invokes a direct-Swarm stack deployment.
        await settled_blocking(self.runtime.prepare_stack_assets, name)
        await settled_blocking(self.client._ensure_external_overlay_networks, target)
        async def verified(value):
            await operation.verify_effective_routes()
            await operation.record_stack_ownership(name, value)
        await managed.apply(target, effective, images, definition_fingerprint(target, effective), owner, verified)


async def verify_completed_stacks(root, manifest, backend, *, node_names):
    """Read-only full selected proof, mandatory gateway included for minimal setup."""
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client import LxcPortainerHttpClient
    from tiny_swarm_world.infrastructure.adapters.lifecycle.completion_runtime import verify_selected_runtime
    from tiny_swarm_world.infrastructure.project_paths import default_project_paths
    from tiny_swarm_world.infrastructure.composition_configuration import _required_operator_secret_value

    if default_project_paths().repository_root != root:
        raise LifecycleStateError('Original completion source root differs from configured repository.')
    gateway = LxcManagerShellGateway(backend=backend, manager_node='swarm-manager', timeout_seconds=15,
                                     logger=logging.getLogger('creation_completion_observer'))
    client = LxcPortainerHttpClient(backend=backend, username='admin',
        password=_required_operator_secret_value('TSW_PORTAINER_ADMIN_PASSWORD'))
    await settled_blocking(verify_selected_runtime, gateway, client._client(), root, manifest, node_names)
