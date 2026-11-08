import unittest

from tiny_swarm_world.application.services.platform.host import DetectHostEnvironment
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    SetupPath,
)


class TestDetectHostEnvironment(unittest.TestCase):
    def test_delegates_once_and_preserves_supported_report(self):
        report = _report(HostEnvironmentKind.WSL2, SetupPath.WSL2)
        detector = _Detector(report)

        actual = DetectHostEnvironment(detector).run()

        self.assertIs(report, actual)
        self.assertEqual(detector.calls, 1)

    def test_preserves_unsupported_report_without_reclassification(self):
        report = _report(
            HostEnvironmentKind.WSL1_UNSUPPORTED,
            SetupPath.UNSUPPORTED,
        )

        actual = DetectHostEnvironment(_Detector(report)).run()

        self.assertIs(report, actual)
        self.assertFalse(actual.supported)


class _Detector:
    def __init__(self, report: HostEnvironmentReport) -> None:
        self.report = report
        self.calls = 0

    def detect(self) -> HostEnvironmentReport:
        self.calls += 1
        return self.report


def _report(
    environment: HostEnvironmentKind,
    setup_path: SetupPath,
) -> HostEnvironmentReport:
    return HostEnvironmentReport(
        environment=environment,
        setup_path=setup_path,
        distribution="Ubuntu",
        kernel_release="6.1.0-synthetic",
        windows_interop_available=environment is HostEnvironmentKind.WSL2,
        remediation=("Inspect the host classification.",),
        evidence={"classification": environment.value},
    )
