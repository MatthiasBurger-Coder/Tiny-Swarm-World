"""Observe everything before mutation; reconcile only the current exact plan."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from collections.abc import Callable

from tiny_swarm_world.application.ports.incus_preparation import IncusPreparationFailure
from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.domain.network_preparation import NetworkAction, NetworkSnapshot
from tiny_swarm_world.infrastructure.adapters.native_preparation_evidence import NativePreparationEvidenceWriter
from tiny_swarm_world.infrastructure.adapters.network_preparation import forwarding, runtime
from tiny_swarm_world.infrastructure.adapters.network_preparation import files
from tiny_swarm_world.infrastructure.adapters.network_preparation.inventory import inspect_network



class LocalNetworkPreparation:
    def __init__(self, root: Path, config_root: Path, *, release: str, profile: str,
                 target_snapshot: Callable[[], tuple[object, ...]],
                 evidence: NativePreparationEvidenceWriter | None = None, windows: Any = None,
                 proc_root: Path = Path("/proc/sys")) -> None:
        self.root, self.config_root = root, config_root
        self.release, self.profile = release, profile
        self.target_snapshot = target_snapshot
        self.evidence = evidence or NativePreparationEvidenceWriter(selection=profile)
        self.windows = windows
        self.proc_root = proc_root
        self._payloads: dict[str, Any] = {}
        self._snapshot: NetworkSnapshot | None = None

    async def inspect(self) -> NetworkSnapshot:
        self._payloads = {}
        try:
            self._snapshot = await inspect_network(self)
            try:
                self.evidence.validate(platform_release=self.release, capability="network")
            except OSError:
                from dataclasses import replace
                self._snapshot = replace(self._snapshot, blockers=self._snapshot.blockers + ("Bootstrap state blocked; preserve evidence. Next: ./prepare_linux.sh --dry-run",))
        except (NetworkPreparationFailure, IncusPreparationFailure, OSError, RuntimeError, ValueError) as error:
            if isinstance(error, NetworkPreparationFailure) and error.exit_code:
                raise
            self._snapshot = NetworkSnapshot("blocked", "blocked", blockers=(str(error),), is_wsl=self.windows is not None)
        except (TypeError, KeyError, IndexError, AttributeError):
            self._snapshot = NetworkSnapshot("blocked", "blocked", blockers=("Incomplete/unrecognized network inventory; preserve host state.",), is_wsl=self.windows is not None)
        return self._snapshot

    async def execute(self, action: NetworkAction) -> None:
        if self._snapshot is None or not any(item.id == action.id and item.kind == action.kind for item in self._snapshot.actions):
            raise NetworkPreparationFailure("Action is outside the current network plan.")
        payload = self._payloads[action.id]
        if action.kind == "file":
            path, before, content, mode, shared, source_digest = payload
            await files.install(path, before, content, mode, shared=shared, source_digest=source_digest)
        elif action.kind == "module":
            await runtime.privileged(("modprobe", "br_netfilter"), 15)
        elif action.kind == "sysctl":
            await runtime.privileged(("sysctl", "-w", payload + "=1"), 10)
        elif action.kind == "forwarding":
            await forwarding.apply_missing(*payload)
        elif action.kind == "enable":
            await runtime.privileged(("systemctl", "daemon-reload"), 15)
            await runtime.privileged(("systemctl", "enable", "tsw-incus-forwarding.service"), 15)
        elif action.kind == "windows":
            await self.windows.apply(payload)

    async def action_verified(self, action: NetworkAction) -> bool:
        current = await self.inspect()
        return not current.blockers and all(item.id != action.id for item in current.actions)

    def record(self, status, planned, completed, uncertain, *, exit_code: int | None = None) -> str:
        return str(self.evidence.write(platform_release=self.release, status=status, planned=planned,
                   added=completed, uncertain=uncertain, stage=_record_stage(self, status, uncertain, "network_preparation"), capability="network", exit_code=exit_code,
                   observation=hashlib.sha256(repr(self._snapshot).encode()).hexdigest(),
                   cause="effect_uncertain" if uncertain else "none"))


def _record_stage(adapter, status: str, uncertain: tuple[str, ...], default: str) -> str:
    if status == "started":
        adapter._last_record_stage = default
    if uncertain:
        adapter._last_record_stage = uncertain[-1]
    return getattr(adapter, "_last_record_stage", default)
