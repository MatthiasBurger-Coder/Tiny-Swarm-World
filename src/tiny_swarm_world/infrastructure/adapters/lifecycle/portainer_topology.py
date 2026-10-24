"""API-independent identity, placement and data binding admission."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError


def inspect_topology(state, *, before=None, allow_stopped=False):
    services = state.services()
    server, agent = services['portainer_portainer'], services['portainer_agent']
    mode = server['Spec']['Mode']
    replicas = mode.get('Replicated', {}).get('Replicas')
    if set(mode) != {'Replicated'} or type(replicas) is not int or replicas not in ({0, 1} if allow_stopped else {1}):
        raise LifecycleStateError('Only a single replicated Portainer server is supported.')
    if 'Global' not in agent['Spec']['Mode']:
        raise LifecycleStateError('Only global Classic Portainer agents are supported.')
    template = server['Spec']['TaskTemplate']
    if 'node.role == manager' not in template.get('Placement', {}).get('Constraints', []):
        raise LifecycleStateError('Portainer server must be constrained to the single manager.')
    managers = state.run("docker node ls --filter role=manager --format '{{.ID}}'").splitlines()
    if len(managers) != 1:
        raise LifecycleStateError('Only Classic single-manager topology is supported.')
    mounts = [item for item in template['ContainerSpec']['Mounts'] if item['Target'] == '/data']
    if len(mounts) != 1 or mounts[0]['Type'] != 'volume' or mounts[0].get('ReadOnly', False):
        raise LifecycleStateError('Portainer /data requires a writable local named volume.')
    volume = mounts[0]['Source']
    swarm = state.run("docker info --format '{{.Swarm.Cluster.ID}}'")
    if not swarm:
        raise LifecycleStateError('Manager Swarm identity unavailable.')
    if before is not None and (volume, swarm, server['ID'], agent['ID']) != (
            before.volume, before.swarm_id, before.server_id, before.agent_id):
        raise LifecycleStateError('Portainer data binding, service or Swarm identity changed; no recovery mutation admitted.')
    return services, volume, swarm
