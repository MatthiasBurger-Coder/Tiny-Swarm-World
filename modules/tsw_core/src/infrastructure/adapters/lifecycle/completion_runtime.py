"""Read-only whole-selection task proof with complete global-agent coverage."""
import json
import re
import shlex

import yaml

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership
from tiny_swarm_world.domain.update.runtime_observation import image_matches
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_api import GuardedPortainerStackApi
from tiny_swarm_world.infrastructure.adapters.lifecycle.product_runtime import ClassicProductRuntime, _read_json, verify_service


def image_reference(identity):
    if not identity.image_repository or not (identity.image_digest or identity.image_tag):
        raise LifecycleStateError('Selected completion image identity is unavailable.')
    return identity.image_repository + ('@' + identity.image_digest if identity.image_digest else ':' + identity.image_tag)


def task_ids(shell, command):
    result = shell.run_manager_shell(command, check=False)
    ids = result.stdout.split()
    if result.returncode or not ids or len(ids) > 1024 or len(set(ids)) != len(ids) or any(re.fullmatch('[a-z0-9]{1,128}', item) is None for item in ids):
        raise LifecycleStateError('Selected runtime IDs are unavailable or ambiguous.')
    return ids


def lines(shell, command):
    result = shell.run_manager_shell(command, check=False)
    try:
        if result.returncode:
            raise ValueError
        return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    except ValueError:
        raise LifecycleStateError('Selected completion runtime readback is unavailable.') from None


def node_inventory(shell, names):
    if not names or len(set(names)) != len(names):
        raise LifecycleStateError('Original manager/worker topology is unavailable.')
    ids = task_ids(shell, "docker node ls --no-trunc --format '{{.ID}}'")
    template = '{"id":{{json .ID}},"hostname":{{json .Description.Hostname}},"state":{{json .Status.State}},"availability":{{json .Spec.Availability}}}'
    rows = lines(shell, 'docker node inspect --format ' + shlex.quote(template) + ' -- ' + ' '.join(ids))
    if (len(rows) != len(ids) or any(not isinstance(row, dict) or set(row) != {'id', 'hostname', 'state', 'availability'} for row in rows)
            or any(any(not isinstance(value, str) for value in row.values()) for row in rows)
            or {row['id'] for row in rows} != set(ids) or {row['hostname'] for row in rows} != set(names)
            or len({row['hostname'] for row in rows}) != len(rows)
            or any(row['state'] != 'ready' or row['availability'] != 'active' for row in rows)):
        raise LifecycleStateError('Global agent topology differs from the admitted manager and workers.')
    return sorted(rows, key=lambda row: row['id'])


def verify_agent_nodes(shell, manifest, names):
    before_nodes = node_inventory(shell, names)
    component = next(item for item in manifest.components if item.component_id == 'portainer-agent')
    expected = [image_reference(value) for value in (component.desired, component.observed) if value is not None]
    template = '{"id":{{json .ID}},"version":{{json .Version.Index}},"image":{{json .Spec.TaskTemplate.ContainerSpec.Image}},"mode":{{json .Spec.Mode}}}'
    command = 'docker service inspect --format ' + shlex.quote(template) + ' -- portainer_agent'
    service = _read_json(shell, command)
    if (not isinstance(service, dict) or set(service) != {'id', 'version', 'image', 'mode'}
            or not isinstance(service['id'], str) or not service['id'] or type(service['version']) is not int
            or service['version'] <= 0 or not isinstance(service['image'], str)
            or service['mode'] != {'Global': {}} or not all(image_matches(service['image'], image) for image in expected)):
        raise LifecycleStateError('Mandatory Portainer agent is not the admitted global image service.')
    ids = task_ids(shell, "docker service ps --no-trunc --format '{{.ID}}' -- portainer_agent")
    task = '{"node":{{json .NodeID}},"image":{{json .Spec.ContainerSpec.Image}},"state":{{json .Status.State}},"desired":{{json .DesiredState}}}'
    rows = lines(shell, 'docker inspect --type task --format ' + shlex.quote(task) + ' -- ' + ' '.join(ids))
    if any(not isinstance(row, dict) or set(row) != {'node', 'image', 'state', 'desired'}
           or any(not isinstance(value, str) for value in row.values()) for row in rows):
        raise LifecycleStateError('Mandatory global agent task readback is invalid.')
    current = [row for row in rows if row['desired'] == 'running' or row['state'] == 'running']
    if (len(rows) != len(ids) or len(current) != len(before_nodes)
            or {row['node'] for row in current} != {node['id'] for node in before_nodes}
            or any(row['state'] != 'running' or row['desired'] != 'running'
                   or not all(image_matches(row['image'], image) for image in expected) for row in current)
            or _read_json(shell, command) != service or node_inventory(shell, names) != before_nodes):
        raise LifecycleStateError('Mandatory global agent does not cover every admitted node with converged tasks.')


def verify_selected_runtime(shell, client, root, manifest, node_names):
    def swarm_identity():
        result = shell.run_manager_shell("docker info --format '{{.Swarm.Cluster.ID}}'", check=False)
        if result.returncode or not result.stdout.strip():
            raise LifecycleStateError('Actual local Swarm identity unavailable during completion.')
        return result.stdout.strip()
    management = GuardedPortainerStackApi(client, swarm_identity)
    endpoint = management.local_endpoint()  # Mandatory even with no Portainer-owned optional stack.
    owners = manifest.effective_stack_ownership()
    for name, owner in owners.items():
        if isinstance(owner, PortainerOwnership) and management.inspect(name, owner.endpoint_id, owner.stack_id).ownership != owner:
            raise LifecycleStateError('Original managed ownership changed before completion task proof.')
    inventory = ClassicProductRuntime(root, lambda: shell, lambda: client, None, None)._inventory(manifest)
    selected = {item.component_id: item for item in manifest.components}
    for service in NativeComponentCatalog(root).load().services:
        if service.service_id not in manifest.resolved_services or service.native_asset is None:
            continue
        native = yaml.safe_load((root / service.native_asset).read_text())['services']
        for member, definition in native.items():
            component = NativeComponentCatalog._component(service.service_id, definition)
            observed = selected[component.component_id].observed
            if observed is not None and verify_service(shell, service.service_id + '_' + member,
                    image_reference(observed), one_shot=component.component_id == 'pulsar-manager-bootstrap') != inventory[component.component_id]:
                raise LifecycleStateError('Original observed component service identity changed.')
    verify_agent_nodes(shell, manifest, node_names)
    if management.local_endpoint() != endpoint:
        raise LifecycleStateError('Mandatory authenticated local endpoint changed during completion.')
    for name, owner in owners.items():
        if isinstance(owner, PortainerOwnership) and management.inspect(name, owner.endpoint_id, owner.stack_id).ownership != owner:
            raise LifecycleStateError('Original managed ownership changed after completion task proof.')
