from __future__ import annotations

import asyncio
from collections.abc import Mapping

from tiny_swarm_world.application.ports.configuration import ConfigurationSourceLoadError
from tiny_swarm_world.application.ports.preflight import PortHostPreflightProbe
from tiny_swarm_world.application.services.configuration import ConfigurationValidationService
from tiny_swarm_world.domain.configuration import ConfigurationFinding
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentReport,
    LiveConsent,
    PreflightCategory,
    PreflightCheck,
    PreflightConfiguration,
    PreflightResult,
    PreflightSeverity,
    PreflightStatus,
    default_preflight_configuration,
)


class PreflightService:
    def __init__(
        self,
        host_probe: PortHostPreflightProbe,
        configuration: PreflightConfiguration | None = None,
        configuration_validation: ConfigurationValidationService | None = None,
    ):
        self.host_probe = host_probe
        self.configuration = configuration or default_preflight_configuration()
        self.configuration_validation = configuration_validation

    async def run(self, live_consent: LiveConsent | None = None) -> PreflightResult:
        await asyncio.sleep(0)
        host_environment = self.host_probe.host_environment_report()
        checks = [
            self._setup_manifest_check(),
            *self._configuration_contract_checks(),
            self._host_check(host_environment),
            self._python_check(),
            *self._dependency_checks(),
        ]
        if live_consent is not None:
            checks.insert(0, self._live_consent_check(live_consent))
        if (
            live_consent is not None
            and live_consent.accepted
            and host_environment.allows_live_setup
        ):
            checks.extend(self._runtime_checks())
        secret_checks = (
            self._secret_checks()
            if self.configuration_validation is None
            else ()
        )
        checks.extend(
            (
                self._cpu_check(),
                self._memory_check(),
                self._disk_check(),
                *self._port_checks(),
                *secret_checks,
                *self._ignore_policy_checks(),
                self._forbidden_secret_fingerprint_check(),
            )
        )
        return PreflightResult(
            tuple(checks),
            setup_profile=self.configuration.setup_profile,
            manifest_summary=self.configuration.setup_manifest.summary(),
        )

    def _setup_manifest_check(self) -> PreflightCheck:
        manifest = self.configuration.setup_manifest
        return _passed(
            "SETUP-MANIFEST",
            PreflightCategory.CONFIGURATION,
            "Setup manifest is structured and secret-safe.",
            {
                "profile": manifest.profile.value,
                "services": ",".join(manifest.service_names),
                "evidence_root": manifest.evidence_root,
            },
        )

    def _configuration_contract_checks(self) -> tuple[PreflightCheck, ...]:
        if self.configuration_validation is None:
            return ()
        try:
            validation_result = self.configuration_validation.validate()
        except ConfigurationSourceLoadError as exc:
            evidence = {"classification": "configuration_source_error"}
            if exc.safe_detail:
                evidence["detail"] = exc.safe_detail
            return (
                _failed(
                    "CONFIGURATION-CONTRACT",
                    PreflightCategory.CONFIGURATION,
                    "Configuration contract validation could not load operator configuration.",
                    "Fix the operator-owned environment source syntax, then rerun preflight.",
                    evidence,
                ),
            )
        except ValueError:
            return (
                _failed(
                    "CONFIGURATION-CONTRACT",
                    PreflightCategory.CONFIGURATION,
                    "Configuration contract validation could not load operator configuration.",
                    "Fix the operator-owned environment source syntax, then rerun preflight.",
                    {"classification": "configuration_source_error"},
                ),
            )
        return tuple(
            _configuration_finding_check(finding)
            for finding in validation_result.findings
        )

    def _live_consent_check(self, live_consent: LiveConsent) -> PreflightCheck:
        if live_consent.accepted:
            return _passed(
                "LIVE-CONSENT",
                PreflightCategory.LIVE_CONSENT,
                "Live infrastructure consent is complete.",
                {"required_controls": "flag,interactive_confirmation"},
            )
        return _failed(
            "LIVE-CONSENT",
            PreflightCategory.LIVE_CONSENT,
            "Live infrastructure consent is missing or incomplete.",
            "Run with --live and answer y to the live infrastructure confirmation prompt.",
            {"missing": ",".join(live_consent.missing_reasons)},
        )

    def _host_check(self, host_environment: HostEnvironmentReport) -> PreflightCheck:
        evidence = {
            "environment": host_environment.environment.value,
            "setup_path": host_environment.setup_path.value,
            "supported": _bool_text(host_environment.supported),
            "allows_live_setup": _bool_text(host_environment.allows_live_setup),
            "static_validation_only": _bool_text(host_environment.static_validation_only),
            **host_environment.evidence,
        }
        if host_environment.allows_live_setup:
            return _passed(
                "HOST",
                PreflightCategory.HOST,
                f"Host setup path '{host_environment.setup_path.value}' is supported.",
                evidence,
            )
        return _failed(
            "HOST",
            PreflightCategory.HOST,
            f"Host setup path '{host_environment.setup_path.value}' is not live-ready.",
            _host_environment_remediation(host_environment),
            evidence,
        )

    def _python_check(self) -> PreflightCheck:
        actual = _parse_python_version(self.host_probe.python_version())
        expected = self.configuration.minimum_python_version
        if actual >= expected:
            return _passed(
                "PYTHON",
                PreflightCategory.HOST,
                "Python version satisfies the runtime baseline.",
                {
                    "actual": _format_python_version(actual),
                    "minimum": _format_python_version(expected),
                },
            )
        return _failed(
            "PYTHON",
            PreflightCategory.HOST,
            "Python version is below the runtime baseline.",
            f"Run Tiny Swarm World with Python {_format_python_version(expected)} or newer.",
            {
                "actual": _format_python_version(actual),
                "minimum": _format_python_version(expected),
            },
        )

    def _dependency_checks(self) -> tuple[PreflightCheck, ...]:
        checks: list[PreflightCheck] = []
        for dependency in self.configuration.required_dependencies:
            if self.host_probe.executable_available(dependency.name):
                checks.append(
                    _passed(
                        f"DEPENDENCY-{dependency.name}",
                        PreflightCategory.DEPENDENCY,
                        f"Dependency '{dependency.name}' is available.",
                    )
                )
                continue
            checks.append(
                _failed(
                    f"DEPENDENCY-{dependency.name}",
                    PreflightCategory.DEPENDENCY,
                    f"Dependency '{dependency.name}' is missing.",
                    f"Install '{dependency.name}' or make it available on PATH.",
                )
            )
        return tuple(checks)

    def _runtime_checks(self) -> tuple[PreflightCheck, ...]:
        checks: list[PreflightCheck] = []
        for runtime in self.configuration.required_runtime_readiness:
            checks.append(
                _failed(
                    f"RUNTIME-{runtime.name.upper()}-UNSUPPORTED",
                    PreflightCategory.RUNTIME,
                    f"Runtime readiness probe '{runtime.name}' is not supported.",
                    "Remove the unsupported runtime readiness requirement or add a supported probe.",
                    {"runtime": runtime.name, "classification": "unsupported"},
                )
            )
        return tuple(checks)

    def _cpu_check(self) -> PreflightCheck:
        actual = self.host_probe.cpu_count()
        expected = self.configuration.resources.minimum_cpu_count
        if actual >= expected:
            return _passed(
                "RESOURCE-CPU",
                PreflightCategory.RESOURCE,
                "CPU resource threshold is satisfied.",
                {"actual": str(actual), "minimum": str(expected)},
                severity=PreflightSeverity.RESOURCE_GATED,
            )
        return _failed(
            "RESOURCE-CPU",
            PreflightCategory.RESOURCE,
            "CPU resource threshold is not satisfied.",
            "Provide more CPU capacity or request resource-gated execution.",
            {"actual": str(actual), "minimum": str(expected)},
            severity=PreflightSeverity.RESOURCE_GATED,
        )

    def _memory_check(self) -> PreflightCheck:
        actual = self.host_probe.memory_bytes()
        expected = self.configuration.resources.minimum_memory_bytes
        if actual >= expected:
            return _passed(
                "RESOURCE-MEMORY",
                PreflightCategory.RESOURCE,
                "Memory resource threshold is satisfied.",
                {"actual_bytes": str(actual), "minimum_bytes": str(expected)},
                severity=PreflightSeverity.RESOURCE_GATED,
            )
        return _failed(
            "RESOURCE-MEMORY",
            PreflightCategory.RESOURCE,
            "Memory resource threshold is not satisfied.",
            "Provide more memory or request resource-gated execution.",
            {"actual_bytes": str(actual), "minimum_bytes": str(expected)},
            severity=PreflightSeverity.RESOURCE_GATED,
        )

    def _disk_check(self) -> PreflightCheck:
        path = self.configuration.resources.disk_path
        actual = self.host_probe.disk_free_bytes(path)
        expected = self.configuration.resources.minimum_disk_free_bytes
        if actual >= expected:
            return _passed(
                "RESOURCE-DISK",
                PreflightCategory.RESOURCE,
                "Disk resource threshold is satisfied.",
                {"path": path, "actual_bytes": str(actual), "minimum_bytes": str(expected)},
                severity=PreflightSeverity.RESOURCE_GATED,
            )
        return _failed(
            "RESOURCE-DISK",
            PreflightCategory.RESOURCE,
            "Disk resource threshold is not satisfied.",
            "Free disk space or choose a larger target storage path.",
            {"path": path, "actual_bytes": str(actual), "minimum_bytes": str(expected)},
            severity=PreflightSeverity.RESOURCE_GATED,
        )

    def _port_checks(self) -> tuple[PreflightCheck, ...]:
        checks: list[PreflightCheck] = []
        for required_port in self.configuration.required_ports:
            check_id = f"PORT-{required_port.port}"
            if self.host_probe.port_available(required_port.port):
                checks.append(
                    _passed(
                        check_id,
                        PreflightCategory.PORT,
                        f"Port {required_port.port} for {required_port.service} is available.",
                        {"port": str(required_port.port), "service": required_port.service},
                    )
                )
                continue
            if self.host_probe.port_matches_expected_service(
                required_port.port,
                required_port.service,
            ):
                checks.append(
                    _passed(
                        check_id,
                        PreflightCategory.PORT,
                        (
                            f"Port {required_port.port} for {required_port.service} "
                            "is already serving the expected service."
                        ),
                        {
                            "port": str(required_port.port),
                            "service": required_port.service,
                            "source": "existing_expected_service",
                        },
                    )
                )
                continue
            replaced_service = _planned_replaced_service(required_port.port, required_port.service)
            if replaced_service and self.host_probe.port_matches_expected_service(
                required_port.port,
                replaced_service,
            ):
                checks.append(
                    _passed(
                        check_id,
                        PreflightCategory.PORT,
                        (
                            f"Port {required_port.port} for {required_port.service} "
                            f"is currently serving {replaced_service} and will be reassigned."
                        ),
                        {
                            "port": str(required_port.port),
                            "service": required_port.service,
                            "source": "planned_route_reassignment",
                            "current_service": replaced_service,
                        },
                    )
                )
                continue
            checks.append(
                _failed(
                    check_id,
                    PreflightCategory.PORT,
                    f"Port {required_port.port} for {required_port.service} is occupied.",
                    _port_remediation(required_port.service),
                    {"port": str(required_port.port), "service": required_port.service},
                )
            )
        return tuple(checks)

    def _secret_checks(self) -> tuple[PreflightCheck, ...]:
        checks: list[PreflightCheck] = []
        static_secrets = {
            static_secret.name: static_secret
            for static_secret in self.configuration.static_secret_defaults
            if static_secret.value
        }
        for secret in self.configuration.required_secrets:
            if self.host_probe.secret_available(secret.name):
                checks.append(
                    _passed(
                        f"SECRET-{secret.name}",
                        PreflightCategory.SECRET,
                        _secret_present_message(secret.value_kind, secret.service),
                        {
                            "secret": secret.name,
                            "service": secret.service,
                            "source": "environment",
                            "value_kind": secret.value_kind,
                        },
                    )
                )
                continue
            static_secret = static_secrets.get(secret.name)
            if (
                static_secret is not None
                and secret.value_kind == "secret_name"
                and static_secret.value_kind == "secret_name"
            ):
                checks.append(
                    _passed(
                        f"SECRET-{secret.name}",
                        PreflightCategory.SECRET,
                        _static_secret_default_message(static_secret.value_kind, secret.service),
                        {
                            "secret": secret.name,
                            "service": secret.service,
                            "source": _static_secret_default_source(static_secret.value_kind),
                            "value_kind": static_secret.value_kind,
                        },
                    )
                )
                continue
            evidence = {
                "secret": secret.name,
                "service": secret.service,
                "value_kind": secret.value_kind,
            }
            if static_secret is not None:
                evidence["static_default"] = "local_development_only"
            checks.append(
                _failed(
                    f"SECRET-{secret.name}",
                    PreflightCategory.SECRET,
                    _secret_missing_message(secret.value_kind, secret.service),
                    _secret_missing_remediation(secret.value_kind),
                    evidence,
                )
            )
        return tuple(checks)

    def _ignore_policy_checks(self) -> tuple[PreflightCheck, ...]:
        checks: list[PreflightCheck] = []
        for path in self.configuration.required_ignored_paths:
            if self.host_probe.path_ignored_by_git(path):
                checks.append(
                    _passed(
                        f"IGNORE-{path}",
                        PreflightCategory.IGNORE_POLICY,
                        f"Local path '{path}' is ignored by Git.",
                        {"path": path},
                    )
                )
                continue
            checks.append(
                _failed(
                    f"IGNORE-{path}",
                    PreflightCategory.IGNORE_POLICY,
                    f"Local path '{path}' is not ignored by Git.",
                    "Add the local evidence or secret path to .gitignore before using it.",
                    {"path": path},
                )
            )
        return tuple(checks)

    def _forbidden_secret_fingerprint_check(self) -> PreflightCheck:
        fingerprints = {
            fingerprint.identifier: fingerprint.sha256_digest
            for fingerprint in self.configuration.forbidden_secret_fingerprints
        }
        found = tuple(self.host_probe.forbidden_tracked_secret_fingerprints(fingerprints))
        if not found:
            return _passed(
                "SECRET-FORBIDDEN-FINGERPRINTS",
                PreflightCategory.SECRET,
                "No forbidden tracked secret fingerprints were detected.",
            )
        return _failed(
            "SECRET-FORBIDDEN-FINGERPRINTS",
            PreflightCategory.SECRET,
            "Forbidden tracked secret fingerprints were detected.",
            "Remove hardcoded/default secrets or route them through ignored secret sources.",
            {"fingerprint_ids": ",".join(found)},
        )


def _passed(
    check_id: str,
    category: PreflightCategory,
    message: str,
    evidence: Mapping[str, str] | None = None,
    severity: PreflightSeverity = PreflightSeverity.MANDATORY,
) -> PreflightCheck:
    return PreflightCheck(
        check_id=check_id,
        category=category,
        status=PreflightStatus.PASSED,
        severity=severity,
        message=message,
        remediation="None",
        evidence=evidence or {},
    )


def _failed(
    check_id: str,
    category: PreflightCategory,
    message: str,
    remediation: str,
    evidence: Mapping[str, str] | None = None,
    severity: PreflightSeverity = PreflightSeverity.MANDATORY,
) -> PreflightCheck:
    return PreflightCheck(
        check_id=check_id,
        category=category,
        status=PreflightStatus.FAILED,
        severity=severity,
        message=message,
        remediation=remediation,
        evidence=evidence or {},
    )


def _configuration_finding_check(finding: ConfigurationFinding) -> PreflightCheck:
    evidence = {
        "configuration_key": finding.key,
        "scope": finding.evidence.get("scope", "unknown"),
        "value_kind": finding.evidence.get("value_kind", "unknown"),
        "required": finding.evidence.get("required", "unknown"),
        "source": finding.evidence.get("source", "unknown"),
    }
    status = PreflightStatus.PASSED if finding.passed else PreflightStatus.FAILED
    return PreflightCheck(
        check_id=f"CONFIG-{finding.key}",
        category=PreflightCategory.CONFIGURATION,
        status=status,
        severity=PreflightSeverity.MANDATORY,
        message=finding.message,
        remediation=finding.remediation,
        evidence=evidence,
    )


def _secret_present_message(value_kind: str, service: str) -> str:
    if value_kind == "secret_name":
        return f"Secret source name for {service} is present."
    return f"Secret source for {service} is present."


def _static_secret_default_message(value_kind: str, service: str) -> str:
    if value_kind == "secret_name":
        return f"Static local secret source name default for {service} is present."
    return f"Static local secret default for {service} is present."


def _secret_missing_message(value_kind: str, service: str) -> str:
    if value_kind == "secret_name":
        return f"Secret source name for {service} is missing."
    return f"Secret source for {service} is missing."


def _secret_missing_remediation(value_kind: str) -> str:
    if value_kind == "secret_name":
        return "Provide the external secret name through an environment variable or ignored local file."
    return "Provide the secret through an environment variable or ignored local file."


def _static_secret_default_source(value_kind: str) -> str:
    if value_kind == "secret_name":
        return "static_local_secret_name_default"
    return "static_local_default"


def _parse_python_version(version_text: str) -> tuple[int, ...]:
    parts: list[int] = []
    for raw_part in version_text.split("."):
        try:
            parts.append(int(raw_part))
        except ValueError:
            break
    return tuple(parts)


def _format_python_version(version: tuple[int, ...]) -> str:
    if not version:
        return "unknown"
    return ".".join(str(part) for part in version)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _host_environment_remediation(host_environment: HostEnvironmentReport) -> str:
    if host_environment.remediation:
        return " ".join(host_environment.remediation)
    return "Run Tiny Swarm World from supported native Linux or WSL2."


def _port_remediation(service: str) -> str:
    if service in {"Traefik HTTP ingress", "Traefik HTTPS ingress"}:
        return (
            "Clear the stale localhost listener or forwarding for this Traefik ingress port, "
            "then rerun preflight. Until localhost forwarding is repaired, use the current "
            "Swarm node IP with the same port."
        )
    return "Stop the process using the port or change the service mapping before live execution."


def _planned_replaced_service(port: int, service: str) -> str | None:
    if port == 80 and service == "Traefik HTTP ingress":
        return "Swagger/NGINX"
    if port == 443 and service == "Traefik HTTPS ingress":
        return "Infisical HTTPS"
    if port == 8084 and service == "Swagger/NGINX":
        return "Swagger API"
    return None
