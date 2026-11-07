"""Recognize the canonical Incus bridge-set bypass and outbound NAT pair."""
from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure

from ipaddress import ip_network



def checked_expressions(rule):
    expressions = rule.get("expr")
    if not isinstance(expressions, list):
        raise NetworkPreparationFailure("Incomplete native Incus expression inventory.")
    result = []
    for expression in expressions:
        if not isinstance(expression, dict) or len(expression) != 1:
            raise NetworkPreparationFailure("Mixed or unreadable native Incus expression.")
        if "counter" in expression:
            counter = expression["counter"]
            if (not isinstance(counter, dict) or set(counter) != {"packets", "bytes"}
                    or any(type(value) is not int or value < 0 for value in counter.values())):
                raise NetworkPreparationFailure("Unreadable native Incus counter.")
            continue
        result.append(expression)
    return result


def validate_bridge_scope(targets, owners):
    import re

    if not isinstance(owners, tuple) or not owners:
        raise NetworkPreparationFailure("Explicit managed bridge owner scope required.")
    names = set()
    networks = []
    for owner in owners:
        if (not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", owner.name) or owner.name in names
                or owner.name == owner.egress):
            raise NetworkPreparationFailure("Invalid or duplicate managed bridge owner.")
        names.add(owner.name)
        network = ip_network(owner.subnet)
        if network.version != 4 or any(network.overlaps(existing) for existing in networks):
            raise NetworkPreparationFailure("Managed bridge owner subnets overlap or are unsupported.")
        networks.append(network)
    by_name = {owner.name: owner for owner in owners}
    for target in targets:
        owner = by_name.get(target.name)
        if owner is None or any(getattr(target, field) != getattr(owner, field)
                                for field in ("name", "subnet", "gateway", "egress")):
            raise NetworkPreparationFailure("Selected TSW bridge is outside authoritative Incus owner scope.")


def bypass(rule, bridge) -> bool:
    if rule.get("chain") != "pstrt." + bridge.name or rule.get("table") != "incus":
        return False
    subnet = ip_network(bridge.subnet)
    source = {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "saddr"}},
                         "right": {"prefix": {"addr": str(subnet.network_address), "len": subnet.prefixlen}}}}
    expressions = checked_expressions(rule)
    if len(expressions) != 3 or expressions[0] != source or expressions[-1] != {"accept": None}:
        return False
    match = expressions[1].get("match", {})
    return (match.get("op") == "==" and match.get("left") == {"meta": {"key": "oifname"}}
            and match.get("right") in ("@bridges", {"set": "bridges"}))


def bridge_set(entries, bridges) -> bool:
    matching = [entry["set"] for entry in entries if "set" in entry and entry["set"].get("family") == "inet"
                and entry["set"].get("table") == "incus" and entry["set"].get("name") == "bridges"]
    if len(matching) != 1 or matching[0].get("type") != "ifname":
        return False
    elements = matching[0].get("elem", [])
    if not isinstance(elements, list) or not all(isinstance(item, str) for item in elements):
        return False
    return (len(elements) == len(set(elements)) and set(elements) == {bridge.name for bridge in bridges}
            and all(bridge.egress not in elements for bridge in bridges))


def verify_filter(rule, bridges):
    allowed = {prefix + bridge.name for bridge in bridges for prefix in ("in.", "out.", "fwd.")}
    chain = rule.get("chain")
    if chain not in allowed or rule.get("family") != "inet":
        raise NetworkPreparationFailure("Unknown native Incus filter chain owner.")
    expressions = checked_expressions(rule)
    checksum = {"mangle": {"key": {"payload": {"protocol": "udp", "field": "checksum"}}, "value": 0}}
    for expression in expressions:
        if "match" in expression:
            match = expression["match"]
            if isinstance(match, dict) and set(match) == {"op", "left", "right"} and match["op"] in {"==", "!=", "in"}:
                continue
        if expression == {"accept": None}:
            continue
        if expression == checksum and chain.startswith(("in.", "out.")):
            interface = {"match": {"op": "==", "left": {"meta": {"key": "iifname" if chain.startswith("in.") else "oifname"}},
                                   "right": chain.split(".", 1)[1]}}
            udp = {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "protocol"}}, "right": "udp"}}
            if (expressions[-1] == checksum and expressions.count(checksum) == 1
                    and interface in expressions and udp in expressions
                    and all("match" in item for item in expressions[:-1])):
                continue
        raise NetworkPreparationFailure("Unknown native Incus control/mutation statement.")


def legacy_nat(rule, bridge) -> bool:
    """Recognize an exact existing per-bridge Incus 6.0 masquerade; no isolation claim."""
    if (rule.get("family") != "inet" or rule.get("table") != "incus"
            or rule.get("chain") != "pstrt." + bridge.name):
        return False
    subnet = ip_network(bridge.subnet)
    prefix = {"prefix": {"addr": str(subnet.network_address), "len": subnet.prefixlen}}
    expected = [
        {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "saddr"}}, "right": prefix}},
        {"match": {"op": "!=", "left": {"payload": {"protocol": "ip", "field": "daddr"}}, "right": prefix}},
        {"masquerade": None},
    ]
    return checked_expressions(rule) == expected
