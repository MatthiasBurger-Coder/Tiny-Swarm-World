import unittest
from dataclasses import dataclass, replace
from collections.abc import Mapping, Sequence
from typing import Any
from tests.support.sonar_safe_literals import token_marker

from tiny_swarm_world.application.ports.configuration import ConfigurationSourceLoadError
from tiny_swarm_world.application.ports.preflight import PortHostPreflightProbe
from tiny_swarm_world.application.services.platform.preflight_service import PreflightService
from tiny_swarm_world.domain.configuration import (
    ConfigurationFinding,
    ConfigurationStatus,
    ConfigurationValidationResult,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.network import (
    PortExposureClass,
    PortRange,
    PortRegistry,
    ServicePortMapping,
)
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    LiveConsent,
    PreflightSeverity,
    PreflightStatus,
    RequiredPort,
    RequiredDependency,
    RequiredSecret,
    SetupPath,
    SetupManifest,
    SetupPortRequirement,
    SetupProfile,
    SetupSecretRequirement,
    SetupServiceRequirement,
    WindowsWslBridgeStatus,
    default_preflight_configuration,
)
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemAssessment,
    ProjectFilesystemInspection,
    ProjectFilesystemKind,
    assess_project_filesystem,
)
from tiny_swarm_world.domain.preflight.resources import HostResources, MemoryPressureReport


class TestPreflightService(unittest.IsolatedAsyncioTestCase):
    def test_wsl_resource_checks_cover_supported_and_pressure_paths(self):
        service = PreflightService(_fake_probe())
        service.resource_inspector = _ResourceInspector()
        host = HostEnvironmentReport(
            environment=HostEnvironmentKind.WSL2,
            setup_path=SetupPath.WSL2,
            remediation=(),
            evidence={"classification": "wsl2"},
        )

        resource_check = service._structured_resource_check(host)
        pressure_check = service._memory_pressure_check(host)

        self.assertIsNotNone(resource_check)
        self.assertEqual("PASSED", resource_check.status)
        self.assertIsNotNone(pressure_check)
        self.assertEqual("PASSED", pressure_check.status)

    def test_wsl_resource_checks_reject_insufficient_and_critical_pressure(self):
        service = PreflightService(_fake_probe())
        service.resource_inspector = _ResourceInspector(critical=True)
        host = HostEnvironmentReport(
            environment=HostEnvironmentKind.WSL2,
            setup_path=SetupPath.WSL2,
            remediation=(),
            evidence={"classification": "wsl2"},
        )

        resource_check = service._structured_resource_check(host)
        pressure_check = service._memory_pressure_check(host)

        self.assertEqual("FAILED", resource_check.status)
        self.assertEqual("FAILED", pressure_check.status)
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
        self.assertIn("SECRET-TSW_PORTAINER_ADMIN_PASSWORD", check_ids)

    async def test_static_preflight_can_run_without_live_consent_check(self):
        probe = _fake_probe()
        result = await PreflightService(probe).run()

        check_ids = {check.check_id for check in result.checks}
        self.assertTrue(result.passed)
        self.assertNotIn("LIVE-CONSENT", check_ids)
        self.assertNotIn("RUNTIME-MULTIPASS", check_ids)
        self.assertFalse(any(check_id.startswith("RUNTIME-") for check_id in check_ids))

    async def test_host_filesystem_block_is_immediately_after_host_and_stops_later_checks(self):
        project_path = "/mnt/d/private/project"
        evaluator = _ProjectFilesystemService(
            _filesystem_assessment(
                ProjectFilesystemKind.WINDOWS_MOUNTED,
                project_path,
                allow_override=False,
            )
        )

        result = await PreflightService(
            _fake_probe(host_environment=_wsl2_environment()),
            project_filesystem_evaluator=evaluator,
            project_path=project_path,
        ).run()

        check_ids = [check.check_id for check in result.checks]
        host_index = check_ids.index("HOST")
        self.assertEqual(check_ids[host_index + 1], "HOST-FILESYSTEM")
        self.assertEqual(PreflightStatus.FAILED, result.checks[host_index + 1].status)
        self.assertNotIn("PYTHON", check_ids)
        self.assertFalse(any(check_id.startswith("DEPENDENCY-") for check_id in check_ids))
        self.assertNotIn(project_path, str(result.to_dict()))

    async def test_live_preflight_authorizes_and_records_explicit_override(self):
        project_path = "/mnt/d/private/project"
        evaluator = _ProjectFilesystemService(
            _filesystem_assessment(
                ProjectFilesystemKind.WINDOWS_MOUNTED,
                project_path,
                allow_override=True,
            )
        )
        authorizer = _ProjectFilesystemService(evaluator.assessment)

        result = await PreflightService(
            _fake_probe(host_environment=_wsl2_environment()),
            project_filesystem_evaluator=evaluator,
            project_filesystem_authorizer=authorizer,
            project_path=project_path,
            allow_wsl_windows_filesystem=True,
        ).run(LiveConsent(live_flag=True, confirmed=True))

        check = next(item for item in result.checks if item.check_id == "HOST-FILESYSTEM")
        self.assertEqual(PreflightStatus.PASSED, check.status)
        self.assertEqual(check.evidence["decision"], "allowed_by_override")
        self.assertEqual(len(authorizer.calls), 1)
        self.assertNotIn(project_path, str(result.to_dict()))

    async def test_static_override_evaluates_without_authorizing_or_writing_evidence(self):
        project_path = "/mnt/e/private/project"
        evaluator = _ProjectFilesystemService(
            _filesystem_assessment(
                ProjectFilesystemKind.WINDOWS_MOUNTED,
                project_path,
                allow_override=True,
            )
        )
        authorizer = _ProjectFilesystemService(evaluator.assessment)

        result = await PreflightService(
            _fake_probe(host_environment=_wsl2_environment()),
            project_filesystem_evaluator=evaluator,
            project_filesystem_authorizer=authorizer,
            project_path=project_path,
            allow_wsl_windows_filesystem=True,
        ).run()

        check = next(item for item in result.checks if item.check_id == "HOST-FILESYSTEM")
        self.assertEqual(PreflightStatus.PASSED, check.status)
        self.assertEqual(check.evidence["decision"], "allowed_by_override")
        self.assertEqual(len(evaluator.calls), 1)
        self.assertEqual(authorizer.calls, [])
        self.assertNotIn(project_path, str(result.to_dict()))

    async def test_live_override_evidence_failure_blocks_before_runtime_checks(self):
        project_path = "/mnt/d/private/project"
        evaluator = _ProjectFilesystemService(
            _filesystem_assessment(
                ProjectFilesystemKind.WINDOWS_MOUNTED,
                project_path,
                allow_override=True,
            )
        )
        blocked = evaluator.assessment.block_for_evidence_failure()
        authorizer = _ProjectFilesystemService(blocked)

        result = await PreflightService(
            _fake_probe(host_environment=_wsl2_environment()),
            project_filesystem_evaluator=evaluator,
            project_filesystem_authorizer=authorizer,
            project_path=project_path,
            allow_wsl_windows_filesystem=True,
        ).run(LiveConsent(live_flag=True, confirmed=True))

        check_ids = [check.check_id for check in result.checks]
        check = next(item for item in result.checks if item.check_id == "HOST-FILESYSTEM")
        self.assertEqual(PreflightStatus.FAILED, check.status)
        self.assertEqual(check.evidence["evidence_status"], "protected_evidence_unavailable")
        self.assertFalse(any(check_id.startswith("RUNTIME-") for check_id in check_ids))

    async def test_preflight_reports_selected_provider_backend_dependency(self):
        configuration = replace(
            default_preflight_configuration(),
            required_dependencies=(
                RequiredDependency("python3"),
                RequiredDependency("docker"),
                RequiredDependency("lxc"),
            ),
        )

        result = await PreflightService(
            _fake_probe(executable_availability={"lxc": False}),
            configuration,
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertIn("DEPENDENCY-lxc", failed_by_id)
        self.assertEqual(PreflightStatus.FAILED, failed_by_id["DEPENDENCY-lxc"].status)
        self.assertIn("lxc", failed_by_id["DEPENDENCY-lxc"].remediation)

    async def test_configuration_contract_checks_are_reported_as_preflight_checks(self):
        result = await PreflightService(
            _fake_probe(),
            configuration_validation=_FakeConfigurationValidation(
                (
                    ConfigurationFinding(
                        key="TSW_EXAMPLE_PASSWORD",
                        status=ConfigurationStatus.PASSED,
                        message="Configuration value satisfies the typed contract.",
                        remediation="None.",
                        evidence={
                            "scope": "example",
                            "value_kind": "secret_value",
                            "required": "true",
                            "source": "environment",
                        },
                    ),
                )
            ),
        ).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        config_check = checks_by_id["CONFIG-TSW_EXAMPLE_PASSWORD"]

        self.assertTrue(result.passed)
        self.assertEqual(PreflightStatus.PASSED, config_check.status)
        self.assertEqual(config_check.category.value, "CONFIGURATION")
        self.assertEqual(config_check.evidence["scope"], "example")
        self.assertEqual(config_check.evidence["value_kind"], "secret_value")

    async def test_missing_configuration_contract_value_blocks_preflight(self):
        result = await PreflightService(
            _fake_probe(),
            configuration_validation=_FakeConfigurationValidation(
                (
                    ConfigurationFinding(
                        key="TSW_REQUIRED_PASSWORD",
                        status=ConfigurationStatus.FAILED,
                        message="Required configuration value is missing.",
                        remediation="Provide TSW_REQUIRED_PASSWORD through an operator-owned environment source.",
                        evidence={
                            "scope": "example",
                            "value_kind": "secret_value",
                            "required": "true",
                            "source": "missing",
                        },
                    ),
                )
            ),
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("CONFIG-TSW_REQUIRED_PASSWORD", failed_by_id)
        self.assertEqual(failed_by_id["CONFIG-TSW_REQUIRED_PASSWORD"].evidence["source"], "missing")

    async def test_configuration_source_errors_fail_closed_without_value_leak(self):
        result = await PreflightService(
            _fake_probe(),
            configuration_validation=_RaisingConfigurationValidation(
                ValueError("secret-value must not leak")
            ),
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("CONFIGURATION-CONTRACT", failed_by_id)
        self.assertEqual(
            failed_by_id["CONFIGURATION-CONTRACT"].evidence["classification"],
            "configuration_source_error",
        )
        self.assertNotIn("secret-value", repr(result.to_dict()))

    async def test_configuration_source_error_reports_safe_detail_without_value_leak(self):
        result = await PreflightService(
            _fake_probe(),
            configuration_validation=_RaisingConfigurationValidation(
                ConfigurationSourceLoadError(
                    "Duplicate configuration key TSW_EXAMPLE_PASSWORD at lines 1 and 2.",
                    safe_detail="Duplicate configuration key TSW_EXAMPLE_PASSWORD at lines 1 and 2.",
                )
            ),
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        evidence = failed_by_id["CONFIGURATION-CONTRACT"].evidence

        self.assertFalse(result.passed)
        self.assertEqual(evidence["classification"], "configuration_source_error")
        self.assertEqual(
            evidence["detail"],
            "Duplicate configuration key TSW_EXAMPLE_PASSWORD at lines 1 and 2.",
        )
        self.assertNotIn("secret-value", repr(result.to_dict()))

    async def test_configuration_contract_validation_replaces_legacy_secret_probe(self):
        result = await PreflightService(
            _fake_probe(secret_availability={"TSW_NEXUS_ADMIN_PASSWORD": False}),
            configuration_validation=_FakeConfigurationValidation(()),
        ).run()

        check_ids = {check.check_id for check in result.checks}

        self.assertTrue(result.passed)
        self.assertNotIn("SECRET-TSW_NEXUS_ADMIN_PASSWORD", check_ids)

    async def test_static_preflight_reports_typed_host_evidence_without_runtime_readiness(self):
        probe = _fake_probe(
            host_environment=HostEnvironmentReport(
                environment=HostEnvironmentKind.WSL2,
                setup_path=SetupPath.WSL2,
                distribution="Ubuntu-24.04",
                kernel_release="6.1.21.2-microsoft-standard-WSL2",
                windows_interop_available=False,
                remediation=("Verify runtime readiness before live setup.",),
                evidence={"classification": "wsl2"},
            )
        )

        result = await PreflightService(probe).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        host_check = checks_by_id["HOST"]

        self.assertTrue(result.passed)
        self.assertEqual(PreflightStatus.PASSED, host_check.status)
        self.assertEqual(host_check.evidence["environment"], "wsl2")
        self.assertEqual(host_check.evidence["setup_path"], "wsl2")
        self.assertEqual(host_check.evidence["supported"], "true")
        self.assertEqual(host_check.evidence["allows_live_setup"], "true")
        self.assertEqual(host_check.evidence["static_validation_only"], "false")
        self.assertEqual(host_check.evidence["distribution"], "Ubuntu-24.04")
        self.assertEqual(
            host_check.evidence["kernel_release"],
            "6.1.21.2-microsoft-standard-WSL2",
        )
        self.assertEqual(host_check.evidence["windows_interop_available"], "false")
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
                self.assertEqual(host_check.evidence["allows_live_setup"], "false")
                self.assertIn(remediation, host_check.remediation)
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
        self.assertNotIn("SECRET-TSW_PORTAINER_ADMIN_PASSWORD", check_ids)

    async def test_preflight_uses_port_registry_external_ports_when_provided(self):
        registry = PortRegistry(
            ranges=(PortRange("public-ingress", 80, 443),),
            mappings=(
                ServicePortMapping(
                    service_id="traefik",
                    port_id="traefik-http",
                    internal_port=80,
                    external_port=80,
                    exposure=PortExposureClass.PUBLIC_INGRESS,
                    range_id="public-ingress",
                    required_for_preflight=True,
                ),
            ),
        )

        result = await PreflightService(
            _fake_probe(port_availability={80: False}),
            port_registry=registry,
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertIn("PORT-80", failed_by_id)
        self.assertEqual(failed_by_id["PORT-80"].evidence["port"], "80")
        self.assertEqual(failed_by_id["PORT-80"].evidence["service"], "traefik-http")

    async def test_preflight_ignores_non_preflight_registry_ports(self):
        registry = PortRegistry(
            ranges=(PortRange("diagnostic", 10000, 19999),),
            mappings=(
                ServicePortMapping(
                    service_id="jenkins",
                    port_id="jenkins-http",
                    internal_port=8080,
                    external_port=11080,
                    exposure=PortExposureClass.DIAGNOSTIC,
                    range_id="diagnostic",
                    required_for_preflight=False,
                ),
            ),
        )

        result = await PreflightService(
            _fake_probe(port_availability={11080: False}),
            port_registry=registry,
        ).run()

        self.assertNotIn("PORT-11080", {check.check_id for check in result.checks})

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
            executable_availability={"python3": False},
            secret_availability={"TSW_NEXUS_ADMIN_PASSWORD": False},
        )

        result = await PreflightService(probe, configuration).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertFalse(result.passed)
        self.assertIn("DEPENDENCY-python3", failed_by_id)
        self.assertIn("SECRET-TSW_NEXUS_ADMIN_PASSWORD", failed_by_id)
        self.assertIn("Install 'python3'", failed_by_id["DEPENDENCY-python3"].remediation)
        self.assertIn(
            "Provide the secret",
            failed_by_id["SECRET-TSW_NEXUS_ADMIN_PASSWORD"].remediation,
        )

    async def test_live_preflight_does_not_run_removed_runtime_readiness(self):
        probe = _fake_probe()

        result = await PreflightService(probe).run(
            LiveConsent(live_flag=True, confirmed=True)
        )

        checks_by_id = {check.check_id: check for check in result.checks}

        self.assertTrue(result.passed)
        self.assertFalse(any(check_id.startswith("RUNTIME-") for check_id in checks_by_id))

    async def test_wsl2_live_preflight_blocks_when_windows_bridge_state_is_missing(self):
        result = await PreflightService(
            _fake_probe(
                host_environment=_wsl2_environment(),
                windows_bridge_status=WindowsWslBridgeStatus(
                    prepared=False,
                    reason="state_missing",
                    state_path="tools/windows/.tws-wsl-bridge.state.json",
                    expected_ports=(80, 10000),
                    missing_ports=(80, 10000),
                ),
            ),
            port_registry=_bridge_port_registry(),
        ).run(LiveConsent(live_flag=True, confirmed=True))

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        bridge_check = failed_by_id["WINDOWS-WSL-BRIDGE"]

        self.assertFalse(result.passed)
        self.assertEqual(bridge_check.category.value, "WINDOWS_EXPOSURE")
        self.assertIn("Windows <-> WSL bridge is not prepared", bridge_check.message)
        self.assertIn("tools/windows/tws-wsl-bridge.ps1 -Action install", bridge_check.remediation)
        self.assertEqual(bridge_check.evidence["missing_ports"], "80,10000")

    async def test_wsl2_live_preflight_reports_stale_bridge_refresh_guidance(self):
        result = await PreflightService(
            _fake_probe(
                host_environment=_wsl2_environment(),
                windows_bridge_status=WindowsWslBridgeStatus(
                    prepared=False,
                    reason="wsl_ip_changed",
                    state_path="tools/windows/.tws-wsl-bridge.state.json",
                    current_wsl_ip="172.21.0.9",
                    state_wsl_ip="172.20.0.2",
                    expected_ports=(80,),
                    mapped_ports=(80,),
                    state_age_seconds=42,
                ),
            ),
            port_registry=_bridge_port_registry(),
        ).run(LiveConsent(live_flag=True, confirmed=True))

        bridge_check = {check.check_id: check for check in result.failed_checks}["WINDOWS-WSL-BRIDGE"]

        self.assertFalse(result.passed)
        self.assertEqual(bridge_check.evidence["state_age_seconds"], "42")
        self.assertIn("Restart-Service", bridge_check.remediation)

    async def test_wsl2_live_preflight_passes_when_windows_bridge_state_is_prepared(self):
        result = await PreflightService(
            _fake_probe(host_environment=_wsl2_environment()),
            port_registry=_bridge_port_registry(),
        ).run(LiveConsent(live_flag=True, confirmed=True))

        checks_by_id = {check.check_id: check for check in result.checks}
        bridge_check = checks_by_id["WINDOWS-WSL-BRIDGE"]

        self.assertTrue(result.passed)
        self.assertEqual(PreflightStatus.PASSED, bridge_check.status)
        self.assertEqual(bridge_check.evidence["expected_ports"], "80,10000")

    async def test_windows_bridge_expected_ports_falls_back_to_required_ports_without_registry(self):
        configuration = default_preflight_configuration()
        service = PreflightService(_fake_probe(), configuration)

        self.assertEqual(
            tuple(required.port for required in configuration.required_ports),
            service._windows_bridge_expected_ports(),
        )

    async def test_native_linux_live_preflight_does_not_require_windows_bridge(self):
        result = await PreflightService(
            _fake_probe(),
            port_registry=_bridge_port_registry(),
        ).run(LiveConsent(live_flag=True, confirmed=True))

        self.assertTrue(result.passed)
        self.assertNotIn("WINDOWS-WSL-BRIDGE", {check.check_id for check in result.checks})

    async def test_wsl2_live_preflight_allows_explicitly_disabled_windows_exposure(self):
        configuration = replace(
            default_preflight_configuration(),
            windows_wsl_bridge_required=False,
        )

        result = await PreflightService(
            _fake_probe(
                host_environment=_wsl2_environment(),
                windows_bridge_status=WindowsWslBridgeStatus(
                    prepared=False,
                    reason="state_missing",
                    state_path="tools/windows/.tws-wsl-bridge.state.json",
                ),
            ),
            configuration,
            port_registry=_bridge_port_registry(),
        ).run(LiveConsent(live_flag=True, confirmed=True))

        checks_by_id = {check.check_id: check for check in result.checks}
        bridge_check = checks_by_id["WINDOWS-WSL-BRIDGE"]

        self.assertTrue(result.passed)
        self.assertEqual(PreflightStatus.PASSED, bridge_check.status)
        self.assertEqual(bridge_check.evidence["required"], "false")

    async def test_legacy_boolean_host_probe_fails_closed_as_unverified(self):
        probe = _LegacyBooleanProbe()

        result = await PreflightService(probe).run(
            LiveConsent(live_flag=True, confirmed=True)
        )

        checks_by_id = {check.check_id: check for check in result.checks}
        host_check = checks_by_id["HOST"]

        self.assertFalse(result.passed)
        self.assertEqual(host_check.evidence["environment"], "sandbox_unverified")
        self.assertEqual(host_check.evidence["classification"], "legacy_boolean_unverified")
        self.assertFalse(any(check_id.startswith("RUNTIME-") for check_id in checks_by_id))

    def test_legacy_boolean_probe_uses_default_windows_bridge_status(self):
        status = _LegacyBooleanProbe().windows_wsl_bridge_status((10000, 80))

        self.assertFalse(status.prepared)
        self.assertEqual(status.reason, "unsupported_probe")
        self.assertEqual(status.expected_ports, (80, 10000))
        self.assertEqual(status.missing_ports, (80, 10000))

    async def test_static_local_password_defaults_do_not_satisfy_missing_secret_values(self):
        result = await PreflightService(
            _fake_probe(secret_availability={"TSW_NEXUS_ADMIN_PASSWORD": False})
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        secret_check = failed_by_id["SECRET-TSW_NEXUS_ADMIN_PASSWORD"]

        self.assertFalse(result.passed)
        self.assertEqual(secret_check.evidence["value_kind"], "secret_value")
        self.assertNotIn("static_default", secret_check.evidence)
        self.assertIn("Provide the secret", secret_check.remediation)
        self.assertNotIn("password_value", repr(secret_check.to_dict()).lower())

    async def test_missing_infisical_platform_secret_blocks_service_access_preflight(self):
        configuration = default_preflight_configuration(
            service_profile=ServiceStackProfile.SERVICE_ACCESS
        )
        result = await PreflightService(
            _fake_probe(
                secret_availability={"TSW_INFISICAL_ENCRYPTION_KEY": False},
            ),
            configuration,
        ).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        secret_check = checks_by_id["SECRET-TSW_INFISICAL_ENCRYPTION_KEY"]

        self.assertFalse(result.passed)
        self.assertEqual(secret_check.evidence["value_kind"], "secret_value")
        self.assertNotIn(token_marker(), repr(secret_check.to_dict()).casefold())

    async def test_host_port_and_ignore_policy_failures_are_reported(self):
        result = await PreflightService(
            _fake_probe(
                host_compatible=False,
                port_availability={16081: False},
                ignored_paths={".env": False},
            )
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertFalse(result.passed)
        self.assertIn("HOST", failed_by_id)
        self.assertIn("PORT-16081", failed_by_id)
        self.assertIn("IGNORE-.env", failed_by_id)
        self.assertIn("Run Tiny Swarm World from Linux or WSL", failed_by_id["HOST"].remediation)

    async def test_occupied_port_passes_when_expected_service_is_detected(self):
        result = await PreflightService(
            _fake_probe(
                port_availability={10001: False},
                expected_service_ports={10001: True},
            )
        ).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        port_check = checks_by_id["PORT-10001"]

        self.assertTrue(result.passed)
        self.assertEqual(port_check.status, "PASSED")
        self.assertEqual(port_check.evidence["source"], "existing_expected_service")

    async def test_occupied_unknown_port_still_fails_preflight(self):
        result = await PreflightService(
            _fake_probe(
                port_availability={10001: False},
                expected_service_ports={10001: False},
            )
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("PORT-10001", failed_by_id)
        self.assertIn("occupied", failed_by_id["PORT-10001"].message)

    async def test_service_access_profile_blocks_unexpected_local_http_ingress_listener(self):
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
        self.assertIn("Traefik HTTP ingress", failed_by_id["PORT-80"].message)
        self.assertIn("stale localhost listener", failed_by_id["PORT-80"].remediation)

    async def test_service_access_profile_blocks_swagger_on_public_http_ingress(self):
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

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("PORT-80", failed_by_id)

    async def test_service_access_profile_blocks_infisical_on_public_https_ingress(self):
        configuration = default_preflight_configuration(
            service_profile=ServiceStackProfile.SERVICE_ACCESS
        )

        result = await PreflightService(
            _fake_probe(
                port_availability={443: False},
                expected_service_ports={443: False},
                service_matches={(443, "Infisical HTTPS"): True},
            ),
            configuration,
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("PORT-443", failed_by_id)

    async def test_service_access_profile_blocks_existing_service_access_http_listener(self):
        configuration = default_preflight_configuration(
            service_profile=ServiceStackProfile.SERVICE_ACCESS
        )

        result = await PreflightService(
            _fake_probe(
                port_availability={80: False},
                expected_service_ports={80: False},
                service_matches={(80, "Service Access"): True},
            ),
            configuration,
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("PORT-80", failed_by_id)

    async def test_service_access_profile_blocks_existing_service_access_https_listener(self):
        configuration = default_preflight_configuration(
            service_profile=ServiceStackProfile.SERVICE_ACCESS
        )

        result = await PreflightService(
            _fake_probe(
                port_availability={443: False},
                expected_service_ports={443: False},
                service_matches={(443, "Service Access"): True},
            ),
            configuration,
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}

        self.assertFalse(result.passed)
        self.assertIn("PORT-443", failed_by_id)

    async def test_swagger_port_allows_old_swagger_api_listener_to_be_reassigned(self):
        result = await PreflightService(
            _fake_probe(
                port_availability={16081: False},
                expected_service_ports={16081: False},
                service_matches={(16081, "Swagger API"): True},
            )
        ).run()

        checks_by_id = {check.check_id: check for check in result.checks}
        port_check = checks_by_id["PORT-16081"]

        self.assertTrue(result.passed)
        self.assertEqual(port_check.evidence["source"], "planned_route_reassignment")
        self.assertEqual(port_check.evidence["current_service"], "Swagger API")

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
                executable_availability={"python3": False},
                cpu_count_value=2,
                memory_bytes_value=8,
                disk_free_bytes_value=8,
            )
        ).run()

        failed_by_id = {check.check_id: check for check in result.failed_checks}
        self.assertEqual("FAILED", result.status)
        self.assertIn("DEPENDENCY-python3", failed_by_id)
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


class _ProjectFilesystemService:
    def __init__(self, assessment: ProjectFilesystemAssessment) -> None:
        self.assessment = assessment
        self.calls: list[tuple[HostEnvironmentKind, str, bool]] = []

    def run(
        self,
        host_environment: HostEnvironmentKind,
        project_path: str,
        *,
        allow_wsl_windows_filesystem: bool,
    ) -> ProjectFilesystemAssessment:
        self.calls.append(
            (host_environment, project_path, allow_wsl_windows_filesystem)
        )
        return self.assessment


def _filesystem_assessment(
    kind: ProjectFilesystemKind,
    project_path: str,
    *,
    allow_override: bool,
) -> ProjectFilesystemAssessment:
    return assess_project_filesystem(
        HostEnvironmentKind.WSL2,
        ProjectFilesystemInspection(
            kind=kind,
            resolved_project_path=project_path,
            filesystem_type="9p" if kind is ProjectFilesystemKind.WINDOWS_MOUNTED else "ext4",
            classification_source="test_fixture",
        ),
        allow_wsl_windows_filesystem=allow_override,
    )


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
    host_environment: HostEnvironmentReport | None = None
    windows_bridge_status: WindowsWslBridgeStatus | None = None


def _fake_probe(**overrides: Any) -> "_FakeProbe":
    return _FakeProbe(_FakeProbeOptions(**overrides))


class _ResourceInspector:
    def __init__(self, critical: bool = False) -> None:
        self.critical = critical

    def inspect(self) -> HostResources:
        if self.critical:
            return HostResources(1, 1, 1, 0, 1)
        return HostResources(32, 32 * 1024**3, 32 * 1024**3, 0, 500 * 1024**3)

    def memory_pressure(self) -> MemoryPressureReport:
        return MemoryPressureReport(
            assessment="oom_kill_detected" if self.critical else "none",
            confidence="high",
            memory_current=1,
            memory_max=2,
            memory_high=2,
            oom_events=1 if self.critical else 0,
            oom_kill_events=1 if self.critical else 0,
            reclaim_events=0,
        )


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
        self.windows_bridge_status = selected.windows_bridge_status

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

    def windows_wsl_bridge_status(
        self,
        expected_ports: Sequence[int],
    ) -> WindowsWslBridgeStatus:
        if self.windows_bridge_status is not None:
            return self.windows_bridge_status
        return WindowsWslBridgeStatus(
            prepared=True,
            reason="prepared",
            state_path="tools/windows/.tws-wsl-bridge.state.json",
            current_wsl_ip="172.20.0.2",
            state_wsl_ip="172.20.0.2",
            generated_at="2026-07-05T09:00:00+00:00",
            listen_address="0.0.0.0",
            expected_ports=tuple(expected_ports),
            mapped_ports=tuple(expected_ports),
        )


class _LegacyBooleanProbe(PortHostPreflightProbe):
    def is_linux_or_wsl(self) -> bool:
        return True

    def python_version(self) -> str:
        return "3.12.3"

    def executable_available(self, name: str) -> bool:
        return True

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


class _FakeConfigurationValidation:
    def __init__(self, findings: tuple[ConfigurationFinding, ...]) -> None:
        self.findings = findings

    def validate(self) -> ConfigurationValidationResult:
        return ConfigurationValidationResult(self.findings)


class _RaisingConfigurationValidation:
    def __init__(self, error: ValueError) -> None:
        self.error = error

    def validate(self) -> ConfigurationValidationResult:
        raise self.error


def _wsl2_environment() -> HostEnvironmentReport:
    return HostEnvironmentReport(
        environment=HostEnvironmentKind.WSL2,
        setup_path=SetupPath.WSL2,
        remediation=("Verify WSL2 Incus readiness before live setup.",),
        evidence={"classification": "wsl2"},
    )


def _bridge_port_registry() -> PortRegistry:
    return PortRegistry(
        ranges=(),
        mappings=(
            ServicePortMapping(
                service_id="traefik",
                port_id="traefik-http",
                internal_port=80,
                external_port=80,
                exposure=PortExposureClass.PUBLIC_INGRESS,
                protocol="tcp",
            ),
            ServicePortMapping(
                service_id="service-access",
                port_id="service-access-http",
                internal_port=80,
                external_port=10000,
                exposure=PortExposureClass.DIAGNOSTIC,
                protocol="tcp",
            ),
            ServicePortMapping(
                service_id="dns-test",
                port_id="dns-test",
                internal_port=53,
                external_port=1053,
                exposure=PortExposureClass.DIAGNOSTIC,
                protocol="udp",
            ),
        ),
    )
