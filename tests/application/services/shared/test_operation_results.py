import unittest

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure, OperationOutcome
from tiny_swarm_world.application.services.shared.operation_results import (
    aggregate_operation, failure_from_exception, failures_from_evidence,
    progress_from_evidence, progress_to_evidence,
)


class TestOperationAggregation(unittest.TestCase):
    def test_origin_failure_and_order_survive_parent_aggregation(self):
        first = OperationFailure.for_cause("image.publish", "image_publisher", "process_timeout")
        second = OperationFailure.for_cause("evidence.write", "repository", "filesystem_error")
        self.assertIs(first, failure_from_exception(OperationError(first), "outer", "parent"))
        result = aggregate_operation(
            OperationOutcome.BLOCKED, completed=("step.1",), pending=("step.3",),
            uncertain=("step.2",), failures=(first, second),
        )
        self.assertEqual(OperationOutcome.PARTIAL, result.outcome)
        evidence = progress_to_evidence(result)
        self.assertEqual((first, second), failures_from_evidence(evidence, allowed_origins=frozenset({("image.publish", "image_publisher"), ("evidence.write", "repository")})))
        self.assertEqual(("step.1",), progress_from_evidence(evidence, "completed", allowed_operations=frozenset({"step.1", "step.2", "step.3"})))
        self.assertEqual(("step.2",), progress_from_evidence(evidence, "uncertain", allowed_operations=frozenset({"step.1", "step.2", "step.3"})))

    def test_attempted_work_does_not_become_partial(self):
        failure = failure_from_exception(RuntimeError("private"), "step.1", "platform")
        result = aggregate_operation(OperationOutcome.BLOCKED, uncertain=("step.1",), failures=(failure,))
        self.assertEqual(OperationOutcome.FAILED, result.outcome)
        self.assertEqual("unexpected_failure", result.failures[0].cause)
        self.assertNotIn("private", str(result.to_dict()))

    def test_progress_and_failure_metadata_must_match_the_declared_contract(self):
        failure = OperationFailure.for_cause("image.publish", "image_publisher", "process_timeout")
        result = aggregate_operation(OperationOutcome.FAILED, uncertain=("step.1",), failures=(failure,))
        evidence = progress_to_evidence(result)
        with self.assertRaises(ValueError):
            progress_from_evidence(evidence, "uncertain", allowed_operations=frozenset({"other"}))
        evidence["failure_1_recommended_action"] = "untrusted action"
        with self.assertRaises(ValueError):
            failures_from_evidence(evidence)

    def test_duplicate_ids_are_rejected_instead_of_deduplicated(self):
        with self.assertRaises(ValueError):
            aggregate_operation(OperationOutcome.SUCCESS, completed=("step.1", "step.1"))

    def test_orphan_and_oversized_failure_fields_are_rejected(self):
        for evidence in ({"failure_1_operation": "secret"}, {"failure_" + "9" * 5000 + "_cause": "process_timeout"}, {"failure_operation": "secret"}):
            with self.subTest(keys=len(evidence)), self.assertRaises(ValueError):
                failures_from_evidence(evidence)

    def test_unknown_regex_valid_origin_is_not_promoted_and_legacy_uses_caller(self):
        secret = OperationFailure.for_cause("secret.value", "secret.component", "process_timeout")
        with self.assertRaises(ValueError):
            failures_from_evidence(progress_to_evidence(aggregate_operation(OperationOutcome.FAILED, failures=(secret,))))
        failure, = failures_from_evidence({"failure_cause": "process_timeout", "failure_operation": "secret.value", "failure_component": "secret.component"}, fallback_operation="caller.check", fallback_component="caller")
        self.assertEqual(("caller.check", "caller"), (failure.operation, failure.component))
