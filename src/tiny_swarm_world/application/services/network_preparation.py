"""Exact-plan reconciliation with bounded effects and protected intent evidence."""
from __future__ import annotations

import asyncio

from tiny_swarm_world.application.ports.network_preparation import (
    NetworkPreparationFailure, NetworkPreparationPort,
)
from tiny_swarm_world.domain.network_preparation import (
    NetworkPreparationResult, NetworkSnapshot,
)


class NetworkPreparationService:
    def __init__(self, port: NetworkPreparationPort) -> None:
        self._port = port

    async def plan(self) -> NetworkSnapshot:
        return await asyncio.wait_for(self._port.inspect(), timeout=180)

    async def apply(self, plan: NetworkSnapshot, *, approved: bool) -> NetworkPreparationResult:
        if plan.blockers or not approved:
            return NetworkPreparationResult("BLOCKED", message="Explicit exact-plan consent is required.")
        current = await self.plan()
        if current != plan:
            return NetworkPreparationResult("BLOCKED", message="Network plan changed; review a fresh plan.")
        if not plan.actions:
            return NetworkPreparationResult("READY" if plan.verified else "BLOCKED")
        return await self._execute(plan)

    async def _execute(self, plan: NetworkSnapshot) -> NetworkPreparationResult:
        completed: list[str] = []
        uncertain: list[str] = []
        planned = tuple(action.id for action in plan.actions)
        expected = plan
        try:
            self._port.record("started", planned, (), ())
            for action in plan.actions:
                current = await self.plan()
                if current != expected or current.invariant != plan.invariant:
                    raise NetworkPreparationFailure("Network inventory changed; review a fresh plan.")
                self._port.record("pending", planned, tuple(completed), (action.id,))
                uncertain.append(action.id)
                await asyncio.wait_for(self._port.execute(action), timeout=action.timeout_seconds)
                if not await asyncio.wait_for(self._port.action_verified(action), timeout=180):
                    raise NetworkPreparationFailure("Network effect could not be verified.")
                completed.append(action.id)
                uncertain.remove(action.id)
                expected = await self.plan()
                if expected.blockers or expected.invariant != plan.invariant:
                    raise NetworkPreparationFailure("Network prerequisites changed after an effect.")
        except (asyncio.CancelledError, KeyboardInterrupt):
            self._finish("PARTIAL", planned, completed, uncertain, f"Interrupted at {uncertain[-1] if uncertain else 'network_preparation'}. Next: ./prepare_linux.sh --dry-run.", 130)
            raise
        except (NetworkPreparationFailure, OSError, RuntimeError, ValueError, TimeoutError) as error:
            transport = error.exit_code if isinstance(error, NetworkPreparationFailure) else None
            if isinstance(error, TimeoutError):
                transport = 124
            return self._finish("PARTIAL" if completed or uncertain else "FAILED", planned,
                                completed, uncertain, f"Stage {uncertain[-1] if uncertain else 'network_preparation'} stopped. Next: ./prepare_linux.sh --dry-run.", transport)
        return self._finish("READY" if expected.verified else "PARTIAL", planned, completed,
                            uncertain, "Prerequisites observed; endpoints and login remain unverified.")

    def _finish(self, status: str, planned: tuple[str, ...], completed: list[str],
                uncertain: list[str], message: str, transport: int | None = None) -> NetworkPreparationResult:
        try:
            path = self._port.record(status, planned, tuple(completed), tuple(uncertain), exit_code=transport)
        except OSError:
            path = None
            status = "PARTIAL" if completed or uncertain else "FAILED"
            message = "Protected network evidence could not be written; inspect before resuming."
        return NetworkPreparationResult(status, tuple(completed), tuple(uncertain), message, path, transport)
