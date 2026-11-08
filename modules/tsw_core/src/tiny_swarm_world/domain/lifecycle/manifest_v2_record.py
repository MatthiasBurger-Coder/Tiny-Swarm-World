"""Isolated unadopted v2 draft, never an admitted installation."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import json
from types import MappingProxyType

from tiny_swarm_world.domain.lifecycle.desired_manifest_v2 import ConversionStatus, plan_desired_manifest_v2
from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog, InstallationManifest
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if value is None or type(value) in {str, int, bool}:
        return value
    raise ValueError("Invalid draft.")


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


@dataclass(frozen=True, slots=True, init=False, repr=False)
class UnadoptedV2Record:
    """Detached immutable draft; never represents an admitted installation."""

    _wire: Mapping[str, object]

    def __init__(self) -> None:
        raise TypeError("Draft creation requires validated conversion.")

    def __repr__(self) -> str:
        return "<UnadoptedV2Record redacted>"

    __str__ = __repr__

    def wire(self) -> dict[str, object]:
        result = _plain(self._wire)
        if type(result) is not dict:
            raise ValueError("Invalid draft.")
        return result


def create_v2_record(manifest: object, catalog: object, *, exposure: object, listen_address: object) -> UnadoptedV2Record:
    """Recompute all desired values from strict v1 and catalog inputs."""
    try:
        if type(manifest) is not InstallationManifest or type(catalog) is not ComponentCatalog:
            raise ValueError
        plan = plan_desired_manifest_v2(manifest, catalog, exposure=exposure, listen_address=listen_address)
        if plan.status is not ConversionStatus.DESIRED or plan.desired is None:
            raise ValueError
        desired = plan.desired
        if type(listen_address) is not str or type(exposure) is not SwaggerMode:
            raise ValueError
        wire = {
            "schema_version": 2, "record_state": "UNADOPTED",
            "v1": _plain(desired.v1_snapshot),
            "desired": {
                "project": desired.desired_project, "profile_name": desired.desired_profile_name,
                "policy_version": "scoped-route-policy-v2", "profile_algorithm": "profile-name-v1",
                "listen_address": listen_address,
                "routes": [asdict(route) for route in desired.desired_routes],
                "stack_policies": [{"service_id": service, "owner": owner}
                                   for service, owner in desired.stack_policies],
                "swagger_exposure": desired.swagger_exposure.value,
            },
            "provenance": {
                "runtime_source": "UNKNOWN", "host": "UNKNOWN", "project": "UNKNOWN",
                "profile": "UNKNOWN", "routes": "UNKNOWN", "owner": "UNKNOWN",
                "applied": False, "qualified": False,
            },
        }
        frozen = _freeze(wire)
        if not isinstance(frozen, Mapping):
            raise ValueError
        record = object.__new__(UnadoptedV2Record)
        object.__setattr__(record, "_wire", frozen)
        return record
    except Exception:
        raise ValueError("Invalid draft.") from None


def encode_v2_record(record: object) -> bytes:
    try:
        if type(record) is not UnadoptedV2Record:
            raise ValueError
        return (json.dumps(record.wire(), ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    except Exception:
        raise ValueError("Invalid draft.") from None


def validate_v2_wire(payload: object, catalog: object, *, exposure: object, listen_address: object) -> UnadoptedV2Record:
    """Recompute the whole draft and compare strict canonical JSON semantics."""
    try:
        if type(payload) is not dict or type(payload.get("schema_version")) is not int or payload["schema_version"] != 2:
            raise ValueError
        v1 = payload["v1"]
        if type(v1) is not dict or type(v1.get("schema_version")) is not int or v1["schema_version"] != 1:
            raise ValueError
        manifest = InstallationManifest.model_validate_json(json.dumps(v1, allow_nan=False))
        record = create_v2_record(manifest, catalog, exposure=exposure, listen_address=listen_address)
        actual = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
        expected = json.dumps(record.wire(), ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if actual != expected:
            raise ValueError
        return record
    except Exception:
        raise ValueError("Invalid draft.") from None
