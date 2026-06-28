from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from logging import Logger
from typing import Literal, Protocol

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from tiny_swarm_world.application.ports.node_provider import (
    PortManagedNodeTeardown,
    PortNodeLifecycle,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
    NodeSpec,
    ProviderSelection,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    ProviderBackendResourceResolution,
    NodeProviderConfig,
    NodeProviderNodeConfig,
    NodeProviderProfileRequirement,
    ProviderResourceResolution,
)
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


DEFAULT_LXC_LAUNCH_TIMEOUT_SECONDS = 300.0
DEFAULT_LXC_START_TIMEOUT_SECONDS = 60.0
DEFAULT_LXC_TEARDOWN_TIMEOUT_SECONDS = 300.0
DEFAULT_LXC_IMAGE_REFERENCES = {
    "incus:ubuntu-24.04": "images:ubuntu/24.04",
    "lxd:ubuntu-24.04": "ubuntu:24.04",
    "ubuntu-24.04": "ubuntu:24.04",
}
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


class LxcNodeProvider(PortNodeLifecycle, PortManagedNodeTeardown):
    def __init__(
        self,
        *,
        config_repository: NodeProviderConfigRepository,
        runner: LxcNodeCommandRunner,
        launch_timeout_seconds: float = DEFAULT_LXC_LAUNCH_TIMEOUT_SECONDS,
        start_timeout_seconds: float = DEFAULT_LXC_START_TIMEOUT_SECONDS,
        teardown_timeout_seconds: float = DEFAULT_LXC_TEARDOWN_TIMEOUT_SECONDS,
        image_references: Mapping[str, str] | None = None,
        allow_live_mutation: bool = False,
        logger: Logger | None = None,
    ):
        if launch_timeout_seconds <= 0:
            raise ValueError("LXC launch timeout must be positive.")
        if start_timeout_seconds <= 0:
            raise ValueError("LXC start timeout must be positive.")
        if teardown_timeout_seconds <= 0:
            raise ValueError("LXC teardown timeout must be positive.")
        self.config_repository = config_repository
        self.runner = runner
        self.launch_timeout_seconds = launch_timeout_seconds
        self.start_timeout_seconds = start_timeout_seconds
        self.teardown_timeout_seconds = teardown_timeout_seconds
        self.allow_live_mutation = allow_live_mutation
        self.image_references = {
            **DEFAULT_LXC_IMAGE_REFERENCES,
            **dict(image_references or {}),
        }
        self.logger = logger or LoggerFactory.get_logger(self.__class__.__name__)

    async def verify_node(
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
        config, node_config, _ = config_result

        lookup = await self._lookup_node(node, backend, config)
        if lookup.failed:
            return _blocked(
                node,
                selection,
                "verify_node_lookup_failed",
                backend=backend,
                return_code=lookup.returncode,
                timed_out=lookup.timed_out,
            )
        if lookup.node is None:
            return _verify_failed(
                node,
                selection,
                "managed_node_missing",
                backend=backend,
                return_code=lookup.returncode,
            )
        if not lookup.node.matches_expected(node_config):
            return _managed_node_verify_failed(
                node,
                selection,
                "managed_node_mismatch",
                backend=backend,
                return_code=lookup.returncode,
                observed_node=lookup.node,
                node_config=node_config,
            )
        if not lookup.node.running:
            return _managed_node_verify_failed(
                node,
                selection,
                "managed_node_not_running",
                backend=backend,
                return_code=lookup.returncode,
                observed_node=lookup.node,
                node_config=node_config,
            )
        return _verified(node, backend, "already_present")

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
        config, node_config, profiles = config_result

        resource_result = await self._verify_provider_resources(
            node,
            selection,
            backend,
            config,
            node_config,
        )
        if resource_result is not None:
            return resource_result

        profile_result = await self._ensure_profiles_available(
            node,
            selection,
            backend,
            config,
            profiles,
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
                lookup.node,
            )

        mutation_block = self._mutation_block(node, selection, backend)
        if mutation_block is not None:
            return mutation_block

        image_result = await self._verify_provider_image_available(
            node,
            selection,
            backend,
            config,
            node_config,
        )
        if image_result is not None:
            return image_result

        launch_result = await self.runner.run(
            _launch_args(
                backend,
                node_config,
                self.image_references,
                provider_resource_resolution=(
                    _selected_provider_resource_resolution(config, backend)
                    if _uses_provider_resource_resolution(config)
                    else None
                ),
            ),
            self.launch_timeout_seconds,
        )
        self._log_command_result("launch", node, backend, launch_result)
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

    async def _verify_provider_image_available(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        node_config: NodeProviderNodeConfig,
    ) -> VerificationResult | None:
        if "provider_image_availability" not in config.verification_metadata.checks:
            return None
        result = await self.runner.run(
            _image_info_args(
                backend,
                _image_ref(node_config.image_alias, self.image_references, backend),
            ),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        self._log_command_result("image_info", node, backend, result)
        if not _command_failed(result):
            return None
        return _blocked(
            node,
            selection,
            "image_unavailable",
            backend=backend,
            return_code=result.returncode,
            timed_out=result.timed_out,
            extra_evidence=_launch_failure_evidence(
                result,
                config,
                node_config,
                backend=backend,
                image_references=self.image_references,
            ),
        )

    async def reset_nodes(
        self,
        nodes: Sequence[NodeSpec],
        selection: ProviderSelection,
    ) -> VerificationResult:
        return await self._teardown_nodes(tuple(nodes), selection, "reset")

    async def destroy_nodes(
        self,
        nodes: Sequence[NodeSpec],
        selection: ProviderSelection,
    ) -> VerificationResult:
        return await self._teardown_nodes(tuple(nodes), selection, "destroy")

    async def _teardown_nodes(
        self,
        nodes: tuple[NodeSpec, ...],
        selection: ProviderSelection,
        operation: Literal["reset", "destroy"],
    ) -> VerificationResult:
        results: list[VerificationResult] = []
        plans: list[_TeardownNodePlan] = []
        for node in nodes:
            preflight = await self._teardown_node_preflight(node, selection, operation)
            if isinstance(preflight, VerificationResult):
                results.append(preflight)
            else:
                plans.append(preflight)

        if any(result.status != VerificationStatus.VERIFIED for result in results):
            return _teardown_summary(
                operation,
                results,
                expected_count=len(nodes),
                planned_count=len(plans),
            )

        for plan in plans:
            results.append(await self._delete_teardown_node(plan, selection, operation))
        return _teardown_summary(operation, results, expected_count=len(nodes))

    async def _teardown_node_preflight(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        operation: Literal["reset", "destroy"],
    ) -> _TeardownNodePlan | VerificationResult:
        backend_selection = _selected_backend(node, selection)
        if isinstance(backend_selection, VerificationResult):
            return backend_selection
        backend = backend_selection

        config_result = _load_config(self.config_repository, node, selection, backend)
        if isinstance(config_result, VerificationResult):
            return config_result
        config, node_config, _ = config_result

        lookup = await self._lookup_node(node, backend, config)
        if lookup.failed:
            return _blocked(
                node,
                selection,
                f"{operation}_node_lookup_failed",
                backend=backend,
                return_code=lookup.returncode,
                timed_out=lookup.timed_out,
            )
        if lookup.node is None:
            return _verified(node, backend, "already_absent")
        if not lookup.node.matches_expected(node_config):
            return _blocked(
                node,
                selection,
                f"{operation}_existing_node_not_managed",
                backend=backend,
                extra_evidence=_managed_node_mismatch_evidence(lookup.node, node_config),
            )

        mutation_block = self._mutation_block(node, selection, backend)
        if mutation_block is not None:
            return mutation_block

        return _TeardownNodePlan(node=node, backend=backend, config=config)

    async def _delete_teardown_node(
        self,
        plan: _TeardownNodePlan,
        selection: ProviderSelection,
        operation: Literal["reset", "destroy"],
    ) -> VerificationResult:
        delete_result = await self.runner.run(
            _delete_args(plan.backend, plan.node.name),
            self.teardown_timeout_seconds,
        )
        if _command_failed(delete_result):
            raced_lookup = await self._lookup_node(plan.node, plan.backend, plan.config)
            if not raced_lookup.failed and raced_lookup.node is None:
                return _verified(plan.node, plan.backend, "deleted", applied=True)
            return _apply_failed(
                plan.node,
                selection,
                f"{operation}_delete_failed",
                backend=plan.backend,
                result=delete_result,
            )

        verify = await self._lookup_node(plan.node, plan.backend, plan.config)
        if verify.failed:
            return _verify_failed(
                plan.node,
                selection,
                f"{operation}_delete_lookup_failed",
                backend=plan.backend,
                return_code=verify.returncode,
                timed_out=verify.timed_out,
            )
        if verify.node is not None:
            return _verify_failed(
                plan.node,
                selection,
                f"{operation}_delete_not_verified",
                backend=plan.backend,
                return_code=verify.returncode,
            )
        return _verified(plan.node, plan.backend, "deleted", applied=True)

    def _mutation_block(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
    ) -> VerificationResult | None:
        if self.allow_live_mutation:
            return None
        return _blocked(
            node,
            selection,
            "live_mutation_consent_missing",
            backend=backend,
        )

    async def _ensure_profiles_available(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        profiles: tuple[NodeProviderProfileRequirement, ...],
    ) -> VerificationResult | None:
        for profile in profiles:
            result = await self._ensure_profile_available(
                node,
                selection,
                backend,
                config,
                profile,
            )
            if result is not None:
                return result
        return None

    async def _verify_provider_resources(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        node_config: NodeProviderNodeConfig,
    ) -> VerificationResult | None:
        if "provider_resource_resolution" not in config.verification_metadata.checks:
            return None
        resource_resolution = config.provider_resource_resolution
        backend_resource_resolution = _selected_provider_resource_resolution(config, backend)
        logical_networks = node_config.networks
        if resource_resolution is None or backend_resource_resolution is None or not logical_networks:
            return _blocked(
                node,
                selection,
                "inventory_mapping_missing",
                backend=backend,
                extra_evidence=_resource_resolution_evidence(
                    node_config,
                    resource_resolution,
                    backend=backend,
                ),
            )
        unresolved_networks = tuple(
            network
            for network in logical_networks
            if network not in backend_resource_resolution.network_mappings
        )
        if unresolved_networks:
            return _blocked(
                node,
                selection,
                "inventory_mapping_missing",
                backend=backend,
                extra_evidence=_resource_resolution_evidence(
                    node_config,
                    resource_resolution,
                    backend=backend,
                ),
            )

        resolved_network = _resolved_network(node_config, backend_resource_resolution)
        available_networks = await self._available_network_names(backend, config)
        if resolved_network not in available_networks:
            return _blocked(
                node,
                selection,
                "network_missing",
                backend=backend,
                extra_evidence=_resource_resolution_evidence(
                    node_config,
                    resource_resolution,
                    backend=backend,
                    available_networks=available_networks,
                ),
            )

        available_storage_pools = await self._available_storage_pool_names(backend, config)
        if backend_resource_resolution.storage_pool not in available_storage_pools:
            return _blocked(
                node,
                selection,
                "storage_pool_missing",
                backend=backend,
                extra_evidence=_resource_resolution_evidence(
                    node_config,
                    resource_resolution,
                    backend=backend,
                    available_networks=available_networks,
                    available_storage_pools=available_storage_pools,
                ),
            )
        return None

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
            if _profile_output_safe(
                result.stdout,
                profile.name,
                allow_project_proxy_devices=_profile_allows_project_proxy_devices(profile),
            ):
                missing_settings = _missing_profile_settings(result.stdout, profile)
                if not missing_settings:
                    return None
                mutation_block = self._mutation_block(node, selection, backend)
                if mutation_block is not None:
                    return _blocked(
                        node,
                        selection,
                        "profile_reconciliation_requires_live_consent",
                        backend=backend,
                        extra_evidence=_profile_evidence(profile.name, (profile.name,)),
                    )
                return await self._reconcile_profile_settings(
                    node,
                    selection,
                    backend,
                    config,
                    profile,
                    missing_settings,
                )
            return _blocked(
                node,
                selection,
                "profile_invalid",
                backend=backend,
                return_code=result.returncode,
                extra_evidence=_profile_evidence(profile.name, (profile.name,)),
            )
        if result.timed_out:
            return _blocked(
                node,
                selection,
                "profile_check_timed_out",
                backend=backend,
                return_code=result.returncode,
                timed_out=True,
                extra_evidence=_profile_evidence(profile.name, ()),
            )

        available_profiles = await self._available_profile_names(backend, config)
        if profile.name in available_profiles:
            return _blocked(
                node,
                selection,
                "profile_lookup_failed",
                backend=backend,
                return_code=result.returncode,
                extra_evidence=_profile_evidence(profile.name, available_profiles),
            )
        mutation_block = self._mutation_block(node, selection, backend)
        if mutation_block is not None:
            return _blocked(
                node,
                selection,
                "profile_missing",
                backend=backend,
                return_code=result.returncode,
                extra_evidence=_profile_evidence(profile.name, available_profiles),
            )
        return await self._create_missing_profile(
            node,
            selection,
            backend,
            config,
            profile,
            available_profiles,
        )

    async def _available_profile_names(
        self,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
    ) -> tuple[str, ...]:
        result = await self.runner.run(
            _profile_list_args(backend),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        if _command_failed(result):
            return ()
        try:
            payload = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            return ()
        if not isinstance(payload, list):
            return ()
        names = (
            name
            for item in payload
            if isinstance(item, Mapping)
            for name in (_mapping_name(item),)
            if name is not None
        )
        return tuple(sorted(names))

    async def _available_network_names(
        self,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
    ) -> tuple[str, ...]:
        result = await self.runner.run(
            _network_list_args(backend),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        return _name_list_from_json(result)

    async def _available_storage_pool_names(
        self,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
    ) -> tuple[str, ...]:
        result = await self.runner.run(
            _storage_pool_list_args(backend),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        return _name_list_from_json(result)

    async def _create_missing_profile(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        profile: NodeProviderProfileRequirement,
        available_profiles: tuple[str, ...],
    ) -> VerificationResult | None:
        create_result = await self.runner.run(
            _profile_create_args(backend, profile.name),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        self._log_command_result("profile_create", node, backend, create_result)
        if _command_failed(create_result):
            return _profile_apply_failed(
                node,
                selection,
                "profile_create_failed",
                backend=backend,
                result=create_result,
                profile_name=profile.name,
                available_profiles=available_profiles,
            )

        missing_settings = _required_profile_settings(profile)
        reconcile_result = await self._reconcile_profile_settings(
            node,
            selection,
            backend,
            config,
            profile,
            missing_settings,
            available_profiles=available_profiles,
        )
        if reconcile_result is not None:
            return reconcile_result
        return None

    async def _reconcile_profile_settings(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        profile: NodeProviderProfileRequirement,
        settings: Mapping[str, str],
        available_profiles: tuple[str, ...] | None = None,
    ) -> VerificationResult | None:
        for key, value in settings.items():
            set_result = await self.runner.run(
                _profile_set_args(backend, profile.name, key, value),
                float(config.verification_metadata.readiness_timeout_seconds),
            )
            self._log_command_result("profile_set", node, backend, set_result)
            if _command_failed(set_result):
                return _profile_apply_failed(
                    node,
                    selection,
                    "profile_configure_failed",
                    backend=backend,
                    result=set_result,
                    profile_name=profile.name,
                    available_profiles=available_profiles or (profile.name,),
                )

        verify_result = await self.runner.run(
            _profile_show_args(backend, profile.name),
            float(config.verification_metadata.readiness_timeout_seconds),
        )
        self._log_command_result("profile_show", node, backend, verify_result)
        if _command_failed(verify_result):
            return _profile_verify_failed(
                node,
                selection,
                "profile_verify_failed",
                backend=backend,
                result=verify_result,
                profile_name=profile.name,
                available_profiles=available_profiles or (profile.name,),
            )
        if not _profile_output_safe(
            verify_result.stdout,
            profile.name,
            allow_project_proxy_devices=_profile_allows_project_proxy_devices(profile),
        ):
            return _blocked(
                node,
                selection,
                "profile_invalid",
                backend=backend,
                return_code=verify_result.returncode,
                extra_evidence=_profile_evidence(
                    profile.name,
                    available_profiles or (profile.name,),
                ),
            )
        if _missing_profile_settings(verify_result.stdout, profile):
            return _profile_verify_failed(
                node,
                selection,
                "profile_invalid",
                backend=backend,
                result=verify_result,
                profile_name=profile.name,
                available_profiles=available_profiles or (profile.name,),
            )
        return None

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
    ) -> VerificationResult:
        mutation_block = self._mutation_block(node, selection, backend)
        if mutation_block is not None:
            return mutation_block

        start_result = await self.runner.run(
            _start_args(backend, node.name),
            self.start_timeout_seconds,
        )
        self._log_command_result("start", node, backend, start_result)
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

    def _log_command_result(
        self,
        action: str,
        node: NodeSpec,
        backend: ManagedLxcBackend,
        result: LxcNodeCommandResult,
    ) -> None:
        log = self.logger.warning if _command_failed(result) else self.logger.info
        log(
            "lxc_node_provider action=%s backend=%s node=%s returncode=%s timed_out=%s stdout=%s stderr=%s",
            action,
            backend.value,
            node.name,
            result.returncode,
            str(result.timed_out).lower(),
            _safe_log_text(result.stdout),
            _safe_log_text(result.stderr),
        )

    async def _handle_existing_node(
        self,
        node: NodeSpec,
        selection: ProviderSelection,
        backend: ManagedLxcBackend,
        config: NodeProviderConfig,
        node_config: NodeProviderNodeConfig,
        observed_node: _ObservedNode,
    ) -> VerificationResult:
        if not observed_node.matches_expected(node_config):
            return _blocked(
                node,
                selection,
                "existing_node_not_managed",
                backend=backend,
                extra_evidence=_managed_node_mismatch_evidence(observed_node, node_config),
            )
        if observed_node.running:
            return _verified(node, backend, "already_present")
        return await self._start_existing_node(
            node,
            selection,
            backend,
            config,
            node_config,
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
        if _lookup_existing_expected(raced_lookup, node_config):
            return await self._start_existing_node(
                node,
                selection,
                backend,
                config,
                node_config,
            )
        return _apply_failed(
            node,
            selection,
            "launch_failed",
            backend=backend,
            result=launch_result,
            extra_evidence=_launch_failure_evidence(
                launch_result,
                config,
                node_config,
                backend=backend,
                image_references=self.image_references,
            ),
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
class _TeardownNodePlan:
    node: NodeSpec
    backend: ManagedLxcBackend
    config: NodeProviderConfig


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
        return not self.mismatch_reasons(node_config)

    def mismatch_reasons(
        self,
        node_config: NodeProviderNodeConfig,
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.instance_type.casefold() != "container":
            reasons.append("instance_type_not_container")
        if any(profile not in self.profiles for profile in node_config.expected_profiles):
            reasons.append("expected_profile_missing")
        if self.config.get(MANAGED_MARKER) != "true":
            if MANAGED_MARKER in self.config:
                reasons.append("managed_marker_not_true")
            else:
                reasons.append("managed_marker_missing")
        if self.config.get(NODE_MARKER) != node_config.spec.name:
            reasons.append("node_marker_mismatch")
        if self.config.get(IMAGE_ALIAS_MARKER) != node_config.image_alias:
            reasons.append("image_alias_marker_mismatch")
        if _has_unsafe_instance_config(self.config):
            reasons.append("unsafe_instance_config")
        if _has_unsafe_instance_devices(self.devices):
            reasons.append("unsafe_instance_devices")
        return tuple(reasons)


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


def _lookup_existing_expected(
    lookup: _NodeLookup,
    node_config: NodeProviderNodeConfig,
) -> bool:
    return (
        not lookup.failed
        and lookup.node is not None
        and lookup.node.matches_expected(node_config)
    )


def _load_config(
    repository: NodeProviderConfigRepository,
    node: NodeSpec,
    selection: ProviderSelection,
    backend: ManagedLxcBackend,
) -> tuple[
    NodeProviderConfig,
    NodeProviderNodeConfig,
    tuple[NodeProviderProfileRequirement, ...],
] | VerificationResult:
    try:
        config = repository.load()
    except ValueError:
        return _blocked(node, selection, "provider_config_invalid", backend=backend)

    node_config = _node_config(config, node.name)
    if node_config is None:
        return _blocked(node, selection, "inventory_mapping_missing", backend=backend)
    if node_config.spec != node and _node_spec_mismatches(node_config, node):
        return _blocked(node, selection, "node_config_mismatch", backend=backend)
    if node_config.spec.backend is not None and node_config.spec.backend != backend:
        return _blocked(node, selection, "config_backend_mismatch", backend=backend)

    profiles = _profiles(config, node_config.expected_profiles)
    if len(profiles) != len(node_config.expected_profiles):
        return _blocked(node, selection, "profile_config_missing", backend=backend)
    for profile in profiles:
        if backend not in profile.backend_support:
            return _blocked(node, selection, "profile_backend_unsupported", backend=backend)
        if profile.privileged_default or profile.host_network or profile.host_mounts:
            return _blocked(node, selection, "unsafe_profile_default", backend=backend)
    if not _resources_supported(node_config.resources):
        return _blocked(node, selection, "unsupported_resource_config", backend=backend)

    return config, node_config, profiles


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


def _profiles(
    config: NodeProviderConfig,
    profile_names: Sequence[str],
) -> tuple[NodeProviderProfileRequirement, ...]:
    profiles_by_name = {profile.name: profile for profile in config.profiles}
    return tuple(
        profile
        for profile_name in profile_names
        if (profile := profiles_by_name.get(profile_name)) is not None
    )


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


def _profile_list_args(backend: ManagedLxcBackend) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "profile", "list", "--format", "json")


def _network_list_args(backend: ManagedLxcBackend) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "network", "list", "--format", "json")


def _storage_pool_list_args(backend: ManagedLxcBackend) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "storage", "list", "--format", "json")


def _profile_create_args(
    backend: ManagedLxcBackend,
    profile_name: str,
) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "profile", "create", profile_name)


def _profile_set_args(
    backend: ManagedLxcBackend,
    profile_name: str,
    key: str,
    value: str,
) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "profile", "set", profile_name, key, value)


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


def _image_info_args(
    backend: ManagedLxcBackend,
    image_ref: str,
) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "image", "info", image_ref)


def _delete_args(
    backend: ManagedLxcBackend,
    node_name: str,
) -> tuple[str, ...]:
    return (_BACKEND_CLI[backend], "delete", node_name, "--force")


def _launch_args(
    backend: ManagedLxcBackend,
    node_config: NodeProviderNodeConfig,
    image_references: Mapping[str, str],
    *,
    provider_resource_resolution: ProviderBackendResourceResolution | None = None,
) -> tuple[str, ...]:
    args: list[str] = [
        _BACKEND_CLI[backend],
        "launch",
        _image_ref(node_config.image_alias, image_references, backend),
        node_config.spec.name,
    ]
    if provider_resource_resolution is not None:
        args.extend(("--network", _resolved_network(node_config, provider_resource_resolution)))
        args.extend(("--storage", provider_resource_resolution.storage_pool))
    for profile_name in node_config.expected_profiles:
        args.extend(("--profile", profile_name))
    args.extend(
        (
            "-c",
            f"{MANAGED_MARKER}=true",
            "-c",
            f"{NODE_MARKER}={node_config.spec.name}",
            "-c",
            f"{IMAGE_ALIAS_MARKER}={node_config.image_alias}",
        )
    )
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


def _image_ref(
    image_alias: str,
    image_references: Mapping[str, str],
    backend: ManagedLxcBackend | None = None,
) -> str:
    if backend is not None:
        backend_key = f"{backend.value}:{image_alias}"
        if backend_key in image_references:
            return image_references[backend_key]
    return image_references.get(image_alias, image_alias)


def _uses_provider_resource_resolution(config: NodeProviderConfig) -> bool:
    return "provider_resource_resolution" in config.verification_metadata.checks


def _selected_provider_resource_resolution(
    config: NodeProviderConfig,
    backend: ManagedLxcBackend,
) -> ProviderBackendResourceResolution | None:
    if config.provider_resource_resolution is None:
        return None
    return config.provider_resource_resolution.for_backend(backend)


def _resolved_network(
    node_config: NodeProviderNodeConfig,
    provider_resource_resolution: ProviderBackendResourceResolution,
) -> str:
    return provider_resource_resolution.network_mappings[node_config.networks[0]]


def _name_list_from_json(result: LxcNodeCommandResult) -> tuple[str, ...]:
    if _command_failed(result):
        return ()
    try:
        payload = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return ()
    if not isinstance(payload, list):
        return ()
    names = (
        name
        for item in payload
        if isinstance(item, Mapping)
        for name in (_mapping_name(item),)
        if name is not None
    )
    return tuple(sorted(names))


def _mapping_name(item: Mapping[object, object]) -> str | None:
    name = item.get("name")
    return name if isinstance(name, str) else None


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


def _has_unsafe_instance_devices(
    devices: Mapping[str, Mapping[str, str]],
    *,
    allow_project_proxy_devices: bool = False,
) -> bool:
    return any(
        _unsafe_instance_device(
            name,
            device,
            allow_project_proxy_devices=allow_project_proxy_devices,
        )
        for name, device in devices.items()
    )


def _unsafe_instance_device(
    name: str,
    device: Mapping[str, str],
    *,
    allow_project_proxy_devices: bool,
) -> bool:
    device_type = device.get("type", "").casefold()
    if device_type == "disk":
        return "source" in device
    if device_type == "nic":
        return _unsafe_network_device(device)
    if allow_project_proxy_devices and _safe_project_proxy_device(name, device):
        return False
    return bool(device_type)


def _safe_project_proxy_device(name: str, device: Mapping[str, str]) -> bool:
    name_match = _PROJECT_PROXY_DEVICE_NAME_PATTERN.fullmatch(name)
    if name_match is None:
        return False
    return (
        device.get("type", "").casefold() == "proxy"
        and set(device) <= {"type", "listen", "connect"}
        and _safe_proxy_endpoint_pair(
            device.get("listen", ""),
            device.get("connect", ""),
            expected_port=int(name_match.group("port")),
        )
    )


_PROJECT_PROXY_DEVICE_NAME_PATTERN = re.compile(r"^tsw-proxy-(?P<port>[1-9]\d{0,4})$")


def _safe_proxy_endpoint_pair(listen: str, connect: str, *, expected_port: int) -> bool:
    listen_endpoint = _parse_tcp_proxy_endpoint(listen)
    connect_endpoint = _parse_tcp_proxy_endpoint(connect)
    if listen_endpoint is None or connect_endpoint is None:
        return False
    listen_host, listen_port = listen_endpoint
    connect_host, connect_port = connect_endpoint
    return (
        listen_host in {"0.0.0.0", "127.0.0.1"}
        and connect_host == "127.0.0.1"
        and listen_port == connect_port
        and listen_port == expected_port
        and 1 <= listen_port <= 65535
    )


def _parse_tcp_proxy_endpoint(value: str) -> tuple[str, int] | None:
    prefix, separator, port_text = value.rpartition(":")
    if not separator or not port_text.isdigit():
        return None
    scheme, scheme_separator, host = prefix.partition(":")
    if scheme != "tcp" or scheme_separator != ":":
        return None
    port = int(port_text)
    return host, port


def _unsafe_network_device(device: Mapping[str, str]) -> bool:
    return (
        "parent" in device
        or "network" not in device
        or device.get("nictype", "").casefold() in {"macvlan", "physical", "sriov"}
    )


def _profile_output_safe(
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
    return not _has_unsafe_instance_config(config) and not _has_unsafe_instance_devices(
        devices,
        allow_project_proxy_devices=allow_project_proxy_devices,
    )


def _profile_allows_project_proxy_devices(profile: NodeProviderProfileRequirement) -> bool:
    return "manager_proxy_profile_requires_profile_reconciliation" in profile.risk_labels


def _missing_profile_settings(
    output: str,
    profile: NodeProviderProfileRequirement,
) -> Mapping[str, str]:
    try:
        data = _YAML.load(output) or {}
    except YAMLError:
        return _required_profile_settings(profile)
    if not isinstance(data, Mapping):
        return _required_profile_settings(profile)
    config = _string_mapping(data.get("config", {}))
    return {
        key: value
        for key, value in _required_profile_settings(profile).items()
        if config.get(key) != value
    }


def _required_profile_settings(
    profile: NodeProviderProfileRequirement,
) -> Mapping[str, str]:
    settings: dict[str, str] = {}
    if profile.nesting_required:
        settings["security.nesting"] = "true"
    if profile.syscall_interception_required:
        settings["security.syscalls.intercept.mknod"] = "true"
        settings["security.syscalls.intercept.setxattr"] = "true"
    return settings


def _profile_evidence(
    expected_profile: str,
    available_profiles: Sequence[str],
) -> dict[str, str]:
    return {
        "expected_profile": expected_profile,
        "resolved_profile": expected_profile,
        "available_profiles": ",".join(available_profiles),
    }


def _resource_resolution_evidence(
    node_config: NodeProviderNodeConfig,
    provider_resource_resolution: ProviderResourceResolution | None,
    *,
    backend: ManagedLxcBackend,
    available_networks: Sequence[str] = (),
    available_storage_pools: Sequence[str] = (),
) -> dict[str, str]:
    logical_network = ",".join(node_config.networks)
    backend_resource_resolution = (
        provider_resource_resolution.for_backend(backend)
        if provider_resource_resolution is not None
        else None
    )
    resolved_network = (
        _resolved_network(node_config, backend_resource_resolution)
        if backend_resource_resolution is not None
        and node_config.networks
        and node_config.networks[0] in backend_resource_resolution.network_mappings
        else ""
    )
    expected_storage_pool = (
        backend_resource_resolution.storage_pool
        if backend_resource_resolution is not None
        else ""
    )
    return {
        "expected_profile": node_config.profile,
        "available_profiles": "",
        "backend": backend.value,
        "logical_network": logical_network,
        "resolved_network": resolved_network,
        "available_networks": ",".join(available_networks),
        "expected_storage_pool": expected_storage_pool,
        "available_storage_pools": ",".join(available_storage_pools),
        "remediation_hint": _resource_resolution_remediation_hint(
            node_config,
            provider_resource_resolution,
            backend=backend,
            available_networks=available_networks,
            available_storage_pools=available_storage_pools,
        ),
    }


def _resource_resolution_remediation_hint(
    node_config: NodeProviderNodeConfig,
    provider_resource_resolution: ProviderResourceResolution | None,
    *,
    backend: ManagedLxcBackend,
    available_networks: Sequence[str],
    available_storage_pools: Sequence[str],
) -> str:
    if provider_resource_resolution is None:
        return "Configure provider resource resolution for the LXC-native node inventory."
    backend_resource_resolution = provider_resource_resolution.for_backend(backend)
    if backend_resource_resolution is None:
        return "Configure provider resource resolution for the selected backend."
    if not node_config.networks:
        return "Configure at least one logical network for the LXC-native node."
    if node_config.networks[0] not in backend_resource_resolution.network_mappings:
        return "Add an explicit logical-to-backend network mapping for the inventory network."
    resolved_network = _resolved_network(node_config, backend_resource_resolution)
    if resolved_network not in available_networks:
        return "Create or configure the resolved backend network before platform mutation."
    if backend_resource_resolution.storage_pool not in available_storage_pools:
        return "Create or configure the expected backend storage pool before platform mutation."
    return "Provider resource resolution is satisfied."


def _launch_failure_evidence(
    result: LxcNodeCommandResult,
    config: NodeProviderConfig,
    node_config: NodeProviderNodeConfig,
    *,
    backend: ManagedLxcBackend,
    image_references: Mapping[str, str],
) -> dict[str, str]:
    provider_image_ref = _image_ref(node_config.image_alias, image_references, backend)
    evidence = {
        "failure_reason": _classify_provider_failure(result),
        "operator_action": _operator_action_for_provider_failure(result),
        "expected_image_alias": node_config.image_alias,
        "expected_profile": node_config.profile,
        "expected_profiles": ",".join(node_config.expected_profiles),
        "provider_image_ref": provider_image_ref,
    }
    backend_resource_resolution = _selected_provider_resource_resolution(config, backend)
    if backend_resource_resolution is not None:
        if node_config.networks and node_config.networks[0] in backend_resource_resolution.network_mappings:
            evidence["resolved_network"] = _resolved_network(node_config, backend_resource_resolution)
        evidence["expected_storage_pool"] = backend_resource_resolution.storage_pool
    return evidence


def _classify_provider_failure(result: LxcNodeCommandResult) -> str:
    if result.timed_out:
        return "provider_command_timed_out"
    output = f"{result.stdout}\n{result.stderr}".casefold()
    if any(fragment in output for fragment in ("permission denied", "not authorized", "access denied")):
        return "daemon_access_denied"
    if any(
        fragment in output
        for fragment in (
            "image couldn't be found",
            "image could not be found",
            "failed getting remote image",
            "failed to get remote image",
            "no such image",
            "not found for remote",
            "remote not found",
            "requested image",
            "unable to resolve remote",
            "unknown remote",
        )
    ):
        return "image_unavailable"
    if any(
        fragment in output
        for fragment in (
            "network not found",
            "network doesn't exist",
            "unknown network",
            "failed to load network",
        )
    ):
        return "network_unavailable"
    if any(
        fragment in output
        for fragment in (
            "storage pool not found",
            "storage pool doesn't exist",
            "unknown storage pool",
            "no storage pool",
        )
    ):
        return "storage_pool_unavailable"
    if any(
        fragment in output
        for fragment in (
            "profile not found",
            "profile doesn't exist",
            "invalid devices",
            "failed to start device",
            "failed to add device",
        )
    ):
        return "profile_launch_rejected"
    if any(
        fragment in output
        for fragment in (
            "cgroup",
            "apparmor",
            "seccomp",
            "operation not permitted",
            "not supported",
        )
    ):
        return "wsl2_lxd_capability_blocked"
    if any(
        fragment in output
        for fragment in (
            "no space left",
            "insufficient",
            "not enough",
            "quota exceeded",
            "cannot allocate",
        )
    ):
        return "host_resource_exhausted"
    return "provider_launch_failed_unclassified"


def _operator_action_for_provider_failure(result: LxcNodeCommandResult) -> str:
    reason = _classify_provider_failure(result)
    if reason == "daemon_access_denied":
        return "verify_backend_daemon_access"
    if reason == "image_unavailable":
        return "verify_provider_image_remote"
    if reason == "network_unavailable":
        return "verify_backend_network_mapping"
    if reason == "storage_pool_unavailable":
        return "verify_backend_storage_pool"
    if reason == "profile_launch_rejected":
        return "inspect_provider_profiles"
    if reason == "wsl2_lxd_capability_blocked":
        return "verify_wsl2_lxd_capabilities"
    if reason == "host_resource_exhausted":
        return "verify_provider_host_resources"
    if reason == "provider_command_timed_out":
        return "inspect_provider_daemon_or_image_download"
    return "inspect_provider_launch_error"


def _command_failed(result: LxcNodeCommandResult) -> bool:
    return result.timed_out or result.returncode != 0


def _result_indicates_existing_node(result: LxcNodeCommandResult) -> bool:
    output = f"{result.stdout}\n{result.stderr}".casefold()
    return "already exists" in output or "already in use" in output


def _verified(
    node: NodeSpec,
    backend: ManagedLxcBackend,
    outcome: str,
    *,
    applied: bool = False,
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
            applied=applied,
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
    extra_evidence: Mapping[str, str] | None = None,
) -> VerificationResult:
    evidence = _evidence(
        "pre_apply",
        reason,
        node,
        backend,
        return_code=return_code,
        timed_out=timed_out,
        selection_status=selection.status.value,
    )
    if extra_evidence:
        evidence.update(extra_evidence)
    return VerificationResult(
        target_id=_target_id(node),
        status=VerificationStatus.BLOCKED,
        message="LXC node lifecycle is blocked before mutation.",
        evidence=evidence,
    )


def _apply_failed(
    node: NodeSpec,
    selection: ProviderSelection,
    reason: str,
    *,
    backend: ManagedLxcBackend,
    result: LxcNodeCommandResult,
    extra_evidence: Mapping[str, str] | None = None,
) -> VerificationResult:
    evidence = _evidence(
        "apply",
        reason,
        node,
        backend,
        return_code=result.returncode,
        timed_out=result.timed_out,
        selection_status=selection.status.value,
    )
    if extra_evidence:
        evidence.update(extra_evidence)
    return VerificationResult(
        target_id=_target_id(node),
        status=VerificationStatus.FAILED_TO_APPLY,
        message="LXC node lifecycle could not apply the desired state.",
        evidence=evidence,
    )


def _profile_apply_failed(
    node: NodeSpec,
    selection: ProviderSelection,
    reason: str,
    *,
    backend: ManagedLxcBackend,
    result: LxcNodeCommandResult,
    profile_name: str,
    available_profiles: Sequence[str],
) -> VerificationResult:
    evidence = _evidence(
        "apply",
        reason,
        node,
        backend,
        return_code=result.returncode,
        timed_out=result.timed_out,
        selection_status=selection.status.value,
    )
    evidence.update(_profile_evidence(profile_name, available_profiles))
    return VerificationResult(
        target_id=_target_id(node),
        status=VerificationStatus.FAILED_TO_APPLY,
        message="LXC node lifecycle could not apply the provider profile state.",
        evidence=evidence,
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


def _managed_node_verify_failed(
    node: NodeSpec,
    selection: ProviderSelection,
    reason: str,
    *,
    backend: ManagedLxcBackend,
    return_code: int,
    observed_node: _ObservedNode,
    node_config: NodeProviderNodeConfig,
) -> VerificationResult:
    evidence = _evidence(
        "verify",
        reason,
        node,
        backend,
        return_code=return_code,
        selection_status=selection.status.value,
    )
    evidence.update(_managed_node_mismatch_evidence(observed_node, node_config))
    evidence["observed_status"] = observed_node.status
    evidence["expected"] = "managed_lxc_node_running"
    evidence["observed"] = (
        "managed_node_configuration_mismatch"
        if reason == "managed_node_mismatch"
        else f"managed_node_{observed_node.status.casefold() or 'unknown'}"
    )
    evidence["next_action"] = "Run platform init or inspect the managed LXC node."
    return VerificationResult(
        target_id=_target_id(node),
        status=VerificationStatus.FAILED_TO_VERIFY,
        message="LXC managed node verification did not reach the desired state.",
        evidence=evidence,
    )


def _profile_verify_failed(
    node: NodeSpec,
    selection: ProviderSelection,
    reason: str,
    *,
    backend: ManagedLxcBackend,
    result: LxcNodeCommandResult,
    profile_name: str,
    available_profiles: Sequence[str],
) -> VerificationResult:
    evidence = _evidence(
        "verify",
        reason,
        node,
        backend,
        return_code=result.returncode,
        timed_out=result.timed_out,
        selection_status=selection.status.value,
    )
    evidence.update(_profile_evidence(profile_name, available_profiles))
    return VerificationResult(
        target_id=_target_id(node),
        status=VerificationStatus.FAILED_TO_VERIFY,
        message="LXC node lifecycle could not verify the provider profile state.",
        evidence=evidence,
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
    applied: bool = False,
) -> dict[str, str]:
    evidence = {
        "phase": phase,
        "classification": classification,
        "provider": NodeProviderKind.LXC_NATIVE.value,
        "node": node.name,
        "node_name": node.name,
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
    if applied:
        evidence["applied"] = "true"
    return evidence


def _target_id(node: NodeSpec) -> str:
    return f"platform:node:{node.name}"


def _teardown_summary(
    operation: Literal["reset", "destroy"],
    results: Sequence[VerificationResult],
    *,
    expected_count: int | None = None,
    planned_count: int = 0,
) -> VerificationResult:
    status = _teardown_summary_status(results)
    evidence = _teardown_summary_evidence(
        operation,
        results,
        status,
        expected_count=expected_count,
        planned_count=planned_count,
    )
    return VerificationResult(
        target_id=f"platform:{operation}:managed-nodes",
        status=status,
        message=f"LXC managed node {operation} reached summarized state.",
        evidence=evidence,
    )


def _teardown_summary_status(
    results: Sequence[VerificationResult],
) -> VerificationStatus:
    if all(result.status == VerificationStatus.VERIFIED for result in results):
        return VerificationStatus.VERIFIED
    if any(result.status == VerificationStatus.FAILED_TO_APPLY for result in results):
        return VerificationStatus.FAILED_TO_APPLY
    if any(result.status == VerificationStatus.FAILED_TO_VERIFY for result in results):
        return VerificationStatus.FAILED_TO_VERIFY
    return VerificationStatus.BLOCKED


def _teardown_summary_evidence(
    operation: Literal["reset", "destroy"],
    results: Sequence[VerificationResult],
    status: VerificationStatus,
    *,
    expected_count: int | None = None,
    planned_count: int = 0,
) -> dict[str, str]:
    verified_count = _status_count(results, VerificationStatus.VERIFIED)
    blocked_count = _status_count(results, VerificationStatus.BLOCKED)
    failed_apply_count = _status_count(results, VerificationStatus.FAILED_TO_APPLY)
    failed_verify_count = _status_count(results, VerificationStatus.FAILED_TO_VERIFY)
    applied = _any_teardown_applied(results)
    evidence = {
        "phase": _teardown_summary_phase(status, applied),
        "classification": _teardown_summary_classification(operation, status),
        "provider": NodeProviderKind.LXC_NATIVE.value,
        "expected_count": str(len(results) if expected_count is None else expected_count),
        "verified_count": str(verified_count),
        "blocked_count": str(blocked_count),
        "failed_apply_count": str(failed_apply_count),
        "failed_verify_count": str(failed_verify_count),
    }
    if planned_count:
        evidence["planned_count"] = str(planned_count)
    if applied:
        evidence["applied"] = "true"
    first_failure = next(
        (result for result in results if result.status != VerificationStatus.VERIFIED),
        None,
    )
    if first_failure is not None:
        first_classification = first_failure.evidence.get("classification")
        if first_classification is not None:
            evidence["first_failure_classification"] = first_classification
        for key in _FIRST_FAILURE_SAFE_EVIDENCE_KEYS:
            value = first_failure.evidence.get(key)
            if value is not None:
                evidence[f"first_failure_{key}"] = value
    return evidence


_FIRST_FAILURE_SAFE_EVIDENCE_KEYS = (
    "backend",
    "expected_image_alias",
    "expected_profile",
    "expected_profiles",
    "mismatch_reasons",
    "node",
    "observed_image_alias_marker",
    "observed_managed_marker",
    "observed_node_marker",
    "repair_action",
    "stale_project_proxy_devices",
)


def _managed_node_mismatch_evidence(
    observed_node: _ObservedNode,
    node_config: NodeProviderNodeConfig,
) -> dict[str, str]:
    evidence = {
        "expected_image_alias": node_config.image_alias,
        "expected_profile": node_config.profile,
        "expected_profiles": ",".join(node_config.expected_profiles),
        "mismatch_reasons": ",".join(observed_node.mismatch_reasons(node_config)),
        "observed_image_alias_marker": _marker_state(
            observed_node.config.get(IMAGE_ALIAS_MARKER),
            expected=node_config.image_alias,
        ),
        "observed_managed_marker": _marker_state(
            observed_node.config.get(MANAGED_MARKER),
            expected="true",
        ),
        "observed_node_marker": _marker_state(
            observed_node.config.get(NODE_MARKER),
            expected=node_config.spec.name,
        ),
    }
    stale_project_proxy_devices = _safe_project_proxy_device_names(observed_node.devices)
    if stale_project_proxy_devices:
        evidence["repair_action"] = "explicit_lxc_proxy_drift_repair_required"
        evidence["stale_project_proxy_devices"] = ",".join(stale_project_proxy_devices)
    return evidence


def _safe_project_proxy_device_names(
    devices: Mapping[str, Mapping[str, str]],
) -> tuple[str, ...]:
    return tuple(
        name
        for name, device in sorted(devices.items())
        if _safe_project_proxy_device(name, device)
    )


def _marker_state(value: str | None, *, expected: str) -> str:
    if value is None:
        return "missing"
    if value == expected:
        return "matches"
    return "different"


def _status_count(
    results: Sequence[VerificationResult],
    status: VerificationStatus,
) -> int:
    return sum(1 for result in results if result.status == status)


def _any_teardown_applied(results: Sequence[VerificationResult]) -> bool:
    return any(result.evidence.get("applied") == "true" for result in results) or any(
        result.status == VerificationStatus.FAILED_TO_APPLY for result in results
    )


def _teardown_summary_phase(status: VerificationStatus, applied: bool) -> str:
    if status == VerificationStatus.FAILED_TO_APPLY:
        return "apply"
    if status == VerificationStatus.BLOCKED and not applied:
        return "pre_apply"
    return "verify"


def _teardown_summary_classification(
    operation: Literal["reset", "destroy"],
    status: VerificationStatus,
) -> str:
    if status == VerificationStatus.VERIFIED:
        return f"managed_nodes_{operation}"
    if status == VerificationStatus.FAILED_TO_APPLY:
        return f"managed_nodes_{operation}_apply_failed"
    if status == VerificationStatus.BLOCKED:
        return f"managed_nodes_{operation}_blocked"
    return f"managed_nodes_{operation}_verify_failed"


def _safe_process_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def _safe_log_text(value: str, limit: int = 400) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit]}..."
