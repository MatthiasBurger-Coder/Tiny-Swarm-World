"""Bounded installation-owned manager profile values; no runtime authority."""
from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal, Self

from pydantic import Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from tiny_swarm_world.domain.lifecycle.models import (
    Contract, Identifier, InstallationManifest, InstallationProfileIntent, PortainerOwnership, ProxyRoute, Revision,
)

SHA256 = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
INCUS_VERSION = Annotated[str, Field(pattern=r'^[0-9]+\.[0-9]+\.[0-9]+$')]
INSTALLATION_MARKER = 'user.tiny_swarm_world.installation_id'
OPERATION_MARKER = 'user.tiny_swarm_world.operation_id'
PROFILE_CAPABILITY: Literal['installation-scoped-incus-manager-profile'] = 'installation-scoped-incus-manager-profile'


class ProfileCapabilityEntry(Contract):
    client_version: INCUS_VERSION
    server_version: INCUS_VERSION
    fixture_source_revision: Revision
    fixture_sha256: SHA256


class ProfileCapabilityMatrix(Contract):
    schema_version: Literal[1] = 1
    capability: Literal['installation-scoped-incus-manager-profile'] = PROFILE_CAPABILITY
    admitted_versions: tuple[ProfileCapabilityEntry, ...]

    @model_validator(mode='after')
    def unique_admissions(self) -> Self:
        keys = [(row.client_version, row.server_version) for row in self.admitted_versions]
        if keys != sorted(set(keys)):
            raise ValueError('Capability admissions must be unique and ordered.')
        return self

    def admits(self, client: str, server: str) -> bool:
        return any((row.client_version, row.server_version) == (client, server)
                   for row in self.admitted_versions)



class WorkerCreateIntent(Contract):
    node_name: Annotated[str, Field(pattern=r'^[a-z0-9][a-z0-9-]{0,62}$')]
    image_fingerprint: SHA256
    base_profiles: tuple[Identifier, ...]
    network: Identifier
    storage_pool: Identifier
    cpu: Annotated[int, Field(gt=0, le=1024)]
    memory: Annotated[str, Field(pattern=r'^[1-9][0-9]{0,4}(MiB|GiB)$')]
    disk: Annotated[str, Field(pattern=r'^[1-9][0-9]{0,4}(MiB|GiB)$')]


class ManagerCreateIntent(Contract):
    profile: InstallationProfileIntent
    endpoint_kind: Literal['incus_run', 'incus_var_lib']
    node_name: Literal['swarm-manager'] = 'swarm-manager'
    image_fingerprint: SHA256
    base_profiles: tuple[Identifier, ...]
    base_profiles_sha256: SHA256
    preservation_sha256: SHA256
    network: Identifier
    storage_pool: Identifier
    catalog_ports: Annotated[tuple[Annotated[int, Field(ge=1, le=65535)], ...], Field(max_length=64)]
    cpu: Annotated[int, Field(gt=0, le=1024)]
    memory: Annotated[str, Field(pattern=r'^[1-9][0-9]{0,4}(MiB|GiB)$')]
    disk: Annotated[str, Field(pattern=r'^[1-9][0-9]{0,4}(MiB|GiB)$')]
    workers: Annotated[tuple[WorkerCreateIntent, ...], Field(max_length=2)] = ()
    initial_manifest: InstallationManifest | None = None
    planned_stack_owners: dict[Identifier, Literal['swarm', 'portainer']] = Field(default_factory=dict)

    @model_validator(mode='after')
    def owned_attachment(self) -> Self:
        binding = self.profile.profile
        if binding is None:
            raise ValueError('Scoped creation requires an explicit bound exposure profile.')
        if (tuple(sorted(set(self.catalog_ports))) != self.catalog_ports
                or not {route.listen_port for route in binding.routes} <= set(self.catalog_ports)):
            raise ValueError('Route ports must come from the complete canonical listener catalog.')
        if set(self.planned_stack_owners) != set(self.profile.stack_ownership):
            raise ValueError('Desired stack ownership must cover the exact selected optional services.')
        if (self.initial_manifest is not None
                and (self.initial_manifest.installation_id != self.profile.installation_id
                     or self.initial_manifest.product.revision != self.profile.product_source_revision)):
            raise ValueError('Original transient installation identity differs from the profile intent.')
        worker_names = [worker.node_name for worker in self.workers]
        if worker_names != sorted(set(worker_names)) or self.node_name in worker_names:
            raise ValueError('Selected worker identities must be unique and ordered.')
        if any((worker.network, worker.storage_pool, worker.base_profiles, worker.image_fingerprint) !=
               (self.network, self.storage_pool, self.base_profiles, self.image_fingerprint) for worker in self.workers):
            raise ValueError('First scoped topology requires the same admitted image/base/network/pool for all nodes.')
        if (not self.base_profiles or len(set(self.base_profiles)) != len(self.base_profiles)
                or binding.profile_name in self.base_profiles
                or 'docker-swarm-manager' in self.base_profiles):
            raise ValueError('Only distinct admitted non-routing base profiles may be retained.')
        return self

    def markers(self) -> dict[str, str]:
        return {INSTALLATION_MARKER: self.profile.installation_id,
                OPERATION_MARKER: self.profile.operation_id}

    def attachments(self) -> tuple[str, ...]:
        binding = self.profile.profile
        if binding is None:
            raise ValueError('Missing bound profile.')
        return (*self.base_profiles, binding.profile_name)

    def devices(self) -> dict[str, dict[str, str]]:
        binding = self.profile.profile
        if binding is None:
            raise ValueError('Missing bound profile.')
        return {route.device_name: route_device(route) for route in binding.routes}


def route_device(route: ProxyRoute) -> dict[str, str]:
    return {'type': 'proxy', 'bind': route.bind,
            'listen': f'{route.listen_protocol}:{route.listen_address}:{route.listen_port}',
            'connect': f'{route.connect_protocol}:{route.connect_address}:{route.connect_port}',
            'nat': 'false', 'proxy_protocol': 'false'}


class ProfileLifecycleCheckpoint(Contract):
    schema_version: Literal[1] = 1
    intent: ManagerCreateIntent
    stage: Literal['intent', 'profile-configured', 'instance-initialized', 'routes-verified',
                   'instance-started', 'completed', 'recoverable', 'cleaned'] = 'intent'
    previous_stage: Literal['intent', 'profile-configured', 'instance-initialized', 'routes-verified',
                            'instance-started', 'completed', 'cleaned'] = 'intent'
    generation: Annotated[int, Field(ge=0)] = 0
    observation_sha256: SHA256
    installation_committed: bool = False
    installation_manifest_sha256: SHA256 | None = None
    instance_uuid: Annotated[str, Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')] | None = None
    pending_action: Literal['profile-create', 'instance-init', 'instance-start', 'instance-delete', 'profile-delete', 'worker-init', 'worker-start'] | None = None
    pending_node: Identifier | None = None
    worker_uuids: dict[Identifier, Annotated[str, Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')]] = Field(default_factory=dict)

    verified_stack_ownership: dict[Identifier, PortainerOwnership] = Field(default_factory=dict)

    @model_serializer(mode='wrap')
    def original_checkpoint_fields(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        result = handler(self)
        if self.installation_manifest_sha256 is None:
            result.pop('installation_manifest_sha256', None)
        return result

    @property
    def settled(self) -> bool:
        return self.stage == 'cleaned' or (self.stage == 'completed' and self.installation_committed)

    @model_validator(mode='after')
    def durable_completion(self) -> Self:
        effective = self.previous_stage if self.stage == 'recoverable' else self.stage
        planned = {name for name, owner in self.intent.planned_stack_owners.items() if owner == 'portainer'}
        if not set(self.verified_stack_ownership) <= planned:
            raise ValueError('Verified Portainer ownership lies outside the desired plan.')
        if self.installation_committed and set(self.verified_stack_ownership) != planned:
            raise ValueError('Every desired Portainer stack needs verified ownership before completion.')
        workers = {worker.node_name for worker in self.intent.workers}
        if not set(self.worker_uuids) <= workers:
            raise ValueError('Checkpoint worker identity is outside the bound topology.')
        if self.pending_action in {'worker-init', 'worker-start'}:
            if self.pending_node not in workers:
                raise ValueError('Pending worker mutation requires an exact bound target.')
        elif self.pending_node is not None:
            raise ValueError('Unexpected worker target in profile checkpoint.')
        if self.installation_committed and set(self.worker_uuids) != workers:
            raise ValueError('Every selected worker requires a verified bound identity before installation completion.')
        if self.stage != 'recoverable' and self.previous_stage != self.stage:
            raise ValueError('Checkpoint stage history is inconsistent.')
        if effective in {'instance-initialized', 'routes-verified', 'instance-started', 'completed'} and self.instance_uuid is None:
            raise ValueError('Initialized manager identity must remain bound to its checkpoint.')
        if self.installation_committed and (self.stage != 'completed' or self.pending_action is not None):
            raise ValueError('Only a completed profile operation can bind installation completion.')
        return self


class ProfileRuntimeIntent(Contract):
    """Current policy plus the retained creation evidence; never a create request."""
    profile: InstallationProfileIntent
    original: ManagerCreateIntent
    planned_stack_owners: dict[Identifier, Literal['swarm', 'portainer']]

    @model_validator(mode='after')
    def same_installation(self) -> Self:
        if (self.profile.installation_id != self.original.profile.installation_id
                or self.profile.profile != self.original.profile.profile
                or set(self.planned_stack_owners) != set(self.profile.stack_ownership)
                or any(self.planned_stack_owners[name] != owner.owner
                       for name, owner in self.profile.stack_ownership.items())):
            raise ValueError('Runtime authority must preserve the actual installation-owned policy.')
        return self


class ProfileChangeIntent(Contract):
    operation_id: Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]
    controller_revision: Revision
    manifest_token: SHA256
    before_manifest: InstallationManifest
    before: ManagerCreateIntent
    target: ManagerCreateIntent
    instance_uuid: Annotated[str, Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')]
    worker_uuids: dict[Identifier, Annotated[str, Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')]]

    @property
    def profile(self) -> InstallationProfileIntent:
        return self.target.profile

    @property
    def planned_stack_owners(self) -> dict[str, Literal['swarm', 'portainer']]:
        return dict(self.target.planned_stack_owners)

    @model_validator(mode='after')
    def same_owned_runtime(self) -> Self:
        if (self.before_manifest.installation_id != self.before.profile.installation_id
                or self.before_manifest.installation_profile != self.before.profile.profile):
            raise ValueError('Actual baseline manifest differs from profile change ownership.')
        before = self.before.model_dump(exclude={'profile', 'planned_stack_owners'})
        target = self.target.model_dump(exclude={'profile', 'planned_stack_owners'})
        if before != target or self.before.markers() != self.target.markers():
            raise ValueError('Profile change cannot rebind nodes, source image or creator ownership.')
        a, b = self.before.profile, self.target.profile
        baseline_owners = self.before_manifest.effective_stack_ownership()
        if a.stack_ownership != baseline_owners:
            raise ValueError('Profile change baseline ownership differs from its actual manifest.')
        if any(self.target.planned_stack_owners.get(name) != owner.owner
               or b.stack_ownership.get(name) != owner for name, owner in baseline_owners.items()):
            raise ValueError('Adding services cannot transfer existing stack ownership.')
        if (a.profile is None or b.profile is None or a.profile.profile_name != b.profile.profile_name
                or not set(a.resolved_services) <= set(b.resolved_services)
                or set(self.worker_uuids) != {worker.node_name for worker in self.before.workers}):
            raise ValueError('Only additive same-installation profile changes are admitted.')
        return self


class ProfileChangeCheckpoint(Contract):
    schema_version: Literal[1] = 1
    intent: ProfileChangeIntent
    stage: Literal['intent', 'pending', 'verified', 'committed'] = 'intent'
    generation: Annotated[int, Field(ge=0)] = 0
    observation_sha256: SHA256
    verified_stack_ownership: dict[Identifier, PortainerOwnership] = Field(default_factory=dict)

    @property
    def settled(self) -> bool:
        return self.stage == 'committed'

    @model_validator(mode='after')
    def verified_policy(self) -> Self:
        expected = {name for name, mode in self.intent.planned_stack_owners.items() if mode == 'portainer'}
        if not set(self.verified_stack_ownership) <= expected:
            raise ValueError('Profile change has foreign verified ownership.')
        for service_id, owner in self.verified_stack_ownership.items():
            validate_profile_change_owner(self.intent, service_id, owner)
            baseline = self.intent.before_manifest.effective_stack_ownership().get(service_id)
            if self.stage not in {'verified', 'committed'} and owner != baseline:
                raise ValueError('New ownership postconditions require the verified profile target.')
        if self.settled and set(self.verified_stack_ownership) != expected:
            raise ValueError('Committed profile change lacks selected verified ownership.')
        return self


def validate_profile_change_owner(intent: ProfileChangeIntent, service_id: str, owner: PortainerOwnership) -> None:
    checked = PortainerOwnership.model_validate_json(owner.model_dump_json())
    if intent.planned_stack_owners.get(service_id) != 'portainer':
        raise ValueError('Profile change has no selected Portainer ownership.')
    baseline = intent.before_manifest.effective_stack_ownership().get(service_id)
    if baseline is not None and (not isinstance(baseline, PortainerOwnership)
            or checked.model_dump(exclude={'definition_fingerprint'}) != baseline.model_dump(exclude={'definition_fingerprint'})):
        raise ValueError('Existing Portainer ownership identity must remain unchanged.')


def preserve_verified_portainer_identity(previous: PortainerOwnership, current: PortainerOwnership) -> None:
    checked = PortainerOwnership.model_validate_json(current.model_dump_json())
    if checked.model_dump(exclude={'definition_fingerprint'}) != previous.model_dump(exclude={'definition_fingerprint'}):
        raise ValueError('Durably verified Portainer ownership identity must remain unchanged.')


def installation_manifest_sha256(manifest: InstallationManifest) -> str:
    """Bind complete validated metadata before its original adoption write."""
    return hashlib.sha256(json.dumps(manifest.model_dump(mode='json'), sort_keys=True,
        separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
