"""Preserve disjoint Docker NAT; block competing NAT and reserved-port DNAT."""
from ipaddress import ip_address, ip_network

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import parse_rules


def verify(saved, bridges, ports) -> None:
    networks = tuple(ip_network(bridge.subnet) for bridge in bridges)
    parsed = parse_rules(saved)
    for chain, rules in parsed.items():
        if not chain.startswith("nat:"):
            continue
        for rule in rules:
            if "-g" in rule or "-j" not in rule:
                raise NetworkPreparationFailure("Unknown NAT traversal; preserve its owner.")
            target = rule[rule.index("-j") + 1]
            if target in {"ACCEPT", "RETURN"}:
                continue
            if target == "DOCKER" and "nat:DOCKER" in parsed:
                canonical = {"nat:PREROUTING": ("-m", "addrtype", "--dst-type", "LOCAL", "-j", "DOCKER"),
                             "nat:OUTPUT": ("!", "-d", "127.0.0.0/8", "-m", "addrtype", "--dst-type", "LOCAL", "-j", "DOCKER")}
                if rule == canonical.get(chain):
                    continue
                raise NetworkPreparationFailure("Noncanonical Docker NAT traversal may capture managed egress.")
            if target == "MASQUERADE":
                verify_masquerade(chain, rule, networks)
            elif target == "DNAT" and chain == "nat:DOCKER":
                verify_dnat(rule, networks, ports)
            else:
                raise NetworkPreparationFailure("Unknown or competing NAT owner; no TSW NAT mutation is allowed.")


def verify_masquerade(chain, rule, networks):
    if "-s" not in rule:
        raise NetworkPreparationFailure("Broad existing masquerade intersects managed bridge scope.")
    index = rule.index("-s")
    if index and rule[index - 1] == "!":
        raise NetworkPreparationFailure("Negated existing NAT source is ambiguous.")
    expected = ("-s", rule[index + 1], "!", "-o", rule[rule.index("-o") + 1], "-j", "MASQUERADE") if "-o" in rule else ()
    if rule != expected:
        raise NetworkPreparationFailure("Noncanonical Docker masquerade predicates have unknown ownership.")
    source = ip_network(rule[index + 1], strict=False)
    if any(source.overlaps(network) for network in networks):
        raise NetworkPreparationFailure("Competing existing NAT intersects managed bridge subnet.")
    if "-o" not in rule or not rule[rule.index("-o") + 1].startswith(("docker", "br-")):
        raise NetworkPreparationFailure("Existing masquerade cannot be assigned to disjoint Docker bridge ownership.")
    if chain != "nat:POSTROUTING" and chain != "nat:DOCKER":
        raise NetworkPreparationFailure("Unknown NAT chain owner.")


def verify_dnat(rule, networks, ports):
    if "--dport" not in rule or "--to-destination" not in rule:
        raise NetworkPreparationFailure("Docker DNAT publication is incomplete.")
    port = rule[rule.index("--dport") + 1]
    if not port.isdigit() or int(port) in ports:
        raise NetworkPreparationFailure("Existing Docker DNAT occupies a canonical host port; preserve it.")
    address = rule[rule.index("--to-destination") + 1].split(":", 1)[0]
    target = ip_address(address)
    if any(target in network for network in networks):
        raise NetworkPreparationFailure("Docker DNAT targets a managed Incus subnet; ownership conflicts.")
