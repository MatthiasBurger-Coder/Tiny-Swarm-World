"""Stable foreign state excludes only the exact declared preparation effects."""
from __future__ import annotations

import hashlib
import re
import shlex
from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import equivalent, parse_rules
from tiny_swarm_world.infrastructure.adapters.network_preparation import files


def firewall_foreign(firewall):
    desired = firewall["desired_rules"]
    rules = parse_rules(firewall["saved"])
    foreign = {}
    for chain, observed in rules.items():
        expected_chain = "FORWARD" if chain == "ufw-user-forward" else "INPUT" if chain == "ufw-user-input" else chain
        candidates = [rule for target, rule in desired if target == expected_chain]
        kept = [rule for rule in observed if not owned_rule(rule, candidates, firewall)]
        if kept:
            foreign[chain] = kept
    policies = [re.sub(r"\[\d+:\d+\]$", "[counter]", line) for line in firewall["saved"].splitlines() if line.startswith(("*", ":", "COMMIT"))]
    # Compatibility rules are represented completely by iptables-save above;
    # native Incus rules cannot change as a permitted TSW forwarding effect.
    native = [entry for entry in firewall["nft"]["nftables"]
              if any(isinstance(value, dict) and value.get("family") == "inet" for value in entry.values())]
    return foreign, policies, native


def owned_rule(rule, candidates, firewall):
    for desired in candidates:
        tag = desired[desired.index("--comment") + 1]
        tagged = "--comment" in rule and rule[rule.index("--comment") + 1] == tag
        added = [tuple(shlex.split(line)) for line in firewall["added"].splitlines() if line.startswith("ufw ")]
        ufw_tagged = firewall["ufw"] and any(command[-2:] == ("comment", tag) and command in firewall["ufw_desired"] for command in added)
        if (tagged or ufw_tagged) and equivalent(desired, rule, ufw=firewall["ufw"]):
            return True
    return False


def hosts_foreign():
    observation = files.observe(Path("/etc/hosts"))
    lines = observation.content.splitlines(keepends=True)
    outside = []
    managed = False
    for line in lines:
        if line.rstrip(b"\r\n") == b"# BEGIN TINY SWARM WORLD":
            managed = True
        elif line.rstrip(b"\r\n") == b"# END TINY SWARM WORLD":
            managed = False
        elif not managed:
            outside.append(line)
    # Only a missing final line terminator can be added before the new block.
    data = b"".join(outside)
    if data and not data.endswith((b"\r", b"\n")):
        data += b"\r\n" if b"\r\n" in observation.content else b"\n"
    return hashlib.sha256(data).hexdigest(), observation.uid, observation.gid, observation.mode
