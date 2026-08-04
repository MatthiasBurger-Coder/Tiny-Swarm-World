"""Host adapters with lazy exports to keep the installer bootstrap lightweight."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "HostEnvironmentDetector": (
        "tiny_swarm_world.infrastructure.adapters.host.host_environment_detector",
        "HostEnvironmentDetector",
    ),
    "LinuxHostSignalReader": (
        "tiny_swarm_world.infrastructure.adapters.host.linux_host_signal_reader",
        "LinuxHostSignalReader",
    ),
    "LinuxHostSignals": (
        "tiny_swarm_world.infrastructure.adapters.host.linux_host_signal_reader",
        "LinuxHostSignals",
    ),
    "ProjectFilesystemInspector": (
        "tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector",
        "ProjectFilesystemInspector",
    ),
    "WslHostSignalReader": (
        "tiny_swarm_world.infrastructure.adapters.host.wsl_host_signal_reader",
        "WslHostSignalReader",
    ),
    "WslHostSignals": (
        "tiny_swarm_world.infrastructure.adapters.host.wsl_host_signal_reader",
        "WslHostSignals",
    ),
    "NativeLinuxHostPreparation": (
        "tiny_swarm_world.infrastructure.adapters.host.native_linux_host_preparation",
        "NativeLinuxHostPreparation",
    ),
    "WindowsCommandRunner": (
        "tiny_swarm_world.infrastructure.adapters.host.windows_command_runner",
        "WindowsCommandRunner",
    ),
    "WslHostPreparation": (
        "tiny_swarm_world.infrastructure.adapters.host.wsl_host_preparation",
        "WslHostPreparation",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    module = import_module(module_name)
    value = getattr(module, attribute_name)
    globals()[name] = value
    return value
