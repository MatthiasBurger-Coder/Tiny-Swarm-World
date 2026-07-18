import unittest

from tests.support.sonar_safe_literals import ipv6_address, sample_text, sample_url

from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    HostEnvironmentSignals,
    SetupPath,
    classify_host_environment,
)


class TestHostEnvironmentReport(unittest.TestCase):
    def test_legacy_preflight_modules_reexport_identical_host_types_and_sanitizer(self):
        from tiny_swarm_world.domain.host_environment import (
            HostEnvironmentReport as DirectHostEnvironmentReport,
        )
        from tiny_swarm_world.domain.preflight.host_environment import (
            HostEnvironmentReport as LegacyHostEnvironmentReport,
        )
        from tiny_swarm_world.domain.preflight.sanitized_evidence import (
            sanitized_evidence as legacy_sanitized_evidence,
        )
        from tiny_swarm_world.domain.sanitized_evidence import (
            sanitized_evidence as direct_sanitized_evidence,
        )

        self.assertIs(DirectHostEnvironmentReport, LegacyHostEnvironmentReport)
        self.assertIs(direct_sanitized_evidence, legacy_sanitized_evidence)

    def test_environment_kind_values_match_workflow_contract(self):
        self.assertEqual(HostEnvironmentKind.NATIVE_LINUX.value, "native_linux")
        self.assertEqual(HostEnvironmentKind.WSL2.value, "wsl2")
        self.assertEqual(HostEnvironmentKind.WSL1_UNSUPPORTED.value, "wsl1_unsupported")
        self.assertEqual(
            HostEnvironmentKind.UNKNOWN_UNSUPPORTED.value,
            "unknown_unsupported",
        )
        self.assertEqual(
            HostEnvironmentKind.SANDBOX_UNVERIFIED.value,
            "sandbox_unverified",
        )

    def test_native_linux_report_allows_live_setup(self):
        report = HostEnvironmentReport(
            environment=HostEnvironmentKind.NATIVE_LINUX,
            setup_path=SetupPath.NATIVE_LINUX,
            remediation=("Verify provider readiness before setup.",),
            evidence={"kernel_family": "linux"},
        )

        self.assertTrue(report.supported)
        self.assertTrue(report.allows_live_setup)
        self.assertFalse(report.static_validation_only)
        self.assertEqual(report.to_dict()["environment"], "native_linux")
        self.assertEqual(report.to_dict()["setup_path"], "native_linux")

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

        self.assertEqual(report.evidence["classification"], "wsl2")
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
            "incus list",
            "lxc list",
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


class TestHostEnvironmentClassification(unittest.TestCase):
    def test_classifies_native_linux_with_typed_host_fields(self):
        report = classify_host_environment(_signals())

        self.assertEqual(HostEnvironmentKind.NATIVE_LINUX, report.environment)
        self.assertEqual(report.distribution, "Ubuntu 24.04 LTS")
        self.assertEqual(report.kernel_release, "6.8.0-generic")
        self.assertFalse(report.windows_interop_available)
        self.assertTrue(report.supported)

    def test_classifies_wsl1_as_explicitly_unsupported(self):
        report = classify_host_environment(
            _signals(
                kernel_release="4.4.0-19041-Microsoft",
                proc_version="Linux version 4.4.0-19041-Microsoft",
                wsl_distribution="Ubuntu",
                windows_interop_available=True,
            )
        )

        self.assertEqual(HostEnvironmentKind.WSL1_UNSUPPORTED, report.environment)
        self.assertEqual(SetupPath.UNSUPPORTED, report.setup_path)
        self.assertFalse(report.allows_live_setup)

    def test_classifies_wsl2_with_typed_host_fields(self):
        report = classify_host_environment(
            _signals(
                kernel_release="6.1.21.2-microsoft-standard-WSL2",
                proc_version="Linux version 6.1.21.2-microsoft-standard-WSL2",
                wsl_distribution="Ubuntu-24.04",
                windows_interop_available=True,
            )
        )

        self.assertEqual(HostEnvironmentKind.WSL2, report.environment)
        self.assertEqual(report.distribution, "Ubuntu-24.04")
        self.assertEqual(report.kernel_release, "6.1.21.2-microsoft-standard-WSL2")
        self.assertTrue(report.windows_interop_available)

    def test_confirmed_wsl2_without_interop_keeps_host_type(self):
        report = classify_host_environment(
            _signals(
                kernel_release="6.1.21.2-microsoft-standard-WSL2",
                proc_version="Linux version 6.1.21.2-microsoft-standard-WSL2",
                wsl_distribution="Ubuntu",
                windows_interop_available=False,
            )
        )

        self.assertEqual(HostEnvironmentKind.WSL2, report.environment)
        self.assertFalse(report.windows_interop_available)

    def test_wsl_kernel_without_independent_signal_is_unsupported(self):
        report = classify_host_environment(
            _signals(
                kernel_release="6.1.21.2-microsoft-standard-WSL2",
                proc_version="",
                wsl_distribution="",
            )
        )

        self.assertEqual(HostEnvironmentKind.UNKNOWN_UNSUPPORTED, report.environment)
        self.assertEqual(report.evidence["classification"], "wsl_unknown")

    def test_wsl_environment_without_kernel_signal_is_unsupported(self):
        report = classify_host_environment(
            _signals(
                kernel_release="6.8.0-generic",
                proc_version="Linux version 6.8.0-generic",
                wsl_distribution="Ubuntu",
            )
        )

        self.assertEqual(HostEnvironmentKind.UNKNOWN_UNSUPPORTED, report.environment)

    def test_conflicting_wsl_generations_are_unsupported(self):
        report = classify_host_environment(
            _signals(
                kernel_release="6.1.21.2-microsoft-standard-WSL2",
                proc_version="Linux version 4.4.0-19041-Microsoft",
                wsl_distribution="Ubuntu",
                windows_interop_available=True,
            )
        )

        self.assertEqual(HostEnvironmentKind.UNKNOWN_UNSUPPORTED, report.environment)
        self.assertEqual(report.evidence["wsl_generation"], "unknown")

    def test_missing_kernel_files_is_sandbox_unverified(self):
        report = classify_host_environment(
            _signals(kernel_release="", proc_version="")
        )

        self.assertEqual(HostEnvironmentKind.SANDBOX_UNVERIFIED, report.environment)
        self.assertTrue(report.static_validation_only)

    def test_container_or_ci_signal_takes_precedence_over_wsl(self):
        for sandbox_signal in ("container_marker", "ci_marker"):
            with self.subTest(sandbox_signal=sandbox_signal):
                report = classify_host_environment(
                    _signals(
                        kernel_release="6.1.21.2-microsoft-standard-WSL2",
                        wsl_distribution="Ubuntu",
                        windows_interop_available=True,
                        sandbox_signal=sandbox_signal,
                    )
                )

                self.assertEqual(
                    HostEnvironmentKind.SANDBOX_UNVERIFIED,
                    report.environment,
                )

    def test_non_linux_platform_is_unknown_unsupported(self):
        report = classify_host_environment(
            _signals(platform_family="darwin")
        )

        self.assertEqual(HostEnvironmentKind.UNKNOWN_UNSUPPORTED, report.environment)
        self.assertEqual(SetupPath.UNSUPPORTED, report.setup_path)

    def test_report_to_dict_has_stable_typed_schema_without_raw_signals(self):
        raw_proc_signal = "Linux version 6.1.21.2-microsoft-standard-WSL2 synthetic-build-data"
        report = classify_host_environment(
            _signals(
                kernel_release="6.1.21.2-microsoft-standard-WSL2",
                proc_version=raw_proc_signal,
                wsl_distribution="Ubuntu",
                windows_interop_available=False,
            )
        )

        payload = report.to_dict()

        self.assertEqual(
            set(payload),
            {
                "allows_live_setup",
                "distribution",
                "environment",
                "evidence",
                "kernel_release",
                "platform_family",
                "remediation",
                "setup_path",
                "static_validation_only",
                "supported",
                "windows_interop_available",
            },
        )
        self.assertNotIn(raw_proc_signal, str(payload))


def _signals(**overrides: object) -> HostEnvironmentSignals:
    values: dict[str, object] = {
        "platform_family": "linux",
        "distribution": "Ubuntu 24.04 LTS",
        "kernel_release": "6.8.0-generic",
        "proc_version": "Linux version 6.8.0-generic",
        "wsl_distribution": "",
        "windows_interop_available": False,
        "sandbox_signal": "",
    }
    values.update(overrides)
    return HostEnvironmentSignals(**values)  # type: ignore[arg-type]
