from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, TypedDict

from tiny_swarm_world.domain.preflight.sanitized_evidence import sanitized_evidence


HOST_FIELD_MAX_LENGTH = 160
SIGNAL_TEXT_MAX_LENGTH = 1024
_HOST_FIELD_UNSAFE_CHARACTERS = re.compile(r"[^A-Za-z0-9 ._+()\-]")
_SIGNAL_WHITESPACE = re.compile(r"\s+")
_WSL1_KERNEL_PATTERN = re.compile(
    r"\b4\.4\.[^\n]*microsoft|microsoft[^\n]*\b4\.4\.",
    re.IGNORECASE,
)


class _HostReportFields(TypedDict):
    distribution: str
    kernel_release: str
    windows_interop_available: bool
    platform_family: str


class HostEnvironmentKind(str, Enum):
    NATIVE_LINUX = "native_linux"
    WSL2 = "wsl2"
    WSL1_UNSUPPORTED = "wsl1_unsupported"
    UNKNOWN_UNSUPPORTED = "unknown_unsupported"
    SANDBOX_UNVERIFIED = "sandbox_unverified"


class SetupPath(str, Enum):
    NATIVE_LINUX = "native_linux"
    WSL2 = "wsl2"
    UNSUPPORTED = "unsupported"
    SANDBOX_UNVERIFIED = "sandbox_unverified"


@dataclass(frozen=True)
class HostEnvironmentSignals:
    """Read-only host facts collected by infrastructure adapters."""

    platform_family: str
    distribution: str = ""
    kernel_release: str = ""
    proc_version: str = ""
    wsl_distribution: str = ""
    windows_interop_available: bool = False
    sandbox_signal: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "platform_family",
            _normalized_signal_token(self.platform_family, fallback="unknown"),
        )
        object.__setattr__(
            self,
            "distribution",
            _normalized_host_field(self.distribution, fallback=""),
        )
        object.__setattr__(
            self,
            "kernel_release",
            _normalized_host_field(self.kernel_release, fallback=""),
        )
        object.__setattr__(
            self,
            "proc_version",
            _bounded_signal_text(self.proc_version),
        )
        object.__setattr__(
            self,
            "wsl_distribution",
            _normalized_host_field(self.wsl_distribution, fallback=""),
        )
        object.__setattr__(
            self,
            "sandbox_signal",
            _normalized_signal_token(self.sandbox_signal, fallback=""),
        )
        if not isinstance(self.windows_interop_available, bool):
            raise TypeError("windows_interop_available must be a boolean")


@dataclass(frozen=True)
class HostEnvironmentReport:
    environment: HostEnvironmentKind
    setup_path: SetupPath
    remediation: tuple[str, ...] = ()
    evidence: Mapping[str, str] = field(default_factory=dict)
    distribution: str = "unknown"
    kernel_release: str = "unknown"
    windows_interop_available: bool = False
    platform_family: str = "unknown"

    def __post_init__(self) -> None:
        _validate_setup_path(self.environment, self.setup_path)
        if not isinstance(self.windows_interop_available, bool):
            raise TypeError("windows_interop_available must be a boolean")
        object.__setattr__(self, "remediation", tuple(self.remediation))
        object.__setattr__(self, "evidence", sanitized_evidence(self.evidence))
        object.__setattr__(
            self,
            "distribution",
            _normalized_host_field(self.distribution, fallback="unknown"),
        )
        object.__setattr__(
            self,
            "kernel_release",
            _normalized_host_field(self.kernel_release, fallback="unknown"),
        )
        object.__setattr__(
            self,
            "platform_family",
            _normalized_signal_token(self.platform_family, fallback="unknown"),
        )

    @property
    def supported(self) -> bool:
        return self.setup_path in {SetupPath.NATIVE_LINUX, SetupPath.WSL2}

    @property
    def allows_live_setup(self) -> bool:
        return self.supported

    @property
    def static_validation_only(self) -> bool:
        return self.setup_path == SetupPath.SANDBOX_UNVERIFIED

    def to_dict(self) -> dict[str, object]:
        return {
            "environment": self.environment.value,
            "platform_family": self.platform_family,
            "distribution": self.distribution,
            "kernel_release": self.kernel_release,
            "windows_interop_available": self.windows_interop_available,
            "setup_path": self.setup_path.value,
            "supported": self.supported,
            "allows_live_setup": self.allows_live_setup,
            "static_validation_only": self.static_validation_only,
            "remediation": list(self.remediation),
            "evidence": dict(self.evidence),
        }


def classify_host_environment(
    signals: HostEnvironmentSignals,
) -> HostEnvironmentReport:
    """Classify normalized host facts without performing host I/O."""

    common: _HostReportFields = {
        "distribution": _report_distribution(signals),
        "kernel_release": signals.kernel_release or "unknown",
        "windows_interop_available": signals.windows_interop_available,
        "platform_family": signals.platform_family,
    }
    if signals.sandbox_signal:
        return HostEnvironmentReport(
            environment=HostEnvironmentKind.SANDBOX_UNVERIFIED,
            setup_path=SetupPath.SANDBOX_UNVERIFIED,
            remediation=(
                "Use static validation only, or rerun from verified native Linux or WSL2.",
            ),
            evidence={
                "classification": "sandbox_unverified",
                "kernel_family": signals.platform_family,
                "sandbox_signal": signals.sandbox_signal,
            },
            **common,
        )

    if signals.platform_family != "linux":
        return HostEnvironmentReport(
            environment=HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
            setup_path=SetupPath.UNSUPPORTED,
            remediation=("Run Tiny Swarm World from native Linux or WSL2.",),
            evidence={
                "classification": "unknown_unsupported",
                "kernel_family": signals.platform_family,
            },
            **common,
        )

    kernel_signal = "\n".join(
        part for part in (signals.kernel_release, signals.proc_version) if part
    ).casefold()
    has_kernel_signal = bool(kernel_signal)
    has_wsl_hint = _has_wsl_kernel_hint(kernel_signal)
    has_independent_wsl_signal = bool(
        signals.wsl_distribution or signals.windows_interop_available
    )
    has_wsl2_signal = _has_wsl2_kernel_signal(kernel_signal)
    has_wsl1_signal = _has_wsl1_kernel_signal(kernel_signal)

    if has_wsl_hint or has_independent_wsl_signal:
        if has_wsl2_signal and not has_wsl1_signal and has_independent_wsl_signal:
            return HostEnvironmentReport(
                environment=HostEnvironmentKind.WSL2,
                setup_path=SetupPath.WSL2,
                remediation=("Verify WSL2 Incus readiness before live setup.",),
                evidence={
                    "classification": "wsl2",
                    "kernel_family": "linux",
                    "sandbox_signal": "absent",
                    "wsl_generation": "2",
                    "wsl_kernel_signal": "present",
                    "wsl_independent_signal": "present",
                },
                **common,
            )
        if has_wsl1_signal and not has_wsl2_signal and has_independent_wsl_signal:
            return HostEnvironmentReport(
                environment=HostEnvironmentKind.WSL1_UNSUPPORTED,
                setup_path=SetupPath.UNSUPPORTED,
                remediation=("Upgrade the distribution to WSL2 or use native Linux.",),
                evidence={
                    "classification": "wsl1_unsupported",
                    "kernel_family": "linux",
                    "wsl_generation": "1",
                    "wsl_kernel_signal": "present",
                    "wsl_independent_signal": "present",
                },
                **common,
            )
        return HostEnvironmentReport(
            environment=HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
            setup_path=SetupPath.UNSUPPORTED,
            remediation=(
                "Verify the WSL generation from the same Linux shell before live setup.",
            ),
            evidence={
                "classification": "wsl_unknown",
                "kernel_family": "linux",
                "wsl_generation": "unknown",
                "wsl_kernel_signal": _presence_text(has_wsl_hint),
                "wsl_independent_signal": _presence_text(has_independent_wsl_signal),
            },
            **common,
        )

    if not has_kernel_signal:
        return HostEnvironmentReport(
            environment=HostEnvironmentKind.SANDBOX_UNVERIFIED,
            setup_path=SetupPath.SANDBOX_UNVERIFIED,
            remediation=(
                "Use static validation only, or rerun from verified native Linux or WSL2.",
            ),
            evidence={
                "classification": "sandbox_unverified",
                "kernel_family": "linux",
                "sandbox_signal": "kernel_signal_missing",
            },
            **common,
        )

    return HostEnvironmentReport(
        environment=HostEnvironmentKind.NATIVE_LINUX,
        setup_path=SetupPath.NATIVE_LINUX,
        remediation=("Verify Incus readiness before live setup.",),
        evidence={
            "classification": "native_linux",
            "kernel_family": "linux",
            "kernel_signal": "present",
            "sandbox_signal": "absent",
        },
        **common,
    )


def _validate_setup_path(
    environment: HostEnvironmentKind,
    setup_path: SetupPath,
) -> None:
    expected_paths = {
        HostEnvironmentKind.NATIVE_LINUX: SetupPath.NATIVE_LINUX,
        HostEnvironmentKind.WSL2: SetupPath.WSL2,
        HostEnvironmentKind.WSL1_UNSUPPORTED: SetupPath.UNSUPPORTED,
        HostEnvironmentKind.UNKNOWN_UNSUPPORTED: SetupPath.UNSUPPORTED,
        HostEnvironmentKind.SANDBOX_UNVERIFIED: SetupPath.SANDBOX_UNVERIFIED,
    }
    expected_path = expected_paths[environment]
    if setup_path != expected_path:
        raise ValueError("host environment and setup path are inconsistent")


def _report_distribution(signals: HostEnvironmentSignals) -> str:
    return signals.wsl_distribution or signals.distribution or "unknown"


def _has_wsl_kernel_hint(kernel_signal: str) -> bool:
    return "microsoft" in kernel_signal or "wsl" in kernel_signal


def _has_wsl2_kernel_signal(kernel_signal: str) -> bool:
    return "wsl2" in kernel_signal and (
        "microsoft" in kernel_signal or "wsl" in kernel_signal
    )


def _has_wsl1_kernel_signal(kernel_signal: str) -> bool:
    return _WSL1_KERNEL_PATTERN.search(kernel_signal) is not None


def _presence_text(value: bool) -> str:
    return "present" if value else "absent"


def _normalized_host_field(value: object, *, fallback: str) -> str:
    text = " ".join(str(value).split())
    text = _HOST_FIELD_UNSAFE_CHARACTERS.sub("_", text).strip()
    return text[:HOST_FIELD_MAX_LENGTH] or fallback


def _normalized_signal_token(value: object, *, fallback: str) -> str:
    normalized = re.sub(r"[^a-z0-9_+-]", "_", str(value).casefold()).strip("_")
    return normalized[:40] or fallback


def _bounded_signal_text(value: object) -> str:
    normalized = _SIGNAL_WHITESPACE.sub(" ", str(value)).strip()
    return normalized[:SIGNAL_TEXT_MAX_LENGTH]
