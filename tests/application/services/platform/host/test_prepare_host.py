import unittest
from unittest.mock import Mock

from tiny_swarm_world.application.services.platform.host import (
    HostPreparationAdapterFactory,
    HostPreparationService,
)
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentReport,
    HostPreparationResult,
    HostPreparationStatus,
    LiveConsent,
    SetupPath,
)


def _report(environment: HostEnvironmentKind) -> HostEnvironmentReport:
    return HostEnvironmentReport(
        environment=environment,
        distribution="Ubuntu",
        kernel_release="6.1-wsl2",
        platform_family="linux",
        windows_interop_available=environment is HostEnvironmentKind.WSL2,
        setup_path=SetupPath.WSL2 if environment is HostEnvironmentKind.WSL2 else SetupPath.NATIVE_LINUX,
        remediation=(),
        evidence={},
    )


class TestHostPreparationService(unittest.TestCase):
    def test_native_linux_selects_native_adapter_without_windows_runner(self):
        detector = Mock(detect=Mock(return_value=_report(HostEnvironmentKind.NATIVE_LINUX)))
        native = Mock()
        native.prepare.return_value = HostPreparationResult(
            "prepare", "native_linux", HostPreparationStatus.SUCCESS, "ok"
        )
        wsl = Mock()

        result = HostPreparationService(detector, native, wsl, _consent()).prepare()

        self.assertTrue(result.succeeded)
        native.prepare.assert_called_once_with()
        wsl.prepare.assert_not_called()

    def test_wsl2_selects_dedicated_adapter(self):
        detector = Mock(detect=Mock(return_value=_report(HostEnvironmentKind.WSL2)))
        native = Mock()
        wsl = Mock()
        wsl.prepare.return_value = HostPreparationResult(
            "prepare", "wsl2", HostPreparationStatus.SUCCESS, "ok"
        )

        result = HostPreparationService(detector, native, wsl, _consent()).prepare()

        self.assertEqual("wsl2", result.host_environment)
        wsl.prepare.assert_called_once_with()
        native.prepare.assert_not_called()

    def test_mutation_is_blocked_without_consent_before_detection(self):
        detector = Mock()
        result = HostPreparationService(detector, Mock(), Mock()).prepare()

        self.assertEqual(HostPreparationStatus.BLOCKED, result.status)
        detector.detect.assert_not_called()

    def test_verify_is_allowed_without_consent(self):
        detector = Mock(detect=Mock(return_value=_report(HostEnvironmentKind.NATIVE_LINUX)))
        native = Mock()
        native.verify.return_value = HostPreparationResult(
            "verify", "native_linux", HostPreparationStatus.SUCCESS, "ok"
        )

        result = HostPreparationService(detector, native, Mock()).verify()

        self.assertTrue(result.succeeded)
        native.verify.assert_called_once_with()

    def test_factory_for_wsl_is_not_created_on_native_linux(self):
        detector = Mock(detect=Mock(return_value=_report(HostEnvironmentKind.NATIVE_LINUX)))
        native = Mock()
        native.prepare.return_value = HostPreparationResult(
            "prepare", "native_linux", HostPreparationStatus.SUCCESS, "ok"
        )
        native_factory = Mock(return_value=native)
        wsl_factory = Mock()

        result = HostPreparationService(
            detector,
            HostPreparationAdapterFactory(native_factory),
            HostPreparationAdapterFactory(wsl_factory),
            _consent(),
        ).prepare()

        self.assertTrue(result.succeeded)
        native_factory.assert_called_once_with()
        wsl_factory.assert_not_called()


def _consent() -> LiveConsent:
    return LiveConsent(True, confirmed=True)
