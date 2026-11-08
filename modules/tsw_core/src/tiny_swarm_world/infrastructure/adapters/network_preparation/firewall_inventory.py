"""Fail closed on incomplete, mixed or unknown firewall ownership."""
from __future__ import annotations

import json
from ipaddress import ip_network
from typing import Any
from pathlib import Path

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.network_preparation import runtime
from tiny_swarm_world.infrastructure.adapters.network_preparation.nat_policy import bypass, bridge_set, legacy_nat, verify_filter, checked_expressions, validate_bridge_scope
from tiny_swarm_world.infrastructure.adapters.network_preparation import nat_conflicts
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import (
    Bridge, equivalent, exact_present, forwarding_rules, input_rules, parse_rules, verify_no_foreign_denies,
)


async def inventory(bridges: tuple[Bridge, ...], ports: tuple[int, ...] = (), *, owners: tuple[Bridge, ...] | None = None) -> dict[str, Any]:
    version = await runtime.command(("iptables", "--version"))
    if "nf_tables" not in version:
        raise NetworkPreparationFailure("iptables-nft backend required; preserve the current firewall owner.")
    managed_owners = owners
    owner_status = await runtime.command(("systemctl", "show", "firewalld.service", "nftables.service",
                                   "--property=Id", "--property=ActiveState", "--property=UnitFileState"))
    if "ActiveState=active" in owner_status or "UnitFileState=enabled" in owner_status:
        raise NetworkPreparationFailure("Custom nftables/firewalld owner is unsupported; preserve it.")
    status = await ufw_status()
    if not status.startswith(("Status: active", "Status: inactive", "Status: absent")):
        raise NetworkPreparationFailure("UFW ownership is unreadable.")
    ufw = status.startswith("Status: active")
    saved = await runtime.privileged(("iptables-save",))
    if not saved.strip():
        # A fresh nft backend has no compatibility tables to dump. Request the
        # kernel's filter view explicitly; never invent policies or hide a
        # partial, nonempty dump. Full nft ownership is still verified below.
        saved = await runtime.privileged(("iptables-save", "-t", "filter"))
    rules = parse_rules(saved)
    nat_conflicts.verify(saved, bridges, ports)
    if status.startswith("Status: absent") and any(chain.startswith("ufw-") for chain in rules):
        raise NetworkPreparationFailure("Residual UFW rules without its executable; preserve that owner.")
    verify_no_foreign_denies(rules, ufw=ufw)
    nft = await runtime.json_command(("nft", "-j", "list", "ruleset"), privileged_read=True)
    verify_nft(nft, bridges, owners=managed_owners)
    verify_compatibility(nft, saved)
    if ":OUTPUT ACCEPT " not in saved and (not ufw or "allow (outgoing)" not in status):
        raise NetworkPreparationFailure("Restrictive/unknown OUTPUT prevents DHCP replies; consult firewall owner.")
    added = await runtime.privileged(("ufw", "show", "added")) if ufw else ""
    missing = missing_rules(bridges, rules, input_restricted=ufw or ":INPUT ACCEPT " not in saved, ufw=ufw)
    return {"ufw": ufw, "status": status, "saved": "\n".join(line for line in saved.splitlines() if not line.startswith("#")), "nft": stable_nft(nft), "missing": missing,
            "owners": owner_status, "managed_bridge_owners": managed_owners, "added": added, "input_restricted": ufw or ":INPUT ACCEPT " not in saved}


async def ufw_status() -> str:
    if Path("/usr/sbin/ufw").is_file():
        return await runtime.privileged(("ufw", "status", "verbose"))
    if Path("/etc/ufw").exists() or Path("/lib/ufw").exists():
        raise NetworkPreparationFailure("UFW executable is missing but configuration remains; preserve its owner.")
    service = await runtime.command(("systemctl", "show", "ufw.service", "--property=ActiveState", "--property=UnitFileState"))
    if "ActiveState=active" in service or "UnitFileState=enabled" in service:
        raise NetworkPreparationFailure("Residual UFW service owner is active or enabled.")
    return "Status: absent"


def stable_nft(value):
    if isinstance(value, dict):
        return {key: ({counter_key: counter_value for counter_key, counter_value in item.items()
                       if counter_key not in {"packets", "bytes"}} if key == "counter" and isinstance(item, dict)
                      else stable_nft(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [stable_nft(item) for item in value]
    return value


def verify_compatibility(nft, saved):
    represented = {chain: len(rules) for chain, rules in parse_rules(saved).items()}
    observed = {}
    for entry in nft["nftables"]:
        rule = entry.get("rule", {})
        if rule.get("family") != "ip":
            continue
        chain = rule["chain"] if rule["table"] == "filter" else rule["table"] + ":" + rule["chain"]
        observed[chain] = observed.get(chain, 0) + 1
    if represented != observed:
        raise NetworkPreparationFailure("Native compatibility rules do not match complete iptables ownership inventory.")


def missing_rules(bridges: tuple[Bridge, ...], rules: dict[str, list[tuple[str, ...]]],
                  *, input_restricted: bool, ufw: bool = False) -> tuple[tuple[str, tuple[str, ...]], ...]:
    missing: list[tuple[str, tuple[str, ...]]] = []
    for bridge in bridges:
        for chain, candidates in (("FORWARD", forwarding_rules(bridge)),
                                   ("INPUT", input_rules(bridge) if input_restricted else ())):
            observed = rules.get(chain, [])
            if chain == "FORWARD":
                observed = observed + rules.get("ufw-user-forward", [])
            else:
                observed = observed + rules.get("ufw-user-input", [])
            for rule in candidates:
                if ufw and rule[rule.index("--comment") + 1].endswith(":return"):
                    continue
                found = exact_present(rule, observed)
                if not found and ufw:
                    found = any(equivalent(rule, item, ufw=True) for item in observed)
                if not found:
                    missing.append((chain, rule))
    return tuple(missing)


def verify_nft(value: Any, bridges: tuple[Bridge, ...], *, owners: tuple[Bridge, ...] | None = None) -> None:
    if not isinstance(value, dict) or not isinstance(value.get("nftables"), list):
        raise NetworkPreparationFailure("Complete nft ruleset is required.")
    explicit_owners = owners is not None
    managed = bridges if owners is None else owners
    validate_bridge_scope(bridges, managed)
    recognized = {("ip", "filter"), ("ip", "nat"), ("ip", "mangle"), ("ip", "raw"),
                  ("ip6", "filter"), ("ip6", "nat"), ("ip6", "mangle"), ("ip6", "raw"), ("inet", "incus")}
    nat: list[dict[str, Any]] = []
    nat_chains = set()
    incus_chains = set()
    for entry in value["nftables"]:
        if not isinstance(entry, dict):
            raise NetworkPreparationFailure("Unreadable nft rule entry.")
        chain = entry.get("chain", {})
        if "hook" in chain or chain.get("table") == "incus":
            verify_chain(chain, recognized, managed)
            if chain.get("table") == "incus":
                if chain["name"] in incus_chains:
                    raise NetworkPreparationFailure("Duplicate native Incus chain definition.")
                incus_chains.add(chain["name"])
            if chain.get("table") == "incus" and chain.get("hook") == "postrouting":
                nat_chains.add(chain.get("name"))
        rule = entry.get("rule", {})
        if rule.get("table") == "incus":
            allowed_chains = {prefix + bridge.name for bridge in managed for prefix in ("in.", "out.", "fwd.", "pstrt.")}
            if rule.get("family") != "inet" or rule.get("chain") not in allowed_chains:
                raise NetworkPreparationFailure("Native Incus rule has no authoritative bridge owner.")
            text = json.dumps(rule, sort_keys=True)
            if '"drop"' in text or '"reject"' in text or "acl." in rule.get("chain", ""):
                raise NetworkPreparationFailure("Incus ACL/deny effectiveness cannot be proven.")
            if not rule.get("chain", "").startswith("pstrt."):
                verify_filter(rule, managed)
            nat.append(rule)
    expected_chains = {prefix + bridge.name for bridge in managed for prefix in ("in.", "out.", "fwd.", "pstrt.")}
    if incus_chains != expected_chains:
        raise NetworkPreparationFailure("Incomplete native Incus bridge chain ownership.")
    native_sets = [entry["set"] for entry in value["nftables"] if "set" in entry and entry["set"].get("table") == "incus"]
    if native_sets and not bridge_set(value["nftables"], managed):
        raise NetworkPreparationFailure("Native Incus bridge set differs from complete owner scope.")
    for entry in value["nftables"]:
        item = entry.get("set", {})
        if item.get("table") == "incus" and (item.get("family") != "inet" or item.get("name") != "bridges"):
            raise NetworkPreparationFailure("Unknown native Incus set owner.")
    for bridge in managed:
        scoped = [rule for rule in nat if rule.get("chain") == "pstrt." + bridge.name]
        paired = (bridge_set(value["nftables"], managed) and len(scoped) == 2
                  and bypass(scoped[0], bridge) and managed_nat(scoped[1], bridge))
        # Existing Incus 6.0 rules may NAT between bridges. Recognize that
        # preserved behavior only with explicit complete owner proof; TSW adds no NAT.
        legacy = (explicit_owners or len(bridges) == 1) and len(scoped) == 1 and legacy_nat(scoped[0], bridge)
        if "pstrt." + bridge.name not in nat_chains or not (paired or legacy):
            raise NetworkPreparationFailure("Incus-owned effective NAT missing; inspect Incus network readiness. No TSW NAT is created.")


def verify_chain(chain, recognized, bridges) -> None:
    owner = (chain.get("family"), chain.get("table"))
    if owner not in recognized:
        raise NetworkPreparationFailure("Unrecognized native nft hook owner; preserve its rules.")
    if owner == ("inet", "incus"):
        permitted = {(prefix + bridge.name, hook, priority) for bridge in bridges
                     for prefix, hook, priority in (("in.", "input", 0), ("out.", "output", 0),
                                                    ("fwd.", "forward", 0), ("pstrt.", "postrouting", 100))}
        actual = (chain.get("name"), chain.get("hook"), chain.get("prio"))
        if type(chain.get("prio")) is not int or actual not in permitted or chain.get("policy") != "accept" or chain.get("type") != ("nat" if chain.get("hook") == "postrouting" else "filter"):
            raise NetworkPreparationFailure("Incus hook/policy/priority differs from supported owner.")
    else:
        canonical = {"INPUT": "input", "OUTPUT": "output", "FORWARD": "forward",
                     "PREROUTING": "prerouting", "POSTROUTING": "postrouting"}
        if canonical.get(chain.get("name")) != chain.get("hook"):
            raise NetworkPreparationFailure("Noncanonical compatibility-table hook.")
        priorities = {"filter": {0}, "nat": {-100, 100}, "mangle": {-150}, "raw": {-300}}
        if chain.get("prio") not in priorities[chain["table"]] or chain.get("policy") not in {"accept", "drop"}:
            raise NetworkPreparationFailure("Unrecognized compatibility hook policy/priority.")
        if chain["table"] != "filter" and chain.get("policy") != "accept":
            raise NetworkPreparationFailure("Nonfilter firewall policy may drop scoped traffic.")


def managed_nat(rule: dict[str, Any], bridge: Bridge) -> bool:
    if rule.get("family") != "inet" or rule.get("table") != "incus":
        return False
    if rule.get("chain") != "pstrt." + bridge.name:
        return False
    subnet = ip_network(bridge.subnet)
    prefix = {"prefix": {"addr": str(subnet.network_address), "len": subnet.prefixlen}}
    source = {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "saddr"}}, "right": prefix}}
    destination = {"match": {"op": "!=", "left": {"payload": {"protocol": "ip", "field": "daddr"}}, "right": prefix}}
    output = {"match": {"op": "!=", "left": {"meta": {"key": "oifname"}}, "right": bridge.name}}
    expressions = checked_expressions(rule)
    return expressions in ([source, destination, {"masquerade": None}],
                           [source, destination, output, {"masquerade": None}])
