"""Recognize the canonical Incus bridge-set bypass and outbound NAT pair."""
from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure

from ipaddress import ip_network


def bypass(rule, bridge) -> bool:
    if rule.get("chain") != "pstrt." + bridge.name or rule.get("table") != "incus":
        return False
    subnet = ip_network(bridge.subnet)
    source = {"match": {"op": "==", "left": {"payload": {"protocol": "ip", "field": "saddr"}},
                         "right": {"prefix": {"addr": str(subnet.network_address), "len": subnet.prefixlen}}}}
    expressions = [item for item in rule.get("expr", ()) if "counter" not in item]
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
    return (set(elements) == {bridge.name for bridge in bridges}
            and all(bridge.egress not in elements for bridge in bridges))


def verify_filter(rule, bridges):
    allowed = {prefix + bridge.name for bridge in bridges for prefix in ("in.", "out.", "fwd.")}
    chain = rule.get("chain")
    if chain not in allowed:
        raise NetworkPreparationFailure("Unknown native Incus filter chain owner.")
    for expression in rule.get("expr", []):
        if len(expression) == 1 and set(expression) <= {"match", "counter", "accept"}:
            continue
        checksum = {"mangle": {"key": {"payload": {"protocol": "udp", "field": "checksum"}}, "value": 0}}
        if chain.startswith(("in.", "out.")) and expression == checksum:
            continue
        raise NetworkPreparationFailure("Unknown native Incus control/mutation statement.")
