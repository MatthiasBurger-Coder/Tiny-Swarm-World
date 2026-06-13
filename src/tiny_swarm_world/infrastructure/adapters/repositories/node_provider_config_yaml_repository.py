from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
)
from tiny_swarm_world.infrastructure.project_paths import config_root


DEFAULT_NODE_PROVIDER_CONFIG_PATH = Path("node-providers") / "provider_config.yaml"
SUPPORTED_SCHEMA_VERSION = "1"

_ROOT_FIELDS = frozenset(
    (
        "schema_version",
        "default_provider",
        "backend_selection",
        "nodes",
        "profiles",
        "provider_resource_resolution",
        "verification_metadata",
    )
)
_BACKEND_SELECTION_FIELDS = frozenset(("preferred_backend", "candidates"))
_NODE_FIELDS = frozenset(
    (
        "name",
        "role",
        "provider",
        "backend",
        "profile",
        "additional_profiles",
        "image_alias",
        "resources",
        "networks",
    )
)
_PROFILE_FIELDS = frozenset(
    (
        "backend_support",
        "risk_labels",
        "privileged_default",
        "nesting_required",
        "syscall_interception_required",
        "cgroup_policy",
        "apparmor_policy",
        "seccomp_policy",
        "capability_additions",
        "host_network",
        "host_mounts",
        "live_mutation_consent_required",
        "blocks_mutation_when_missing",
    )
)
_VERIFICATION_FIELDS = frozenset(("readiness_timeout_seconds", "evidence_policy", "checks"))
_EVIDENCE_POLICY_FIELDS = frozenset(("summary_only", "store_raw_output"))
_PROVIDER_RESOURCE_RESOLUTION_FIELDS = frozenset(("network_mappings", "storage_pool"))

_FORBIDDEN_KEY_PARTS = (
    "api_key",
    "authorization",
    "credential",
    "external_ip",
    "gateway",
    "host_ip",
    "host_user",
    "ip_address",
    "local_path",
    "password",
    "secret",
    "stderr",
    "stdout",
    "token",
    "username",
)
_IPV4_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_IPV6_PATTERN = re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F]{0,4}\b")
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^|[\s=:])/(?:home|mnt|Users|var/lib/docker|var/run)[/\w.-]*")
_WINDOWS_PATH_PATTERN = re.compile(r"\b[A-Za-z]:\\")
_COMMAND_PATTERN = re.compile(
    r"\b(?:bash|curl|docker|docker-compose|incus|lxc|netplan|python3?|sh|"
    r"socat|sudo|wsl)\s+\S+",
    re.IGNORECASE,
)
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:api[_-]?key|passphrase|password|secret|token)\s*[:=]",
    re.IGNORECASE,
)
_SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


class NodeProviderConfigError(ValueError):
    pass


@dataclass(frozen=True)
class NodeProviderNodeConfig:
    spec: NodeSpec
    profile: str
    image_alias: str
    resources: Mapping[str, str]
    networks: tuple[str, ...]
    additional_profiles: tuple[str, ...] = ()

    @property
    def expected_profiles(self) -> tuple[str, ...]:
        return (self.profile, *self.additional_profiles)


@dataclass(frozen=True)
class NodeProviderProfileRequirement:
    name: str
    backend_support: tuple[ManagedLxcBackend, ...]
    risk_labels: tuple[str, ...]
    privileged_default: bool
    nesting_required: bool
    syscall_interception_required: bool
    cgroup_policy: str
    apparmor_policy: str
    seccomp_policy: str
    capability_additions: tuple[str, ...]
    host_network: bool
    host_mounts: tuple[str, ...]
    live_mutation_consent_required: bool
    blocks_mutation_when_missing: bool


@dataclass(frozen=True)
class ProviderVerificationMetadata:
    readiness_timeout_seconds: int
    evidence_summary_only: bool
    store_raw_output: bool
    checks: tuple[str, ...]


@dataclass(frozen=True)
class ProviderResourceResolution:
    network_mappings: Mapping[str, str]
    storage_pool: str


@dataclass(frozen=True)
class NodeProviderConfig:
    schema_version: str
    default_provider: NodeProviderKind
    preferred_backend: ManagedLxcBackend | None
    backend_candidates: tuple[ManagedLxcBackend, ...]
    nodes: tuple[NodeProviderNodeConfig, ...]
    profiles: tuple[NodeProviderProfileRequirement, ...]
    provider_resource_resolution: ProviderResourceResolution | None
    verification_metadata: ProviderVerificationMetadata

    @property
    def profile_names(self) -> tuple[str, ...]:
        return tuple(profile.name for profile in self.profiles)


class NodeProviderConfigYamlRepository:
    def __init__(self, path: Path | None = None):
        self.path = path or (config_root() / DEFAULT_NODE_PROVIDER_CONFIG_PATH)
        self.yaml = YAML(typ="safe")

    def load(self) -> NodeProviderConfig:
        if not self.path.exists():
            raise NodeProviderConfigError("node provider config file is missing")

        try:
            data = self.yaml.load(self.path.read_text(encoding="utf-8"))
        except YAMLError as exc:
            raise NodeProviderConfigError("node provider config YAML is invalid") from exc

        if not isinstance(data, Mapping):
            raise NodeProviderConfigError("node provider config YAML root must be a mapping")
        _reject_unknown_fields(data, _ROOT_FIELDS, "root")
        _reject_unsafe_config_values(data)
        return _config_from_mapping(data)


def _config_from_mapping(data: Mapping[str, Any]) -> NodeProviderConfig:
    schema_version = str(_required(data, "schema_version", "root"))
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise NodeProviderConfigError("unsupported node provider config schema version")

    default_provider = _provider(_required(data, "default_provider", "root"))
    if default_provider != NodeProviderKind.LXC_NATIVE:
        raise NodeProviderConfigError("node provider config default must be lxc_native")

    backend_selection = _required_mapping(data, "backend_selection", "root")
    _reject_unknown_fields(backend_selection, _BACKEND_SELECTION_FIELDS, "backend_selection")
    preferred_backend = _optional_backend(backend_selection.get("preferred_backend"))
    backend_candidates = _backend_tuple(
        _required_sequence(backend_selection, "candidates", "backend_selection")
    )
    if set(backend_candidates) != {ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD}:
        raise NodeProviderConfigError("backend candidates must include incus and lxd")

    profiles_mapping = _required_mapping(data, "profiles", "root")
    profiles = tuple(
        _profile_requirement(name, profile_data)
        for name, profile_data in profiles_mapping.items()
    )
    profile_names = {profile.name for profile in profiles}
    if len(profile_names) != len(profiles):
        raise NodeProviderConfigError("profile names must be unique")

    nodes = tuple(
        _node_config(item, index, profile_names)
        for index, item in enumerate(_required_sequence(data, "nodes", "root"), start=1)
    )
    node_names = {node.spec.name for node in nodes}
    if len(node_names) != len(nodes):
        raise NodeProviderConfigError("node names must be unique")

    verification_metadata = _verification_metadata(
        _required_mapping(data, "verification_metadata", "root")
    )
    provider_resource_resolution = _provider_resource_resolution(data, verification_metadata)
    _validate_provider_resource_resolution(
        nodes,
        provider_resource_resolution,
        verification_metadata,
    )

    return NodeProviderConfig(
        schema_version=schema_version,
        default_provider=default_provider,
        preferred_backend=preferred_backend,
        backend_candidates=backend_candidates,
        nodes=nodes,
        profiles=profiles,
        provider_resource_resolution=provider_resource_resolution,
        verification_metadata=verification_metadata,
    )


def _node_config(
    item: object,
    index: int,
    profile_names: set[str],
) -> NodeProviderNodeConfig:
    if not isinstance(item, Mapping):
        raise NodeProviderConfigError(f"node {index} must be a mapping")
    _reject_unknown_fields(item, _NODE_FIELDS, f"nodes[{index}]")
    profile = _safe_identifier(_required(item, "profile", f"nodes[{index}]"), "node profile")
    if profile not in profile_names:
        raise NodeProviderConfigError(f"node {index} references unknown profile")
    additional_profiles = tuple(
        _safe_identifier(item, "additional node profile")
        for item in _optional_sequence(item, "additional_profiles", f"nodes[{index}]")
    )
    if profile in additional_profiles or len(set(additional_profiles)) != len(additional_profiles):
        raise NodeProviderConfigError(f"node {index} profiles must be unique")
    unknown_profiles = set(additional_profiles) - profile_names
    if unknown_profiles:
        raise NodeProviderConfigError(f"node {index} references unknown additional profile")

    resources = _string_mapping(_required_mapping(item, "resources", f"nodes[{index}]"))
    networks = tuple(
        _safe_identifier(network, "node network")
        for network in _required_sequence(item, "networks", f"nodes[{index}]")
    )
    backend = _optional_backend(item.get("backend"))
    spec = NodeSpec(
        name=str(_required(item, "name", f"nodes[{index}]")),
        role=NodeRole(str(_required(item, "role", f"nodes[{index}]"))),
        provider=_provider(_required(item, "provider", f"nodes[{index}]")),
        backend=backend,
    )
    return NodeProviderNodeConfig(
        spec=spec,
        profile=profile,
        additional_profiles=additional_profiles,
        image_alias=_safe_identifier(
            _required(item, "image_alias", f"nodes[{index}]"),
            "image alias",
        ),
        resources=resources,
        networks=networks,
    )


def _profile_requirement(
    name: object,
    data: object,
) -> NodeProviderProfileRequirement:
    profile_name = _safe_identifier(name, "profile name")
    if not isinstance(data, Mapping):
        raise NodeProviderConfigError(f"profile {profile_name} must be a mapping")
    _reject_unknown_fields(data, _PROFILE_FIELDS, f"profiles.{profile_name}")

    backend_support = _backend_tuple(
        _required_sequence(data, "backend_support", f"profiles.{profile_name}")
    )
    risk_labels = tuple(
        _safe_identifier(label, "risk label")
        for label in _required_sequence(data, "risk_labels", f"profiles.{profile_name}")
    )
    if not risk_labels:
        raise NodeProviderConfigError("profile risk labels are required")

    privileged_default = _bool_value(_required(data, "privileged_default", profile_name))
    host_network = _bool_value(_required(data, "host_network", profile_name))
    host_mounts = tuple(str(item) for item in _required_sequence(data, "host_mounts", profile_name))
    if privileged_default:
        raise NodeProviderConfigError("privileged container profile must not be the default")
    if host_network or host_mounts:
        raise NodeProviderConfigError("host network and host mounts must not be default provider config")

    return NodeProviderProfileRequirement(
        name=profile_name,
        backend_support=backend_support,
        risk_labels=risk_labels,
        privileged_default=privileged_default,
        nesting_required=_bool_value(_required(data, "nesting_required", profile_name)),
        syscall_interception_required=_bool_value(
            _required(data, "syscall_interception_required", profile_name)
        ),
        cgroup_policy=_safe_identifier(_required(data, "cgroup_policy", profile_name), "cgroup policy"),
        apparmor_policy=_safe_identifier(
            _required(data, "apparmor_policy", profile_name),
            "apparmor policy",
        ),
        seccomp_policy=_safe_identifier(
            _required(data, "seccomp_policy", profile_name),
            "seccomp policy",
        ),
        capability_additions=tuple(
            _safe_identifier(item, "capability addition")
            for item in _required_sequence(data, "capability_additions", profile_name)
        ),
        host_network=host_network,
        host_mounts=host_mounts,
        live_mutation_consent_required=_bool_value(
            _required(data, "live_mutation_consent_required", profile_name)
        ),
        blocks_mutation_when_missing=_bool_value(
            _required(data, "blocks_mutation_when_missing", profile_name)
        ),
    )


def _verification_metadata(data: Mapping[str, Any]) -> ProviderVerificationMetadata:
    _reject_unknown_fields(data, _VERIFICATION_FIELDS, "verification_metadata")
    evidence_policy = _required_mapping(data, "evidence_policy", "verification_metadata")
    _reject_unknown_fields(evidence_policy, _EVIDENCE_POLICY_FIELDS, "evidence_policy")
    summary_only = _bool_value(_required(evidence_policy, "summary_only", "evidence_policy"))
    store_raw_output = _bool_value(_required(evidence_policy, "store_raw_output", "evidence_policy"))
    if not summary_only or store_raw_output:
        raise NodeProviderConfigError("provider evidence policy must be summary-only")

    timeout_seconds = int(str(_required(data, "readiness_timeout_seconds", "verification_metadata")))
    if timeout_seconds <= 0 or timeout_seconds > 30:
        raise NodeProviderConfigError("provider readiness timeout must be between 1 and 30 seconds")

    checks = tuple(
        _safe_identifier(item, "verification check")
        for item in _required_sequence(data, "checks", "verification_metadata")
    )
    if "backend_readiness" not in checks or "profile_requirements" not in checks:
        raise NodeProviderConfigError("provider verification checks are incomplete")

    return ProviderVerificationMetadata(timeout_seconds, summary_only, store_raw_output, checks)


def _provider_resource_resolution(
    data: Mapping[str, Any],
    verification_metadata: ProviderVerificationMetadata,
) -> ProviderResourceResolution | None:
    if "provider_resource_resolution" not in data:
        if "provider_resource_resolution" in verification_metadata.checks:
            raise NodeProviderConfigError("provider resource resolution is required")
        return None

    resolution = _required_mapping(data, "provider_resource_resolution", "root")
    _reject_unknown_fields(
        resolution,
        _PROVIDER_RESOURCE_RESOLUTION_FIELDS,
        "provider_resource_resolution",
    )
    network_mappings = {
        _safe_identifier(logical_network, "logical provider network"): _safe_identifier(
            provider_network,
            "resolved provider network",
        )
        for logical_network, provider_network in _required_mapping(
            resolution,
            "network_mappings",
            "provider_resource_resolution",
        ).items()
    }
    if not network_mappings:
        raise NodeProviderConfigError("provider network mappings must not be empty")

    return ProviderResourceResolution(
        network_mappings=network_mappings,
        storage_pool=_safe_identifier(
            _required(resolution, "storage_pool", "provider_resource_resolution"),
            "provider storage pool",
        ),
    )


def _validate_provider_resource_resolution(
    nodes: tuple[NodeProviderNodeConfig, ...],
    provider_resource_resolution: ProviderResourceResolution | None,
    verification_metadata: ProviderVerificationMetadata,
) -> None:
    if "provider_resource_resolution" not in verification_metadata.checks:
        return
    if provider_resource_resolution is None:
        raise NodeProviderConfigError("provider resource resolution is required")

    mapped_networks = set(provider_resource_resolution.network_mappings)
    missing_networks = sorted(
        {
            network
            for node in nodes
            for network in node.networks
            if network not in mapped_networks
        }
    )
    if missing_networks:
        raise NodeProviderConfigError(
            f"node networks require provider resource mappings: {missing_networks}"
        )


def _provider(value: object) -> NodeProviderKind:
    try:
        return NodeProviderKind(str(value))
    except ValueError as exc:
        raise NodeProviderConfigError(f"unsupported node provider {value!r}") from exc


def _backend_tuple(values: Sequence[object]) -> tuple[ManagedLxcBackend, ...]:
    backends: list[ManagedLxcBackend] = []
    for value in values:
        try:
            backend = ManagedLxcBackend(str(value))
        except ValueError as exc:
            raise NodeProviderConfigError(f"unsupported managed LXC backend {value!r}") from exc
        if backend in backends:
            raise NodeProviderConfigError("managed LXC backends must be unique")
        backends.append(backend)
    if not backends:
        raise NodeProviderConfigError("managed LXC backend list must not be empty")
    return tuple(backends)


def _optional_backend(value: object) -> ManagedLxcBackend | None:
    if value is None:
        return None
    return _backend_tuple((value,))[0]


def _required(data: Mapping[str, Any], key: str, path: str) -> object:
    if key not in data:
        raise NodeProviderConfigError(f"{path}: missing required field {key}")
    return data[key]


def _required_mapping(data: Mapping[str, Any], key: str, path: str) -> Mapping[str, Any]:
    value = _required(data, key, path)
    if not isinstance(value, Mapping):
        raise NodeProviderConfigError(f"{path}.{key} must be a mapping")
    return value


def _required_sequence(data: Mapping[str, Any], key: str, path: str) -> tuple[object, ...]:
    value = _required(data, key, path)
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise NodeProviderConfigError(f"{path}.{key} must be a list")
    return tuple(value)


def _optional_sequence(data: Mapping[str, Any], key: str, path: str) -> tuple[object, ...]:
    if key not in data:
        return ()
    return _required_sequence(data, key, path)


def _string_mapping(data: Mapping[str, Any]) -> Mapping[str, str]:
    return {str(key): str(value) for key, value in data.items()}


def _bool_value(value: object) -> bool:
    if not isinstance(value, bool):
        raise NodeProviderConfigError("expected boolean provider config value")
    return value


def _safe_identifier(value: object, label: str) -> str:
    text = str(value)
    if not _SAFE_IDENTIFIER_PATTERN.fullmatch(text):
        raise NodeProviderConfigError(f"{label} contains invalid characters")
    return text


def _reject_unknown_fields(data: Mapping[str, object], allowed: frozenset[str], path: str) -> None:
    unknown = set(data) - allowed
    if unknown:
        raise NodeProviderConfigError(f"{path}: unsupported fields: {sorted(unknown)}")


def _reject_unsafe_config_values(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_key(str(key))
            _reject_unsafe_config_values(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, str):
        for item in value:
            _reject_unsafe_config_values(item)
        return
    _reject_unsafe_text(str(value))


def _reject_unsafe_key(key: str) -> None:
    normalized = key.casefold()
    if any(part in normalized for part in _FORBIDDEN_KEY_PARTS):
        raise NodeProviderConfigError("provider config contains unsafe key")


def _reject_unsafe_text(value: str) -> None:
    if any(
        pattern.search(value)
        for pattern in (
            _IPV4_PATTERN,
            _IPV6_PATTERN,
            _ABSOLUTE_PATH_PATTERN,
            _WINDOWS_PATH_PATTERN,
            _COMMAND_PATTERN,
            _SECRET_ASSIGNMENT_PATTERN,
        )
    ):
        raise NodeProviderConfigError("provider config contains unsafe value")
