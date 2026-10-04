"""Create-only resource policy: reject collisions instead of editing resources."""
from __future__ import annotations

import json
from ipaddress import IPv4Network, ip_interface, ip_network
from typing import Any
from ruamel.yaml import YAML
from io import StringIO
from tiny_swarm_world.application.ports.incus_preparation import IncusPreparationFailure
from tiny_swarm_world.domain.incus_preparation import IncusAction
from tiny_swarm_world.infrastructure.adapters.incus_preparation.configuration import IncusRequirements
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.policy import (
    profile_allows_project_proxy_devices, profile_output_safe, required_profile_settings,
)


def create_action(kind: str, name: str, **properties: Any) -> IncusAction:
    return IncusAction(f"create:{kind}:{name}", kind, name,
                       json.dumps({"name": name, **properties}, sort_keys=True))


def resource_actions(requirements: IncusRequirements, inventory: dict[str, Any],
                     routes: list[dict[str, Any]], links: list[dict[str, Any]]) -> tuple[IncusAction, ...]:
    actions: list[IncusAction] = []
    pool = find_resource(inventory["storage-pools"], requirements.storage)
    if pool is None:
        actions.append(create_action("storage-pools", requirements.storage, driver="dir", config={}))
    elif pool.get("driver") not in {"dir", "btrfs", "zfs", "lvm", "ceph", "linstor"} or pool.get("status") != "Created":
        raise IncusPreparationFailure("Storage name/configuration collision; preserve the pool and select a compatible resolved pool in provider_config.yaml.")
    occupied = occupied_subnets(inventory["networks"], routes, links)
    link_names = {link["ifname"] for link in links}
    for name in requirements.networks:
        network = find_resource(inventory["networks"], name)
        if network is None:
            if name in link_names:
                raise IncusPreparationFailure("Bridge name collides with a host interface; select a different resolved network in provider_config.yaml.")
            subnet = choose_subnet(occupied)
            occupied.append((name, subnet))
            actions.append(create_action("networks", name, type="bridge", config={
                "ipv4.address": f"{subnet.network_address + 1}/{subnet.prefixlen}",
                "ipv4.nat": "true", "ipv4.dhcp": "true", "ipv6.address": "none",
            }))
        else:
            verify_bridge(network, occupied)
    for profile in requirements.profiles:
        devices: dict[str, dict[str, str]] = {}
        network_name = dict(requirements.profile_networks).get(profile.name)
        if network_name:
            devices = {"root": {"type": "disk", "path": "/", "pool": requirements.storage},
                       "eth0": {"type": "nic", "name": "eth0", "network": network_name}}
        desired = create_action("profiles", profile.name, config=dict(required_profile_settings(profile)), devices=devices)
        existing = find_resource(inventory["profiles"], profile.name)
        if existing is None:
            actions.append(desired)
        elif not profile_compatible(existing, desired, profile_allows_project_proxy_devices(profile)):
            raise IncusPreparationFailure("Profile name/configuration collision; preserve it and select a compatible declared profile in provider_config.yaml.")
    return tuple(actions)


def find_resource(items: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    matching = [item for item in items if item.get("name") == name]
    if len(matching) > 1:
        raise IncusPreparationFailure("Duplicate resource identity; inspect the Incus installation.")
    return matching[0] if matching else None


def occupied_subnets(networks: list[dict[str, Any]], routes: list[dict[str, Any]],
                     links: list[dict[str, Any]]) -> list[tuple[str, IPv4Network]]:
    occupied: list[tuple[str, IPv4Network]] = []
    for network in networks:
        address = network.get("config", {}).get("ipv4.address", "none")
        if address not in {"none", "auto", ""}:
            occupied.append((network["name"], ipv4_subnet(address)))
    for route in routes:
        destination = route.get("dst")
        if destination and destination != "default":
            occupied.append((route.get("dev", ""), ipv4_subnet(destination)))
    for link in links:
        for address in link.get("addr_info", []):
            if address.get("family") == "inet":
                occupied.append((link["ifname"], ipv4_subnet(f"{address['local']}/{address['prefixlen']}")))
    return occupied


def ipv4_subnet(address: str) -> IPv4Network:
    try:
        value = ip_network(address, strict=False)
    except ValueError:
        raise IncusPreparationFailure("Unreadable network address; inspect Incus and host routes.") from None
    if not isinstance(value, IPv4Network):
        raise IncusPreparationFailure("Unexpected IPv6 address in IPv4 inventory.")
    return value


def choose_subnet(occupied: list[tuple[str, IPv4Network]]) -> IPv4Network:
    for index in range(50, 250):
        candidate = IPv4Network(f"10.231.{index}.0/24")
        if not any(candidate.overlaps(subnet) for _, subnet in occupied):
            return candidate
    raise IncusPreparationFailure("No collision-free bootstrap subnet; resolve overlapping host/VPN routes, then ./prepare_linux.sh --dry-run.")


def verify_bridge(network: dict[str, Any], occupied: list[tuple[str, IPv4Network]]) -> None:
    config = network.get("config", {})
    if (network.get("type") != "bridge" or network.get("managed") is not True
            or network.get("status") != "Created" or config.get("ipv4.address", "none") in {"none", "auto", ""}
            or config.get("ipv4.nat") != "true" or config.get("ipv4.dhcp", "true") != "true"
            or config.get("bridge.external_interfaces")):
        raise IncusPreparationFailure("Incompatible bridge configuration; preserve it and select a compatible resolved network in provider_config.yaml.")
    subnet = ipv4_subnet(config["ipv4.address"])
    address = ip_interface(config["ipv4.address"]).ip
    if not subnet.is_private or address in {subnet.network_address, subnet.broadcast_address}:
        raise IncusPreparationFailure("Bridge address is unsuitable for private container networking; review the resolved network.")
    if any(owner != network["name"] and subnet.overlaps(other) for owner, other in occupied):
        raise IncusPreparationFailure("Bridge subnet collides with host or Incus networking; review routes/resolved network without replacing it.")


def profile_compatible(existing: dict[str, Any], desired: IncusAction, allow_proxy: bool,
                       *, require_devices: bool = False) -> bool:
    payload = json.loads(desired.payload)
    output = StringIO()
    YAML(typ="safe").dump(existing, output)
    if existing.get("config", {}).get("security.privileged", "false").casefold() != "false":
        return False
    if not profile_output_safe(output.getvalue(), desired.name, allow_project_proxy_devices=allow_proxy):
        return False
    config = existing.get("config", {})
    devices = existing.get("devices", {})
    return (all(config.get(key) == value for key, value in payload["config"].items())
            and all((not require_devices and name not in devices)
                    or all(devices.get(name, {}).get(key) == value for key, value in device.items())
                    for name, device in payload["devices"].items()))
