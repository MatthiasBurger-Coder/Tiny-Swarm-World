"""Consent-controlled, observed-effect reconciliation through an Incus port."""
from __future__ import annotations

import asyncio
from tiny_swarm_world.application.ports.incus_preparation import (
    IncusPreparationFailure, IncusPreparationPort,
)
from tiny_swarm_world.domain.incus_preparation import (
    IncusAction, IncusPreparationResult, IncusSnapshot,
)


class IncusPreparationService:
    def __init__(self, port: IncusPreparationPort) -> None:
        self._port = port

    async def plan(self) -> IncusSnapshot:
        return await self._port.inspect()

    async def apply(self, plan: IncusSnapshot, *, approved: bool) -> IncusPreparationResult:
        if not approved or plan.blockers:
            return IncusPreparationResult("BLOCKED", message="Review the plan and give explicit consent.")
        current = await self.plan()
        if current != plan:
            return IncusPreparationResult("BLOCKED", message="Incus plan changed; review again.")
        if current.restart_required:
            return IncusPreparationResult("RESTART_REQUIRED", message="Log out and log in; rerun ./prepare_linux.sh.")
        if not plan.actions:
            return IncusPreparationResult("READY" if current.verified else "BLOCKED")
        return await self._execute_plan(plan)

    async def _execute_plan(self, plan: IncusSnapshot) -> IncusPreparationResult:
        completed: list[str] = []
        uncertain: list[str] = []
        planned = tuple(action.id for action in plan.actions)
        expected = plan
        self._port.record("started", planned, (), ())
        try:
            for action in plan.actions:
                current = await self.plan()
                if current != expected:
                    return self._finish("PARTIAL" if completed else "BLOCKED", planned,
                                        completed, uncertain, "Incus inventory changed; review again.")
                # Persist intent before the command; interrupted mutations remain uncertain.
                uncertain.append(action.id)
                self._port.record("pending", planned, tuple(completed), tuple(uncertain))
                await self._port.execute(action)
                if not await self._port.action_verified(action):
                    raise IncusPreparationFailure("post_action_verification_failed")
                completed.append(action.id)
                uncertain.remove(action.id)
                expected = await self.plan()
                if expected.blockers:
                    return self._finish("PARTIAL", planned, completed, uncertain,
                                        "Incus verification blocked; inspect resources before retrying.")
        except (IncusPreparationFailure, OSError) as error:
            return await self._failure(action, planned, completed, uncertain, error)
        except (asyncio.CancelledError, KeyboardInterrupt):
            self._port.record("interrupted", planned, tuple(completed), tuple(uncertain))
            raise
        status = "PARTIAL"
        if expected.restart_required:
            status = "RESTART_REQUIRED"
        elif expected.verified:
            status = "READY"
        return self._finish(status, planned, completed, uncertain,
                            "Log out and log in; rerun ./prepare_linux.sh." if expected.restart_required
                            else "Reinventory and approve the next Incus stage; services are not verified.",
                            stage_complete=not expected.restart_required and not expected.verified)

    async def _failure(self, action: IncusAction, planned: tuple[str, ...],
                       completed: list[str], uncertain: list[str],
                       error: IncusPreparationFailure | OSError) -> IncusPreparationResult:
        try:
            if action.id in uncertain and await self._port.action_verified(action):
                completed.append(action.id)
                uncertain.remove(action.id)
        except (IncusPreparationFailure, OSError):
            pass
        status = "PARTIAL" if completed or uncertain else "FAILED"
        transport = error.exit_code if isinstance(error, IncusPreparationFailure) else None
        return self._finish(status, planned, completed, uncertain,
                            "Incus preparation stopped; inspect permissions/systemd/resources"
                            + (" and run sudo -v" if action.privilege == "sudo" else "")
                            + ", then ./prepare_linux.sh --dry-run.", transport)

    def _finish(self, status: str, planned: tuple[str, ...], completed: list[str],
                uncertain: list[str], message: str, transport: int | None = None,
                *, stage_complete: bool = False) -> IncusPreparationResult:
        try:
            path = self._port.record(status, planned, tuple(completed), tuple(uncertain))
        except OSError:
            return IncusPreparationResult("PARTIAL" if completed or uncertain else "FAILED",
                                          tuple(completed), tuple(uncertain), "Protected Incus evidence write failed.", transport)
        return IncusPreparationResult(status, tuple(completed), tuple(uncertain), message, transport, path, stage_complete)
