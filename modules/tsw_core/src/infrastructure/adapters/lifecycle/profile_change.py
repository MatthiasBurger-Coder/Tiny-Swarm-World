"""Private existing-profile CAS journal; creation history stays unchanged."""
from contextlib import contextmanager

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileChangeCheckpoint, preserve_verified_portainer_identity
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal, read_checkpoint


class JsonProfileChangeJournal:
    def __init__(self, root):
        self.root = root
        self.path = root / '.tiny-swarm-world/installation/profile-change.json'
        self.creation = JsonProfileLifecycleJournal(root)
        self._lease = None

    @contextmanager
    def exclusive(self, lease):
        if self._lease is not None:
            raise LifecycleStateError('Profile change journal already has an admitted holder.')
        with self.creation.exclusive(lease):
            self._lease = lease
            try:
                yield
            finally:
                self._lease = None

    def load(self):
        try:
            raw = read_checkpoint(self.root, 'profile-change.json')
            return None if raw is None else ProfileChangeCheckpoint.model_validate_json(raw)
        except (OSError, ValueError):
            raise LifecycleStateError('Invalid profile change; preserve original state for recovery.') from None

    def save(self, checkpoint, *, expected, lease):
        lease.require_active()
        if lease is not self._lease:
            raise LifecycleStateError('Profile change requires its explicit journal holder.')
        current = self.load()
        checked = ProfileChangeCheckpoint.model_validate_json(checkpoint.model_dump_json())
        replacing = current is not None and current.settled and current.intent != checked.intent
        if (current != expected or (current is not None and not replacing and current.intent != checked.intent)
                or checked.generation != (0 if current is None or replacing else current.generation + 1)):
            raise LifecycleStateError('Profile change intent or generation changed.')
        if current is not None:
            try:
                for name, owner in current.verified_stack_ownership.items():
                    if name not in checked.verified_stack_ownership:
                        raise ValueError('Verified owner was removed.')
                    preserve_verified_portainer_identity(owner, checked.verified_stack_ownership[name])
            except ValueError:
                raise LifecycleStateError('Durably verified managed-stack identity changed.') from None
        JsonManifestRepository(self.path)._replace(checked.model_dump_json(indent=2).encode() + b'\n')


def current_evidence(root, manifest):
    creation = JsonProfileLifecycleJournal(root).load()
    changed = JsonProfileChangeJournal(root).load()
    if creation is None or not creation.installation_committed:
        raise LifecycleStateError('Original installation-owned profile completion is unproven.')
    template = creation.intent
    if changed is not None:
        if not changed.settled:
            raise LifecycleStateError('Resume the original pending profile change explicitly.')
        template = changed.intent.target
    if (manifest.installation_id != template.profile.installation_id
            or manifest.installation_profile != template.profile.profile):
        raise LifecycleStateError('Actual installation differs from its retained profile history.')
    return template, creation.instance_uuid, creation.worker_uuids


async def prepare_profile_change(state, setup_manifest, consent, lease, *, recovery=False, listen_address='0.0.0.0'):
    from tiny_swarm_world.application.services.installation_profile import InstallationProfileService, admitted_matrix
    from tiny_swarm_world.application.services.profile_change import ProfileChangeOperation, inspect_template
    from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileChangeIntent
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import AsyncLxcNodeCommandRunner
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle import IncusProfileLifecycleRuntime
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import clean_source_revision
    from tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository import IncusProfileCapabilityRepository

    lease.require_active()
    journal = JsonProfileChangeJournal(state.root)
    service = InstallationProfileService(IncusProfileCapabilityRepository(state.root),
        IncusProfileLifecycleRuntime(AsyncLxcNodeCommandRunner()).for_preparation(lease), JsonProfileLifecycleJournal(state.root),
        state.lifecycle.manifests, state.lifecycle.operation_lock)
    matrix = admitted_matrix(service.capabilities, consent)
    snapshot = state.lifecycle.manifests.load()
    manifest = snapshot.manifest
    if manifest is None or snapshot.token != state.plan.manifest_token or snapshot.token is None:
        raise LifecycleStateError('Existing profile selection baseline changed.')
    previous = journal.load()
    if previous is not None and not previous.settled:
        if not recovery:
            raise LifecycleStateError('Existing profile change requires explicit original recovery.')
        intent = previous.intent
    else:
        if recovery:
            raise LifecycleStateError('No pending original profile change is available.')
        before, target, uuid, workers = change_templates(state, manifest, setup_manifest, listen_address)
        if target == before:
            from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import for_runtime
            return await for_runtime(state.root, state.lifecycle, lease, 'recovery', consent)
        intent = ProfileChangeIntent(operation_id=lease.operation_id,
            controller_revision=await clean_source_revision(service.runtime, state.root), manifest_token=snapshot.token,
            before_manifest=manifest,
            before=before, target=target, instance_uuid=uuid, worker_uuids=workers)
    if await clean_source_revision(service.runtime, state.root) != intent.controller_revision:
        raise LifecycleStateError('Original profile change controller source changed.')
    operation = ProfileChangeOperation(service, journal, intent, lease, state.plan, consent, recovery=recovery)
    if (state.plan.requested_services != intent.target.profile.requested_services
            or state.plan.resolved_services != intent.target.profile.resolved_services
            or getattr(state.plan, 'service_exposure', intent.target.profile.service_exposure) != intent.target.profile.service_exposure
            or getattr(state.plan, 'stack_owners', intent.planned_stack_owners) != intent.planned_stack_owners):
        raise LifecycleStateError('Recovery must preserve the exact original desired selection and policy.')
    if previous is None or previous.settled:
        observed = await inspect_template(operation, intent.before, matrix)
        verified = {name: owner for name, owner in manifest.effective_stack_ownership().items() if owner.owner == 'portainer'}
        checkpoint = ProfileChangeCheckpoint(intent=intent, observation_sha256=observed.observation_sha256,
                                             verified_stack_ownership=verified)
        with journal.exclusive(lease):
            journal.save(checkpoint, expected=previous, lease=lease)
    await operation.admit_desired(state.plan)
    return operation


def commit_selection(state):
    from tiny_swarm_world.application.services.selection_commit import selected_components, selection_payload, validate_selection
    from tiny_swarm_world.domain.lifecycle.models import InstallationManifest, SwarmOwnership

    operation = state.profile_operation
    operation.lease.require_active()
    checkpoint = operation.require_checkpoint()
    snapshot = state.lifecycle.manifests.load()
    current = snapshot.manifest
    if current is not None and operation.target_manifest_matches(current):
        return
    if current is None or snapshot.token != operation.intent.manifest_token or checkpoint.stage != 'verified':
        raise LifecycleStateError('Profile change selection commit has no verified original baseline.')
    catalog = state.lifecycle.catalog.load()
    validate_selection(catalog, current, state.plan)
    components = selected_components(catalog, current, state.plan, state.component_inventory)
    payload = selection_payload(current, state.plan, components, state.credential_inventory, state.configuration_inventory)
    owners = {}
    for name, mode in operation.intent.planned_stack_owners.items():
        if mode == 'portainer':
            owner = checkpoint.verified_stack_ownership.get(name)
            if owner is None:
                raise LifecycleStateError('Selected managed-stack ownership remains unproven.')
            owners[name] = owner
        else:
            owners[name] = SwarmOwnership()
    payload.update(service_exposure=operation.intent.target.profile.service_exposure,
                   stack_ownership=owners, installation_profile=operation.intent.target.profile.profile,
                   checkpoint_reference='profile-change-' + operation.intent.operation_id)
    candidate = InstallationManifest.model_validate(payload)
    catalog.validate_manifest(candidate)
    if candidate != current:
        state.lifecycle.manifests.save(candidate, expected_token=snapshot.token)


def change_templates(state, manifest, setup_manifest, listen_address):
    from tiny_swarm_world.domain.lifecycle.models import InstallationProfileBinding, SwarmOwnership
    from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent

    before, uuid, workers = current_evidence(state.root, manifest)
    if uuid is None:
        raise LifecycleStateError('Existing manager UUID is unproven.')
    actual_profile = before.profile.model_copy(update={'requested_services': manifest.requested_services,
        'resolved_services': manifest.resolved_services, 'service_exposure': manifest.effective_exposure(),
        'stack_ownership': manifest.effective_stack_ownership()})
    before = ManagerCreateIntent.model_validate_json(before.model_copy(update={'profile': actual_profile,
        'planned_stack_owners': {name: owner.owner for name, owner in manifest.effective_stack_ownership().items()}}).model_dump_json())
    binding = before.profile.profile
    if binding is None:
        raise LifecycleStateError('Existing own exposure binding is absent.')
    addresses = {route.listen_address for route in binding.routes}
    if len(addresses) > 1:
        raise LifecycleStateError('Mixed existing listen scopes are unsupported.')
    address = next(iter(addresses)) if addresses else listen_address
    from tiny_swarm_world.application.services.profile_setup import proxy_routes_from_setup_manifest
    routes = proxy_routes_from_setup_manifest(setup_manifest, address)
    owners = manifest.effective_stack_ownership()
    for name in state.plan.resolved_services:
        if name not in {'incus', 'portainer'}:
            owners.setdefault(name, SwarmOwnership())
    target_profile = before.profile.model_copy(update={'requested_services': state.plan.requested_services,
        'resolved_services': state.plan.resolved_services,
        'service_exposure': getattr(state.plan, 'service_exposure', manifest.effective_exposure()),
        'stack_ownership': owners, 'profile': InstallationProfileBinding(profile_name=binding.profile_name, routes=routes)})
    target = ManagerCreateIntent.model_validate_json(before.model_copy(update={'profile': target_profile,
        'planned_stack_owners': getattr(state.plan, 'stack_owners', {name: owner.owner for name, owner in owners.items()})}).model_dump_json())
    return before, target, uuid, workers
