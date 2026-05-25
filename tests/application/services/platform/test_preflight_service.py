import unittest
from dataclasses import replace
from collections.abc import Mapping, Sequence

from tiny_swarm_world.application.ports.preflight import PortHostPreflightProbe
from tiny_swarm_world.application.services.platform.preflight_service import PreflightService
from tiny_swarm_world.domain.preflight import (
    LiveConsent,
    PreflightSeverity,
    RequiredPort,
    RequiredSecret,
    SetupManifest,
    SetupPortRequirement,
    SetupProfile,
    SetupSecretRequirement,
    SetupServiceRequirement,
    default_preflight_configuration,
)


class TestPreflightService(unittest.IsolatedAsyncioTestCase):
    async def test_successful_preflight_reports_passed_checks(self):
        result = await PreflightService(_FakeProbe()).run(
            LiveConsent(live_flag=True, confirmed=True)
        )

        check_ids = {check.check_id for check in result.checks}
        self.assertTrue(result.passed)
        self.assertEqual("PASSED", result.status)
        self.assertEqual("full", result.to_dict()["setup_profile"])
        self.assertIn("SETUP-MANIFEST", check_ids)
        self.assertIn("LIVE-CONSENT", check_ids)
        self.assertIn("PYTHON", check_ids)
        self.assertIn("DEPENDENCY-python3", check_ids)
        self.assertIn("SECRET-TSW_PORTAINER_PASSWORD", check_ids)

    async def test_static_preflight_can_run_without_live_consent_check(self):
        result = await PreflightService(_FakeProbe()).run()

        check_ids = {check.check_id for check in result.checks}
        self.assertTrue(result.passed)
        self.assertNotIn("LIVE-CONSENT", check_ids)

    async def test_preflight_reports_selected_setup_profile_and_manifest(self):
        configuration = default_preflight_configuration(SetupProfile.RESOURCE_GATED)
        result = await PreflightService(_FakeProbe(), configuration).run()

        manifest = result.to_dict()["manifest"]
        self.assertEqual("resource-gated", result.to_dict()["setup_profile"])
        self.assertEqual("resource-gated", manifest["profile"])
        self.assertIn("Portainer", manifest["services"])

    async def test_custom_manifest_drives_port_and_secret_checks(self):
        manifest = SetupManifest(
            profile=SetupProfile.FULL,
            evidence_root=".tiny-swarm-world/evidence/custom",
            services=(
                SetupServiceRequirement(
                    "Custom",
                    ports=(SetupPortRequirement(12345, "Custom"),),
                    secrets=(SetupSecretRequirement("TSW_CUSTOM_SECRET", "Custom"),),
                ),
            ),
        )
        configuration = replace(
            default_preflight_configuration(),
            setup_manifest=manifest,
            required_ports=tuple(
                RequiredPort(port.port, port.service)
                for port in manifest.required_ports
            ),
            required_secrets=tuple(
                RequiredSecret(secret.name, secret.service)
                for secret in manifest.required_secrets
            ),
        )

        result = await PreflightService(_FakeProbe(), configuration).run()
        check_ids = {check.check_id for check in result.checks}

        self.assertIn("PORT-12345", check_ids)
        self.assertIn("SECRET-TSW_CUSTOM_SECRET", check_ids)
        self.assertNotIn("PORT-9000", check_ids)
        self.assertNotIn("SECRET-TSW_PORTAINER_PASSWORD", check_ids)

    async def test_incomplete_live_consent_fails_preflight(self):
        result = await PreflightService(_FakeProbe()).run(
            LiveConsent(live_flag=True, confirmed=False)
        )

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertFalse(result.passed)
        self.assertIn("LIVE-CONSENT", failed_by_id)
        self.assertIn(
            "missing live confirmation",
            failed_by_id["LIVE-CONSENT"].evidence["missing"],
        )

    async def test_missing_dependency_and_secret_are_actionable_failures(self):
        configuration = replace(default_preflight_configuration(), static_secret_defaults=())
        probe = _FakeProbe(
            executable_availability={"docker": False},
            secret_availability={"TSW_NEXUS_ADMIN_PASSWORD": False},
        )

        result = await PreflightService(probe, configuration).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertFalse(result.passed)
        self.assertIn("DEPENDENCY-docker", failed_by_id)
        self.assertIn("SECRET-TSW_NEXUS_ADMIN_PASSWORD", failed_by_id)
        self.assertIn("Install 'docker'", failed_by_id["DEPENDENCY-docker"].remediation)
        self.assertIn(
            "Provide the secret",
            failed_by_id["SECRET-TSW_NEXUS_ADMIN_PASSWORD"].remediation,
        )

    async def test_static_local_secret_defaults_satisfy_missing_environment_secrets(self):
        result = await PreflightService(
            _FakeProbe(secret_availability={"TSW_NEXUS_ADMIN_PASSWORD": False})
        ).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        secret_check = checks_by_id["SECRET-TSW_NEXUS_ADMIN_PASSWORD"]

        self.assertTrue(result.passed)
        self.assertEqual("static_local_default", secret_check.evidence["source"])
        self.assertNotIn("password_value", repr(secret_check.to_dict()).lower())

    async def test_host_port_and_ignore_policy_failures_are_reported(self):
        result = await PreflightService(
            _FakeProbe(
                host_compatible=False,
                port_availability={80: False},
                ignored_paths={".env": False},
            )
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertFalse(result.passed)
        self.assertIn("HOST", failed_by_id)
        self.assertIn("PORT-80", failed_by_id)
        self.assertIn("IGNORE-.env", failed_by_id)
        self.assertIn("Run Tiny Swarm World from Linux or WSL", failed_by_id["HOST"].remediation)

    async def test_occupied_port_passes_when_expected_service_is_detected(self):
        result = await PreflightService(
            _FakeProbe(
                port_availability={9000: False},
                expected_service_ports={9000: True},
            )
        ).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        port_check = checks_by_id["PORT-9000"]

        self.assertTrue(result.passed)
        self.assertEqual("PASSED", port_check.status)
        self.assertEqual("existing_expected_service", port_check.evidence["source"])

    async def test_occupied_unknown_port_still_fails_preflight(self):
        result = await PreflightService(
            _FakeProbe(
                port_availability={9000: False},
                expected_service_ports={9000: False},
            )
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("PORT-9000", failed_by_id)
        self.assertIn("occupied", failed_by_id["PORT-9000"].message)

    async def test_resource_failures_are_resource_gated(self):
        result = await PreflightService(
            _FakeProbe(cpu_count_value=2, memory_bytes_value=8, disk_free_bytes_value=8)
        ).run()

        resource_failures = [
            check
            for check in result.failed_checks
            if check.check_id in {"RESOURCE-CPU", "RESOURCE-MEMORY", "RESOURCE-DISK"}
        ]
        self.assertEqual(3, len(resource_failures))
        self.assertEqual("RESOURCE_GATED", result.status)
        self.assertTrue(
            all(check.severity == PreflightSeverity.RESOURCE_GATED for check in resource_failures)
        )

    async def test_mandatory_failure_keeps_resource_failures_from_resource_gated_status(self):
        result = await PreflightService(
            _FakeProbe(
                executable_availability={"docker": False},
                cpu_count_value=2,
                memory_bytes_value=8,
                disk_free_bytes_value=8,
            )
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertEqual("FAILED", result.status)
        self.assertIn("DEPENDENCY-docker", failed_by_id)
        self.assertIn("RESOURCE-CPU", failed_by_id)

    async def test_forbidden_secret_fingerprint_failures_report_ids_only(self):
        result = await PreflightService(
            _FakeProbe(forbidden_fingerprints=("legacy-nexus-admin-password",))
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        failure = failed_by_id["SECRET-FORBIDDEN-FINGERPRINTS"]
        self.assertEqual("legacy-nexus-admin-password", failure.evidence["fingerprint_ids"])

    async def test_python_version_below_baseline_fails_preflight(self):
        result = await PreflightService(_FakeProbe(python_version_value="3.11.9")).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertIn("PYTHON", failed_by_id)
        self.assertEqual("3.11.9", failed_by_id["PYTHON"].evidence["actual"])


class _FakeProbe(PortHostPreflightProbe):
    def __init__(
        self,
        executable_availability: dict[str, bool] | None = None,
        secret_availability: dict[str, bool] | None = None,
        forbidden_fingerprints: tuple[str, ...] = (),
        host_compatible: bool = True,
        port_availability: dict[int, bool] | None = None,
        expected_service_ports: dict[int, bool] | None = None,
        ignored_paths: dict[str, bool] | None = None,
        cpu_count_value: int = 8,
        memory_bytes_value: int = 32 * 1024**3,
        disk_free_bytes_value: int = 120 * 1024**3,
        python_version_value: str = "3.12.3",
    ):
        self.executable_availability = executable_availability or {}
        self.secret_availability = secret_availability or {}
        self.forbidden_fingerprints = forbidden_fingerprints
        self.host_compatible = host_compatible
        self.port_availability = port_availability or {}
        self.expected_service_ports = expected_service_ports or {}
        self.ignored_paths = ignored_paths or {}
        self.cpu_count_value = cpu_count_value
        self.memory_bytes_value = memory_bytes_value
        self.disk_free_bytes_value = disk_free_bytes_value
        self.python_version_value = python_version_value

    def is_linux_or_wsl(self) -> bool:
        return self.host_compatible

    def python_version(self) -> str:
        return self.python_version_value

    def executable_available(self, name: str) -> bool:
        return self.executable_availability.get(name, True)

    def cpu_count(self) -> int:
        return self.cpu_count_value

    def memory_bytes(self) -> int:
        return self.memory_bytes_value

    def disk_free_bytes(self, path: str) -> int:
        return self.disk_free_bytes_value

    def port_available(self, port: int) -> bool:
        return self.port_availability.get(port, True)

    def port_matches_expected_service(self, port: int, service: str) -> bool:
        return self.expected_service_ports.get(port, False)

    def secret_available(self, name: str) -> bool:
        return self.secret_availability.get(name, True)

    def path_ignored_by_git(self, path: str) -> bool:
        return self.ignored_paths.get(path, True)

    def forbidden_tracked_secret_fingerprints(
        self,
        fingerprints: Mapping[str, str],
    ) -> Sequence[str]:
        return self.forbidden_fingerprints
