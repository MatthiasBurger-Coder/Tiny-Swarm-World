"""Durable batch and existing Classic runtime boundaries."""
from contextlib import AbstractContextManager
from typing import Protocol

from tiny_swarm_world.domain.lifecycle.update_execution import UpdateBatch, UpdateStage
from tiny_swarm_world.domain.preflight import LiveConsent


class UpdateJournal(Protocol):
    def exclusive(self) -> AbstractContextManager[None]: ...
    def load(self) -> UpdateBatch | None: ...
    def save(self, batch: UpdateBatch) -> None: ...


class ComponentRuntime(Protocol):
    def validate(self, stages: tuple[UpdateStage, ...]) -> None: ...
    async def transition(self, stage: UpdateStage, consent: LiveConsent, *, recovery: bool) -> bool: ...
