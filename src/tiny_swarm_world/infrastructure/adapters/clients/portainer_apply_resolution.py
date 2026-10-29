"""Visibility-limited Portainer apply resolution; no stack mutation occurs here."""

from collections.abc import Callable

import requests

from tiny_swarm_world.application.ports.clients.port_portainer_client import PortainerClientError
from tiny_swarm_world.application.ports.operation_result import OperationFailure


def resolve_apply_target(send: Callable[..., requests.Response], endpoint_name: str, stack_name: str) -> tuple[int, int | None]:
    try:
        first = _apply_snapshot(send, endpoint_name, stack_name)
        second = _apply_snapshot(send, endpoint_name, stack_name)
        if first != second:
            raise ValueError("inventory drift")
        return first[0], first[1]
    except Exception:
        raise PortainerClientError(
            OperationFailure.for_cause("service.request", "portainer", "request_failed")
        ) from None


def _apply_snapshot(
    send: Callable[..., requests.Response], endpoint_name: str, stack_name: str
) -> tuple[int, int | None, tuple[tuple[int, str, int], ...], tuple[tuple[int, str, int], ...], tuple[tuple[int, str, int, int], ...]]:
    response = send("GET", "/api/endpoints", allow_redirects=False)
    if response.status_code != 200:
        raise ValueError("endpoint inventory status")
    endpoint_payload = response.json()
    endpoints = _strict_inventory(endpoint_payload, False)
    if not isinstance(endpoint_payload, list):
        raise ValueError("inventory")
    response = send("GET", "/api/stacks", allow_redirects=False)
    if response.status_code != 200:
        raise ValueError("stack inventory status")
    stacks = _strict_inventory(response.json(), True)
    candidates = [record for record in endpoints if record[1] == endpoint_name]
    if not candidates and endpoint_name == "local":
        socket_ids = {
            record["Id"] for record in endpoint_payload
            if isinstance(record.get("URL"), str) and "docker.sock" in record["URL"].casefold()
        }
        candidates = [
            record for record in endpoints
            if record[1].casefold() in {"primary", "docker", "swarm"} or record[0] in socket_ids
        ]
    if len(candidates) != 1:
        raise ValueError("endpoint selection")
    endpoint_id = candidates[0][0]
    matches = [record for record in stacks if record[1] == stack_name]
    if len(matches) > 1 or (matches and matches[0][2] != endpoint_id):
        raise ValueError("stack conflict")
    stack_id = matches[0][0] if matches else None
    fingerprint = _endpoint_fingerprint(endpoint_payload)
    return endpoint_id, stack_id, tuple(sorted(endpoints)), tuple(sorted(stacks)), fingerprint


def _strict_inventory(payload: object, stack: bool) -> list[tuple[int, str, int]]:
    if not isinstance(payload, list):
        raise ValueError("inventory")
    result: list[tuple[int, str, int]] = []
    ids: set[int] = set()
    for record in payload:
        if not isinstance(record, dict):
            raise ValueError("record")
        identifier = record.get("Id")
        name = record.get("Name")
        endpoint = record.get("EndpointId") if stack else 0
        if (not isinstance(identifier, int) or type(identifier) is not int
                or identifier <= 0 or identifier in ids
                or not isinstance(name, str) or type(name) is not str or not name
                or not isinstance(endpoint, int) or type(endpoint) is not int
                or (stack and endpoint <= 0)):
            raise ValueError("identity")
        ids.add(identifier)
        result.append((identifier, name, endpoint))
    return result


def _endpoint_fingerprint(payload: list[dict[str, object]]) -> tuple[tuple[int, str, int, int], ...]:
    result: list[tuple[int, str, int, int]] = []
    for record in payload:
        identifier = record["Id"]
        url = record.get("URL", "")
        kind = record.get("Type", 0)
        status = record.get("Status", 0)
        if (not isinstance(identifier, int) or type(identifier) is not int
                or not isinstance(url, str) or type(url) is not str
                or not isinstance(kind, int) or type(kind) is not int
                or not isinstance(status, int) or type(status) is not int):
            raise ValueError("endpoint fingerprint")
        result.append((identifier, url, kind, status))
    return tuple(sorted(result))
