import unittest
from dataclasses import dataclass, replace
from collections.abc import Mapping, Sequence
from typing import Any
from tests.support.sonar_safe_literals import token_marker

from tiny_swarm_world.application.ports.preflight import PortHostPreflightProbe
from tiny_swarm_world.application.services.platform.preflight_service import PreflightService
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    HostRuntimeReadiness,
    HostRuntimeReadinessStatus,
    LiveConsent,
    PreflightCategory,
    PreflightSeverity,
    PreflightStatus,
    RequiredPort,
    RequiredSecret,
    SetupPath,
    SetupManifest,
    SetupPortRequirement,
    SetupProfile,
    SetupSecretRequirement,
    SetupServiceRequirement,
    default_preflight_configuration,
)


class TestPreflightService(unittest.IsolatedAsyncioTestCase):
    async def test_successful_preflight_reports_passed_checks(self):
        result = await PreflightService(_fake_probe()).run(
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
        probe = _fake_probe()
        result = await PreflightService(probe).run()

        check_ids = {check.check_id for check in result.checks}
        self.assertTrue(result.passed)
        self.assertNotIn("LIVE-CONSENT", check_ids)
        self.assertNotIn("RUNTIME-MULTIPASS", check_ids)
        self.assertEqual((), tuple(probe.runtime_probe_calls))

    async def test_static_preflight_reports_typed_host_evidence_without_runtime_readiness(self):
        probe = _fake_probe(
            host_environment=HostEnvironmentReport(
                environment=HostEnvironmentKind.WSL2,
                setup_path=SetupPath.WSL2,
                remediation=("Verify runtime readiness before live setup.",),
                evidence={"classification": "wsl2"},
            )
        )

        result = await PreflightService(probe).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        host_check = checks_by_id["HOST"]

        self.assertTrue(result.passed)
        self.assertEqual(PreflightStatus.PASSED, host_check.status)
        self.assertEqual("wsl2", host_check.evidence["environment"])
        self.assertEqual("wsl2", host_check.evidence["setup_path"])
        self.assertEqual("true", host_check.evidence["supported"])
        self.assertEqual("true", host_check.evidence["allows_live_setup"])
        self.assertEqual("false", host_check.evidence["static_validation_only"])
        self.assertEqual((), tuple(probe.runtime_probe_calls))
        self.assertNotIn("RUNTIME-MULTIPASS", checks_by_id)
        self.assertNotIn("qemu", repr(result.to_dict()).casefold())
        self.assertNotIn("runtime is reachable", repr(result.to_dict()).casefold())

    async def test_live_preflight_fails_closed_for_unsupported_host_reports(self):
        cases = (
            (
                HostEnvironmentKind.WSL1_UNSUPPORTED,
                SetupPath.UNSUPPORTED,
                "Upgrade to WSL2.",
            ),
            (
                HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
                SetupPath.UNSUPPORTED,
                "Use native Linux or WSL2.",
            ),
            (
                HostEnvironmentKind.SANDBOX_UNVERIFIED,
                SetupPath.SANDBOX_UNVERIFIED,
                "Run live validation from a real WSL2 console.",
            ),
        )

        for environment, setup_path, remediation in cases:
            with self.subTest(environment=environment.value):
                probe = _fake_probe(
                    host_environment=HostEnvironmentReport(
                        environment=environment,
                        setup_path=setup_path,
                        remediation=(remediation,),
                        evidence={"classification": environment.value},
                    )
                )

                result = await PreflightService(probe).run(
                    LiveConsent(live_flag=True, confirmed=True)
                )

                checks_by_id = {check.check_id: check for check in result.checks}
                host_check = checks_by_id["HOST"]

                self.assertFalse(result.passed)
                self.assertEqual(PreflightStatus.FAILED, host_check.status)
                self.assertEqual(environment.value, host_check.evidence["environment"])
                self.assertEqual(setup_path.value, host_check.evidence["setup_path"])
                self.assertEqual("false", host_check.evidence["allows_live_setup"])
                self.assertIn(remediation, host_check.remediation)
                self.assertEqual((), tuple(probe.runtime_probe_calls))
                self.assertNotIn("RUNTIME-MULTIPASS", checks_by_id)

    async def test_preflight_reports_selected_setup_profile_and_manifest(self):
        configuration = default_preflight_configuration(SetupProfile.RESOURCE_GATED)
        result = await PreflightService(_fake_probe(), configuration).run()

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

        result = await PreflightService(_fake_probe(), configuration).run()
        check_ids = {check.check_id for check in result.checks}

        self.assertIn("PORT-12345", check_ids)
        self.assertIn("SECRET-TSW_CUSTOM_SECRET", check_ids)
        self.assertNotIn("PORT-9000", check_ids)
        self.assertNotIn("SECRET-TSW_PORTAINER_PASSWORD", check_ids)

    async def test_incomplete_live_consent_fails_preflight(self):
        result = await PreflightService(_fake_probe()).run(
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
        probe = _fake_probe(
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

    async def test_live_preflight_reports_multipass_runtime_readiness(self):
        probe = _fake_probe()

        result = await PreflightService(probe).run(
            LiveConsent(live_flag=True, confirmed=True)
        )

        checks_by_id = {check.check_id: check for check in result.checks}
        runtime_check = checks_by_id["RUNTIME-MULTIPASS"]

        self.assertTrue(result.passed)
        self.assertEqual(PreflightCategory.RUNTIME, runtime_check.category)
        self.assertEqual("ready", runtime_check.evidence["classification"])
        self.assertEqual("qemu", runtime_check.evidence["expected_driver"])
        self.assertEqual(("qemu",), tuple(probe.runtime_probe_calls))

    async def test_legacy_boolean_host_probe_still_runs_live_runtime_readiness(self):
        probe = _LegacyBooleanProbe()

        result = await PreflightService(probe).run(
            LiveConsent(live_flag=True, confirmed=True)
        )

        checks_by_id = {check.check_id: check for check in result.checks}
        host_check = checks_by_id["HOST"]
        runtime_check = checks_by_id["RUNTIME-MULTIPASS"]

        self.assertTrue(result.passed)
        self.assertEqual("native_linux", host_check.evidence["environment"])
        self.assertEqual("legacy_boolean_compatible", host_check.evidence["classification"])
        self.assertEqual("ready", runtime_check.evidence["classification"])
        self.assertEqual(("qemu",), tuple(probe.runtime_probe_calls))

    async def test_live_preflight_fails_when_multipass_socket_is_unavailable(self):
        result = await PreflightService(
            _fake_probe(
                runtime_readiness=HostRuntimeReadiness(
                    "multipass",
                    HostRuntimeReadinessStatus.SOCKET_UNAVAILABLE,
                    {"probe": "list", "return_code": "2"},
                )
            )
        ).run(LiveConsent(live_flag=True, confirmed=True))

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        runtime_failure = failed_by_id["RUNTIME-MULTIPASS-SOCKET"]

        self.assertFalse(result.passed)
        self.assertEqual(PreflightCategory.RUNTIME, runtime_failure.category)
        self.assertEqual("socket_unavailable", runtime_failure.evidence["classification"])
        self.assertEqual("2", runtime_failure.evidence["return_code"])
        self.assertIn("daemon or socket", runtime_failure.message)
        self.assertIn("same Linux/WSL shell", runtime_failure.remediation)
        self.assertNotIn("cannot connect", repr(runtime_failure.to_dict()).casefold())

    async def test_live_preflight_fails_when_multipass_driver_mismatches(self):
        result = await PreflightService(
            _fake_probe(
                runtime_readiness=HostRuntimeReadiness(
                    "multipass",
                    HostRuntimeReadinessStatus.DRIVER_MISMATCH,
                    {
                        "probe": "driver",
                        "actual_driver": "lxd",
                        "expected_driver": "qemu",
                    },
                )
            )
        ).run(LiveConsent(live_flag=True, confirmed=True))

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        runtime_failure = failed_by_id["RUNTIME-MULTIPASS-DRIVER"]

        self.assertFalse(result.passed)
        self.assertEqual("driver_mismatch", runtime_failure.evidence["classification"])
        self.assertEqual("lxd", runtime_failure.evidence["actual_driver"])
        self.assertIn("unsupported driver", runtime_failure.message)

    async def test_static_local_password_defaults_do_not_satisfy_missing_secret_values(self):
        result = await PreflightService(
            _fake_probe(secret_availability={"TSW_NEXUS_ADMIN_PASSWORD": False})
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        secret_check = failed_by_id["SECRET-TSW_NEXUS_ADMIN_PASSWORD"]

        self.assertFalse(result.passed)
        self.assertEqual("secret_value", secret_check.evidence["value_kind"])
        self.assertNotIn("static_default", secret_check.evidence)
        self.assertIn("Provide the secret", secret_check.remediation)
        self.assertNotIn("password_value", repr(secret_check.to_dict()).lower())

    async def test_static_local_secret_name_default_satisfies_missing_secret_name_source(self):
        configuration = default_preflight_configuration(
            service_profile=ServiceStackProfile.SERVICE_ACCESS
        )
        result = await PreflightService(
            _fake_probe(
                secret_availability={"TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET": False},
            ),
            configuration,
        ).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        secret_check = checks_by_id["SECRET-TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET"]

        self.assertTrue(result.passed)
        self.assertEqual("secret_name", secret_check.evidence["value_kind"])
        self.assertEqual("static_local_secret_name_default", secret_check.evidence["source"])
        self.assertNotIn(token_marker(), repr(secret_check.to_dict()).casefold())

    async def test_host_port_and_ignore_policy_failures_are_reported(self):
        result = await PreflightService(
            _fake_probe(
                host_compatible=False,
                port_availability={8084: False},
                ignored_paths={".env": False},
            )
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertFalse(result.passed)
        self.assertIn("HOST", failed_by_id)
        self.assertIn("PORT-8084", failed_by_id)
        self.assertIn("IGNORE-.env", failed_by_id)
        self.assertIn("Run Tiny Swarm World from Linux or WSL", failed_by_id["HOST"].remediation)

    async def test_occupied_port_passes_when_expected_service_is_detected(self):
        result = await PreflightService(
            _fake_probe(
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
            _fake_probe(
                port_availability={9000: False},
                expected_service_ports={9000: False},
            )
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("PORT-9000", failed_by_id)
        self.assertIn("occupied", failed_by_id["PORT-9000"].message)

    async def test_service_access_profile_blocks_unexpected_local_dashboard_listener(self):
        configuration = default_preflight_configuration(
            service_profile=ServiceStackProfile.SERVICE_ACCESS
        )

        result = await PreflightService(
            _fake_probe(
                port_availability={80: False},
                expected_service_ports={80: False},
            ),
            configuration,
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("PORT-80", failed_by_id)
        self.assertIn("Service Access dashboard", failed_by_id["PORT-80"].message)
        self.assertIn("stale localhost listener", failed_by_id["PORT-80"].remediation)

    async def test_service_access_profile_allows_swagger_to_be_reassigned_from_localhost_root(self):
        configuration = default_preflight_configuration(
            service_profile=ServiceStackProfile.SERVICE_ACCESS
        )

        result = await PreflightService(
            _fake_probe(
                port_availability={80: False},
                expected_service_ports={80: False},
                service_matches={(80, "Swagger/NGINX"): True},
            ),
            configuration,
        ).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        port_check = checks_by_id["PORT-80"]

        self.assertTrue(result.passed)
        self.assertEqual("planned_route_reassignment", port_check.evidence["source"])
        self.assertEqual("Swagger/NGINX", port_check.evidence["current_service"])

    async def test_swagger_port_allows_old_swagger_api_listener_to_be_reassigned(self):
        result = await PreflightService(
            _fake_probe(
                port_availability={8084: False},
                expected_service_ports={8084: False},
                service_matches={(8084, "Swagger API"): True},
            )
        ).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        port_check = checks_by_id["PORT-8084"]

        self.assertTrue(result.passed)
        self.assertEqual("planned_route_reassignment", port_check.evidence["source"])
        self.assertEqual("Swagger API", port_check.evidence["current_service"])

    async def test_resource_failures_are_resource_gated(self):
        result = await PreflightService(
            _fake_probe(cpu_count_value=2, memory_bytes_value=8, disk_free_bytes_value=8)
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
            _fake_probe(
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
            _fake_probe(forbidden_fingerprints=("legacy-nexus-admin-password",))
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        failure = failed_by_id["SECRET-FORBIDDEN-FINGERPRINTS"]
        self.assertEqual("legacy-nexus-admin-password", failure.evidence["fingerprint_ids"])

    async def test_python_version_below_baseline_fails_preflight(self):
        result = await PreflightService(_fake_probe(python_version_value="3.11.9")).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertIn("PYTHON", failed_by_id)
        self.assertEqual("3.11.9", failed_by_id["PYTHON"].evidence["actual"])


@dataclass(frozen=True)
class _FakeProbeOptions:
    executable_availability: dict[str, bool] | None = None
    secret_availability: dict[str, bool] | None = None
    forbidden_fingerprints: tuple[str, ...] = ()
    host_compatible: bool = True
    port_availability: dict[int, bool] | None = None
    expected_service_ports: dict[int, bool] | None = None
    service_matches: dict[tuple[int, str], bool] | None = None
    ignored_paths: dict[str, bool] | None = None
    cpu_count_value: int = 8
    memory_bytes_value: int = 32 * 1024**3
    disk_free_bytes_value: int = 120 * 1024**3
    python_version_value: str = "3.12.3"
    runtime_readiness: HostRuntimeReadiness | None = None
    host_environment: HostEnvironmentReport | None = None


def _fake_probe(**overrides: Any) -> "_FakeProbe":
    return _FakeProbe(_FakeProbeOptions(**overrides))


class _FakeProbe(PortHostPreflightProbe):
    def __init__(self, options: _FakeProbeOptions | None = None):
        selected = options or _FakeProbeOptions()
        self.executable_availability = selected.executable_availability or {}
        self.secret_availability = selected.secret_availability or {}
        self.forbidden_fingerprints = selected.forbidden_fingerprints
        self.host_compatible = selected.host_compatible
        self.port_availability = selected.port_availability or {}
        self.expected_service_ports = selected.expected_service_ports or {}
        self.service_matches = selected.service_matches or {}
        self.ignored_paths = selected.ignored_paths or {}
        self.cpu_count_value = selected.cpu_count_value
        self.memory_bytes_value = selected.memory_bytes_value
        self.disk_free_bytes_value = selected.disk_free_bytes_value
        self.python_version_value = selected.python_version_value
        self.host_environment = selected.host_environment or HostEnvironmentReport(
            environment=HostEnvironmentKind.NATIVE_LINUX,
            setup_path=SetupPath.NATIVE_LINUX,
            remediation=("Verify runtime readiness before live setup.",),
            evidence={"classification": "native_linux"},
        )
        self.runtime_readiness = selected.runtime_readiness or HostRuntimeReadiness(
            "multipass",
            HostRuntimeReadinessStatus.READY,
            {
                "probe": "list,driver",
                "actual_driver": "qemu",
                "expected_driver": "qemu",
            },
        )
        self.runtime_probe_calls: list[str | None] = []

    def is_linux_or_wsl(self) -> bool:
        return self.host_compatible

    def host_environment_report(self) -> HostEnvironmentReport:
        if self.host_compatible:
            return self.host_environment
        return HostEnvironmentReport(
            environment=HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
            setup_path=SetupPath.UNSUPPORTED,
            remediation=("Run Tiny Swarm World from Linux or WSL.",),
            evidence={"classification": "unknown_unsupported"},
        )

    def python_version(self) -> str:
        return self.python_version_value

    def executable_available(self, name: str) -> bool:
        return self.executable_availability.get(name, True)

    def multipass_runtime_readiness(
        self,
        expected_driver: str | None = None,
    ) -> HostRuntimeReadiness:
        self.runtime_probe_calls.append(expected_driver)
        return self.runtime_readiness

    def cpu_count(self) -> int:
        return self.cpu_count_value

    def memory_bytes(self) -> int:
        return self.memory_bytes_value

    def disk_free_bytes(self, path: str) -> int:
        return self.disk_free_bytes_value

    def port_available(self, port: int) -> bool:
        return self.port_availability.get(port, True)

    def port_matches_expected_service(self, port: int, service: str) -> bool:
        if (port, service) in self.service_matches:
            return self.service_matches[(port, service)]
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


class _LegacyBooleanProbe(PortHostPreflightProbe):
    def __init__(self):
        self.runtime_probe_calls: list[str | None] = []

    def is_linux_or_wsl(self) -> bool:
        return True

    def python_version(self) -> str:
        return "3.12.3"

    def executable_available(self, name: str) -> bool:
        return True

    def multipass_runtime_readiness(
        self,
        expected_driver: str | None = None,
    ) -> HostRuntimeReadiness:
        self.runtime_probe_calls.append(expected_driver)
        return HostRuntimeReadiness(
            "multipass",
            HostRuntimeReadinessStatus.READY,
            {
                "probe": "list,driver",
                "actual_driver": "qemu",
                "expected_driver": "qemu",
            },
        )

    def cpu_count(self) -> int:
        return 8

    def memory_bytes(self) -> int:
        return 32 * 1024**3

    def disk_free_bytes(self, path: str) -> int:
        return 120 * 1024**3

    def port_available(self, port: int) -> bool:
        return True

    def port_matches_expected_service(self, port: int, service: str) -> bool:
        return False

    def secret_available(self, name: str) -> bool:
        return True

    def path_ignored_by_git(self, path: str) -> bool:
        return True

    def forbidden_tracked_secret_fingerprints(
        self,
        fingerprints: Mapping[str, str],
    ) -> Sequence[str]:
        return ()
