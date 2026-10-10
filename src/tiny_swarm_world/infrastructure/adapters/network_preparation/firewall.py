"""Exact IPv4 scopes using the existing forwarding persistence owner."""
from __future__ import annotations

import shlex
from ipaddress import ip_network
from dataclasses import dataclass

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure


@dataclass(frozen=True)
class Bridge:
    name: str
    subnet: str
    gateway: str
    egress: str


def forwarding_rules(bridge: Bridge) -> tuple[tuple[str, ...], ...]:
    scope = (("internal", bridge.name, bridge.name, ("-s", bridge.subnet, "-d", bridge.subnet), "NEW,ESTABLISHED,RELATED"),
             ("egress", bridge.name, bridge.egress, ("-s", bridge.subnet), "NEW,ESTABLISHED,RELATED"),
             ("return", bridge.egress, bridge.name, ("-d", bridge.subnet), "ESTABLISHED,RELATED"))
    return tuple(("-i", incoming, "-o", outgoing, *address, "-m", "conntrack", "--ctstate", state,
                  "-m", "comment", "--comment", f"tsw:{bridge.name}:{purpose}", "-j", "ACCEPT")
                 for purpose, incoming, outgoing, address, state in scope)


def input_rules(bridge: Bridge) -> tuple[tuple[str, ...], ...]:
    dhcp = tuple(("-i", bridge.name, "-s", source, "-p", "udp", "--sport", "68", "--dport", "67",
                  "-m", "comment", "--comment", f"tsw:{bridge.name}:dhcp{index}", "-j", "ACCEPT")
                 for index, source in enumerate(("0.0.0.0/32", bridge.subnet)))
    dns = tuple(("-i", bridge.name, "-s", bridge.subnet, "-d", bridge.gateway, "-p", protocol,
                 "--dport", "53", "-m", "comment", "--comment", f"tsw:{bridge.name}:dns-{protocol}", "-j", "ACCEPT")
                for protocol in ("tcp", "udp"))
    return dhcp + dns


def ufw_rules(bridge: Bridge) -> tuple[tuple[str, ...], ...]:
    routes = (("route", "allow", "in", "on", bridge.name, "out", "on", bridge.name, "from", bridge.subnet,
               "to", bridge.subnet, "comment", f"tsw:{bridge.name}:internal"),
              ("route", "allow", "in", "on", bridge.name, "out", "on", bridge.egress, "from", bridge.subnet,
               "to", "any", "comment", f"tsw:{bridge.name}:egress"))
    inputs = tuple(("allow", "in", "on", bridge.name, "proto", "udp", "from", source, "port", "68",
                    "to", "any", "port", "67", "comment", f"tsw:{bridge.name}:dhcp{index}")
                   for index, source in enumerate(("0.0.0.0/32", bridge.subnet)))
    dns = tuple(("allow", "in", "on", bridge.name, "proto", protocol, "from", bridge.subnet,
                 "to", bridge.gateway, "port", "53", "comment", f"tsw:{bridge.name}:dns-{protocol}")
                for protocol in ("tcp", "udp"))
    return routes + inputs + dns


def parse_rules(saved: str) -> dict[str, list[tuple[str, ...]]]:
    if "*filter" not in saved or "COMMIT" not in saved or ":FORWARD " not in saved:
        raise NetworkPreparationFailure("Incomplete iptables inventory.")
    rules: dict[str, list[tuple[str, ...]]] = {}
    table = ""
    for line in saved.splitlines():
        if line.startswith("*"):
            table = line[1:]
        if line.startswith("-A "):
            tokens = shlex.split(line)
            chain = tokens[1] if table == "filter" else table + ":" + tokens[1]
            rules.setdefault(chain, []).append(tuple(tokens[2:]))
    return rules


def verify_no_foreign_denies(rules: dict[str, list[tuple[str, ...]]], *, ufw: bool) -> None:
    for chain in rules:
        if chain.startswith("nat:"):
            continue
        for rule in rules.get(chain, ()):
            if "--notrack" in rule or "NOTRACK" in rule:
                raise NetworkPreparationFailure("Conntrack disabling conflicts with scoped stateful forwarding.")
            if "-j" in rule:
                target = rule[rule.index("-j") + 1]
                known = target in {"ACCEPT", "DROP", "REJECT", "RETURN", "LOG", "NFLOG", "MARK", "CONNMARK", "CT", "TCPMSS"}
                if not known and not target.startswith(("ufw-", "DOCKER")):
                    raise NetworkPreparationFailure("Unknown firewall jump owner; preserve its chains.")
            if "-g" in rule:
                raise NetworkPreparationFailure("Unknown firewall goto ordering; preserve its owner.")
            if not any(verdict in rule for verdict in ("DROP", "REJECT")):
                continue
            if chain == "FORWARD" and rule == ("-j", "DROP") and "DOCKER-FORWARD" in rules:
                continue
            if ufw and rule == ("-m", "conntrack", "--ctstate", "INVALID", "-j", "DROP") and chain.startswith("ufw-before-"):
                continue
            if ufw and chain == "ufw-not-local" and rule == ("-j", "DROP"):
                expected = {("-m", "addrtype", "--dst-type", kind, "-j", "RETURN") for kind in ("LOCAL", "MULTICAST", "BROADCAST")}
                if len(rules[chain]) == 4 and set(rules[chain][:3]) == expected and rules[chain][-1] == rule:
                    continue
            if ufw and chain.startswith("ufw-skip-to-policy-") and rule == ("-j", "DROP"):
                continue
            raise NetworkPreparationFailure("Foreign explicit firewall deny/order conflict; preserve policy and consult its owner.")
    if ufw:
        verify_ufw_traversal(rules)


def verify_ufw_traversal(rules) -> None:
    returns = {("-m", "conntrack", "--ctstate", states, "-j", "ACCEPT") for states in ("RELATED,ESTABLISHED", "ESTABLISHED,RELATED")}
    if not any(rule in returns for rule in rules.get("ufw-before-forward", [])):
        raise NetworkPreparationFailure("UFW unrestricted established return allowance is missing.")
    for direction in ("input", "forward"):
        before_rules = rules.get("ufw-before-" + direction, [])
        user = ("-j", "ufw-user-" + direction)
        if user not in before_rules:
            raise NetworkPreparationFailure("UFW canonical user-chain ordering is unavailable.")
        earlier = before_rules[:before_rules.index(user)]
        for rule in earlier:
            if "-j" in rule:
                target = rule[rule.index("-j") + 1]
                if target == "DROP" and rule == ("-m", "conntrack", "--ctstate", "INVALID", "-j", "DROP"):
                    continue
                allowed_targets = {"ACCEPT", "LOG", "NFLOG"} | ({"ufw-not-local"} if direction == "input" else set())
                if target not in allowed_targets:
                    raise NetworkPreparationFailure("UFW nested terminal chain precedes scoped user allowances.")
        top = rules.get(direction.upper(), [])
        before_jump = ("-j", "ufw-before-" + direction)
        if before_jump not in top:
            raise NetworkPreparationFailure("UFW top-level before-chain traversal is unavailable.")
        allowed = {"ufw-before-logging-" + direction}
        for rule in top[:top.index(before_jump)]:
            if "-j" in rule and rule[rule.index("-j") + 1] not in allowed | {"ACCEPT", "LOG", "NFLOG"}:
                raise NetworkPreparationFailure("UFW terminal/default chain precedes scoped user allowances.")
        for leaf in allowed:
            for rule in rules.get(leaf, []):
                if "-j" not in rule or rule[rule.index("-j") + 1] not in {"LOG", "NFLOG", "RETURN"}:
                    raise NetworkPreparationFailure("UFW logging leaf has an unrecognized nested verdict.")


def exact_present(rule: tuple[str, ...], observed: list[tuple[str, ...]]) -> bool:
    tag = rule[rule.index("--comment") + 1]
    matching = [item for item in observed if "--comment" in item and item[item.index("--comment") + 1] == tag]
    if matching and (len(matching) != 1 or not equivalent(rule, matching[0], ufw=False)):
        raise NetworkPreparationFailure("Tagged firewall rule collision or duplicate; preserve existing rules.")
    return bool(matching)


def equivalent(rule: tuple[str, ...], observed: tuple[str, ...], *, ufw: bool) -> bool:
    def normalize(tokens: tuple[str, ...]) -> dict[str, str]:
        values: dict[str, str] = {}
        index = 0
        while index < len(tokens):
            key = tokens[index]
            if index + 1 >= len(tokens) or key == "!":
                values["unrecognized:" + str(index)] = key
                index += 1
                continue
            value = tokens[index + 1]
            if key == "-m" and value in {"udp", "tcp", "conntrack", "comment"}:
                index += 2
                continue
            if key != "--comment":
                identity = key if key not in values else key + ":duplicate:" + str(index)
                values[identity] = value
            index += 2
        if "--ctstate" in values:
            values["--ctstate"] = ",".join(sorted(values["--ctstate"].split(",")))
        for key in ("-s", "-d"):
            if key in values:
                values[key] = str(ip_network(values[key], strict=False))
        return values
    expected, actual = normalize(rule), normalize(observed)
    if ufw and "--ctstate" not in actual:
        expected.pop("--ctstate", None)
    return expected == actual
