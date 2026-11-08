"""Admit proven-fresh Classic setups and commit verified desired selection metadata."""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease, require_legacy_runtime_policy
from tiny_swarm_world.application.ports.update import PortUpdateRuntimeObserver
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.domain.lifecycle.models import ComponentState, ConfigurationReference, CredentialReference, InstallationManifest
from tiny_swarm_world.domain.preflight.setup_manifest import default_setup_manifest
from tiny_swarm_world.infrastructure.adapters.repositories.secret_manifest_yaml_repository import SecretManifestYamlRepository
from tiny_swarm_world.domain.lifecycle.selection import SelectionPlan
from tiny_swarm_world.infrastructure.process.runner import ProcessRunner
from tiny_swarm_world.infrastructure.adapters.lifecycle import setup_inventory
from tiny_swarm_world.infrastructure.adapters.lifecycle.setup_observations import (
    SetupComponentObservations, enrich_setup_inventory, observations_required, require_complete_observations,
)


if TYPE_CHECKING:
    from tiny_swarm_world.application.services.profile_setup import ScopedProfileSetupOperation, ProfileRuntimeOperation
    from tiny_swarm_world.application.services.profile_change import ProfileChangeOperation


class SetupSelectionState:
    def __init__(self, lifecycle: InstallationLifecycleService, plan: SelectionPlan, root: Path):
        self.lifecycle = lifecycle
        self.plan = plan
        self.root = root
        self.operation_lease: InstallationLease | None = None
        self.profile_operation: ScopedProfileSetupOperation | ProfileRuntimeOperation | ProfileChangeOperation | None = None
        self.fresh: InstallationManifest | None = None
        self.component_inventory: tuple[ComponentState, ...] = ()
        self.credential_inventory: tuple[CredentialReference, ...] = ()
        self.configuration_inventory: tuple[ConfigurationReference, ...] = ()
        self._observations: SetupComponentObservations | None = None

    def admit(self, runner: ProcessRunner, *, backend: str, node_names: tuple[str, ...], host: Literal["native-linux", "wsl2"], recover_manifest: InstallationManifest | None = None) -> None:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.desired_images import require_settled_updates, require_settled_product

        require_settled_product(self.root)
        require_settled_updates(self.root)
        snapshot = self.lifecycle.manifests.load()
        if snapshot.token != self.plan.manifest_token:
            raise LifecycleStateError("Selection is stale; inspect installation state and preview again.")
        if self.plan.removals:
            raise LifecycleStateError("Implicit removal is unsupported; use services remove --preview.")
        self.component_inventory = self._effective_inventory(snapshot.manifest)
        self.credential_inventory = self._credential_references(snapshot.manifest)
        self.configuration_inventory = self._configuration_references(snapshot.manifest)
        self._observations = SetupComponentObservations(
            self.component_inventory, self.lifecycle.catalog.load(), snapshot.manifest,
        )
        if snapshot.manifest is not None:
            if snapshot.manifest.installation_profile is None:
                require_legacy_runtime_policy(snapshot.manifest)
            self.lifecycle.catalog.load().validate_manifest(snapshot.manifest)
            if snapshot.manifest.host != host:
                raise LifecycleStateError("Installation manifest host differs; inspect/adopt the correct host before mutation.")
            return
        if any(note.startswith("interrupted_write") for note in snapshot.diagnostics):
            raise LifecycleStateError("Interrupted adoption requires explicit inventory review before setup.")
        if recover_manifest is not None:
            if recover_manifest.host != host:
                raise LifecycleStateError('Original setup host changed.')
            self.fresh = recover_manifest
        else:
            self._require_fresh(runner, backend, node_names)
            self.fresh = self._fresh_manifest(runner, host)

    def _require_fresh(self, runner: ProcessRunner, backend: str, node_names: tuple[str, ...]) -> None:
        setup_inventory.require_fresh(runner, backend, node_names)

    def _fresh_manifest(self, runner: ProcessRunner, host: Literal["native-linux", "wsl2"]) -> InstallationManifest:
        return setup_inventory.fresh_manifest(runner, host, self.root, self.plan,
            self.component_inventory, self.credential_inventory, self.configuration_inventory)

    @property
    def observation_required(self) -> bool:
        return observations_required(self._observations)

    async def observe_new_components(self, observer: PortUpdateRuntimeObserver) -> None:
        self.component_inventory, self.fresh = await enrich_setup_inventory(
            self._observations, self.lifecycle.manifests, self.plan.manifest_token, self.fresh, observer,
        )

    async def admit_exposure(self) -> None:
        desired = getattr(self.plan, 'service_exposure', {})
        if self.profile_operation is not None:
            await self.profile_operation.admit_desired(self.plan)
        elif desired.get('swagger') == 'internal':
            raise LifecycleStateError('Internal exposure requires a private, admitted installation profile operation.')

    def commit(self) -> None:
        require_complete_observations(self._observations)
        if self.fresh is not None:
            from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import commit_fresh_selection
            commit_fresh_selection(self)
        elif self.profile_operation is not None and hasattr(self.profile_operation.intent, 'target'):
            from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import commit_selection
            commit_selection(self)
        else:
            ServiceSelectionService(self.lifecycle.manifests, self.lifecycle.catalog, operation_lock=self.lifecycle.operation_lock).persist(self.plan, approved=True,
                operation_lease=self.operation_lease, verified_migration=True, component_inventory=self.component_inventory,
                credential_inventory=self.credential_inventory, configuration_inventory=self.configuration_inventory)

    def _effective_inventory(self, existing: InstallationManifest | None) -> tuple[ComponentState, ...]:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.desired_images import effective_component_inventory

        return effective_component_inventory(self.lifecycle.catalog, self.plan.resolved_services, existing, self.root)

    def _credential_references(self, existing: InstallationManifest | None) -> tuple[CredentialReference, ...]:
        retained = () if existing is None else existing.credential_references
        keys = {item.key for item in retained}
        selected_keys = {item.name for item in default_setup_manifest(
            service_profile=self.plan.service_preset, resolved_services=self.plan.resolved_services,
            service_exposure=self.plan.service_exposure).required_secrets}
        root = getattr(self.lifecycle.catalog, "root", self.root)
        entries = SecretManifestYamlRepository(root / "infra/config/secrets/infisical-secrets.yaml").load()
        return (*retained, *(CredentialReference.model_validate({"key": item.key, "source": item.source})
                             for item in entries if item.key in selected_keys and item.key not in keys))

    def _configuration_references(self, existing: InstallationManifest | None) -> tuple[ConfigurationReference, ...]:
        from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT

        retained = () if existing is None else existing.configuration_references
        keys = {item.key for item in retained}
        result = list(retained)
        for component in self.component_inventory:
            name = IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT.get(component.component_id)
            if name and os.environ.get(name) and name.lower() not in keys:
                result.append(ConfigurationReference(key=name.lower(), source="environment", reference=name.lower()))
        return tuple(result)
