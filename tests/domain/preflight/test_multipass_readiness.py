import unittest

from tiny_swarm_world.domain.multipass.readiness import (
    MultipassReadinessReport,
    MultipassReadinessStatus,
)


class TestMultipassReadinessReport(unittest.TestCase):
    def test_ready_status_reports_ready(self):
        report = MultipassReadinessReport(
            status=MultipassReadinessStatus.READY,
            remediation=("Proceed to guarded setup.",),
            evidence={"driver": "qemu", "version_seen": "true"},
        )

        self.assertTrue(report.ready)
        self.assertEqual("ready", report.to_dict()["status"])
        self.assertEqual("qemu", report.to_dict()["evidence"]["driver"])

    def test_blocked_status_reports_not_ready_with_remediation(self):
        report = MultipassReadinessReport(
            status=MultipassReadinessStatus.DRIVER_MISMATCH,
            remediation=("Select the qemu driver before live setup.",),
            evidence={"expected_driver": "qemu", "driver_match": "false"},
        )

        self.assertFalse(report.ready)
        self.assertEqual(
            ("Select the qemu driver before live setup.",),
            report.remediation,
        )

    def test_evidence_is_immutable_and_rejects_unsafe_keys(self):
        evidence = {"socket_access": "denied"}
        report = MultipassReadinessReport(
            status=MultipassReadinessStatus.SOCKET_PERMISSION_DENIED,
            remediation=("Review Multipass socket permissions.",),
            evidence=evidence,
        )
        evidence["socket_access"] = "changed"

        self.assertEqual("denied", report.evidence["socket_access"])
        with self.assertRaises(TypeError):
            report.evidence["socket_access"] = "changed-again"

        with self.assertRaises(ValueError):
            MultipassReadinessReport(
                status=MultipassReadinessStatus.UNKNOWN_FAILURE,
                remediation=("Inspect sanitized diagnostics.",),
                evidence={"command": "not safe"},
            )
