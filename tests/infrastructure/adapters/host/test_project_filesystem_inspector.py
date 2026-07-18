import tempfile
import unittest
from pathlib import Path

from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind
from tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector import (
    ProjectFilesystemInspector,
)


class TestProjectFilesystemInspector(unittest.TestCase):
    def test_detects_windows_drive_mounts_generically(self):
        for drive in ("c", "d", "e", "z"):
            with self.subTest(drive=drive):
                inspector = ProjectFilesystemInspector(
                    mountinfo_reader=lambda drive=drive: _mountinfo(
                        f"/mnt/{drive}", "9p", "drvfs", "rw,aname=drvfs"
                    )
                )

                result = inspector.inspect(
                    f"/mnt/{drive}/Projects/Tiny-Swarm-World",
                    HostEnvironmentKind.WSL2,
                )

                self.assertEqual(ProjectFilesystemKind.WINDOWS_MOUNTED, result.kind)

    def test_detects_drvfs_outside_standard_automount_root(self):
        inspector = ProjectFilesystemInspector(
            mountinfo_reader=lambda: _mountinfo(
                "/workspace/windows", "v9fs", "host-share", "rw,aname=drvfs"
            )
        )

        result = inspector.inspect(
            "/workspace/windows/project",
            HostEnvironmentKind.WSL2,
        )

        self.assertEqual(ProjectFilesystemKind.WINDOWS_MOUNTED, result.kind)

    def test_mnt_data_is_not_a_drive_prefix_false_positive(self):
        inspector = ProjectFilesystemInspector(
            mountinfo_reader=lambda: _mountinfo("/", "ext4", "/dev/sda", "rw")
        )

        result = inspector.inspect("/mnt/data/project", HostEnvironmentKind.WSL2)

        self.assertEqual(ProjectFilesystemKind.WSL_LINUX, result.kind)

    def test_longest_matching_mountpoint_wins(self):
        mountinfo = "\n".join(
            (
                _mountinfo("/", "ext4", "/dev/sda", "rw"),
                _mountinfo("/mnt/d", "9p", "drvfs", "rw,aname=drvfs", mount_id=37),
            )
        )
        inspector = ProjectFilesystemInspector(mountinfo_reader=lambda: mountinfo)

        result = inspector.inspect("/mnt/d/project", HostEnvironmentKind.WSL2)

        self.assertEqual(ProjectFilesystemKind.WINDOWS_MOUNTED, result.kind)

    def test_mountinfo_octal_escapes_are_decoded(self):
        inspector = ProjectFilesystemInspector(
            mountinfo_reader=lambda: _mountinfo(
                "/mnt/My\\040Drive",
                "9p",
                "drvfs\\134share",
                "rw,aname=drvfs",
            )
        )

        result = inspector.inspect(
            "/mnt/My Drive/project",
            HostEnvironmentKind.WSL2,
        )

        self.assertEqual(ProjectFilesystemKind.WINDOWS_MOUNTED, result.kind)

    def test_resolved_symlink_target_is_classified(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            windows_mount = root / "windows"
            windows_mount.mkdir()
            project = windows_mount / "project"
            project.mkdir()
            link = root / "project-link"
            link.symlink_to(project, target_is_directory=True)
            inspector = ProjectFilesystemInspector(
                mountinfo_reader=lambda: _mountinfo(
                    windows_mount.as_posix(),
                    "9p",
                    "drvfs",
                    "rw,aname=drvfs",
                )
            )

            result = inspector.inspect(link.as_posix(), HostEnvironmentKind.WSL2)

        self.assertEqual(ProjectFilesystemKind.WINDOWS_MOUNTED, result.kind)
        self.assertEqual(project.resolve().as_posix(), result.resolved_project_path)

    def test_unreadable_or_unrecognized_wsl_mountinfo_is_unknown(self):
        cases = (
            lambda: (_ for _ in ()).throw(OSError("unreadable")),
            lambda: _mountinfo("/mnt/d", "9p", "unknown", "rw"),
            lambda: "malformed mountinfo",
        )
        for reader in cases:
            with self.subTest(reader=reader):
                result = ProjectFilesystemInspector(
                    mountinfo_reader=reader,
                ).inspect("/mnt/d/project", HostEnvironmentKind.WSL2)

                self.assertEqual(ProjectFilesystemKind.UNKNOWN, result.kind)

    def test_native_linux_never_depends_on_wsl_mountinfo(self):
        calls = 0

        def fail_reader() -> str:
            nonlocal calls
            calls += 1
            raise AssertionError("native Linux must not read WSL mount facts")

        result = ProjectFilesystemInspector(mountinfo_reader=fail_reader).inspect(
            "/srv/project",
            HostEnvironmentKind.NATIVE_LINUX,
        )

        self.assertEqual(ProjectFilesystemKind.NATIVE_LINUX, result.kind)
        self.assertEqual(0, calls)


def _mountinfo(
    mountpoint: str,
    filesystem_type: str,
    source: str,
    super_options: str,
    *,
    mount_id: int = 36,
) -> str:
    return (
        f"{mount_id} 25 0:32 / {mountpoint} rw,relatime - "
        f"{filesystem_type} {source} {super_options}"
    )
