"""Read-only persisted own-profile verification, without live-write authority."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.installation_profile import require_running
from tiny_swarm_world.application.services.platform.preflight_service import RecoveryPortProof
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileCapabilityMatrix
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import AsyncLxcNodeCommandRunner
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle import IncusProfileLifecycleRuntime
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import current_evidence
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import clean_source_revision
from tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository import IncusProfileCapabilityRepository
from tiny_swarm_world.infrastructure.composition_profile import selected_listen_address


class ScopedProfileObserver:
    def __init__(self, root, lifecycle, *, runtime=None, capabilities=None):
        self.root, self.lifecycle = root, lifecycle
        self.runtime = IncusProfileLifecycleRuntime(AsyncLxcNodeCommandRunner()) if runtime is None else runtime
        self.capabilities = IncusProfileCapabilityRepository(root) if capabilities is None else capabilities

    async def observe(self, *, expected_revision: str | None = None):
        template, _, _ = await self._observe(expected_revision=expected_revision)
        return template

    async def observe_port_ownership(self, profile: ServiceStackProfile | str) -> RecoveryPortProof | None:
        try:
            template, observed, manifest = await self._observe()
            routes = template.profile.profile.routes
            listen_address = selected_listen_address(routes)
            if (manifest.host != 'native-linux' or manifest.service_preset != profile
                    or any(route.listen_address != listen_address for route in routes)):
                return None
            return RecoveryPortProof(frozenset(route.listen_port for route in routes), observed.observation_sha256)
        except (OSError, RuntimeError, ValueError):
            return None

    async def _observe(self, *, expected_revision: str | None = None):
        matrix = ProfileCapabilityMatrix.model_validate_json(self.capabilities.load().model_dump_json())
        if not matrix.admitted_versions:
            raise LifecycleStateError('Scoped profile verification has no qualified version observation contract.')
        snapshot = self.lifecycle.manifests.load()
        manifest = snapshot.manifest
        if manifest is None or manifest.installation_profile is None:
            raise LifecycleStateError('No persisted installation-owned profile is available for verification.')
        template, manager_uuid, worker_uuids = current_evidence(self.root, manifest)
        runtime = self.runtime.for_observation(template)
        revision = await clean_source_revision(runtime, self.root)
        if expected_revision is not None and revision != expected_revision:
            raise LifecycleStateError('Original guided installation source changed.')
        observed = await runtime.inspect(template)
        if (not matrix.admits(observed.client_version, observed.server_version)
                or observed.client_version != template.profile.incus_version or observed.server_version != template.profile.incus_version
                or observed.preservation_sha256 != template.preservation_sha256
                or observed.base_profiles_sha256 != template.base_profiles_sha256 or observed.forbidden_listener):
            raise LifecycleStateError('Own-profile verification source, version or preservation changed.')
        require_running(observed)
        workers = {worker.node_name: worker for worker in observed.workers}
        if (observed.instance_uuid != manager_uuid or set(workers) != set(worker_uuids)
                or any(worker.state != 'running' or not worker.no_proxy or worker.instance_uuid != worker_uuids[name]
                       for name, worker in workers.items())):
            raise LifecycleStateError('Persisted own manager or worker identity is unproven.')
        after = self.lifecycle.manifests.load()
        if (after.token != snapshot.token or after.manifest != manifest
                or current_evidence(self.root, manifest) != (template, manager_uuid, worker_uuids)):
            raise LifecycleStateError('Persisted profile authority changed during read-only verification.')
        return template, observed, manifest

    async def verify_node(self, node_name):
        template = await self.observe()
        if node_name not in {template.node_name, *(worker.node_name for worker in template.workers)}:
            raise LifecycleStateError('Unselected node cannot use persisted own-profile verification.')

    async def verify_effective_routes(self):
        await self.observe()
