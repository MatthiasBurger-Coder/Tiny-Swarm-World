"""Profile-specific composition and pure route projection; no alternate executor."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.preflight.setup_manifest import default_setup_manifest


def selected_listen_address():
    from tiny_swarm_world.infrastructure.composition_configuration import _lxc_proxy_listen_address

    return _lxc_proxy_listen_address()


async def prepare_profile_state(state, config, consent, lease, *, recovery=False):
    existing = state.lifecycle.manifests.load().manifest
    if state.fresh is None and (existing is None or existing.installation_profile is None):
        return None
    if lease is None or consent is None:
        raise LifecycleStateError('Scoped setup requires explicit installation ownership and consent.')
    plan = state.plan
    manifest = default_setup_manifest(service_profile=plan.service_preset, resolved_services=plan.resolved_services,
        **({'service_exposure': plan.service_exposure} if hasattr(plan, 'service_exposure') else {}))
    address = selected_listen_address()
    if state.fresh is not None:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import prepare_profile_operation
        return await prepare_profile_operation(state, config, manifest, consent, lease, recovery=recovery, listen_address=address)
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
    creation = JsonProfileLifecycleJournal(state.root).load()
    if creation is not None and not creation.installation_committed:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_completion import prepare_creation_completion
        return await prepare_creation_completion(state, consent, lease, recovery=recovery)
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import prepare_profile_change
    return await prepare_profile_change(state, manifest, consent, lease, recovery=recovery, listen_address=address)


def preview_installation_routes(lifecycle, plan):
    """Project desired routes from persisted policy/source, without runtime reads."""
    from tiny_swarm_world.application.services.profile_setup import proxy_routes_from_setup_manifest

    snapshot = lifecycle.manifests.load()
    if snapshot.token != plan.manifest_token:
        raise LifecycleStateError('Selection route preview is stale; inspect and preview again.')
    binding = None if snapshot.manifest is None else snapshot.manifest.installation_profile
    before = () if binding is None else binding.routes
    addresses = {route.listen_address for route in before}
    if len(addresses) > 1:
        raise LifecycleStateError('Mixed persisted listen scopes require explicit inventory before route changes.')
    address = next(iter(addresses)) if addresses else selected_listen_address()
    manifest = default_setup_manifest(service_profile=plan.service_preset, resolved_services=plan.resolved_services,
        **({'service_exposure': plan.service_exposure} if hasattr(plan, 'service_exposure') else {}))
    after = proxy_routes_from_setup_manifest(manifest, address)
    return {'authority': 'persisted-profile-and-source-policy', 'runtime_observed': False,
            'baseline_bound': binding is not None, 'listen_address': address,
            'before': [route.model_dump(mode='json') for route in before],
            'after': [route.model_dump(mode='json') for route in after],
            'additions': [route.model_dump(mode='json') for route in after if route not in before],
            'removals': [route.model_dump(mode='json') for route in before if route not in after]}


def legacy_full_setup_available(lifecycle):
    """Retain established full published/Swarm setup only before scoped admission."""
    from tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository import IncusProfileCapabilityRepository
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import JsonProfileChangeJournal

    if lifecycle.manifests.load().manifest is not None:
        return False
    root = lifecycle.catalog.root
    return (not IncusProfileCapabilityRepository(root).load().admitted_versions
            and JsonProfileLifecycleJournal(root).load() is None and JsonProfileChangeJournal(root).load() is None)
