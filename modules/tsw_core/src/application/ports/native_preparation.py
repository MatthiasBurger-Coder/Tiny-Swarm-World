"""Ports for native Linux qualification and package ownership."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from tiny_swarm_world.domain.native_preparation import NativeHostFacts


class NativeHostInspector(Protocol):
    def inspect(self) -> NativeHostFacts: ...


class HostPackageManager(Protocol):
    def missing(self, packages: tuple[str, ...]) -> tuple[str, ...]: ...

    def install(self, packages: tuple[str, ...]) -> None: ...


class HostPackagePreparationFailure(RuntimeError):
    """Safe failed substage and transport exit, without package command output."""

    def __init__(self, stage: str, exit_code: int, message: str) -> None:
        self.stage = stage
        self.exit_code = 128 - exit_code if exit_code < 0 else exit_code
        super().__init__(message)


PackageCandidateConsent = Callable[[tuple[str, ...]], bool]
PreparationTargetSnapshot = Callable[[], object]
