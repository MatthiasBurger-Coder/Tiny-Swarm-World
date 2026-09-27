"""The shared contract rejects ambiguous progress and unsafe public failures."""
import unittest
from dataclasses import FrozenInstanceError

from tiny_swarm_world.application.ports.operation_result import (
    OperationError, OperationFailure, OperationOutcome, OperationResult, Recoverability,
)


def failure(cause="process_timeout"):
    return OperationFailure.for_cause("platform.apply", "command_runner", cause)


class TestOperationResult(unittest.TestCase):
    def test_valid_outcomes_and_origin_failures_serialize_independently(self):
        failures = (failure(), failure("verification_failed"))
        result = OperationResult(
            OperationOutcome.PARTIAL, failures, ("prepare",), ("verify",), ("apply",),
        )
        payload = result.to_dict()
        self.assertEqual("partial", payload["outcome"])
        self.assertEqual([item.to_dict() for item in failures], payload["failures"])
        payload["completed_operations"].append("invented")
        payload["failures"][0]["cause"] = "changed"
        self.assertEqual(["prepare"], result.to_dict()["completed_operations"])
        self.assertEqual("process_timeout", result.to_dict()["failures"][0]["cause"])
        for outcome in (OperationOutcome.BLOCKED, OperationOutcome.REFUSED):
            self.assertEqual(outcome.value, OperationResult(outcome).to_dict()["outcome"])
        self.assertEqual("success", OperationResult(OperationOutcome.SUCCESS).to_dict()["outcome"])
        restored = OperationResult(OperationOutcome.ROLLED_BACK, failures, rollback_verified=True)
        self.assertTrue(restored.rollback_verified)

    def test_invalid_outcome_combinations_are_rejected(self):
        cases = (
            dict(outcome=OperationOutcome.SUCCESS, failures=(failure(),)),
            dict(outcome=OperationOutcome.SUCCESS, pending_operations=("apply",)),
            dict(outcome=OperationOutcome.SUCCESS, uncertain_operations=("apply",)),
            dict(outcome=OperationOutcome.FAILED),
            dict(outcome=OperationOutcome.FAILED, failures=(failure(),), completed_operations=("prepare",)),
            dict(outcome=OperationOutcome.PARTIAL, failures=(failure(),), pending_operations=("apply",)),
            dict(outcome=OperationOutcome.PARTIAL, completed_operations=("prepare",), pending_operations=("apply",)),
            dict(outcome=OperationOutcome.PARTIAL, failures=(failure(),), completed_operations=("prepare",)),
            dict(outcome=OperationOutcome.ROLLED_BACK),
            dict(outcome=OperationOutcome.ROLLED_BACK, rollback_verified=True, uncertain_operations=("apply",)),
            dict(outcome=OperationOutcome.SUCCESS, rollback_verified=True),
            dict(outcome=OperationOutcome.BLOCKED, completed_operations=("prepare",)),
            dict(outcome=OperationOutcome.REFUSED, uncertain_operations=("apply",)),
            dict(outcome=OperationOutcome.FAILED, failures=(failure(),), pending_operations=("apply",), uncertain_operations=("apply",)),
        )
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                OperationResult(**kwargs)

    def test_immutable_values_require_typed_immutable_fields(self):
        item = failure()
        with self.assertRaises(FrozenInstanceError):
            item.cause = "changed"
        with self.assertRaises(FrozenInstanceError):
            OperationResult(OperationOutcome.SUCCESS).outcome = OperationOutcome.FAILED
        for kwargs in (
            dict(outcome="success"),
            dict(outcome=OperationOutcome.SUCCESS, completed_operations=[]),
            dict(outcome=OperationOutcome.FAILED, failures=(RuntimeError("private"),)),
            dict(outcome=OperationOutcome.SUCCESS, rollback_verified=1),
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises((TypeError, ValueError)):
                OperationResult(**kwargs)

    def test_failures_use_only_catalogue_actions_and_constrained_identifiers(self):
        item = failure("launch_permission_denied")
        self.assertEqual(Recoverability.NONRECOVERABLE, item.recoverability)
        self.assertEqual(Recoverability.UNKNOWN, failure().recoverability)
        for operation in ("/home/private", "echo password", "TOKEN=value", "", "x" * 129):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                OperationFailure.for_cause(operation, "command_runner", "process_timeout")
        with self.assertRaises(ValueError):
            failure("raw exception text")
        with self.assertRaises(ValueError):
            OperationFailure("apply", "runner", "process_timeout", Recoverability.UNKNOWN, "private diagnostic")
        error = OperationError(item)
        self.assertIs(item, error.failure)
        self.assertIn(item.cause, str(error))
        self.assertIn(item.recommended_action, str(error))
