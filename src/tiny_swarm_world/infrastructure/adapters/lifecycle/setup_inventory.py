"""Fresh-install inventory and prepared-source manifest factory; no persistence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tomllib
from typing import Literal
from uuid import uuid4

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.models import ComponentState, ConfigurationReference, CredentialReference, InstallationManifest, ProductIdentity, migrate_manifest_v1
from tiny_swarm_world.domain.lifecycle.selection import SelectionPlan
from tiny_swarm_world.infrastructure.process.runner import ProcessRunner, ProcessRunnerError


def require_fresh( runner: ProcessRunner, backend: str, node_names: tuple[str, ...]) -> None:
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

def fresh_manifest(runner: ProcessRunner, host: Literal["native-linux", "wsl2"], root: Path, plan: SelectionPlan, component_inventory: tuple[ComponentState, ...], credential_inventory: tuple[CredentialReference, ...], configuration_inventory: tuple[ConfigurationReference, ...]) -> InstallationManifest:
    try:
        revision = runner.run_text(("git", "rev-parse", "--verify", "HEAD"), cwd=root, timeout=5)
        if revision.returncode:
            raise ValueError
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        product = ProductIdentity(release=project["version"], revision=revision.stdout.strip(),
                                  dependency_lock="sha256:" + hashlib.sha256((root / "requirements.lock").read_bytes()).hexdigest())
        components = component_inventory
        manifest = InstallationManifest(
            installation_id=str(uuid4()), host=host, service_preset=plan.service_preset,
            product=product, requested_services=plan.requested_services,
            resolved_services=plan.resolved_services, selection_reasons=plan.selection_reasons,
            components=components, credential_references=credential_inventory,
            configuration_references=configuration_inventory,
        )
        if 'internal' in plan.service_exposure.values():
            payload = migrate_manifest_v1(manifest).model_dump()
            payload['service_exposure'] = plan.service_exposure
            return InstallationManifest.model_validate(payload)
        return manifest
    except (ProcessRunnerError, OSError, KeyError, ValueError):
        raise LifecycleStateError("Prepared checkout identity cannot be verified; inspect product revision and lock before setup.") from None
