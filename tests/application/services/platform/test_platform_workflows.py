import unittest

from tiny_swarm_world.application.services.platform import (
    DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION,
    PLATFORM_WORKFLOW_TAXONOMY,
    RESET_TINY_SWARM_PLATFORM_CONFIRMATION,
    PlatformDestroyWorkflow,
    PlatformInitWorkflow,
    PlatformReconcileWorkflow,
    PlatformResetWorkflow,
    PlatformVerifyWorkflow,
    PlatformWorkflowKind,
    PlatformWorkflowStatus,
)


class TestPlatformWorkflowTaxonomy(unittest.TestCase):
    def test_workflow_semantics_are_explicit(self):
        expected = {
            PlatformWorkflowKind.INIT: (True, False, False),
            PlatformWorkflowKind.RECONCILE: (True, False, False),
            PlatformWorkflowKind.RESET: (True, True, True),
            PlatformWorkflowKind.DESTROY: (True, True, True),
            PlatformWorkflowKind.VERIFY: (False, False, False),
        }

        self.assertEqual(set(expected), set(PLATFORM_WORKFLOW_TAXONOMY))
        for kind, (mutating, destructive, requires_confirmation) in expected.items():
            semantics = PLATFORM_WORKFLOW_TAXONOMY[kind]
            self.assertEqual(mutating, semantics.mutating)
            self.assertEqual(destructive, semantics.destructive)
            self.assertEqual(requires_confirmation, semantics.requires_confirmation)


class TestPlatformWorkflows(unittest.IsolatedAsyncioTestCase):
    async def test_init_and_reconcile_run_only_configured_safe_steps(self):
        init_step = _RecordingAction("init")
        reconcile_step = _RecordingAction("reconcile")

        init_result = await PlatformInitWorkflow([init_step]).run()
        reconcile_result = await PlatformReconcileWorkflow([reconcile_step]).run()

        self.assertEqual(["init"], init_step.calls)
        self.assertEqual(["reconcile"], reconcile_step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, init_result.status)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, reconcile_result.status)
        self.assertFalse(PlatformInitWorkflow.semantics.destructive)
        self.assertFalse(PlatformReconcileWorkflow.semantics.destructive)

    async def test_verify_is_non_mutating_and_runs_configured_safe_steps(self):
        verify_step = _RecordingAction("verify")

        result = await PlatformVerifyWorkflow([verify_step]).run()

        self.assertEqual(["verify"], verify_step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)
        self.assertFalse(PlatformVerifyWorkflow.semantics.mutating)
        self.assertFalse(PlatformVerifyWorkflow.semantics.destructive)

    async def test_reset_refuses_missing_or_wrong_confirmation_before_running_steps(self):
        destructive_step = _ForbiddenAction()
        workflow = PlatformResetWorkflow([destructive_step])

        missing_result = await workflow.run()
        wrong_result = await workflow.run("wrong")

        self.assertEqual(PlatformWorkflowStatus.REFUSED, missing_result.status)
        self.assertEqual(PlatformWorkflowStatus.REFUSED, wrong_result.status)
        self.assertFalse(missing_result.executed)
        self.assertFalse(wrong_result.executed)

    async def test_destroy_refuses_missing_or_wrong_confirmation_before_running_steps(self):
        destructive_step = _ForbiddenAction()
        workflow = PlatformDestroyWorkflow([destructive_step])

        missing_result = await workflow.run()
        wrong_result = await workflow.run("wrong")

        self.assertEqual(PlatformWorkflowStatus.REFUSED, missing_result.status)
        self.assertEqual(PlatformWorkflowStatus.REFUSED, wrong_result.status)
        self.assertFalse(missing_result.executed)
        self.assertFalse(wrong_result.executed)

    async def test_reset_and_destroy_confirmations_are_not_cross_accepted(self):
        reset_result = await PlatformResetWorkflow([_ForbiddenAction()]).run(
            DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION
        )
        destroy_result = await PlatformDestroyWorkflow([_ForbiddenAction()]).run(
            RESET_TINY_SWARM_PLATFORM_CONFIRMATION
        )

        self.assertEqual(PlatformWorkflowStatus.REFUSED, reset_result.status)
        self.assertEqual(PlatformWorkflowStatus.REFUSED, destroy_result.status)
        self.assertFalse(reset_result.executed)
        self.assertFalse(destroy_result.executed)

    async def test_reset_runs_steps_only_after_exact_confirmation(self):
        destructive_step = _RecordingAction("reset")

        result = await PlatformResetWorkflow([destructive_step]).run(
            RESET_TINY_SWARM_PLATFORM_CONFIRMATION
        )

        self.assertEqual(["reset"], destructive_step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)

    async def test_destroy_runs_steps_only_after_exact_confirmation(self):
        destructive_step = _RecordingAction("destroy")

        result = await PlatformDestroyWorkflow([destructive_step]).run(
            DESTROY_TINY_SWARM_PLATFORM_CONFIRMATION
        )

        self.assertEqual(["destroy"], destructive_step.calls)
        self.assertEqual(PlatformWorkflowStatus.COMPLETED, result.status)

    async def test_confirmed_reset_without_steps_is_blocked_until_policy_exists(self):
        result = await PlatformResetWorkflow().run(RESET_TINY_SWARM_PLATFORM_CONFIRMATION)

        self.assertEqual(PlatformWorkflowStatus.BLOCKED, result.status)
        self.assertFalse(result.executed)


class _RecordingAction:
    def __init__(self, name: str):
        self.name = name
        self.calls: list[str] = []

    async def run(self) -> object:
        self.calls.append(self.name)
        return self.name


class _ForbiddenAction:
    async def run(self) -> object:
        raise AssertionError("destructive step must not run without confirmation")


if __name__ == "__main__":
    unittest.main()
