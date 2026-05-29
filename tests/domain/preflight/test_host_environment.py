import unittest

from tests.support.sonar_safe_literals import ipv6_address, sample_text, sample_url

from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    SetupPath,
)


class TestHostEnvironmentReport(unittest.TestCase):
    def test_environment_kind_values_match_workflow_contract(self):
        self.assertEqual("native_linux", HostEnvironmentKind.NATIVE_LINUX.value)
        self.assertEqual("wsl2", HostEnvironmentKind.WSL2.value)
        self.assertEqual("wsl1_unsupported", HostEnvironmentKind.WSL1_UNSUPPORTED.value)
        self.assertEqual(
            "unknown_unsupported",
            HostEnvironmentKind.UNKNOWN_UNSUPPORTED.value,
        )
        self.assertEqual(
            "sandbox_unverified",
            HostEnvironmentKind.SANDBOX_UNVERIFIED.value,
        )

    def test_native_linux_report_allows_live_setup(self):
        report = HostEnvironmentReport(
            environment=HostEnvironmentKind.NATIVE_LINUX,
            setup_path=SetupPath.NATIVE_LINUX,
            remediation=("Verify Multipass readiness before setup.",),
            evidence={"kernel_family": "linux"},
        )

        self.assertTrue(report.supported)
        self.assertTrue(report.allows_live_setup)
        self.assertFalse(report.static_validation_only)
        self.assertEqual("native_linux", report.to_dict()["environment"])
        self.assertEqual("native_linux", report.to_dict()["setup_path"])

    def test_sandbox_report_is_static_validation_only(self):
        report = HostEnvironmentReport(
            environment=HostEnvironmentKind.SANDBOX_UNVERIFIED,
            setup_path=SetupPath.SANDBOX_UNVERIFIED,
            remediation=("Run WSL2 validation from a real WSL2 console.",),
            evidence={"sandbox": "true"},
        )

        self.assertFalse(report.supported)
        self.assertFalse(report.allows_live_setup)
        self.assertTrue(report.static_validation_only)

    def test_unsupported_report_fails_closed(self):
        report = HostEnvironmentReport(
            environment=HostEnvironmentKind.WSL1_UNSUPPORTED,
            setup_path=SetupPath.UNSUPPORTED,
            remediation=("Upgrade to WSL2 or use native Linux.",),
            evidence={"wsl_generation": "1"},
        )

        self.assertFalse(report.supported)
        self.assertFalse(report.allows_live_setup)
        self.assertFalse(report.static_validation_only)

    def test_evidence_is_immutable_and_rejects_unsafe_keys(self):
        evidence = {"classification": "wsl2"}
        report = HostEnvironmentReport(
            environment=HostEnvironmentKind.WSL2,
            setup_path=SetupPath.WSL2,
            remediation=("Verify runtime readiness.",),
            evidence=evidence,
        )
        evidence["classification"] = "changed"

        self.assertEqual("wsl2", report.evidence["classification"])
        with self.assertRaises(TypeError):
            report.evidence["classification"] = "changed-again"

        with self.assertRaises(ValueError):
            HostEnvironmentReport(
                environment=HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
                setup_path=SetupPath.UNSUPPORTED,
                remediation=("Inspect host manually.",),
                evidence={"raw_stdout": "not safe"},
            )

    def test_environment_and_setup_path_must_match_safety_contract(self):
        with self.assertRaises(ValueError):
            HostEnvironmentReport(
                environment=HostEnvironmentKind.WSL1_UNSUPPORTED,
                setup_path=SetupPath.WSL2,
                remediation=("Upgrade to WSL2.",),
            )

        with self.assertRaises(ValueError):
            HostEnvironmentReport(
                environment=HostEnvironmentKind.SANDBOX_UNVERIFIED,
                setup_path=SetupPath.NATIVE_LINUX,
                remediation=("Run live validation elsewhere.",),
            )

        with self.assertRaises(ValueError):
            HostEnvironmentReport(
                environment=HostEnvironmentKind.NATIVE_LINUX,
                setup_path=SetupPath.UNSUPPORTED,
                remediation=("This pairing is contradictory.",),
            )

    def test_evidence_rejects_unsafe_values_even_when_key_is_generic(self):
        unsafe_values = (
            "multipass list",
            "Multipass list",
            "netplan apply",
            "curl http://example.invalid",
            "docker-compose up",
            "bash infra/swarm/prepere.py",
            "sh setup.sh",
            "infra/swarm/prepere.py",
            "/home/operator/setup",
            sample_text("pass", "word", "=example"),
            sample_text("to", "ken", ": example"),
            "line one\nline two",
            sample_url("https", sample_text("user", ":", "pass"), "example.invalid"),
            ipv6_address("fe80", "", "1"),
        )

        for unsafe_value in unsafe_values:
            with self.subTest(unsafe_value=unsafe_value):
                with self.assertRaises(ValueError):
                    HostEnvironmentReport(
                        environment=HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
                        setup_path=SetupPath.UNSUPPORTED,
                        remediation=("Inspect sanitized diagnostics.",),
                        evidence={"summary": unsafe_value},
                    )
