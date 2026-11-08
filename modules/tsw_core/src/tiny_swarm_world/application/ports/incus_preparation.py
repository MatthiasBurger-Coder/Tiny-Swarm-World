"""Technology-neutral boundary for the explicit Incus preparation capability."""
from __future__ import annotations

from typing import Protocol
from tiny_swarm_world.domain.incus_preparation import IncusAction, IncusSnapshot


class IncusPreparationFailure(RuntimeError):
    def __init__(self, code: str, *, exit_code: int | None = None) -> None:
        self.code = code
        self.exit_code = exit_code
        super().__init__(code)


class IncusPreparationPort(Protocol):
    async def inspect(self) -> IncusSnapshot: ...

    async def execute(self, action: IncusAction) -> None: ...

    async def action_verified(self, action: IncusAction) -> bool: ...

    def record(self, status: str, planned: tuple[str, ...], completed: tuple[str, ...],
               uncertain: tuple[str, ...], *, exit_code: int | None = None) -> str: ...
