"""Kernel, persistence and name plans with every collision observed first."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.domain.network_preparation import NetworkAction
from tiny_swarm_world.infrastructure.adapters.network.host_network_repair import FORWARDING_SCRIPT_PATH, FORWARDING_SERVICE_PATH
from tiny_swarm_world.infrastructure.adapters.network_preparation import files, forwarding, runtime

CONTROLS = ("net.ipv4.ip_forward", "net.bridge.bridge-nf-call-iptables", "net.bridge.bridge-nf-call-ip6tables")
SYSCTL_PATH = Path("/etc/sysctl.d/90-tiny-swarm-world.conf")
MODULES_PATH = Path("/etc/modules-load.d/tiny-swarm-world.conf")

class LinuxPlanner:
    def __init__(self, config_root: Path, proc_root: Path, payloads) -> None:
        self.config_root, self.proc_root, self._payloads = config_root, proc_root, payloads

    async def plan(self, names, bridges, firewall):
        actions: list[NetworkAction] = []
        observations: dict[str, Any] = {}
        config = (self.config_root / "host/tiny-swarm-world-sysctl.conf").read_bytes()
        modules = (self.config_root / "host/tiny-swarm-world-modules.conf").read_bytes()
        if [line for line in modules.decode().splitlines() if line and not line.startswith("#")] != ["br_netfilter"]:
            raise NetworkPreparationFailure("Canonical module asset is incompatible.")
        values = dict(line.split("=", 1) for line in config.decode().splitlines() if line and not line.startswith("#"))
        if values != dict.fromkeys(CONTROLS, "1"):
            raise NetworkPreparationFailure("Canonical kernel control asset is incompatible.")
        for control in CONTROLS:
            path = self.proc_root / control.replace(".", "/")
            observations[control] = path.read_text().strip() if path.exists() else None
        if any(value is None for value in observations.values()):
            await runtime.command(("modinfo", "br_netfilter"))
            self._add(actions, "module:br_netfilter", "module", "Load required br_netfilter; missing bridge controls become observable.", None)
        for control in CONTROLS:
            if observations[control] != "1":
                self._add(actions, "sysctl:" + control, "sysctl", f"Host-wide {control}: {observations[control]} -> 1", control)
        desired_files = ((SYSCTL_PATH, config, 0o644, False),
                         (MODULES_PATH, modules, 0o644, False),
                         (FORWARDING_SCRIPT_PATH, forwarding.render_script(bridges, firewall), 0o755, False),
                         (FORWARDING_SERVICE_PATH, forwarding.render_service(), 0o644, False))
        for path, content, mode, shared in desired_files:
            self._file(actions, observations, path, content, mode, shared)
        if firewall["missing"]:
            self._add(actions, "forwarding:rules", "forwarding", "Add only missing exact scoped firewall allowances; preserve policies and Incus NAT.", (bridges, firewall), 90)
        service = await runtime.command(("systemctl", "show", "tsw-incus-forwarding.service", "--property=UnitFileState"))
        observations["forwarding_service"] = service
        if "UnitFileState=enabled" not in service:
            self._add(actions, "forwarding:enable", "enable", "Enable the bounded existing forwarding persistence owner.", None)
        hosts = files.observe(Path("/etc/hosts"))
        desired = files.desired_hosts(hosts.content, names)
        self._file(actions, observations, Path("/etc/hosts"), desired, hosts.mode, True)
        observations["resolution"] = {}
        for name in names:
            output = await runtime.command(("getent", "ahostsv4", name), permit_failure=True)
            observations["resolution"][name] = output
            if hosts.content == desired and (not output or any(line.split()[0] != "127.0.0.1" for line in output.splitlines())):
                raise NetworkPreparationFailure("Canonical names do not resolve to loopback; inspect NSS policy.")
        return actions, observations

    def _file(self, actions, observations, path, content, mode, shared):
        before = files.observe(path)
        observations[str(path)] = before.fingerprint
        source_digest = files.helper_source_digest()
        observations["file_helper"] = source_digest
        if before.exists and (before.content != content or before.mode != mode) and not shared:
            raise NetworkPreparationFailure(f"Incompatible persistence file preserved: {path}. Resolve its owner before preparation.")
        if before.content != content or not before.exists:
            self._add(actions, "file:" + str(path), "file", f"Protected {'managed block' if shared else 'new file'}: {path}; sha256={hashlib.sha256(content).hexdigest()}", (path, before, content, mode, shared, source_digest))

    def _add(self, actions, id, kind, description, payload, timeout=30):
        actions.append(NetworkAction(id, kind, description, timeout))
        self._payloads[id] = payload
