"""Persistence rendering for the existing TSW forwarding script and service."""
from __future__ import annotations

import shlex
from typing import Any

from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import Bridge, ufw_rules
from tiny_swarm_world.infrastructure.adapters.network_preparation import runtime
from tiny_swarm_world.infrastructure.adapters.network_preparation.persistence_guard import render_guard


def render_script(bridges: tuple[Bridge, ...], firewall: dict[str, Any]) -> bytes:
    lines = ["#!/bin/bash", "# Tiny Swarm World W06 forwarding owner v1", "set -euo pipefail",
             "export PATH=/usr/sbin:/usr/bin:/sbin:/bin",
             "deadline=$((SECONDS + 60))"]
    for bridge in bridges:
        name = shlex.quote(bridge.name)
        lines.extend((f"while ! timeout 3 ip link show dev {name} >/dev/null 2>&1; do",
                      '  if (( SECONDS >= deadline )); then exit 1; fi', "  sleep 1", "done"))
    lines.append(render_guard(bridges, firewall["ufw"], absent=firewall["status"].startswith("Status: absent"), ports=firewall.get("ports", ())))
    # No NAT, policies, flushes or broad accepts. Recheck collisions/owner in fresh
    # preparation before installing this immutable, explicitly scoped asset.
    if not firewall["ufw"]:
        for chain, rule in firewall["desired_rules"]:
            check = shlex.join(("iptables", "-w", "3", "-C", chain, *rule))
            apply = shlex.join(("iptables", "-w", "3", "-I", chain, "1", *rule))
            lines.append(f"timeout 5 {check} 2>/dev/null || timeout 5 {apply}")
    return ("\n".join(lines) + "\n").encode()


def render_service() -> bytes:
    return b"""[Unit]
Description=Tiny Swarm World scoped Incus forwarding prerequisites
After=network-online.target incus.service
Wants=network-online.target incus.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/tsw-apply-incus-forwarding.sh
TimeoutStartSec=75s
RemainAfterExit=yes
Restart=no

[Install]
WantedBy=multi-user.target
"""


async def apply_missing(bridges: tuple[Bridge, ...], firewall: dict[str, Any]) -> None:
    if firewall["ufw"]:
        missing_tags = {rule[rule.index("--comment") + 1] for _, rule in firewall["missing"]}
        for bridge in bridges:
            for args in ufw_rules(bridge):
                if args[-1] in missing_tags:
                    await runtime.privileged(("ufw", *args), 10)
    else:
        for chain, rule in reversed(firewall["missing"]):
            await runtime.privileged(("iptables", "-w", "3", "-I", chain, "1", *rule), 10)
