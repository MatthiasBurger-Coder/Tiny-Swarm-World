"""Provider profile policy and safe profile evidence helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from tiny_swarm_world.infrastructure.adapters.clients.lxc.node.safety import (
    SECURITY_PRIVILEGED_KEY,
    SECURITY_PRIVILEGED_VALUE,
    allow_privileged_swarm_ingress,
    has_unsafe_instance_config,
    has_unsafe_instance_devices,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderProfileRequirement,
)


_YAML = YAML(typ="safe")


def _string_mapping(value: object) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def _device_mapping(value: object) -> Mapping[str, Mapping[str, str]]:
    if not isinstance(value, Mapping):
        return {}
    devices: dict[str, Mapping[str, str]] = {}
    for name, item in value.items():
        if isinstance(item, Mapping):
            devices[str(name)] = {str(key): str(data) for key, data in item.items()}
    return devices


def profile_output_safe(
    output: str,
    profile_name: str,
    *,
    allow_project_proxy_devices: bool = False,
) -> bool:
    try:
        data = _YAML.load(output) or {}
    except YAMLError:
        return False
    if not isinstance(data, Mapping):
        return False
    name = data.get("name")
    if name is not None and str(name) != profile_name:
        return False
    config = _string_mapping(data.get("config", {}))
    devices = _device_mapping(data.get("devices", {}))
    return not has_unsafe_instance_config(config) and not has_unsafe_instance_devices(
        devices,
        allow_project_proxy_devices=allow_project_proxy_devices,
    )


def profile_allows_project_proxy_devices(
    profile: NodeProviderProfileRequirement,
) -> bool:
    return "manager_proxy_profile_requires_profile_reconciliation" in profile.risk_labels


def missing_profile_settings(
    output: str,
    profile: NodeProviderProfileRequirement,
) -> Mapping[str, str]:
    try:
        data = _YAML.load(output) or {}
    except YAMLError:
        return required_profile_settings(profile)
    if not isinstance(data, Mapping):
        return required_profile_settings(profile)
    config = _string_mapping(data.get("config", {}))
    return {
        key: value
        for key, value in required_profile_settings(profile).items()
        if config.get(key) != value
    }


def required_profile_settings(
    profile: NodeProviderProfileRequirement,
) -> Mapping[str, str]:
    settings: dict[str, str] = {}
    if allow_privileged_swarm_ingress() and profile.nesting_required:
        settings[SECURITY_PRIVILEGED_KEY] = SECURITY_PRIVILEGED_VALUE
    if profile.nesting_required:
        settings["security.nesting"] = "true"
    if profile.syscall_interception_required:
        settings["security.syscalls.intercept.mknod"] = "true"
        settings["security.syscalls.intercept.setxattr"] = "true"
    return settings


def profile_evidence(
    expected_profile: str,
    available_profiles: Sequence[str],
) -> dict[str, str]:
    return {
        "expected_profile": expected_profile,
        "resolved_profile": expected_profile,
        "available_profiles": ",".join(available_profiles),
    }
