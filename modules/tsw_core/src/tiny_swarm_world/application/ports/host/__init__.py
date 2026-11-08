"""Host ports with lazy exports for the dependency-light installer bootstrap."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "PortHostEnvironmentDetector": (
        "tiny_swarm_world.application.ports.host.port_host_environment_detector",
        "PortHostEnvironmentDetector",
    ),
    "PortProjectFilesystemInspector": (
        "tiny_swarm_world.application.ports.host.port_project_filesystem_inspector",
        "PortProjectFilesystemInspector",
    ),
    "PortHostPreparation": (
        "tiny_swarm_world.application.ports.host.port_host_preparation",
        "PortHostPreparation",
    ),
    "PortWindowsCommandRunner": (
        "tiny_swarm_world.application.ports.host.port_windows_command_runner",
        "PortWindowsCommandRunner",
    ),
    "WindowsCommandResult": (
        "tiny_swarm_world.application.ports.host.port_windows_command_runner",
        "WindowsCommandResult",
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
