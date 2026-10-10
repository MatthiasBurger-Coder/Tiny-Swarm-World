"""Complete host observations assembled without mutable preparation state."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.domain.network_preparation import NetworkAction, NetworkSnapshot
from tiny_swarm_world.infrastructure.adapters.incus_preparation import runtime as incus
from tiny_swarm_world.infrastructure.adapters.incus_preparation.preservation import stable_links
from tiny_swarm_world.infrastructure.adapters.network_preparation import configuration, firewall_inventory, runtime
from tiny_swarm_world.infrastructure.adapters.network_preparation.linux_plan import LinuxPlanner
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import forwarding_rules, input_rules, ufw_rules
from tiny_swarm_world.infrastructure.adapters.network_preparation.preservation import firewall_foreign, hosts_foreign



def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


async def inspect_network(self) -> NetworkSnapshot:
    identity = self.target_snapshot()
    daemon = await incus.daemon_state()
    if daemon["ActiveState"] != "active":
        raise NetworkPreparationFailure("Incus is stopped; network inventory cannot activate it. Run Incus preparation.")
    networks = incus.named_resources(await incus.query("/1.0/networks?recursion=1&project=default"), "networks")
    instances = incus.named_resources(await incus.query("/1.0/instances?recursion=1&project=default"), "instances")
    routes = await incus.json_command(("ip", "-j", "-4", "route", "show", "table", "all"))
    links = stable_links(await incus.json_command(("ip", "-j", "address", "show")))
    bridges = configuration.resolve_bridges(self.config_root / "node-providers/provider_config.yaml", networks, routes, links)
    names, ports, exposure = configuration.local_names(self.config_root / "ports.yaml", self.profile)
    listeners = await runtime.privileged(("ss", "-H", "-ltnp"))
    provenance = await configuration.verify_listeners(listeners, ports, instances, exposure)
    firewall = await firewall_inventory.inventory(bridges, ports)
    firewall["ports"] = ports
    firewall["desired_rules"] = tuple((chain, rule) for bridge in bridges
        for chain, rules in (("FORWARD", forwarding_rules(bridge)), ("INPUT", input_rules(bridge) if firewall["input_restricted"] else ()))
        for rule in rules)
    firewall["ufw_desired"] = tuple(("ufw", *rule) for bridge in bridges for rule in ufw_rules(bridge))
    base = {"identity": identity, "networks": networks, "routes": routes, "links": links,
            "listeners": listeners, "listener_provenance": provenance, "instances": instances, "names": names, "exposure": exposure,
            "owner": (firewall["ufw"], firewall["owners"], firewall["status"].splitlines()[0]), "foreign_firewall": firewall_foreign(firewall),
            "foreign_hosts": hosts_foreign()}
    actions, observations = await LinuxPlanner(self.config_root, self.proc_root, self._payloads).plan(names, bridges, firewall)
    windows_state = await self.windows.inspect(links) if self.windows is not None else None
    if windows_state and windows_state["blockers"]:
        raise NetworkPreparationFailure("Windows bridge inventory blocked: " + ", ".join(windows_state["blockers"]))
    linux_ready = not actions
    if windows_state and windows_state.get("action"):
        kind = windows_state["action"]
        action = NetworkAction("windows:" + kind, "windows", f"Existing Windows bridge owner: {kind}, selected distro and observed address.", 180)
        self._payloads[action.id] = windows_state
        actions.append(action)
    fingerprint = digest((base, observations, firewall, windows_state))
    return NetworkSnapshot(fingerprint, digest(base), tuple(actions), linux_ready=linux_ready,
                           bridge_ready=bool(windows_state and windows_state["bridge_ready"]), is_wsl=self.windows is not None)
