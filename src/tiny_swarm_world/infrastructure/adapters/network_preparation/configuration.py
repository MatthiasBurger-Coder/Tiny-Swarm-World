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
    names = tuple(sorted({"tsw.local", *(route.hostname for route in ingress.routes)}))
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
        if endpoint.rsplit(":", 1)[0] != exposure:
            raise NetworkPreparationFailure("Canonical-port listener address differs from its exposure contract.")
        owned = any(device.get("type") == "proxy" and device.get("listen") == f"tcp:{exposure}:{port}"
                    and device.get("connect") == f"tcp:127.0.0.1:{port}" for device in devices)
        pids = set(re.findall(r"pid=(\d+)", line))
        if not owned or len(pids) != 1:
            raise NetworkPreparationFailure("Foreign or unknown canonical-port listener; preserve its process.")
        provenance.append(await trusted_process.verify(int(next(iter(pids)))))
    return tuple(provenance)
