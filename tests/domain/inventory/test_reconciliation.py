import unittest

from tiny_swarm_world.domain.inventory import (
    CurrentState,
    DesiredState,
    ReconcileActionKind,
    ReconcilePlanner,
    ReconcileResourceKind,
    ReconcileResult,
    ReconcileResultStatus,
    VmDesiredState,
    VmObservedState,
)


class TestReconciliation(unittest.TestCase):
    def test_plans_create_update_remove_and_noop_without_infrastructure(self):
        plan = ReconcilePlanner().plan(
            DesiredState(
                vms=(VmDesiredState("manager", role="manager"),),
                stacks=("traefik", "swagger"),
                artifact_registries=("nexus",),
            ),
            CurrentState(
                vms=(VmObservedState("manager", role="worker"), VmObservedState("old")),
                stacks=(),
            ),
        )

        self.assertEqual(
            [(action.resource_kind, action.resource_name, action.kind) for action in plan.actions],
            [
                (ReconcileResourceKind.ARTIFACT_REGISTRY, "nexus", ReconcileActionKind.CREATE),
                (ReconcileResourceKind.STACK, "swagger", ReconcileActionKind.CREATE),
                (ReconcileResourceKind.STACK, "traefik", ReconcileActionKind.CREATE),
                (ReconcileResourceKind.VM, "manager", ReconcileActionKind.UPDATE),
                (ReconcileResourceKind.VM, "old", ReconcileActionKind.REMOVE),
            ],
        )

    def test_equivalent_inputs_produce_identical_sorted_plans(self):
        desired = DesiredState(stacks=("b", "a"))
        current = CurrentState()

        first = ReconcilePlanner().plan(desired, current)
        second = ReconcilePlanner().plan(desired, current)

        self.assertEqual(first, second)
        self.assertEqual([action.resource_name for action in first.actions], ["a", "b"])

    def test_empty_states_produce_explainable_noop(self):
        plan = ReconcilePlanner().plan(DesiredState(), CurrentState())

        self.assertTrue(plan.is_noop)
        self.assertEqual(plan.actions[0].kind, ReconcileActionKind.NOOP)

    def test_result_is_execution_data_and_does_not_execute_plan(self):
        action = ReconcilePlanner().plan(DesiredState(), CurrentState()).actions[0]
        result = ReconcileResult(action, ReconcileResultStatus.SKIPPED, "preview only")

        self.assertTrue(result.succeeded)
        self.assertEqual(result.status, ReconcileResultStatus.SKIPPED)
