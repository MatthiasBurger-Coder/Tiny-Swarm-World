"""Reject drift beyond an approved resource creation's own observable effects."""
from __future__ import annotations

import json
from typing import Any
from tiny_swarm_world.application.ports.incus_preparation import IncusPreparationFailure
from tiny_swarm_world.domain.incus_preparation import IncusAction
from tiny_swarm_world.infrastructure.adapters.incus_preparation import runtime


def normalized(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # New profiles legitimately add references to existing pools and bridges.
    return sorted(({key: value for key, value in item.items() if key != "used_by"}
                   for item in items), key=lambda item: item["name"])


def stable_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """DHCP/SLAAC lifetimes count down without changing the approved topology."""
    return [{**link, "addr_info": [{key: value for key, value in address.items()
                                    if key not in {"valid_life_time", "preferred_life_time"}}
                                   for address in link.get("addr_info", [])]}
            for link in links]


async def preserved_inventory(before: dict[str, Any], action: IncusAction) -> dict[str, Any]:
    inventory = {kind: runtime.named_resources(await runtime.query(f"/1.0/{kind}?recursion=1&project=default"), kind)
                 for kind in ("storage-pools", "networks", "profiles", "instances")}
    for kind, items in inventory.items():
        remaining = [item for item in items if not (kind == action.kind and item.get("name") == action.name)]
        if normalized(remaining) != normalized(before["inventory"][kind]):
            raise IncusPreparationFailure("Unrelated Incus resources changed during apply; review a fresh plan before continuing.")
    server = await runtime.query("/1.0")
    if server != before["server"]:
        raise IncusPreparationFailure("Incus server configuration changed during apply; review a fresh plan.")
    routes = await runtime.json_command(("ip", "-j", "-4", "route", "show", "table", "all"))
    links = await runtime.json_command(("ip", "-j", "address", "show"))
    allowed_bridge = action.name if action.kind == "networks" else None
    old_routes = sorted(json.dumps(item, sort_keys=True) for item in before["routes"])
    current_routes = sorted(json.dumps(item, sort_keys=True) for item in routes if allowed_bridge is None or item.get("dev") != allowed_bridge)
    old_links = sorted(json.dumps(item, sort_keys=True) for item in before["links"])
    current_links = sorted(json.dumps(item, sort_keys=True) for item in stable_links(links) if allowed_bridge is None or item.get("ifname") != allowed_bridge)
    if current_routes != old_routes or current_links != old_links:
        raise IncusPreparationFailure("Host networking changed during apply; review a fresh plan.")
    return inventory
