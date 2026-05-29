from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from typing import Protocol

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from tiny_swarm_world.application.ports.node_provider import PortNodeLifecycle
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    NodeSpec,
    ProviderSelection,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderConfig,
    NodeProviderNodeConfig,
    NodeProviderProfileRequirement,
)


DEFAULT_LXC_LAUNCH_TIMEOUT_SECONDS = 300.0
DEFAULT_LXC_START_TIMEOUT_SECONDS = 60.0
DEFAULT_LXC_IMAGE_REFERENCES = {"ubuntu-24.04": "ubuntu:24.04"}
MANAGED_MARKER = "user.tiny_swarm_world.managed"
NODE_MARKER = "user.tiny_swarm_world.node"
IMAGE_ALIAS_MARKER = "user.tiny_swarm_world.image_alias"

_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}
_RESOURCE_KEYS = frozenset(("cpu", "memory", "disk"))
_CPU_PATTERN = re.compile(r"^[1-9]\d*$")
_SIZE_PATTERN = re.compile(r"^[1-9]\d*[KMGT]i?B?$")
_YAML = YAML(typ="safe")


@dataclass(frozen=True)
class LxcNodeCommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


class LxcNodeCommandRunner(Protocol):
    async def run(
        self,
        args: Sequence[str],
        timeout_seconds: float,
    ) -> LxcNodeCommandResult:
        # Protocol declaration; concrete runners execute the provider command.
        pass


class NodeProviderConfigRepository(Protocol):
    def load(self) -> NodeProviderConfig:
        # Protocol declaration; concrete repositories load provider configuration.
        pass


class AsyncLxcNodeCommandRunner:
    async def run(
        self,
        args: Sequence[str],
        timeout_seconds: float,
    ) -> LxcNodeCommandResult:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            with suppress(ProcessLookupError):
                process.kill()
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(process.wait(), timeout=1.0)
            return LxcNodeCommandResult(returncode=124, timed_out=True)

        return LxcNodeCommandResult(
            returncode=process.returncode if process.returncode is not None else -1,
            stdout=_safe_process_text(stdout),
            stderr=_safe_process_text(stderr),
        )


class LxcNodeProvider(PortNodeLifecycle):
    def __init__(
        self,
        *,
        config_repository: NodeProviderConfigRepository,
        runner: LxcNodeCommandRunner,
        launch_timeout_seconds: float = DEFAULT_LXC_LAUNCH_TIMEOUT_SECONDS,
        start_timeout_seconds: float = DEFAULT_LXC_START_TIMEOUT_SECONDS,
        image_references: Mapping[str, str] | None = None,
        allow_live_mutation: bool = False,
    ):
        if launch_timeout_seconds <= 0:
            raise ValueError("LXC launch timeout must be positive.")
        if start_timeout_seconds <= 0:
            raise ValueError("LXC start timeout must be positive.")
        self.config_repository = config_repository
        self.runner = runner
        self.launch_timeout_seconds = launch_timeout_seconds
        self.start_timeout_seconds = start_timeout_seconds
        self.allow_live_mutation = allow_live_mutation
        self.image_references = {
            **DEFAULT_LXC_IMAGE_REFERENCES,
            **dict(image_references or {}),
        }

    async def ensure_node(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
    ) -> VerificationResult:
        backend_selection = _selected_backend(node, selection)
        if isinstance(backend_selection, VerificationResult):
            return backend_selection
        backend = backend_selection

        config_result = _load_config(self.config_repository, node, selection, backend)
        if isinstance(config_result, VerificationResult):
            return config_result
        config, node_config, profile = config_result

        profile_result = await self._ensure_profile_available(
            node,
            selection,
            backend,
            config,
            profile,
        )
        if profile_result is not None:
            return profile_result

        lookup = await self._lookup_node(node, backend, config)
        if lookup.failed:
            return _blocked(
                node,
                selection,
                "node_lookup_failed",
                backend=backend,
                return_code=lookup.returncode,
                timed_out=lookup.timed_out,
            )
        if lookup.node is not None:
            return await self._handle_existing_node(
                node,
                selection,
                backend,
                config,
                node_config,
                profile,
                lookup.node,
            )

        mutation_block = self._mutation_block(node, selection, backend, profile)
        if mutation_block is not None:
            return mutation_block

        launch_result = await self.runner.run(
            _launch_args(backend, node_config, self.image_references),
            self.launch_timeout_seconds,
        )
        if _command_failed(launch_result):
            return await self._handle_launch_failure(
                node,
                selection,
                backend,
                config,
                node_config,
                launch_result,
            )

        verification_failure = await self._created_node_verification_failure(
            node,
            selection,
            backend,
            config,
            node_config,
        )
        if verification_failure is not None:
            return verification_failure
        return _verified(node, backend, "created")

    def _mutation_block(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        profile: NodeProviderProfileRequirement,
    ) -> VerificationResult | None:
        if self.allow_live_mutation:
            return None
        return _blocked(
            node,
            selection,
            "live_mutation_consent_missing",
            backend=backend,
        )

    async def _ensure_profile_available(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        profile: NodeProviderProfileRequirement,
    ) -> VerificationResult | None:
        result = await self.runner.run(
            _profile_show_args(backend, profile.name),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        if not _command_failed(result):
            if _profile_output_safe(result.stdout, profile.name):
                return None
            return _blocked(
                node,
                selection,
                "unsafe_provider_profile",
                backend=backend,
                return_code=result.returncode,
            )
        reason = "profile_check_timed_out" if result.timed_out else "profile_missing"
        return _blocked(
            node,
            selection,
            reason,
            backend=backend,
            return_code=result.returncode,
            timed_out=result.timed_out,
        )

    async def _lookup_node(
        self,
        node: NodeSpec,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
    ) -> _NodeLookup:
        result = await self.runner.run(
            _list_args(backend, node.name),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        if _command_failed(result):
            return _NodeLookup.failed_result(result)

        try:
            payload = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            return _NodeLookup(returncode=result.returncode, parse_failed=True)
        if not isinstance(payload, list):
            return _NodeLookup(returncode=result.returncode, parse_failed=True)

        for item in payload:
            if not isinstance(item, Mapping):
                continue
            if item.get("name") == node.name:
                return _NodeLookup(
                    returncode=result.returncode,
                    node=_ObservedNode(
                        name=node.name,
                        status=str(item.get("status", "")),
                        instance_type=str(item.get("type", "")),
                        profiles=_string_tuple(item.get("profiles", ())),
                        config=_string_mapping(item.get("config", {})),
                        devices=_device_mapping(item.get("devices", {})),
                    ),
                )
        return _NodeLookup(returncode=result.returncode)

    async def _start_existing_node(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        node_config: NodeProviderNodeConfig,
        profile: NodeProviderProfileRequirement,
    ) -> VerificationResult:
        mutation_block = self._mutation_block(node, selection, backend, profile)
        if mutation_block is not None:
            return mutation_block

        start_result = await self.runner.run(
            _start_args(backend, node.name),
            self.start_timeout_seconds,
        )
        if _command_failed(start_result):
            return _apply_failed(
                node,
                selection,
                "start_failed",
                backend=backend,
                result=start_result,
            )

        verify = await self._lookup_node(node, backend, config)
        if (
            verify.failed
            or verify.node is None
            or not verify.node.running
            or not verify.node.matches_expected(node_config)
        ):
            return _verify_failed(
                node,
                selection,
                "started_node_not_verified",
                backend=backend,
                return_code=verify.returncode,
                timed_out=verify.timed_out,
            )
        return _verified(node, backend, "started")

    async def _handle_existing_node(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        node_config: NodeProviderNodeConfig,
        profile: NodeProviderProfileRequirement,
        observed_node: _ObservedNode,
    ) -> VerificationResult:
        if not observed_node.matches_expected(node_config):
            return _blocked(
                node,
                selection,
                "existing_node_not_managed",
                backend=backend,
            )
        if observed_node.running:
            return _verified(node, backend, "already_present")
        return await self._start_existing_node(
            node,
            selection,
            backend,
            config,
            node_config,
            profile,
        )

    async def _handle_launch_failure(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        node_config: NodeProviderNodeConfig,
        launch_result: LxcNodeCommandResult,
    ) -> VerificationResult:
        raced_lookup = await self._lookup_node(node, backend, config)
        if _launch_race_recovered(launch_result, raced_lookup, node_config):
            return _verified(node, backend, "already_present")
        return _apply_failed(
            node,
            selection,
            "launch_failed",
            backend=backend,
            result=launch_result,
        )

    async def _created_node_verification_failure(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        node_config: NodeProviderNodeConfig,
    ) -> VerificationResult | None:
        verify = await self._lookup_node(node, backend, config)
        if _lookup_matches_expected(verify, node_config):
            return None
        return _verify_failed(
            node,
            selection,
            "created_node_not_verified",
            backend=backend,
            return_code=verify.returncode,
            timed_out=verify.timed_out,
        )


@dataclass(frozen=True)
class _ObservedNode:
    name: str
    status: str
    instance_type: str
    profiles: tuple[str, ...]
    config: Mapping[str, str]
    devices: Mapping[str, Mapping[str, str]]

    @property
    def running(self) -> bool:
        return self.status.casefold() == "running"

    def matches_expected(self, node_config: NodeProviderNodeConfig) -> bool:
        return (
            self.instance_type.casefold() == "container"
            and node_config.profile in self.profiles
            and self.config.get(MANAGED_MARKER) == "true"
            and self.config.get(NODE_MARKER) == node_config.spec.name
            and self.config.get(IMAGE_ALIAS_MARKER) == node_config.image_alias
            and not _has_unsafe_instance_config(self.config)
            and not _has_unsafe_instance_devices(self.devices)
        )


@dataclass(frozen=True)
class _NodeLookup:
    returncode: int
    node: _ObservedNode | None = None
    timed_out: bool = False
    parse_failed: bool = False

    @property
    def failed(self) -> bool:
        return self.timed_out or self.parse_failed or self.returncode != 0

    @classmethod
    def failed_result(cls, result: LxcNodeCommandResult) -> _NodeLookup:
        return cls(returncode=result.returncode, timed_out=result.timed_out)


def _selected_backend(
    node: NodeSpec,
    selection: ProviderSelection,
) -> ManagedLxcBackend | VerificationResult:
    if selection.blocks_mutation:
        return _blocked(node, selection, "provider_selection_blocked")
    if node.provider != NodeProviderKind.LXC_NATIVE:
        return _blocked(node, selection, "unsupported_node_provider")
    if selection.selected_provider != NodeProviderKind.LXC_NATIVE:
        return _blocked(node, selection, "unsupported_selected_provider")

    backend = None if selection.backend_selection is None else selection.backend_selection.backend
    if backend is None:
        return _blocked(node, selection, "selected_backend_missing")
    if node.backend is not None and node.backend != backend:
        return _blocked(node, selection, "node_backend_mismatch", backend=backend)
    return backend


def _launch_race_recovered(
    launch_result: LxcNodeCommandResult,
    raced_lookup: _NodeLookup,
    node_config: NodeProviderNodeConfig,
) -> bool:
    return (
        _result_indicates_existing_node(launch_result)
        and _lookup_matches_expected(raced_lookup, node_config)
    )


def _lookup_matches_expected(
    lookup: _NodeLookup,
    node_config: NodeProviderNodeConfig,
) -> bool:
    return (
        not lookup.failed
        and lookup.node is not None
        and lookup.node.running
        and lookup.node.matches_expected(node_config)
    )


def _load_config(
    repository: NodeProviderConfigRepository,
    node: NodeSpec,
    selection: ProviderSelection,
    backend: ManagedLxcBackend,
) -> tuple[NodeProviderConfig, NodeProviderNodeConfig, NodeProviderProfileRequirement] | VerificationResult:
    try:
        config = repository.load()
    except ValueError:
        return _blocked(node, selection, "provider_config_invalid", backend=backend)

    node_config = _node_config(config, node.name)
    if node_config is None:
        return _blocked(node, selection, "node_config_missing", backend=backend)
    if node_config.spec != node and _node_spec_mismatches(node_config, node):
        return _blocked(node, selection, "node_config_mismatch", backend=backend)
    if node_config.spec.backend is not None and node_config.spec.backend != backend:
        return _blocked(node, selection, "config_backend_mismatch", backend=backend)

    profile = _profile(config, node_config.profile)
    if profile is None:
        return _blocked(node, selection, "profile_config_missing", backend=backend)
    if backend not in profile.backend_support:
        return _blocked(node, selection, "profile_backend_unsupported", backend=backend)
    if profile.privileged_default or profile.host_network or profile.host_mounts:
        return _blocked(node, selection, "unsafe_profile_default", backend=backend)
    if not _resources_supported(node_config.resources):
        return _blocked(node, selection, "unsupported_resource_config", backend=backend)

    return config, node_config, profile


def _node_config(
    config: NodeProviderConfig,
    node_name: str,
) -> NodeProviderNodeConfig | None:
    return next((item for item in config.nodes if item.spec.name == node_name), None)


def _profile(
    config: NodeProviderConfig,
    profile_name: str,
) -> NodeProviderProfileRequirement | None:
    return next((item for item in config.profiles if item.name == profile_name), None)


def _node_spec_mismatches(node_config: NodeProviderNodeConfig, node: NodeSpec) -> bool:
    return (
        node_config.spec.name != node.name
        or node_config.spec.role != node.role
        or node_config.spec.provider != node.provider
        or (
            node_config.spec.backend is not None
            and node_config.spec.backend != node.backend
        )
    )


def _resources_supported(resources: Mapping[str, str]) -> bool:
    if set(resources) - _RESOURCE_KEYS:
        return False
    cpu = resources.get("cpu")
    memory = resources.get("memory")
    disk = resources.get("disk")
    return (
        (cpu is None or _CPU_PATTERN.fullmatch(cpu) is not None)
        and (memory is None or _SIZE_PATTERN.fullmatch(memory) is not None)
        and (disk is None or _SIZE_PATTERN.fullmatch(disk) is not None)
    )


def _profile_show_args(
    backend: ManagedLxcBackend,
    profile_name: str,
) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "profile", "show", profile_name)


def _list_args(
    backend: ManagedLxcBackend,
    node_name: str,
) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "list", node_name, "--format", "json")


def _start_args(
    backend: ManagedLxcBackend,
    node_name: str,
) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "start", node_name)


def _launch_args(
    backend: ManagedLxcBackend,
    node_config: NodeProviderNodeConfig,
    image_references: Mapping[str, str],
) -> tuple[str, ...]:
    args: list[str] = [
        _BACKEND_CLI[backend],
        "launch",
        _image_ref(node_config.image_alias, image_references),
        node_config.spec.name,
        "--profile",
        node_config.profile,
        "-c",
        f"{MANAGED_MARKER}=true",
        "-c",
        f"{NODE_MARKER}={node_config.spec.name}",
        "-c",
        f"{IMAGE_ALIAS_MARKER}={node_config.image_alias}",
    ]
    cpu = node_config.resources.get("cpu")
    if cpu is not None:
        args.extend(("-c", f"limits.cpu={cpu}"))
    memory = node_config.resources.get("memory")
    if memory is not None:
        args.extend(("-c", f"limits.memory={memory}"))
    disk = node_config.resources.get("disk")
    if disk is not None:
        args.extend(("-d", f"root,size={disk}"))
    return tuple(args)


def _image_ref(image_alias: str, image_references: Mapping[str, str]) -> str:
    return image_references.get(image_alias, image_alias)


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        return ()
    return tuple(str(item) for item in value)


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


def _has_unsafe_instance_config(config: Mapping[str, str]) -> bool:
    return config.get("security.privileged", "").casefold() == "true" or any(
        key.startswith("raw.") for key in config
    )


def _has_unsafe_instance_devices(devices: Mapping[str, Mapping[str, str]]) -> bool:
    return any(_unsafe_instance_device(device) for device in devices.values())


def _unsafe_instance_device(device: Mapping[str, str]) -> bool:
    device_type = device.get("type", "").casefold()
    if device_type == "disk":
        return "source" in device
    if device_type == "nic":
        return _unsafe_network_device(device)
    return bool(device_type)


def _unsafe_network_device(device: Mapping[str, str]) -> bool:
    return (
        "parent" in device
        or "network" not in device
        or device.get("nictype", "").casefold() in {"macvlan", "physical", "sriov"}
    )


def _profile_output_safe(output: str, profile_name: str) -> bool:
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
    return not _has_unsafe_instance_config(config) and not _has_unsafe_instance_devices(devices)


def _command_failed(result: LxcNodeCommandResult) -> bool:
    return result.timed_out or result.returncode != 0


def _result_indicates_existing_node(result: LxcNodeCommandResult) -> bool:
    output = f"{result.stdout}\n{result.stderr}".casefold()
    return "already exists" in output or "already in use" in output


def _verified(
    node: NodeSpec,
    backend: ManagedLxcBackend,
    outcome: str,
) -> VerificationResult:
    return VerificationResult(
        target_id=_target_id(node),
        status=VerificationStatus.VERIFIED,
        message="LXC node lifecycle reached the desired state.",
        evidence=_evidence(
            "verify",
            "verified",
            node,
            backend,
            lifecycle_outcome=outcome,
        ),
    )


def _blocked(
    node: NodeSpec,
    selection: ProviderSelection,
    reason: str,
    *,
    backend: ManagedLxcBackend | None = None,
    return_code: int | None = None,
    timed_out: bool = False,
) -> VerificationResult:
    return VerificationResult(
        target_id=_target_id(node),
        status=VerificationStatus.BLOCKED,
        message="LXC node lifecycle is blocked before mutation.",
        evidence=_evidence(
            "pre_apply",
            reason,
            node,
            backend,
            return_code=return_code,
            timed_out=timed_out,
            selection_status=selection.status.value,
        ),
    )


def _apply_failed(
    node: NodeSpec,
    selection: ProviderSelection,
    reason: str,
    *,
    backend: ManagedLxcBackend,
    result: LxcNodeCommandResult,
) -> VerificationResult:
    return VerificationResult(
        target_id=_target_id(node),
        status=VerificationStatus.FAILED_TO_APPLY,
        message="LXC node lifecycle could not apply the desired state.",
        evidence=_evidence(
            "apply",
            reason,
            node,
            backend,
            return_code=result.returncode,
            timed_out=result.timed_out,
            selection_status=selection.status.value,
        ),
    )


def _verify_failed(
    node: NodeSpec,
    selection: ProviderSelection,
    reason: str,
    *,
    backend: ManagedLxcBackend,
    return_code: int,
    timed_out: bool = False,
) -> VerificationResult:
    return VerificationResult(
        target_id=_target_id(node),
        status=VerificationStatus.FAILED_TO_VERIFY,
        message="LXC node lifecycle could not verify the desired state.",
        evidence=_evidence(
            "verify",
            reason,
            node,
            backend,
            return_code=return_code,
            timed_out=timed_out,
            selection_status=selection.status.value,
        ),
    )


def _evidence(
    phase: str,
    classification: str,
    node: NodeSpec,
    backend: ManagedLxcBackend | None,
    *,
    lifecycle_outcome: str | None = None,
    return_code: int | None = None,
    timed_out: bool = False,
    selection_status: str | None = None,
) -> dict[str, str]:
    evidence = {
        "phase": phase,
        "classification": classification,
        "provider": NodeProviderKind.LXC_NATIVE.value,
        "node": node.name,
    }
    if backend is not None:
        evidence["backend"] = backend.value
    if lifecycle_outcome is not None:
        evidence["lifecycle_outcome"] = lifecycle_outcome
    if return_code is not None:
        evidence["return_code"] = str(return_code)
    if timed_out:
        evidence["timed_out"] = "true"
    if selection_status is not None:
        evidence["selection_status"] = selection_status
    return evidence


def _target_id(node: NodeSpec) -> str:
    return f"platform:node:{node.name}"


def _safe_process_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value
