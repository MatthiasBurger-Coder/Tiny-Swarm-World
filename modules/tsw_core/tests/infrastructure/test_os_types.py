import unittest

from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    SetupPath,
)
from tiny_swarm_world.infrastructure.os_types import OsTypes, _has_wsl_signal


class TestOsTypes(unittest.TestCase):
    def test_maps_wsl_values_to_wsl_linux(self):
        for value in ("wsl", "wsl2", "wsl_linux", "WSL_LINUX"):
            with self.subTest(value=value):
                self.assertEqual(OsTypes.WSL_LINUX, OsTypes.get_enum_from_value(value))

    def test_keeps_existing_linux_and_windows_mappings(self):
        self.assertEqual(OsTypes.LINUX, OsTypes.get_enum_from_value("Linux"))
        self.assertEqual(OsTypes.WINDOWS, OsTypes.get_enum_from_value("Windows"))

    def test_detect_current_rejects_typed_unsupported_windows_platform(self):
        detector = _Detector(
            _report(
                HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
                SetupPath.UNSUPPORTED,
                platform_family="windows",
            )
        )

        with self.assertRaises(ValueError):
            OsTypes.detect_current(detector)

    def test_detect_current_maps_typed_native_linux(self):
        detector = _Detector(
            _report(HostEnvironmentKind.NATIVE_LINUX, SetupPath.NATIVE_LINUX)
        )

        self.assertEqual(OsTypes.LINUX, OsTypes.detect_current(detector))

    def test_detect_current_maps_typed_wsl2(self):
        detector = _Detector(_report(HostEnvironmentKind.WSL2, SetupPath.WSL2))

        self.assertEqual(OsTypes.WSL_LINUX, OsTypes.detect_current(detector))
        self.assertTrue(_has_wsl_signal(detector))

    def test_detect_current_never_maps_wsl1_or_ambiguous_to_wsl_linux(self):
        cases = (
            _report(HostEnvironmentKind.WSL1_UNSUPPORTED, SetupPath.UNSUPPORTED),
            _report(HostEnvironmentKind.UNKNOWN_UNSUPPORTED, SetupPath.UNSUPPORTED),
        )
        for report in cases:
            with self.subTest(environment=report.environment.value):
                with self.assertRaises(ValueError):
                    OsTypes.detect_current(_Detector(report))

    def test_sandbox_fails_closed_without_claiming_native_linux_or_wsl(self):
        detector = _Detector(
            _report(
                HostEnvironmentKind.SANDBOX_UNVERIFIED,
                SetupPath.SANDBOX_UNVERIFIED,
            )
        )

        with self.assertRaises(ValueError):
            OsTypes.detect_current(detector)
        self.assertFalse(_has_wsl_signal(detector))


class _Detector:
    def __init__(self, report: HostEnvironmentReport) -> None:
        self.report = report

    def detect(self) -> HostEnvironmentReport:
        return self.report


def _report(
    environment: HostEnvironmentKind,
    setup_path: SetupPath,
    *,
    platform_family: str = "linux",
) -> HostEnvironmentReport:
    return HostEnvironmentReport(
        environment=environment,
        setup_path=setup_path,
        platform_family=platform_family,
        remediation=("Inspect host support.",),
        evidence={"classification": environment.value},
    )


if __name__ == "__main__":
    unittest.main()
