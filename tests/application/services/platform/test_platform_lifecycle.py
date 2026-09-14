import unittest
from unittest.mock import AsyncMock

from tiny_swarm_world.application.services.platform import (
    PlatformLifecycleOrchestrator,
    PlatformLifecycleRequest,
    PlatformLifecycleWorkflows,
    PlatformWorkflowKind,
    PlatformWorkflowResult,
    PlatformWorkflowStatus,
)


def _result(kind: PlatformWorkflowKind) -> PlatformWorkflowResult:
    return PlatformWorkflowResult(
        kind=kind,
        status=PlatformWorkflowStatus.COMPLETED,
        message="completed",
        executed=True,
    )


class TestPlatformLifecycleOrchestrator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.workflows = PlatformLifecycleWorkflows(
            init=AsyncMock(run=AsyncMock(return_value=_result(PlatformWorkflowKind.INIT))),
            reconcile=AsyncMock(
                run=AsyncMock(return_value=_result(PlatformWorkflowKind.RECONCILE))
            ),
            expose=AsyncMock(run=AsyncMock(return_value=_result(PlatformWorkflowKind.EXPOSE))),
            repair_lxc_proxy_drift=AsyncMock(
                run=AsyncMock(
                    return_value=_result(PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT)
                )
            ),
            verify=AsyncMock(run=AsyncMock(return_value=_result(PlatformWorkflowKind.VERIFY))),
            reset=AsyncMock(run=AsyncMock(return_value=_result(PlatformWorkflowKind.RESET))),
            destroy=AsyncMock(run=AsyncMock(return_value=_result(PlatformWorkflowKind.DESTROY))),
        )
        self.orchestrator = PlatformLifecycleOrchestrator(self.workflows)

    async def test_dispatches_non_destructive_lifecycle_actions(self):
        for kind in (
            PlatformWorkflowKind.INIT,
            PlatformWorkflowKind.RECONCILE,
            PlatformWorkflowKind.EXPOSE,
            PlatformWorkflowKind.REPAIR_LXC_PROXY_DRIFT,
            PlatformWorkflowKind.VERIFY,
        ):
            result = await self.orchestrator.run(PlatformLifecycleRequest(kind))
            self.assertEqual(kind, result.kind)

        self.workflows.init.run.assert_awaited_once_with()
        self.workflows.reconcile.run.assert_awaited_once_with()
        self.workflows.expose.run.assert_awaited_once_with()
        self.workflows.repair_lxc_proxy_drift.run.assert_awaited_once_with()
        self.workflows.verify.run.assert_awaited_once_with()

    async def test_passes_confirmation_only_to_destructive_actions(self):
        confirmation = "DESTROY_TINY_SWARM_PLATFORM"

        result = await self.orchestrator.run(
            PlatformLifecycleRequest(PlatformWorkflowKind.DESTROY, confirmation)
        )

        self.assertEqual(PlatformWorkflowKind.DESTROY, result.kind)
        self.workflows.destroy.run.assert_awaited_once_with(confirmation)

    async def test_rejects_unknown_lifecycle_action(self):
        with self.assertRaises(ValueError):
            await self.orchestrator.run(PlatformLifecycleRequest("unknown"))


if __name__ == "__main__":
    unittest.main()
