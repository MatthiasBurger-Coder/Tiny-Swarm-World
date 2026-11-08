"""Acquire complete image/task facts for new pinned selective-setup components."""
from __future__ import annotations

import asyncio

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestRepository
from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.application.ports.update import PortUpdateRuntimeObserver
from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog, ComponentState, InstallationManifest, ServiceDefinition, VersionIdentity


OBSERVATION_TIMEOUT_SECONDS = 30.0
_SUPPORTED_SERVICES = frozenset({"swagger", "traefik"})


def observations_required(observations: SetupComponentObservations | None) -> bool:
    return observations is not None and observations.required


def require_complete_observations(observations: SetupComponentObservations | None) -> None:
    if observations is not None and not observations.complete:
        raise LifecycleStateError("New pinned components require verified source observations before selection persistence.")


async def enrich_setup_inventory(
    observations: SetupComponentObservations | None, repository: ManifestRepository,
    expected_token: str | None, fresh: InstallationManifest | None, observer: PortUpdateRuntimeObserver,
) -> tuple[tuple[ComponentState, ...], InstallationManifest | None]:
    if observations is None:
        raise LifecycleStateError("Selection must be admitted before source observation.")
    if repository.load().token != expected_token:
        raise LifecycleStateError("Selection is stale; inspect installation state before source observation.")
    updated = await observations.observe(observer)
    return updated, fresh.model_copy(update={"components": updated}) if fresh is not None else None


def _new_pinned_bundle(service: ServiceDefinition, inventory: dict[str, ComponentState],
                       existing: frozenset[str]) -> tuple[ComponentState, ...]:
    if service.service_id not in _SUPPORTED_SERVICES:
        return ()
    members = tuple(inventory.get(item.component_id) for item in service.components)
    if any(item is None or item.component_id in existing or not item.desired.image_digest
           or not item.desired.image_repository for item in members):
        return ()
    complete = tuple(item for item in members if item is not None)
    bundles = (*tuple(item.source_versions for item in service.update_transitions),
               *tuple(item.versions for item in service.update_targets
                      if item.qualification in {"candidate-transition", "qualified-transition"}))
    return complete if any(_matches_bundle(complete, versions) for versions in bundles) else ()


def _matches_bundle(components: tuple[ComponentState, ...], versions: dict[str, VersionIdentity]) -> bool:
    return {item.component_id for item in components} == versions.keys() and all(
        all(getattr(item.desired, name) == value for name, value in versions[item.component_id].model_dump().items()
            if value is not None) for item in components
    )


def _observed_identity(reference: str) -> VersionIdentity:
    name, separator, digest = reference.partition("@")
    if not separator:
        raise LifecycleStateError("Pinned source observation has no immutable image identity.")
    repository, tag = name.rsplit(":", 1) if ":" in name.rsplit("/", 1)[-1] else (name, None)
    return VersionIdentity(image_repository=repository, image_tag=tag, image_digest=digest)


def _pinned_reference(identity: VersionIdentity) -> str:
    if not identity.image_repository or not identity.image_digest:
        raise LifecycleStateError("New source observation requires an immutable image reference.")
    return identity.image_repository + "@" + identity.image_digest


class SetupComponentObservations:
    """Hold no persistent authority until every new eligible member was observed."""

    def __init__(self, inventory: tuple[ComponentState, ...], catalog: ComponentCatalog,
                 existing: InstallationManifest | None) -> None:
        self.inventory = inventory
        retained = frozenset(item.component_id for item in existing.components) if existing else frozenset()
        indexed = {item.component_id: item for item in inventory}
        self.targets = tuple(item for service in catalog.services
                             for item in _new_pinned_bundle(service, indexed, retained))
        self.complete = not self.targets

    @property
    def required(self) -> bool:
        return bool(self.targets)

    async def observe(self, observer: PortUpdateRuntimeObserver) -> tuple[ComponentState, ...]:
        self.complete = not self.targets
        observed = {}
        try:
            for component in self.targets:
                expected = _pinned_reference(component.desired)
                result = await asyncio.wait_for(
                    observer.observe(component.service_id, component.component_id),
                    timeout=OBSERVATION_TIMEOUT_SECONDS,
                )
                if (result.stack_name != component.service_id or result.service_name != component.component_id
                        or not result.converged(expected)):
                    raise LifecycleStateError("New component image/task observations do not match the pinned selection.")
                observed[component.component_id] = _observed_identity(result.desired_image)
        except (OperationError, TimeoutError, ValueError):
            raise LifecycleStateError("New component observations failed; preserve runtime and inspect the selected source images/tasks.") from None
        updated = tuple(item.model_copy(update={"observed": observed[item.component_id]})
                        if item.component_id in observed else item for item in self.inventory)
        self.complete = True
        return updated
