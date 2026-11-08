"""Canonical Incus resource, ingress, proxy and port policy resolution."""
from __future__ import annotations

import re
from ipaddress import ip_interface
from pathlib import Path
from typing import Any

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.domain.ingress.desired_state import desired_https_ingress_for_profile
from tiny_swarm_world.infrastructure.adapters.incus_preparation.configuration import load_requirements
from tiny_swarm_world.infrastructure.adapters.incus_preparation.resources import occupied_subnets, verify_bridge
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import PortRegistryYamlRepository
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import Bridge
from tiny_swarm_world.infrastructure.composition_configuration import _lxc_proxy_listen_address
from tiny_swarm_world.infrastructure.adapters.network_preparation import trusted_process


def resolve_bridges(path: Path, networks: list[dict[str, Any]], routes: list[dict[str, Any]],
                    links: list[dict[str, Any]]) -> tuple[Bridge, ...]:
    requirements = load_requirements(path)
    defaults = [route for route in routes if route.get("dst") == "default" and route.get("type", "unicast") == "unicast"]
    if len(defaults) != 1 or not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", defaults[0].get("dev", "")):
        raise NetworkPreparationFailure("Unique default IPv4 egress required; resolve VPN/routing ambiguity.")
    egress = defaults[0]["dev"]
    occupied = occupied_subnets(networks, routes, links)
    output: list[Bridge] = []
    for name in requirements.networks:
        matches = [item for item in networks if item.get("name") == name]
        if len(matches) != 1 or not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", name):
            raise NetworkPreparationFailure("Resolved Incus bridge unavailable; rerun Incus preparation.")
        item = matches[0]
        verify_bridge(item, occupied)
        if item["config"].get("ipv6.address") != "none":
            raise NetworkPreparationFailure("Initial network preparation requires IPv6-disabled bridges; preserve IPv6 policy.")
        address = ip_interface(item["config"]["ipv4.address"])
        output.append(Bridge(name, str(address.network), str(address.ip), egress))
    return tuple(output)


def local_names(path: Path, profile: str) -> tuple[tuple[str, ...], tuple[int, ...], str]:
    registry = PortRegistryYamlRepository(path=path).load()
    exposure = _lxc_proxy_listen_address()
    if exposure not in {"127.0.0.1", "0.0.0.0"}:
        raise NetworkPreparationFailure("Canonical proxy exposure cannot support loopback names.")
    ingress = desired_https_ingress_for_profile(profile, port_registry=registry)
    names = tuple(sorted({"tsw.local", *(route.hostname for route in ingress.routes),
                           *(item.route_host for item in registry.preflight_ports if item.route_host)}))
    return names, tuple(item.external_port for item in registry.preflight_ports if item.external_port is not None), exposure


async def verify_listeners(output: str, ports: tuple[int, ...], instances: list[dict[str, Any]],
                     exposure: str) -> tuple[tuple[object, ...], ...]:
    provenance = []
    devices = [device for item in instances if item.get("name") == "swarm-manager"
               for device in item.get("expanded_devices", item.get("devices", {})).values()]
    for line in output.splitlines():
        fields = line.split()
        if len(fields) < 4:
            raise NetworkPreparationFailure("Listener ownership inventory is incomplete.")
        endpoint = fields[3]
        try:
            port = int(endpoint.rsplit(":", 1)[1])
        except (ValueError, IndexError):
            raise NetworkPreparationFailure("Listener endpoint cannot be classified.") from None
        if port not in ports:
            continue
        if not _listener_address_matches(endpoint.rsplit(":", 1)[0], exposure, fields):
            raise NetworkPreparationFailure("Canonical-port listener address differs from its exposure contract.")
        matching = [device for device in devices if device.get("type") == "proxy"
                    and device.get("listen") == f"tcp:{exposure}:{port}"]
        owned = len(matching) == 1 and matching[0].get("connect") == f"tcp:127.0.0.1:{port}"
        pids = set(re.findall(r"pid=(\d+)", line))
        if not owned or len(pids) != 1:
            raise NetworkPreparationFailure("Foreign or unknown canonical-port listener; preserve its process.")
        provenance.append(await trusted_process.verify(int(next(iter(pids))), matching[0]))
    return tuple(provenance)


def _listener_address_matches(address: str, exposure: str, fields: list[str]) -> bool:
    if address == exposure:
        return True
    # ss -e reports the kernel's per-socket flag; retain the raw family evidence.
    flags = [field for field in fields if field.startswith("v6only:")]
    return address == "*" and exposure == "0.0.0.0" and flags == ["v6only:0"]


def managed_bridge_owners(networks: list[dict[str, Any]], links: list[dict[str, Any]],
                          egress: str) -> tuple[Bridge, ...]:
    """Observe Incus ownership separately from the bridges TSW may configure."""
    import re
    from ipaddress import IPv4Interface, ip_interface, ip_network

    if (not isinstance(networks, list) or not isinstance(links, list)
            or not isinstance(egress, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", egress)):
        raise NetworkPreparationFailure("Complete Incus bridge owner and kernel inventory required.")
    owners: list[Bridge] = []
    names: set[str] = set()
    for item in networks:
        if not isinstance(item, dict) or type(item.get("managed")) is not bool:
            raise NetworkPreparationFailure("Incus managed-network identity is unknown.")
        name = item.get("name")
        if not isinstance(name, str) or name in names:
            raise NetworkPreparationFailure("Duplicate or unreadable Incus network identity.")
        names.add(name)
        if not item["managed"] or item.get("type") != "bridge":
            continue
        config = item.get("config")
        if (not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", name) or name == egress
                or item.get("project") != "default" or item.get("status") != "Created"
                or not isinstance(config, dict)
                or any(not isinstance(key, str) or not isinstance(value, str) for key, value in config.items())
                or config.get("ipv6.address") != "none" or config.get("ipv4.nat") != "true"
                or config.get("ipv4.firewall", "true") != "true"
                or config.get("ipv4.dhcp", "true") not in {"true", "false"}
                or any(config.get(key) for key in ("bridge.external_interfaces", "security.acls", "ipv4.nat.address"))):
            raise NetworkPreparationFailure("Existing managed bridge owner has unsupported firewall scope; preserve it.")
        try:
            address = ip_interface(config.get("ipv4.address", ""))
        except ValueError:
            raise NetworkPreparationFailure("Existing managed bridge has no fixed IPv4 authority.") from None
        if (not isinstance(address, IPv4Interface) or not address.network.is_private
                or address.ip in {address.network.network_address, address.network.broadcast_address}):
            raise NetworkPreparationFailure("Existing managed bridge has an unsupported IPv4 scope.")
        matching = [link for link in links if isinstance(link, dict) and link.get("ifname") == name]
        if (len(matching) != 1 or not isinstance(matching[0].get("linkinfo"), dict)
                or matching[0]["linkinfo"].get("info_kind") != "bridge"):
            raise NetworkPreparationFailure("Incus owner has no unique matching kernel bridge.")
        observed = matching[0].get("addr_info")
        if not isinstance(observed, list) or any(not isinstance(value, dict) for value in observed):
            raise NetworkPreparationFailure("Managed bridge kernel address inventory is incomplete.")
        ipv4 = [value for value in observed if value.get("family") == "inet"]
        ipv6 = [value for value in observed if value.get("family") == "inet6" and value.get("scope") != "link"]
        if (len(ipv4) != 1 or ipv6 or ipv4[0].get("local") != str(address.ip)
                or type(ipv4[0].get("prefixlen")) is not int or ipv4[0]["prefixlen"] != address.network.prefixlen):
            raise NetworkPreparationFailure("Managed bridge API and kernel address authority differ.")
        if any(address.network.overlaps(ip_network(owner.subnet))
               for owner in owners):
            raise NetworkPreparationFailure("Managed Incus bridge owner subnets overlap.")
        owners.append(Bridge(name=name, subnet=str(address.network), gateway=str(address.ip), egress=egress))
    if not owners:
        raise NetworkPreparationFailure("No authoritative managed Incus bridge owners observed.")
    return tuple(sorted(owners, key=lambda owner: owner.name))


def incus_owner_identity(output: str) -> tuple[str, ...]:
    """Require a stable already-active local daemon around owner observations."""
    import re

    pairs = [line.split("=", 1) for line in output.splitlines()]
    if any(len(pair) != 2 for pair in pairs):
        raise NetworkPreparationFailure("Incus owner service identity is incomplete.")
    values = dict(pairs)
    if (len(values) != len(pairs) or set(values) != {"LoadState", "ActiveState", "UnitFileState", "MainPID"}
            or values["LoadState"] != "loaded" or values["ActiveState"] != "active"
            or values["UnitFileState"] in {"masked", "masked-runtime", "not-found", ""}
            or not re.fullmatch(r"[1-9][0-9]{0,18}", values["MainPID"])):
        raise NetworkPreparationFailure("Incus owner must already be active with a stable process identity.")
    return tuple(values[key] for key in ("LoadState", "ActiveState", "UnitFileState", "MainPID"))
