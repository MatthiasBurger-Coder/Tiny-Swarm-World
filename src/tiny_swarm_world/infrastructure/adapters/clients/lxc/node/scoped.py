"""Typed scoped-node dispatch separate from legacy shared-profile mutation."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, ProfileChangeIntent, ProfileRuntimeIntent
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend


def template_for(intent):
    if isinstance(intent, ProfileRuntimeIntent):
        return intent.original
    if isinstance(intent, ProfileChangeIntent):
        return intent.target
    if isinstance(intent, ManagerCreateIntent):
        return intent
    raise LifecycleStateError('Unknown scoped operation intent cannot select managed nodes.')


async def dispatch(operation, node, selection, *, ensure):
    from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import _selected_backend, _verified

    operation.lease.require_active()
    template = template_for(operation.intent)
    backend = _selected_backend(node, selection)
    if backend is not ManagedLxcBackend.INCUS:
        raise LifecycleStateError('Scoped installation requires the admitted Incus backend.')
    expected = {template.node_name, *(worker.node_name for worker in template.workers)}
    if node.name not in expected:
        raise LifecycleStateError('Node is outside the exact admitted scoped setup.')
    if ensure:
        if node.name == template.node_name:
            await operation.ensure_manager()
        else:
            await operation.ensure_worker(node.name)
    else:
        await operation.verify_node(node.name)
    return _verified(node, backend, 'scoped_profile_verified', applied=ensure)


async def verify(provider, node, selection):
    from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import _selected_backend, _verified

    if provider.profile_operation is not None:
        return await dispatch(provider.profile_operation, node, selection, ensure=False)
    if provider.profile_observer is None:
        return None
    backend = _selected_backend(node, selection)
    if backend is not ManagedLxcBackend.INCUS:
        raise LifecycleStateError('Persisted scoped verification requires the supported Incus backend.')
    await provider.profile_observer.verify_node(node.name)
    return _verified(node, backend, 'scoped_profile_observed')


def require_writer(provider):
    if provider.profile_observer is not None and provider.profile_operation is None:
        raise LifecycleStateError('Read-only profile observation supplies no node mutation authority.')


async def ensure(provider, node, selection):
    if provider.profile_operation is None:
        return None
    return await dispatch(provider.profile_operation, node, selection, ensure=True)


def refuse_teardown(provider):
    if provider.profile_operation is not None or provider.profile_observer is not None:
        raise LifecycleStateError('Scoped nodes require their exact journal-bound cleanup operation.')
