"""Observe local resources; execute only freshly planned create/start/access actions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from collections.abc import Callable
from tiny_swarm_world.application.ports.incus_preparation import IncusPreparationFailure
from tiny_swarm_world.domain.incus_preparation import IncusAction, IncusSnapshot
from tiny_swarm_world.infrastructure.adapters.incus_preparation.configuration import load_requirements
from tiny_swarm_world.infrastructure.adapters.incus_preparation.resources import (
    find_resource, profile_compatible, resource_actions,
)
from tiny_swarm_world.infrastructure.adapters.incus_preparation import runtime
from tiny_swarm_world.infrastructure.adapters.incus_preparation.preservation import preserved_inventory, stable_links
from tiny_swarm_world.infrastructure.adapters.native_preparation_evidence import NativePreparationEvidenceWriter


class LocalIncusPreparation:
    def __init__(self, configuration_path: Path, *, release: str,
                 evidence: NativePreparationEvidenceWriter | None = None,
                 target_snapshot: Callable[[], tuple[object, ...]] | None = None) -> None:
        self.path = configuration_path
        self.release = release
        self.evidence = evidence or NativePreparationEvidenceWriter()
        self._actions: tuple[IncusAction, ...] = ()
        self._target_snapshot = target_snapshot
        self._before: dict[str, Any] = {}

    async def inspect(self) -> IncusSnapshot:
        self._actions = ()
        try:
            return await self._inspect()
        except IncusPreparationFailure as error:
            if error.exit_code is not None:
                raise
            return IncusSnapshot("blocked", blockers=(error.code,))
        except (OSError, RuntimeError, ValueError):
            return IncusSnapshot("blocked", blockers=("Host/release/provider configuration cannot be qualified; review ./prepare_linux.sh --dry-run.",))

    async def _inspect(self) -> IncusSnapshot:
        actions: tuple[IncusAction, ...]
        requirements = load_requirements(self.path)
        config_hash = hashlib.sha256(self.path.read_bytes()).hexdigest()
        user, active, persisted = runtime.account()
        daemon = await runtime.daemon_state()
        base: dict[str, Any] = {"configuration": config_hash, "user": user,
                                "active_group": active, "persisted_group": persisted, "daemon": daemon}
        if self._target_snapshot is not None:
            base["host"] = self._target_snapshot()
        if daemon["ActiveState"] != "active":
            actions = (IncusAction("daemon:start", "daemon", "incus.service", privilege="sudo"),)
            return self._snapshot(base, actions)
        # No Incus calls on a stopped daemon: read-only inspection cannot socket-activate it.
        access = await runtime.command((*runtime.LOCAL_INCUS, "info"))
        if access.returncode:
            if persisted and not active:
                return self._snapshot(base, (), restart=True)
            if active:
                raise IncusPreparationFailure("Active incus-admin session cannot access Incus; inspect daemon/socket permissions, then ./prepare_linux.sh --dry-run.")
            actions = (IncusAction("access:add-group", "access", user, privilege="sudo", restart="login"),)
            return self._snapshot(base, actions)
        await runtime.checked_command((*runtime.LOCAL_INCUS, "version"))
        server = await runtime.query("/1.0")
        if not isinstance(server, dict) or not isinstance(server.get("environment"), dict) or server["environment"].get("server_clustered") is not False:
            raise IncusPreparationFailure("Clustered or unknown Incus server is outside local bootstrap; preserve it and review the provider target.")
        inventory = {kind: runtime.named_resources(await runtime.query(f"/1.0/{kind}?recursion=1&project=default"), kind)
                     for kind in ("storage-pools", "networks", "profiles", "instances")}
        routes = await runtime.json_command(("ip", "-j", "-4", "route", "show", "table", "all"))
        links = await runtime.json_command(("ip", "-j", "address", "show"))
        base.update(server=server, inventory=inventory, routes=routes, links=stable_links(links))
        actions = resource_actions(requirements, inventory, routes, links)
        return self._snapshot(base, actions, verified=not actions)

    def _snapshot(self, base: dict[str, Any], actions: tuple[IncusAction, ...], *,
                  restart: bool = False, verified: bool = False) -> IncusSnapshot:
        self._actions = actions
        self._before = base
        digest = hashlib.sha256(json.dumps(base, sort_keys=True).encode()).hexdigest()
        return IncusSnapshot(digest, actions, restart_required=restart, verified=verified)

    async def execute(self, action: IncusAction) -> None:
        args: tuple[str, ...]
        if action not in self._actions:
            raise IncusPreparationFailure("Action is outside the currently observed plan.")
        if action.kind == "daemon":
            args = ("sudo", "-n", "/usr/bin/systemctl", "start", "incus.service")
        elif action.kind == "access":
            args = ("sudo", "-n", "/usr/sbin/usermod", "-a", "-G", "incus-admin", "--", action.name)
        else:
            args = (*runtime.LOCAL_INCUS, "query", f"/1.0/{action.kind}?project=default",
                    "-X", "POST", "--wait", "--data", action.payload)
        try:
            await runtime.checked_command(args, action.timeout_seconds)
        except IncusPreparationFailure as error:
            if action.privilege == "sudo":
                raise IncusPreparationFailure("Privileged Incus stage stopped; run sudo -v, inspect systemctl status incus.service, then ./prepare_linux.sh --dry-run.", exit_code=error.exit_code) from None
            raise

    async def action_verified(self, action: IncusAction) -> bool:
        if action.kind == "daemon":
            return (await runtime.daemon_state())["ActiveState"] == "active"
        if action.kind == "access":
            return runtime.account()[2]
        if hashlib.sha256(self.path.read_bytes()).hexdigest() != self._before["configuration"]:
            raise IncusPreparationFailure("Provider configuration changed during apply; review a fresh plan.")
        if self._target_snapshot is not None:
            try:
                target = self._target_snapshot()
            except (OSError, RuntimeError, ValueError):
                raise IncusPreparationFailure("Host/release qualification failed during apply; review a fresh plan.") from None
            if target != self._before["host"]:
                raise IncusPreparationFailure("Host/release changed during apply; review a fresh plan.")
        inventory = await preserved_inventory(self._before, action)
        items = inventory[action.kind]
        existing = find_resource(items, action.name)
        if existing is None:
            return False
        desired = json.loads(action.payload)
        if action.kind == "profiles":
            return profile_compatible(existing, action, False, require_devices=True)
        return (existing.get("status") == "Created"
                and all(existing.get("config", {}).get(key) == value for key, value in desired["config"].items())
                and all(existing.get(key) == desired[key] for key in ("type", "driver") if key in desired))

    def record(self, status: str, planned: tuple[str, ...], completed: tuple[str, ...],
               uncertain: tuple[str, ...]) -> str:
        return str(self.evidence.write(platform_release=self.release, status=status,
                    planned=planned, added=completed, uncertain=uncertain,
                    stage="incus_preparation", capability="incus"))
