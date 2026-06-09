import unittest

from tests.support.sonar_safe_literals import sample_text

from tiny_swarm_world.domain.ingress import (
    IngressDiscoveryCategory,
    IngressDiscoveryFinding,
    IngressDiscoverySnapshot,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class TestIngressDiscoveryModels(unittest.TestCase):
    def test_snapshot_round_trips_redacted_runtime_findings(self):
        verification = VerificationResult(
            target_id="ingress:discovery",
            status=VerificationStatus.VERIFIED,
            message="Ingress discovery summarized.",
            evidence={"classification": "baseline_collected"},
        )
        snapshot = IngressDiscoverySnapshot(
            findings=(
                IngressDiscoveryFinding(
                    category=IngressDiscoveryCategory.GIT,
                    name="branch",
                    status="present",
                    summary="Workflow branch active.",
                    verification=verification,
                ),
                IngressDiscoveryFinding(
                    category=IngressDiscoveryCategory.TRAEFIK,
                    name="stack",
                    status="not_checked",
                    summary="Traefik stack discovery pending.",
                ),
            ),
            verification_results=(verification,),
        )

        round_tripped = IngressDiscoverySnapshot.from_dict(snapshot.to_dict())

        self.assertEqual(snapshot, round_tripped)
        self.assertEqual(
            ("stack",),
            tuple(
                finding.name
                for finding in round_tripped.by_category(IngressDiscoveryCategory.TRAEFIK)
            ),
        )

    def test_finding_rejects_raw_command_output_and_sensitive_values(self):
        unsafe_values = (
            "stdout: raw output",
            "docker ps",
            "incus list",
            sample_text("TLS_", "SECRET", "=hidden"),
            "line one\nline two",
        )

        for unsafe_value in unsafe_values:
            with self.subTest(unsafe_value=unsafe_value):
                with self.assertRaises(ValueError):
                    IngressDiscoveryFinding(
                        category=IngressDiscoveryCategory.DOCKER,
                        name="runtime",
                        summary=unsafe_value,
                    )

    def test_finding_rejects_local_topology_values(self):
        unsafe_values = (
            "manager at 127.0.0.1",
            "manager at 10.0.3.2",
            "manager at 172.16.0.4",
            "manager at 192.168.1.10",
            "certificate at /home/operator/certs/ingress.crt",
            "socket at /var/run/docker.sock",
            "certificate at C:\\Users\\operator\\ingress.crt",
        )

        for unsafe_value in unsafe_values:
            with self.subTest(unsafe_value=unsafe_value):
                with self.assertRaises(ValueError):
                    IngressDiscoveryFinding(
                        category=IngressDiscoveryCategory.NETWORK,
                        name="topology",
                        summary=unsafe_value,
                    )

    def test_snapshot_rejects_unknown_schema_version(self):
        with self.assertRaises(ValueError):
            IngressDiscoverySnapshot(schema_version="2")

    def test_snapshot_collection_fields_reject_plain_strings(self):
        with self.assertRaises(ValueError):
            IngressDiscoverySnapshot.from_dict({"schema_version": "1", "findings": "raw"})


if __name__ == "__main__":
    unittest.main()
