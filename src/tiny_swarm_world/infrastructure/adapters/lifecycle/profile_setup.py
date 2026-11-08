"""Compose a private, immutable fresh-install profile operation; no adoption."""
from __future__ import annotations

import re

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.installation_profile import InstallationProfileService, admit, admitted_matrix
from tiny_swarm_world.application.services.profile_setup import ScopedProfileSetupOperation, proxy_routes_from_setup_manifest
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.lifecycle.models import InstallationProfileBinding, InstallationProfileIntent, installation_profile_name
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, WorkerCreateIntent
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.domain.preflight.setup_manifest import default_setup_manifest
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import AsyncLxcNodeCommandRunner
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle import IncusProfileLifecycleRuntime, _ENV
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.observations import client_versions
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
from tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository import IncusProfileCapabilityRepository

_ERROR = 'Scoped setup requires the original clean source, admitted local image and exact original profile operation.'
_GIT_ENV = ('/usr/bin/env', '-i', 'LC_ALL=C', 'PATH=/usr/sbin:/usr/bin:/sbin:/bin',
            'GIT_CONFIG_NOSYSTEM=1', 'GIT_CONFIG_GLOBAL=/dev/null', '/usr/bin/git')


async def prepare_profile_operation(state, config, setup_manifest, consent, lease, *, recovery=False, listen_address='0.0.0.0'):
    lease.require_active()
    root = state.root
    service = InstallationProfileService(IncusProfileCapabilityRepository(root),
        IncusProfileLifecycleRuntime(AsyncLxcNodeCommandRunner()).for_preparation(lease), JsonProfileLifecycleJournal(root),
        state.lifecycle.manifests, state.lifecycle.operation_lock)
    matrix = admitted_matrix(service.capabilities, consent)
    retained = service.journal.load()
    if retained is not None and (not retained.settled or retained.stage == 'cleaned'):
        if not recovery or retained.intent.initial_manifest is None:
            raise LifecycleStateError(_ERROR)
        intent = retained.intent
        if state.lifecycle.manifests.load().token != intent.profile.manifest_token:
            raise LifecycleStateError(_ERROR)
        state.fresh = intent.initial_manifest
    else:
        if recovery or state.fresh is None:
            raise LifecycleStateError(_ERROR)
        intent = await fresh_intent(service.runtime, state, config, setup_manifest, lease, listen_address)
    revision = await clean_source_revision(service.runtime, root)
    if revision != intent.profile.controller_revision or not matrix.admits(intent.profile.incus_version, intent.profile.incus_version):
        raise LifecycleStateError(_ERROR)
    operation = ScopedProfileSetupOperation(service, intent, lease, state.plan, setup_manifest, consent, recovery=recovery)
    await operation.admit_desired(state.plan)
    with service.journal.exclusive(lease):
        await admit(operation.service, intent, matrix, lease, recovery)
    return operation


async def fresh_intent(runtime, state, config, setup_manifest, lease, listen_address):
    revision = await clean_source_revision(runtime, state.root)
    client, server = client_versions(await runtime.run((*_ENV, 'version')))
    if client != server:
        raise LifecycleStateError(_ERROR)
    resolution = config.provider_resource_resolution
    resource = None if resolution is None else resolution.for_backend(ManagedLxcBackend.INCUS)
    nodes = config.nodes
    if resource is None or tuple(node.spec.name for node in nodes) != ('swarm-manager', 'swarm-worker-1', 'swarm-worker-2'):
        raise LifecycleStateError(_ERROR)
    fingerprints = [await local_image(runtime, node.image_alias) for node in nodes]
    specs = [node_spec(node, resource, fingerprints[index]) for index, node in enumerate(nodes)]
    manifest = state.fresh
    if manifest is None or manifest.product.revision != revision:
        raise LifecycleStateError(_ERROR)
    routes = proxy_routes_from_setup_manifest(setup_manifest, listen_address)
    profile = InstallationProfileIntent(operation_id=lease.operation_id, operation_kind='setup',
        installation_id=manifest.installation_id, controller_revision=revision, product_source_revision=revision,
        product_target_revision=None, incus_version=client, manifest_token=state.plan.manifest_token,
        requested_services=state.plan.requested_services, resolved_services=state.plan.resolved_services,
        service_exposure=getattr(state.plan, 'service_exposure', manifest.effective_exposure()),
        stack_ownership=manifest.effective_stack_ownership(), profile=InstallationProfileBinding(
            profile_name=installation_profile_name(manifest.installation_id), routes=routes))
    ports = tuple(sorted({item.port for mode in ServiceStackProfile
                          for item in default_setup_manifest(service_profile=mode).required_ports}))
    intent = ManagerCreateIntent(profile=profile, endpoint_kind=runtime.endpoint_kind, initial_manifest=manifest,
        planned_stack_owners=getattr(state.plan, 'stack_owners', {key: owner.owner for key, owner in profile.stack_ownership.items()}),
        base_profiles_sha256='0' * 64, preservation_sha256='0' * 64, catalog_ports=ports,
        workers=tuple(WorkerCreateIntent(**spec) for spec in specs[1:]), **specs[0])
    observed = await runtime.inspect(intent)
    return ManagerCreateIntent.model_validate_json(intent.model_copy(update={
        'base_profiles_sha256': observed.base_profiles_sha256,
        'preservation_sha256': observed.preservation_sha256}).model_dump_json())


def node_spec(node, resource, fingerprint):
    if (len(node.networks) != 1 or node.networks[0] not in resource.network_mappings
            or node.profile != 'docker-swarm'
            or node.additional_profiles not in ((), ('docker-swarm-manager',))):
        raise LifecycleStateError(_ERROR)
    return dict(node_name=node.spec.name, image_fingerprint=fingerprint, base_profiles=(node.profile,),
        network=resource.network_mappings[node.networks[0]], storage_pool=resource.storage_pool,
        cpu=int(node.resources['cpu']), memory=node.resources['memory'], disk=node.resources['disk'])


async def local_image(runtime, alias):
    if type(alias) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', alias) is None:
        raise LifecycleStateError(_ERROR)
    row = await runtime.query('/1.0/images/aliases/' + alias + '?project=default')
    if (not isinstance(row, dict) or set(row) != {'name', 'target', 'type', 'description'}
            or any(type(value) is not str for value in row.values()) or row['name'] != alias
            or row['type'] != 'container' or re.fullmatch('[0-9a-f]{64}', row['target']) is None):
        raise LifecycleStateError(_ERROR)
    return row['target']


async def clean_source_revision(runtime, root):
    prefix = (*_GIT_ENV, '-C', str(root), '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null')
    raw = await runtime.run((*prefix, 'config', '--list', '--null', '--includes'))
    suppress = []
    for record in raw.split('\0'):
        key = record.partition('\n')[0]
        if key.startswith('filter.'):
            if re.fullmatch(r'filter\.[A-Za-z0-9_.-]{1,128}\.(clean|smudge|process|required)', key) is None:
                raise LifecycleStateError(_ERROR)
            suppress.extend(('-c', key + ('=false' if key.endswith('.required') else '=')))
    top = (await runtime.run((*prefix, 'rev-parse', '--show-toplevel'))).strip()
    tracked = await runtime.run((*prefix, 'ls-files', '-v', '-z'))
    if top != str(root) or not tracked or any(record and not record.startswith('H ') for record in tracked.split('\0')):
        raise LifecycleStateError(_ERROR)
    revision = (await runtime.run((*prefix, 'rev-parse', '--verify', 'HEAD'))).strip()
    if re.fullmatch('[0-9a-f]{40}', revision) is None:
        raise LifecycleStateError(_ERROR)
    if await runtime.run((*prefix, *suppress, 'status', '--porcelain=v1', '--untracked-files=normal')):
        raise LifecycleStateError(_ERROR)
    return revision



async def for_runtime(root, lifecycle, lease, kind, consent):
    """Admit an existing own profile without manufacturing fresh-create authority."""
    from tiny_swarm_world.application.services.profile_setup import ProfileRuntimeOperation
    from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileRuntimeIntent

    lease.require_active()
    admitted_matrix(IncusProfileCapabilityRepository(root), consent)
    if kind not in {'component-update', 'product-upgrade', 'portainer-upgrade', 'recovery'}:
        raise LifecycleStateError(_ERROR)
    snapshot = lifecycle.manifests.load()
    manifest = snapshot.manifest
    journal = JsonProfileLifecycleJournal(root)
    retained = journal.load()
    if (manifest is None or manifest.schema_version != 2 or manifest.installation_profile is None
            or retained is None or not retained.installation_committed):
        raise LifecycleStateError(_ERROR)
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import current_evidence
    template, _, _ = current_evidence(root, manifest)
    runtime = IncusProfileLifecycleRuntime(AsyncLxcNodeCommandRunner()).for_preparation(lease)
    revision = await clean_source_revision(runtime, root)
    profile = InstallationProfileIntent(operation_id=lease.operation_id, operation_kind=kind,
        installation_id=manifest.installation_id, controller_revision=revision,
        product_source_revision=manifest.product.revision, product_target_revision=None,
        incus_version=template.profile.incus_version, manifest_token=snapshot.token,
        requested_services=manifest.requested_services, resolved_services=manifest.resolved_services,
        service_exposure=manifest.effective_exposure(), stack_ownership=manifest.effective_stack_ownership(),
        profile=manifest.installation_profile, stage='completed')
    intent = ProfileRuntimeIntent(profile=profile, original=template,
        planned_stack_owners={name: owner.owner for name, owner in manifest.effective_stack_ownership().items()})
    service = InstallationProfileService(IncusProfileCapabilityRepository(root),
        runtime.for_operation(lease, template), journal, lifecycle.manifests, lifecycle.operation_lock)
    operation = ProfileRuntimeOperation(service, intent, lease, snapshot.token, consent)
    await operation.admit_runtime()
    return operation


def commit_fresh_selection(state):
    from tiny_swarm_world.domain.lifecycle.models import InstallationManifest, migrate_manifest_v1

    if state.fresh is None:
        raise LifecycleStateError('No original transient installation manifest is available.')
    candidate = migrate_manifest_v1(state.fresh)
    if state.profile_operation is not None:
        from tiny_swarm_world.application.services.profile_setup import ScopedProfileSetupOperation
        if not isinstance(state.profile_operation, ScopedProfileSetupOperation):
            raise LifecycleStateError('Fresh setup requires its original typed creation operation.')
        checkpoint = state.profile_operation.service.journal.load()
        if checkpoint is None or checkpoint.stage != 'completed':
            raise LifecycleStateError('Original scoped runtime completion is unproven.')
        intent = state.profile_operation.intent
        owners = candidate.effective_stack_ownership()
        for name, mode in intent.planned_stack_owners.items():
            if mode == 'portainer':
                owner = checkpoint.verified_stack_ownership.get(name)
                if owner is None:
                    raise LifecycleStateError('Selected Portainer stack ownership is unverified.')
                owners[name] = owner
        candidate = InstallationManifest.model_validate_json(candidate.model_copy(update={
            'service_exposure': intent.profile.service_exposure, 'stack_ownership': owners,
            'installation_profile': intent.profile.profile,
            'checkpoint_reference': 'profile-' + intent.profile.operation_id}).model_dump_json())
    saved = state.lifecycle.adopt(candidate, approved=True, preview=False, operation_lease=state.operation_lease)
    state.fresh = saved.manifest
