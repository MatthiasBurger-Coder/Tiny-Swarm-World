from __future__ import annotations

import re
from collections.abc import Mapping
from logging import Logger

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from tiny_swarm_world.application.ports.node_provider import (
    LxcProxyDriftRepairOutcome,
    LxcProxyDeviceState,
    PortLxcProxyDeviceRuntime,
)
from tiny_swarm_world.domain.network import LxcProxyDevicePlan
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend, NodeSpec
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult,
    LxcNodeCommandRunner,
)
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


DEFAULT_LXC_PROXY_DEVICE_TIMEOUT_SECONDS = 30.0
_YAML = YAML(typ="safe")

_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}
_MISSING_DEVICE_MARKERS = (
    "not found",
    "does not exist",
    "doesn't exist",
    "not exist",
    "no such device",
    "not available",
)
_PROJECT_PROXY_DEVICE_NAME_PATTERN = re.compile(r"^tsw-proxy-(?P<port>[1-9]\d{0,4})$")


class LxcProxyDeviceRuntime(PortLxcProxyDeviceRuntime):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        runner: LxcNodeCommandRunner,
        timeout_seconds: float = DEFAULT_LXC_PROXY_DEVICE_TIMEOUT_SECONDS,
        allow_live_mutation: bool = False,
        logger: Logger | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("LXC proxy device timeout must be positive.")
        self.backend = backend
        self.runner = runner
        self.timeout_seconds = timeout_seconds
        self.allow_live_mutation = allow_live_mutation
        self.logger = logger or LoggerFactory.get_logger(self.__class__.__name__)

    async def inspect_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> LxcProxyDeviceState:
        listen = await self.runner.run(
            _device_get_args(self.backend, profile_name, plan, "listen"),
            self.timeout_seconds,
        )
        self._log_command_result("inspect_listen", profile_name, plan, listen)
        if _command_missing_device(listen):
            return LxcProxyDeviceState.MISSING
        if _command_failed(listen):
            return LxcProxyDeviceState.UNKNOWN

        connect = await self.runner.run(
            _device_get_args(self.backend, profile_name, plan, "connect"),
            self.timeout_seconds,
        )
        self._log_command_result("inspect_connect", profile_name, plan, connect)
        if _command_missing_device(connect):
            return LxcProxyDeviceState.DRIFTED
        if _command_failed(connect):
            return LxcProxyDeviceState.UNKNOWN
        if (
            listen.stdout.strip() == plan.listen_endpoint
            and connect.stdout.strip() == plan.target_endpoint
        ):
            return LxcProxyDeviceState.PRESENT
        return LxcProxyDeviceState.DRIFTED

    async def create_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        if not self.allow_live_mutation:
            self.logger.warning(
                "lxc_proxy_runtime mutation_refused action=create profile=%s device=%s",
                profile_name,
                plan.device_name,
            )
            return False
        result = await self.runner.run(
            _device_add_args(self.backend, profile_name, plan),
            self.timeout_seconds,
        )
        self._log_command_result("create", profile_name, plan, result)
        return not _command_failed(result)

    async def update_proxy_device(
        self,
        profile_name: str,
        plan: LxcProxyDevicePlan,
    ) -> bool:
        if not self.allow_live_mutation:
            self.logger.warning(
                "lxc_proxy_runtime mutation_refused action=update profile=%s device=%s",
                profile_name,
                plan.device_name,
            )
            return False
        listen_result = await self.runner.run(
            _device_set_args(self.backend, profile_name, plan, "listen", plan.listen_endpoint),
            self.timeout_seconds,
        )
        self._log_command_result("update_listen", profile_name, plan, listen_result)
        if _command_failed(listen_result):
            return False
        connect_result = await self.runner.run(
            _device_set_args(self.backend, profile_name, plan, "connect", plan.target_endpoint),
            self.timeout_seconds,
        )
        self._log_command_result("update_connect", profile_name, plan, connect_result)
        return not _command_failed(connect_result)

    async def repair_stale_proxy_devices(
        self,
        profile_name: str,
        gateway_node: NodeSpec,
        plans: tuple[LxcProxyDevicePlan, ...],
    ) -> LxcProxyDriftRepairOutcome:
        if not self.allow_live_mutation:
            return LxcProxyDriftRepairOutcome(
                expected_profile_device_count=len(plans),
                mutation_allowed=False,
            )

        show_result = await self.runner.run(
            _instance_device_show_args(self.backend, gateway_node),
            self.timeout_seconds,
        )
        self._log_command_result("repair_show_instance_devices", profile_name, None, show_result)
        if _command_failed(show_result):
            return LxcProxyDriftRepairOutcome(
                expected_profile_device_count=len(plans),
                lookup_failure_count=1,
            )
        devices = _load_instance_devices(show_result.stdout)
        if devices is None:
            return LxcProxyDriftRepairOutcome(
                expected_profile_device_count=len(plans),
                lookup_failure_count=1,
            )

        expected_plans = {plan.device_name: plan for plan in plans}
        stale_devices = _project_proxy_device_names(devices)
        removed_devices: list[str] = []
        refused_devices: list[str] = []
        failed_devices: list[str] = []
        lookup_failure_count = 0
        remove_failure_count = 0

        for device_name in stale_devices:
            plan = expected_plans.get(device_name)
            device = devices[device_name]
            if plan is None or not _is_proxy_device(device):
                refused_devices.append(device_name)
                continue
            state = await self.inspect_proxy_device(profile_name, plan)
            if state == LxcProxyDeviceState.PRESENT:
                remove_result = await self.runner.run(
                    _instance_device_remove_args(self.backend, gateway_node, device_name),
                    self.timeout_seconds,
                )
                self._log_command_result(
                    "repair_remove_instance_device",
                    profile_name,
                    plan,
                    remove_result,
                )
                if _command_failed(remove_result):
                    remove_failure_count += 1
                    failed_devices.append(device_name)
                else:
                    removed_devices.append(device_name)
                continue
            refused_devices.append(device_name)
            if state == LxcProxyDeviceState.UNKNOWN:
                lookup_failure_count += 1

        return LxcProxyDriftRepairOutcome(
            expected_profile_device_count=len(plans),
            stale_direct_device_count=len(stale_devices),
            removed_count=len(removed_devices),
            refused_count=len(refused_devices),
            lookup_failure_count=lookup_failure_count,
            remove_failure_count=remove_failure_count,
            removed_devices=tuple(removed_devices),
            refused_devices=tuple(refused_devices),
            failed_devices=tuple(failed_devices),
        )

    def _log_command_result(
        self,
        action: str,
        profile_name: str,
        plan: LxcProxyDevicePlan | None,
        result: LxcNodeCommandResult,
    ) -> None:
        device_name = plan.device_name if plan is not None else ""
        listen_port = str(plan.listen_port) if plan is not None else ""
        log = self.logger.warning if _command_failed(result) else self.logger.info
        log(
            "lxc_proxy_runtime action=%s backend=%s profile=%s device=%s port=%s returncode=%s timed_out=%s stdout=%s stderr=%s",
            action,
            self.backend.value,
            profile_name,
            device_name,
            listen_port,
            result.returncode,
            str(result.timed_out).lower(),
            _safe_log_text(result.stdout),
            _safe_log_text(result.stderr),
        )


def _device_get_args(
    backend: ManagedLxcBackend,
    profile_name: str,
    plan: LxcProxyDevicePlan,
    key: str,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "profile",
        "device",
        "get",
        profile_name,
        plan.device_name,
        key,
    )


def _device_add_args(
    backend: ManagedLxcBackend,
    profile_name: str,
    plan: LxcProxyDevicePlan,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "profile",
        "device",
        "add",
        profile_name,
        plan.device_name,
        "proxy",
        f"listen={plan.listen_endpoint}",
        f"connect={plan.target_endpoint}",
    )


def _device_set_args(
    backend: ManagedLxcBackend,
    profile_name: str,
    plan: LxcProxyDevicePlan,
    key: str,
    value: str,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "profile",
        "device",
        "set",
        profile_name,
        plan.device_name,
        key,
        value,
    )


def _instance_device_show_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "config",
        "device",
        "show",
        node.name,
    )


def _instance_device_remove_args(
    backend: ManagedLxcBackend,
    node: NodeSpec,
    device_name: str,
) -> tuple[str, ...]:
    return (
        _BACKEND_CLI[backend],
        "config",
        "device",
        "remove",
        node.name,
        device_name,
    )


def _load_instance_devices(output: str) -> dict[str, Mapping[str, object]] | None:
    try:
        data = _YAML.load(output) or {}
    except YAMLError:
        return None
    if not isinstance(data, Mapping):
        return None
    devices: dict[str, Mapping[str, object]] = {}
    for name, raw_device in data.items():
        if isinstance(name, str) and isinstance(raw_device, Mapping):
            devices[name] = raw_device
    return devices


def _project_proxy_device_names(
    devices: Mapping[str, Mapping[str, object]],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            name
            for name in devices
            if _project_proxy_device_name(name)
        )
    )


def _project_proxy_device_name(device_name: str) -> bool:
    match = _PROJECT_PROXY_DEVICE_NAME_PATTERN.fullmatch(device_name)
    if match is None:
        return False
    return int(match.group("port")) <= 65535


def _is_proxy_device(device: Mapping[str, object]) -> bool:
    return str(device.get("type", "")).casefold() == "proxy"


def _command_failed(result: LxcNodeCommandResult) -> bool:
    return result.timed_out or result.returncode != 0


def _command_missing_device(result: LxcNodeCommandResult) -> bool:
    if result.timed_out or result.returncode == 0:
        return False
    output = _combined_output(result)
    return any(marker in output for marker in _MISSING_DEVICE_MARKERS)


def _combined_output(result: LxcNodeCommandResult) -> str:
    return f"{result.stdout}\n{result.stderr}".lower()


def _safe_log_text(value: str, limit: int = 400) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit]}..."
