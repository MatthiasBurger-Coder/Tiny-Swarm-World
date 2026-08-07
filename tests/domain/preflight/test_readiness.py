import unittest

from tiny_swarm_world.domain.preflight import (
    MAX_READINESS_ATTEMPTS,
    MAX_READINESS_TIMEOUT_SECONDS,
    ReadinessCheckResult,
    ReadinessProbeRequest,
    ReadinessStatus,
)


class TestReadinessContracts(unittest.TestCase):
    def test_probe_request_enforces_bounded_read_only_parameters(self):
        request = ReadinessProbeRequest(
            target_id="registry:reachable",
            timeout_seconds=2.5,
            max_attempts=2,
        )

        self.assertEqual(2.5, request.timeout_seconds)
        self.assertEqual(2, request.max_attempts)
        with self.assertRaises(ValueError):
            ReadinessProbeRequest(
                target_id="registry:reachable",
                timeout_seconds=MAX_READINESS_TIMEOUT_SECONDS + 1,
            )
        with self.assertRaises(ValueError):
            ReadinessProbeRequest(
                target_id="registry:reachable",
                max_attempts=MAX_READINESS_ATTEMPTS + 1,
            )

    def test_non_ready_statuses_remain_distinct_and_block_mutation(self):
        statuses = (
            ReadinessStatus.FAILED,
            ReadinessStatus.UNAVAILABLE,
            ReadinessStatus.TIMED_OUT,
            ReadinessStatus.UNKNOWN,
        )

        for status in statuses:
            with self.subTest(status=status):
                result = ReadinessCheckResult(
                    target_id="docker:manager",
                    status=status,
                    message="Readiness was not established.",
                    remediation="Resolve the prerequisite and retry the bounded check.",
                    evidence={"check_scope": "live"},
                )
                self.assertFalse(result.ready)
                self.assertTrue(result.blocks_mutation)
                self.assertEqual("live", result.to_dict()["evidence_scope"])
                self.assertEqual(status.value, result.to_dict()["status"])

    def test_result_rejects_raw_or_sensitive_evidence(self):
        with self.assertRaises(ValueError):
            ReadinessCheckResult(
                target_id="nexus:reachable",
                status=ReadinessStatus.READY,
                message="Nexus readiness established.",
                remediation="No remediation required.",
                evidence={"stdout": "raw output"},
            )


if __name__ == "__main__":
    unittest.main()
