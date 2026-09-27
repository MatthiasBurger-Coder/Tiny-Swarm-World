"""Ports for native Linux qualification and package ownership."""

from __future__ import annotations

from typing import Protocol

from tiny_swarm_world.domain.native_preparation import NativeHostFacts


class NativeHostInspector(Protocol):
    def inspect(self) -> NativeHostFacts: ...


class HostPackageManager(Protocol):
    def missing(self, packages: tuple[str, ...]) -> tuple[str, ...]: ...

    def install(self, packages: tuple[str, ...]) -> None: ...
