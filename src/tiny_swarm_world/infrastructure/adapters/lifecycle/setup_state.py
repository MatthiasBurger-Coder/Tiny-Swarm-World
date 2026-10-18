"""Admit proven-fresh Classic setups and commit verified desired selection metadata."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tomllib
from uuid import uuid4
from typing import Literal

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.domain.lifecycle.models import ComponentState, ConfigurationReference, CredentialReference, InstallationManifest, ProductIdentity, VersionIdentity
from tiny_swarm_world.domain.artifacts.container_image_contract import DEFAULT_CONTAINER_IMAGE_CONTRACTS
from tiny_swarm_world.domain.preflight.setup_manifest import default_setup_manifest
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import resolve_container_image_contracts
from tiny_swarm_world.infrastructure.adapters.repositories.secret_manifest_yaml_repository import SecretManifestYamlRepository
from tiny_swarm_world.domain.lifecycle.selection import SelectionPlan
from tiny_swarm_world.infrastructure.process.runner import ProcessRunner, ProcessRunnerError


class SetupSelectionState:
    def __init__(self, lifecycle: InstallationLifecycleService, plan: SelectionPlan, root: Path):
        self.lifecycle = lifecycle
        self.plan = plan
        self.root = root
        self.fresh: InstallationManifest | None = None
        self.component_inventory: tuple[ComponentState, ...] = ()
        self.credential_inventory: tuple[CredentialReference, ...] = ()
        self.configuration_inventory: tuple[ConfigurationReference, ...] = ()

    def admit(self, runner: ProcessRunner, *, backend: str, node_names: tuple[str, ...], host: Literal["native-linux", "wsl2"]) -> None:
        snapshot = self.lifecycle.manifests.load()
        if snapshot.token != self.plan.manifest_token:
            raise LifecycleStateError("Selection is stale; inspect installation state and preview again.")
        if self.plan.removals:
            raise LifecycleStateError("Implicit removal is unsupported; use services remove --preview.")
        self.component_inventory = self._effective_inventory(snapshot.manifest)
        self.credential_inventory = self._credential_references(snapshot.manifest)
        self.configuration_inventory = self._configuration_references(snapshot.manifest)
        if snapshot.manifest is not None:
            self.lifecycle.catalog.load().validate_manifest(snapshot.manifest)
            if snapshot.manifest.host != host:
                raise LifecycleStateError("Installation manifest host differs; inspect/adopt the correct host before mutation.")
            return
        if any(note.startswith("interrupted_write") for note in snapshot.diagnostics):
            raise LifecycleStateError("Interrupted adoption requires explicit inventory review before setup.")
        self._require_fresh(runner, backend, node_names)
        self.fresh = self._fresh_manifest(runner, host)

    def _require_fresh(self, runner: ProcessRunner, backend: str, node_names: tuple[str, ...]) -> None:
        if backend != "incus":
            raise LifecycleStateError("Selective Classic setup requires the supported Incus backend.")
        try:
            result = runner.run_text((backend, "list", "--format", "json"), timeout=10)
            payload = json.loads(result.stdout)
            if result.returncode or not isinstance(payload, list):
                raise ValueError
            for node in payload:
                if not isinstance(node, dict) or not isinstance(node.get("name"), str) or not isinstance(node.get("config"), dict):
                    raise ValueError
                if node["name"] in node_names or any(key.startswith("user.tiny_swarm_world.") for key in node["config"]):
                    raise LifecycleStateError("Existing managed nodes have no manifest; explicitly inventory/adopt them before selective setup. No reset was performed.")
        except LifecycleStateError:
            raise
        except (ProcessRunnerError, OSError, ValueError, TypeError):
            raise LifecycleStateError("Cannot prove a fresh installation from bounded Incus inventory; inspect/adopt before mutation.") from None

    def _fresh_manifest(self, runner: ProcessRunner, host: Literal["native-linux", "wsl2"]) -> InstallationManifest:
        try:
            revision = runner.run_text(("git", "rev-parse", "--verify", "HEAD"), cwd=self.root, timeout=5)
            if revision.returncode:
                raise ValueError
            project = tomllib.loads((self.root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
            product = ProductIdentity(release=project["version"], revision=revision.stdout.strip(),
                                      dependency_lock="sha256:" + hashlib.sha256((self.root / "requirements.lock").read_bytes()).hexdigest())
            components = self.component_inventory
            return InstallationManifest(
                installation_id=str(uuid4()), host=host, service_preset=self.plan.service_preset,
                product=product, requested_services=self.plan.requested_services,
                resolved_services=self.plan.resolved_services, selection_reasons=self.plan.selection_reasons,
                components=components, credential_references=self.credential_inventory,
                configuration_references=self.configuration_inventory,
            )
        except (ProcessRunnerError, OSError, KeyError, ValueError):
            raise LifecycleStateError("Prepared checkout identity cannot be verified; inspect product revision and lock before setup.") from None

    def commit(self) -> None:
        if self.fresh is not None:
            self.lifecycle.adopt(self.fresh, approved=True, preview=False)
        else:
            ServiceSelectionService(self.lifecycle.manifests, self.lifecycle.catalog).persist(self.plan, approved=True, component_inventory=self.component_inventory,
                credential_inventory=self.credential_inventory, configuration_inventory=self.configuration_inventory)

    def _effective_inventory(self, existing: InstallationManifest | None) -> tuple[ComponentState, ...]:
        components = tuple(item for service in self.lifecycle.catalog.load().services
                           if service.service_id in self.plan.resolved_services for item in service.components)
        contexts = {item.component_id for item in components}
        contracts = resolve_container_image_contracts(tuple(item for item in DEFAULT_CONTAINER_IMAGE_CONTRACTS
                                                           if item.build_context in contexts), os.environ)
        versions = {item.build_context: VersionIdentity(
            image_repository=item.image_name, image_tag=None if item.tag.startswith("@") else item.tag,
            image_digest=item.tag[1:] if item.tag.startswith("@") else None,
            build_identity=item.tag if item.source == "build" else None,
        ) for item in contracts}
        retained = {} if existing is None else {item.component_id: item for item in existing.components}
        result = []
        for item in components:
            desired = versions.get(item.component_id, item.desired)
            prior = retained.get(item.component_id)
            if prior is not None and item.component_id in versions and not _same_image(prior.desired, desired):
                raise LifecycleStateError("Effective image inputs differ from installed desired state; use a supported component update or restore matching overrides before adding services.")
            result.append(prior if prior is not None else item.model_copy(update={"desired": desired}))
        return tuple(result)

    def _credential_references(self, existing: InstallationManifest | None) -> tuple[CredentialReference, ...]:
        retained = () if existing is None else existing.credential_references
        keys = {item.key for item in retained}
        selected_keys = {item.name for item in default_setup_manifest(
            service_profile=self.plan.service_preset, resolved_services=self.plan.resolved_services).required_secrets}
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


def _same_image(before: VersionIdentity, after: VersionIdentity) -> bool:
    return all(getattr(before, key) == getattr(after, key)
               for key in ("image_repository", "image_tag", "image_digest", "build_identity"))
