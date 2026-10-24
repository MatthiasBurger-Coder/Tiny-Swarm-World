"""Read-only dedicated preview; runtime construction follows existing consent."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import SOURCE_VERSION, TARGET_ID, TARGET_VERSION, versions
from tiny_swarm_world.infrastructure.composition import build_portainer_upgrade_journal, build_component_update_journal


def portainer_preview(lifecycle, *, target=None, recovery=False):
    if target not in {None, TARGET_ID}:
        raise LifecycleStateError('Only portainer-ce-2.45.1 is a supported Portainer target.')
    snapshot = lifecycle.manifests.load()
    if snapshot.manifest is None or snapshot.diagnostics:
        raise LifecycleStateError('Valid installation manifest required before Portainer preview.')
    components = {item.component_id: item for item in snapshot.manifest.components if item.service_id == 'portainer'}
    if set(components) != set(versions(SOURCE_VERSION)):
        raise LifecycleStateError('Portainer manifest bundle is incomplete.')
    for name, component in components.items():
        if not any(component.desired.image_repository == identity.image_repository and (
                component.desired.image_digest == identity.image_digest if component.desired.image_digest
                else component.desired.image_tag == release)
                for release in (SOURCE_VERSION, TARGET_VERSION) for identity in (versions(release)[name],)):
            raise LifecycleStateError('Unsupported recorded Portainer source; no migration admitted.')
    journal = build_portainer_upgrade_journal(lifecycle)
    checkpoint = journal.load()
    if recovery and (checkpoint is None or checkpoint.stage == 'completed'):
        raise LifecycleStateError('No interrupted Portainer transition is available.')
    return {
        'status': 'preview', 'service': 'portainer', 'lifecycle_owner': 'portainer-adapter',
        'observation_source': 'recorded-manifest-not-live', 'execution': 'not performed (read-only preview)',
        'target': {name: item.model_dump(mode='json') for name, item in versions(TARGET_VERSION).items()},
        'source': [item.model_dump(mode='json') for item in snapshot.manifest.components if item.service_id == 'portainer'],
        'transition': '2.45.0 -> 2.45.1; CE and Agent; single-manager Classic only',
        'stages': ['inspect live mode/images/local data/endpoints/ownership', 'cold backup with checksum',
                   'update agent/server through bootstrap runtime', 'authenticate and verify preservation',
                   'reapply existing managed Swarm stack without prune/pull', 'commit desired images'],
        'backup_required': True, 'availability_impact': 'Portainer outage during cold backup/restart; managed stack reapply may restart tasks.',
        'recovery': 'restore cold /data backup and source images through manager shell; failed data is retained; API not required for restore',
        'checkpoint': None if checkpoint is None else checkpoint.stage,
        'direction': 'recover' if recovery else 'apply', 'live_qualification': 'pending W09 native-linux/wsl2',
    }


def require_no_component_batch(lifecycle):
    batch = build_component_update_journal(lifecycle).load()
    if batch is not None and not batch.settled:
        raise LifecycleStateError('Complete/recover the existing component batch before upgrading Portainer.')
