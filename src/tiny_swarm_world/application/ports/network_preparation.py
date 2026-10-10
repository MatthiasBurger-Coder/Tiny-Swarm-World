"""Capability boundary for separately approved network preparation."""
from typing import Protocol

from tiny_swarm_world.domain.network_preparation import NetworkAction, NetworkSnapshot


class NetworkPreparationFailure(RuntimeError):
    def __init__(self, code: str, *, exit_code: int | None = None) -> None:
        self.code = code
        self.exit_code = exit_code
        super().__init__(code)


class NetworkPreparationPort(Protocol):
    async def inspect(self) -> NetworkSnapshot: ...

    async def execute(self, action: NetworkAction) -> None: ...

    async def action_verified(self, action: NetworkAction) -> bool: ...

    def record(self, status: str, planned: tuple[str, ...], completed: tuple[str, ...],
               uncertain: tuple[str, ...], *, exit_code: int | None = None) -> str: ...
