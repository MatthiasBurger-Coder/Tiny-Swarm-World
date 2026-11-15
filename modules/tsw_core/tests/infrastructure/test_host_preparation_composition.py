import unittest
from unittest.mock import Mock, patch

from tiny_swarm_world.domain.host_environment import HostEnvironmentKind, HostEnvironmentReport, SetupPath
from tiny_swarm_world.domain.preflight import HostPreparationResult, HostPreparationStatus
from tiny_swarm_world.infrastructure import composition_platform


class TestHostPreparationComposition(unittest.TestCase):
    def test_composition_routes_native_host_and_blocks_removed_wsl_preparation(self):
        native = Mock()
        native.verify.return_value = HostPreparationResult(
            "verify", "native_linux", HostPreparationStatus.SUCCESS, "native"
        )
        detector = Mock()
        with (
            patch.object(composition_platform, "build_host_environment_detector", return_value=detector),
            patch.object(composition_platform, "_build_native_linux_host_preparation", return_value=native) as native_factory,
        ):
            service = composition_platform.build_host_preparation_service()
            self.assertEqual(
                {HostEnvironmentKind.NATIVE_LINUX},
                set(service.adapters),
            )
            native_factory.assert_not_called()

            detector.detect.return_value = _report(HostEnvironmentKind.NATIVE_LINUX, SetupPath.NATIVE_LINUX)
            self.assertEqual("native", service.verify().message)
            native_factory.assert_called_once_with()

            detector.detect.return_value = _report(HostEnvironmentKind.WSL2, SetupPath.WSL2)
            self.assertEqual(HostPreparationStatus.BLOCKED, service.verify().status)
            native_factory.assert_called_once_with()


def _report(environment: HostEnvironmentKind, setup_path: SetupPath) -> HostEnvironmentReport:
    return HostEnvironmentReport(environment=environment, setup_path=setup_path)
