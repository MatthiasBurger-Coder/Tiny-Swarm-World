"""Recognize the observed IPv4 Tailscale compatibility rules without changing them."""
from __future__ import annotations

from ipaddress import ip_network
import shlex

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import parse_rules


def verify_tailscale(rules, bridges) -> bool:
    chains = {
        "ts-input": "INPUT",
        "ts-forward": "FORWARD",
        "nat:ts-postrouting": "nat:POSTROUTING",
    }
    if not any(chain in rules for chain in chains):
        return False
    carrier_range = ip_network("100.64.0.0/10")
    if not bridges or any(
        "tailscale0" in {bridge.name, bridge.egress} or carrier_range.overlaps(ip_network(bridge.subnet))
        for bridge in bridges
    ):
        raise NetworkPreparationFailure("Tailscale overlaps a managed bridge or its egress.")
    _verify_tailscale_traversal(rules, chains)
    if not _tailscale_rules_match(rules, carrier_range):
        raise NetworkPreparationFailure("Unrecognized Tailscale filter or NAT expressions; preserve its owner.")
    return True


def _verify_tailscale_traversal(rules, chains) -> None:
    parents = {chain.split(":")[-1]: parent for chain, parent in chains.items()}
    jumps: dict[str, list[tuple[str, tuple[str, ...]]]] = {target: [] for target in parents}
    masks = ("--nfmask", "0xff0000", "--ctmask", "0xff0000")
    # Restore applies only to established ingress. Save applies only to new
    # host output, never to the first forwarded packet from an Incus node.
    connmark = {
        "mangle:PREROUTING": ("-m", "conntrack", "--ctstate", "RELATED,ESTABLISHED",
                              "-m", "connmark", "!", "--mark", "0x0/0xff0000",
                              "-j", "CONNMARK", "--restore-mark", *masks),
        "mangle:OUTPUT": ("-m", "conntrack", "--ctstate", "NEW",
                          "-m", "mark", "!", "--mark", "0x0/0xff0000",
                          "-j", "CONNMARK", "--save-mark", *masks),
    }
    observed_connmark = {}
    for chain, entries in rules.items():
        for rule in entries:
            if chain != "ts-forward" and {"MARK", "CONNMARK", "HMARK"} & set(rule):
                if rule != connmark.get(chain) or chain in observed_connmark:
                    raise NetworkPreparationFailure("Competing packet mark writer prevents Tailscale ownership proof.")
                observed_connmark[chain] = rule
            for flag in ("-j", "-g"):
                if flag in rule:
                    target = rule[rule.index(flag) + 1]
                    if target in jumps:
                        jumps[target].append((chain, rule))
    if any(jumps[target] != [(parent, ("-j", target))] for target, parent in parents.items()):
        raise NetworkPreparationFailure("Unrecognized Tailscale traversal; preserve its owner.")
    if observed_connmark and observed_connmark != connmark:
        raise NetworkPreparationFailure("Incomplete Tailscale connection-mark path.")


def _tailscale_rules_match(rules, carrier_range) -> bool:
    mark = ("-m", "mark", "--mark", "0x40000/0xff0000")
    source = str(carrier_range)
    forward = [
        ("-i", "tailscale0", "-j", "MARK", "--set-xmark", "0x40000/0xff0000"),
        (*mark, "-j", "ACCEPT"),
        ("-s", source, "-o", "tailscale0", "-j", "DROP"),
        ("-o", "tailscale0", "-j", "ACCEPT"),
    ]
    inputs = rules.get("ts-input", ())
    if len(inputs) != 5:
        return False
    loopback = inputs[0]
    if len(loopback) != 6 or loopback != ("-s", loopback[1], "-i", "lo", "-j", "ACCEPT"):
        return False
    try:
        address = ip_network(loopback[1])
    except ValueError:
        return False
    return (
        address.version == 4 and address.prefixlen == 32 and address.subnet_of(carrier_range)
        and inputs[1:] == [
            ("-i", "tailscale0", "-j", "ACCEPT"),
            ("-p", "udp", "-m", "udp", "--dport", "41641", "-j", "ACCEPT"),
            ("-s", "100.115.92.0/23", "!", "-i", "tailscale0", "-j", "RETURN"),
            ("-s", source, "!", "-i", "tailscale0", "-j", "DROP"),
        ]
        and rules.get("ts-forward") == forward
        and rules.get("nat:ts-postrouting") == [(*mark, "-j", "MASQUERADE")]
    )


def compatibility_projection(saved, bridges) -> str:
    """Exclude exactly proven foreign rules from an admission-only copy."""
    rules = parse_rules(saved)
    allowed = {("raw:PREROUTING", rule) for rule in rules.get("raw:PREROUTING", ())
               if _disjoint_docker_raw_deny(rule, rules, bridges)}
    if verify_tailscale(rules, bridges):
        allowed.update((
            ("INPUT", ("-j", "ts-input")),
            ("FORWARD", ("-j", "ts-forward")),
            ("nat:POSTROUTING", ("-j", "ts-postrouting")),
        ))
        for chain in ("ts-input", "ts-forward", "nat:ts-postrouting"):
            allowed.update((chain, rule) for rule in rules[chain])
    if not allowed:
        return saved
    table = ""
    retained = []
    for line in saved.splitlines(keepends=True):
        if line.startswith("*"):
            table = line.strip()[1:]
        if line.startswith("-A "):
            tokens = shlex.split(line)
            chain = tokens[1] if table == "filter" else f"{table}:{tokens[1]}"
            if (chain, tuple(tokens[2:])) in allowed:
                continue
        retained.append(line)
    return "".join(retained)


def _disjoint_docker_raw_deny(rule, rules, bridges) -> bool:
    import re

    if len(rule) != 7 or not bridges:
        return False
    destination, interface = rule[1], rule[4]
    if (rule != ("-d", destination, "!", "-i", interface, "-j", "DROP")
            or re.fullmatch(r"docker0|br-[0-9a-f]{12}", interface) is None):
        return False
    network = ip_network(destination)
    if network.version != 4 or network.prefixlen != 32 or any(
        network.overlaps(ip_network(bridge.subnet)) or interface in {bridge.name, bridge.egress}
        for bridge in bridges
    ):
        return False
    prefix = ("-d", destination, "!", "-i", interface, "-o", interface)
    return (("-o", interface, "-j", "DOCKER") in rules.get("DOCKER-BRIDGE", ())
            and any(_docker_host_publication(item, prefix) for item in rules.get("DOCKER", ())))


def _docker_host_publication(rule, prefix) -> bool:
    if rule[:len(prefix)] != prefix:
        return False
    tail = rule[len(prefix):]
    if len(tail) != 8:
        return False
    protocol, port = tail[1], tail[5]
    return (tail == ("-p", protocol, "-m", protocol, "--dport", port, "-j", "ACCEPT")
            and protocol in {"tcp", "udp"} and port.isascii() and port.isdecimal() and 1 <= int(port) <= 65535)
