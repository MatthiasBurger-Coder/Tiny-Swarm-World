"""Private setup admission and selected worker orchestration under one lease."""
from copy import copy

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease
from tiny_swarm_world.application.services.installation_profile import (
    admitted_matrix, observe, observe_checkpoint, record, require_checkpoint, require_running, settle_effect,
)
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, preserve_verified_portainer_identity
from tiny_swarm_world.domain.lifecycle.selection import SelectionPlan
from tiny_swarm_world.domain.preflight import LiveConsent, SetupManifest


class ScopedProfileSetupOperation:
    """Created per admitted operation; never bound onto shared public services."""
    def __init__(self, service, intent: ManagerCreateIntent, lease: InstallationLease,
                 plan: SelectionPlan, setup_manifest: SetupManifest, consent: LiveConsent,
                 *, recovery: bool = False):
        self.intent, self.lease, self.plan = intent, lease, plan
        self.setup_manifest, self.consent, self.recovery = setup_manifest, consent, recovery
        self.service = copy(service)
        self.service.runtime = service.runtime.for_operation(lease, intent)

    @property
    def verified_stack_ownership(self) -> dict[str, PortainerOwnership]:
        self.lease.require_active()
        return dict(require_checkpoint(self.service, self.intent).verified_stack_ownership)

    async def admit_desired(self, plan: SelectionPlan) -> None:
        self.lease.require_active()
        checked = SelectionPlan.model_validate_json(plan.model_dump_json())
        selected = self.intent.profile
        exposure = getattr(checked, 'service_exposure', selected.service_exposure)
        binding = selected.profile
        if binding is None:
            raise LifecycleStateError('Missing admitted scoped profile.')
        if (checked != self.plan or checked.requested_services != selected.requested_services
                or checked.resolved_services != selected.resolved_services or exposure != selected.service_exposure
                or getattr(checked, 'stack_owners', self.intent.planned_stack_owners) != self.intent.planned_stack_owners
                or self.service.manifests.load().token != checked.manifest_token
                or routes_from_setup_manifest(self.setup_manifest, self.intent) != binding.routes):
            raise LifecycleStateError('Desired setup policy differs from the explicitly admitted scoped profile intent.')
        matrix = admitted_matrix(self.service.capabilities, self.consent)
        await observe(self.service, self.intent, matrix)

    async def ensure_manager(self) -> None:
        await self.admit_desired(self.plan)
        await self.service.run(self.intent, consent=self.consent, lease=self.lease, recovery=self.recovery)

    async def ensure_worker(self, node_name: str) -> None:
        await self.admit_desired(self.plan)
        matrix = admitted_matrix(self.service.capabilities, self.consent)
        with self.service.journal.exclusive(self.lease):
            checkpoint = require_checkpoint(self.service, self.intent)
            await ensure_worker(self.service, checkpoint, matrix, self.lease, node_name, self.recovery)

    async def verify_node(self, node_name: str) -> None:
        self.lease.require_active()
        matrix = admitted_matrix(self.service.capabilities, self.consent)
        checkpoint = require_checkpoint(self.service, self.intent)
        observed = await observe_checkpoint(self.service, checkpoint, matrix)
        require_running(observed)
        if node_name == self.intent.node_name:
            return
        worker = next((item for item in observed.workers if item.node_name == node_name), None)
        if (worker is None or worker.state != 'running' or not worker.no_proxy
                or checkpoint.worker_uuids.get(node_name) != worker.instance_uuid):
            raise LifecycleStateError('Selected worker identity is not checkpoint-bound and running.')

    async def verify_effective_routes(self) -> None:
        self.lease.require_active()
        matrix = admitted_matrix(self.service.capabilities, self.consent)
        checkpoint = require_checkpoint(self.service, self.intent)
        observed = await observe_checkpoint(self.service, checkpoint, matrix)
        require_running(observed)
        require_workers_running(checkpoint, observed)

    async def commit_installation(self) -> None:
        self.lease.require_active()
        await self.service.commit_installation(self.intent, consent=self.consent, lease=self.lease)

    async def record_stack_ownership(self, service_id: str, ownership: PortainerOwnership) -> None:
        self.lease.require_active()
        checked = PortainerOwnership.model_validate_json(ownership.model_dump_json())
        if self.intent.planned_stack_owners.get(service_id) != 'portainer':
            raise LifecycleStateError('This service has no admitted Portainer ownership plan.')
        with self.service.journal.exclusive(self.lease):
            checkpoint = require_checkpoint(self.service, self.intent)
            previous = checkpoint.verified_stack_ownership.get(service_id)
            if previous is not None and previous != checked:
                raise LifecycleStateError('Verified stack ownership identity changed; retain the original checkpoint.')
            record(self.service, checkpoint, self.lease,
                   verified_stack_ownership={**checkpoint.verified_stack_ownership, service_id: checked})


def routes_from_setup_manifest(manifest, intent):
    binding = intent.profile.profile
    if binding is None:
        raise LifecycleStateError('Missing bound exposure profile.')
    addresses = {route.listen_address for route in binding.routes}
    if not addresses and not manifest.required_ports:
        return ()
    if len(addresses) != 1:
        raise LifecycleStateError('One explicit IPv4 listen scope is required.')
    return proxy_routes_from_setup_manifest(manifest, next(iter(addresses)))


def proxy_routes_from_setup_manifest(manifest, listen_address):
    from tiny_swarm_world.domain.lifecycle.models import ProxyRoute

    return tuple(sorted((ProxyRoute(device_name='tsw-proxy-' + str(item.port), listen_address=listen_address,
        listen_port=item.port, connect_port=item.port) for item in manifest.required_ports), key=lambda route: route.device_name))


def require_workers_running(checkpoint, observed):
    expected = {worker.node_name for worker in checkpoint.intent.workers}
    actual = {worker.node_name: worker for worker in observed.workers}
    if (set(actual) != expected or set(checkpoint.worker_uuids) != expected
            or any(worker.state != 'running' or not worker.no_proxy
                   or worker.instance_uuid != checkpoint.worker_uuids[name] for name, worker in actual.items())):
        raise LifecycleStateError('Every selected worker requires its exact verified no-proxy identity.')


async def ensure_worker(service, checkpoint, matrix, lease, node_name, recovery):
    if checkpoint.stage != 'completed' or checkpoint.installation_committed:
        raise LifecycleStateError('Selected worker creation requires the original completed manager phase.')
    if node_name not in {worker.node_name for worker in checkpoint.intent.workers}:
        raise LifecycleStateError('Worker is outside the admitted topology.')
    if checkpoint.pending_action is not None and (checkpoint.pending_node != node_name or not recovery):
        raise LifecycleStateError('Resume the exact pending worker operation explicitly.')
    observed = await observe_checkpoint(service, checkpoint, matrix)
    require_running(observed)
    worker = next(item for item in observed.workers if item.node_name == node_name)
    if worker.state == 'absent':
        checkpoint, observed = await worker_write(service, checkpoint, matrix, lease, observed, node_name, 'worker-init')
        worker = next(item for item in observed.workers if item.node_name == node_name)
    if worker.state == 'stopped' and worker.no_proxy and worker.instance_uuid is not None:
        if (node_name not in checkpoint.worker_uuids
                and not (checkpoint.pending_action == 'worker-init' and checkpoint.pending_node == node_name)):
            raise LifecycleStateError('An unrecorded initialized worker cannot be adopted.')
        checkpoint = record(service, checkpoint, lease, pending_action='worker-start', pending_node=node_name,
            worker_uuids={**checkpoint.worker_uuids, node_name: worker.instance_uuid},
            observation_sha256=observed.observation_sha256)
        checkpoint, observed = await worker_write(service, checkpoint, matrix, lease, observed, node_name, 'worker-start')
        worker = next(item for item in observed.workers if item.node_name == node_name)
    if worker.state != 'running' or not worker.no_proxy or worker.instance_uuid is None:
        raise LifecycleStateError('Worker postcondition is unverified; retain its checkpoint.')
    if checkpoint.worker_uuids.get(node_name) != worker.instance_uuid:
        raise LifecycleStateError('Checkpoint-bound worker identity changed.')
    return record(service, checkpoint, lease, pending_action=None, pending_node=None,
                  worker_uuids={**checkpoint.worker_uuids, node_name: worker.instance_uuid},
                  observation_sha256=observed.observation_sha256)


async def worker_write(service, checkpoint, matrix, lease, before, node_name, action):
    checkpoint = record(service, checkpoint, lease, pending_action=action, pending_node=node_name,
                        observation_sha256=before.observation_sha256)
    fresh = await observe_checkpoint(service, checkpoint, matrix)
    if fresh.observation_sha256 != checkpoint.observation_sha256:
        raise LifecycleStateError('Worker precondition changed after durable mutation intent.')
    effect = service.runtime.init_worker if action == 'worker-init' else service.runtime.start_worker
    try:
        await settle_effect(effect(checkpoint.intent, node_name))
    except (OSError, ValueError, RuntimeError, TimeoutError):
        pass
    return checkpoint, await observe(service, checkpoint.intent, matrix)


class ProfileRuntimeOperation:
    """Explicit existing-installation admission, with no create/cleanup authority."""
    def __init__(self, service, intent, lease, manifest_token, consent):
        self.service, self.intent, self.lease = service, intent, lease
        self.manifest_token, self.consent = manifest_token, consent
        self._verified = {name: owner for name, owner in intent.profile.stack_ownership.items()
                          if isinstance(owner, PortainerOwnership)}

    @property
    def verified_stack_ownership(self) -> dict[str, PortainerOwnership]:
        self.lease.require_active()
        return dict(self._verified)

    def require_current_manifest(self):
        self.lease.require_active()
        snapshot = self.service.manifests.load()
        manifest = snapshot.manifest
        if manifest is None or snapshot.token != self.manifest_token:
            raise LifecycleStateError('Existing scoped installation changed after runtime admission.')
        self.intent.profile.validate_manifest(manifest)
        return manifest

    async def admit_runtime(self) -> None:
        self.require_current_manifest()
        matrix = admitted_matrix(self.service.capabilities, self.consent)
        checkpoint = self.service.journal.load()
        if checkpoint is None or checkpoint.intent.profile.installation_id != self.intent.profile.installation_id:
            raise LifecycleStateError('Original installation profile history changed.')
        if not checkpoint.installation_committed or not checkpoint.settled:
            raise LifecycleStateError('Original scoped setup has not been committed.')
        observed = await observe(self.service, self.intent.original, matrix)
        require_running(observed)
        if checkpoint.instance_uuid != observed.instance_uuid:
            raise LifecycleStateError('Original manager identity changed.')
        require_workers_running(checkpoint, observed)

    async def admit_desired(self, plan) -> None:
        profile = self.intent.profile
        if (plan.requested_services != profile.requested_services or plan.resolved_services != profile.resolved_services
                or getattr(plan, 'service_exposure', profile.service_exposure) != profile.service_exposure
                or getattr(plan, 'stack_owners', self.intent.planned_stack_owners) != self.intent.planned_stack_owners):
            raise LifecycleStateError('Existing runtime operation cannot change desired selection or routes.')
        await self.admit_runtime()

    async def ensure_manager(self) -> None:
        await self.admit_runtime()

    async def ensure_worker(self, node_name: str) -> None:
        await self.verify_node(node_name)

    async def verify_node(self, node_name: str) -> None:
        if node_name not in {self.intent.original.node_name, *(worker.node_name for worker in self.intent.original.workers)}:
            raise LifecycleStateError('Unselected node is outside the existing runtime operation.')
        await self.admit_runtime()

    async def commit_installation(self) -> None:
        await self.admit_runtime()

    async def verify_effective_routes(self) -> None:
        await self.admit_runtime()

    async def record_stack_ownership(self, service_id: str, ownership: PortainerOwnership) -> None:
        self.lease.require_active()
        try:
            checked = PortainerOwnership.model_validate_json(ownership.model_dump_json())
        except (AttributeError, ValueError):
            raise LifecycleStateError('Existing runtime ownership type is invalid.') from None
        if self.intent.planned_stack_owners.get(service_id) != 'portainer':
            raise LifecycleStateError('Runtime stack update has no admitted Portainer owner.')
        previous = self._verified.get(service_id)
        if previous is None:
            raise LifecycleStateError('Existing runtime ownership identity is unavailable.')
        try:
            preserve_verified_portainer_identity(previous, checked)
        except ValueError:
            raise LifecycleStateError('Existing runtime managed-stack identity changed.') from None
        # The guarded management writer persists these IDs in its own operation
        # journal before this callback. Its enclosing product/component writer
        # owns the subsequent manifest commit; the creation journal is immutable.
        self._verified[service_id] = checked
