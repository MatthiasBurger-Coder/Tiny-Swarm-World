import asyncio
import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

from tiny_swarm_world import __main__ as entrypoint
from tiny_swarm_world.application.services.platform.preflight_service import (
    PreflightService,
)
from tiny_swarm_world.application.services.platform.host.evaluate_project_filesystem import (
    EvaluateProjectFilesystem,
)
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    PreflightCheck,
    PreflightStatus,
)
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.host import HostEnvironmentDetector
from tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector import (
    ProjectFilesystemInspector,
)
from tiny_swarm_world.infrastructure.adapters.preflight import HostPreflightProbe


class TestHostPlatformPaths(unittest.IsolatedAsyncioTestCase):
    async def test_native_linux_simulated_detector_preflight_and_cli_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _write(root, "proc/version", "Linux version 6.8.0-generic\n")
            _write(root, "proc/sys/kernel/osrelease", "6.8.0-generic\n")
            _write(root, "etc/os-release", 'PRETTY_NAME="Ubuntu 24.04 LTS"\n')
            detector = HostEnvironmentDetector(
                os_root=root,
                environment={},
                platform_system=lambda: "Linux",
            )

            report, host_check, filesystem_check, cli_output = await _exercise_path(
                root, detector
            )

        self.assertEqual(HostEnvironmentKind.NATIVE_LINUX, report.environment)
        self.assertEqual(PreflightStatus.PASSED, host_check.status)
        self.assertEqual(PreflightStatus.PASSED, filesystem_check.status)
        self.assertEqual("native_linux", host_check.evidence["environment"])
        self.assertIn('"environment": "native_linux"', cli_output)
        self.assertIn('"windows_interop_available": false', cli_output)

    async def test_wsl2_simulated_detector_preflight_and_cli_path(self):
        interop_value = "/run/WSL/synthetic_interop"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _write(
                root,
                "proc/version",
                "Linux version 6.1.21.2-microsoft-standard-WSL2\n",
            )
            _write(
                root,
                "proc/sys/kernel/osrelease",
                "6.1.21.2-microsoft-standard-WSL2\n",
            )
            detector = HostEnvironmentDetector(
                os_root=root,
                environment={
                    "WSL_DISTRO_NAME": "Ubuntu-24.04",
                    "WSL_INTEROP": interop_value,
                },
                platform_system=lambda: "Linux",
            )

            report, host_check, filesystem_check, cli_output = await _exercise_path(
                root, detector
            )

        self.assertEqual(HostEnvironmentKind.WSL2, report.environment)
        self.assertEqual("Ubuntu-24.04", report.distribution)
        self.assertEqual(
            "6.1.21.2-microsoft-standard-WSL2",
            report.kernel_release,
        )
        self.assertTrue(report.windows_interop_available)
        self.assertEqual(PreflightStatus.PASSED, host_check.status)
        self.assertEqual(PreflightStatus.PASSED, filesystem_check.status)
        self.assertEqual("wsl2", host_check.evidence["environment"])
        self.assertIn('"environment": "wsl2"', cli_output)
        self.assertNotIn(interop_value, cli_output)

    async def test_wsl2_windows_mount_is_blocked_without_path_leak(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _write(
                root,
                "proc/sys/kernel/osrelease",
                "6.1.21.2-microsoft-standard-WSL2\n",
            )
            detector = HostEnvironmentDetector(
                os_root=root,
                environment={"WSL_DISTRO_NAME": "Ubuntu-24.04"},
                platform_system=lambda: "Linux",
            )
            project_path = Path("/mnt/d/private/project")

            _, _, filesystem_check, _ = await _exercise_path(
                root,
                detector,
                project_path=project_path,
                mountinfo=(
                    "36 25 0:32 / /mnt/d rw,relatime - "
                    "9p drvfs rw,aname=drvfs"
                ),
            )

        self.assertEqual(PreflightStatus.FAILED, filesystem_check.status)
        self.assertEqual("blocked", filesystem_check.evidence["decision"])
        self.assertNotIn(project_path.as_posix(), str(filesystem_check.to_dict()))


async def _exercise_path(
    root: Path,
    detector: HostEnvironmentDetector,
    *,
    project_path: Path | None = None,
    mountinfo: str = "36 25 0:32 / / rw,relatime - ext4 /dev/sda rw",
) -> tuple[HostEnvironmentReport, PreflightCheck, PreflightCheck, str]:
    service = composition.build_host_detection_service(detector)
    probe = HostPreflightProbe(
        root,
        os_root=root,
        host_environment_detector=detector,
    )
    original_open = Path.open

    def guarded_open(path: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError("host detection path must not write files")
        return original_open(path, mode, *args, **kwargs)

    with (
        patch.object(probe, "executable_available", return_value=True),
        patch.object(probe, "cpu_count", return_value=16),
        patch.object(probe, "memory_bytes", return_value=32 * 1024**3),
        patch.object(probe, "disk_free_bytes", return_value=250 * 1024**3),
        patch.object(probe, "port_available", return_value=True),
        patch.object(probe, "port_matches_expected_service", return_value=False),
        patch.object(probe, "secret_available", return_value=True),
        patch.object(probe, "path_ignored_by_git", return_value=True),
        patch.object(
            probe,
            "forbidden_tracked_secret_fingerprints",
            return_value=(),
        ),
        patch.object(
            subprocess,
            "run",
            side_effect=AssertionError("host detection path must not run processes"),
        ),
        patch.object(
            asyncio,
            "create_subprocess_exec",
            side_effect=AssertionError("host detection path must not spawn processes"),
        ),
        patch.object(
            asyncio,
            "create_subprocess_shell",
            side_effect=AssertionError("host detection path must not spawn a shell"),
        ),
        patch.object(
            os,
            "system",
            side_effect=AssertionError("host detection path must not invoke a shell"),
        ),
        patch.object(Path, "open", new=guarded_open),
    ):
        report = service.run()
        preflight = await PreflightService(
            probe,
            project_filesystem_evaluator=EvaluateProjectFilesystem(
                ProjectFilesystemInspector(mountinfo_reader=lambda: mountinfo)
            ),
            project_path=str(project_path or root),
        ).run()
        host_check = next(check for check in preflight.checks if check.check_id == "HOST")
        filesystem_check = next(
            check for check in preflight.checks if check.check_id == "HOST-FILESYSTEM"
        )
        output = io.StringIO()
        with (
            patch.object(
                entrypoint,
                "build_host_detection_service",
                return_value=service,
            ),
            redirect_stdout(output),
        ):
            await entrypoint.main(["--json", "host", "detect"])

    return report, host_check, filesystem_check, output.getvalue()


def _write(root: Path, relative_path: str, text: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
