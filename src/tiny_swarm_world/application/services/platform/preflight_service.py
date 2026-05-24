from __future__ import annotations

from collections.abc import Mapping

from tiny_swarm_world.application.ports.preflight import PortHostPreflightProbe
from tiny_swarm_world.domain.preflight import (
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
    ):
        self.host_probe = host_probe
        self.configuration = configuration or default_preflight_configuration()

    async def run(self, live_consent: LiveConsent | None = None) -> PreflightResult:
        checks = [
            self._setup_manifest_check(),
            self._host_check(),
            self._python_check(),
            *self._dependency_checks(),
            self._cpu_check(),
            self._memory_check(),
            self._disk_check(),
            *self._port_checks(),
            *self._secret_checks(),
            *self._ignore_policy_checks(),
            self._forbidden_secret_fingerprint_check(),
        ]
        if live_consent is not None:
            checks.insert(0, self._live_consent_check(live_consent))
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

    def _host_check(self) -> PreflightCheck:
        if self.host_probe.is_linux_or_wsl():
            return _passed("HOST", PreflightCategory.HOST, "Host is Linux or WSL compatible.")
        return _failed(
            "HOST",
            PreflightCategory.HOST,
            "Host is not reported as Linux or WSL.",
            "Run Tiny Swarm World from Linux or WSL.",
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
            checks.append(
                _failed(
                    check_id,
                    PreflightCategory.PORT,
                    f"Port {required_port.port} for {required_port.service} is occupied.",
                    "Stop the process using the port or change the service mapping before live execution.",
                    {"port": str(required_port.port), "service": required_port.service},
                )
            )
        return tuple(checks)

    def _secret_checks(self) -> tuple[PreflightCheck, ...]:
        checks: list[PreflightCheck] = []
        for secret in self.configuration.required_secrets:
            if self.host_probe.secret_available(secret.name):
                checks.append(
                    _passed(
                        f"SECRET-{secret.name}",
                        PreflightCategory.SECRET,
                        f"Secret source for {secret.service} is present.",
                        {"secret": secret.name, "service": secret.service},
                    )
                )
                continue
            checks.append(
                _failed(
                    f"SECRET-{secret.name}",
                    PreflightCategory.SECRET,
                    f"Secret source for {secret.service} is missing.",
                    "Provide the secret through an environment variable or ignored local file.",
                    {"secret": secret.name, "service": secret.service},
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
