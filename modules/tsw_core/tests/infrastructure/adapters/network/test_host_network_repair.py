import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.application.ports.network import CommandObservation
from tiny_swarm_world.infrastructure.adapters.network import host_network_repair, wslconfig_files
from tiny_swarm_world.infrastructure.adapters.network.host_network_repair import (
    SubprocessNetworkRepair,
)


class TestHostNetworkRepair(unittest.TestCase):
    def setUp(self):
        guard = patch.object(host_network_repair, "_forwarding_write_targets", return_value=(host_network_repair.FORWARDING_SCRIPT_PATH, host_network_repair.FORWARDING_SERVICE_PATH))
        guard.start()
        self.addCleanup(guard.stop)
        installer = patch.object(host_network_repair, "_protected_forwarding_install", side_effect=lambda path, content, mode: _ok(f"protected install -m {mode:04o} {path}"))
        installer.start()
        self.addCleanup(installer.stop)

    def test_set_wsl_networking_mode_updates_existing_wsl2_section(self):
        content = "[wsl2]\nmemory=8GB\nnetworkingMode=mirrored\n[experimental]\nautoMemoryReclaim=gradual\n"

        updated = host_network_repair._set_wsl_networking_mode(content, "nat")

        self.assertIn("[wsl2]\nmemory=8GB\nnetworkingMode=nat\n", updated)
        self.assertIn("[experimental]\nautoMemoryReclaim=gradual", updated)
        self.assertNotIn("networkingMode=mirrored", updated)

    def test_set_wsl_networking_mode_adds_wsl2_section(self):
        updated = host_network_repair._set_wsl_networking_mode("[experimental]\nfoo=bar\n", "nat")

        self.assertTrue(updated.endswith("[wsl2]\nnetworkingMode=nat\n"))

    def test_forwarding_script_contains_scoped_idempotent_rules(self):
        script = host_network_repair._forwarding_script()
        service = host_network_repair._forwarding_service()

        self.assertIn('iptables -C FORWARD -i "$BRIDGE" -j ACCEPT', script)
        self.assertIn('iptables -C FORWARD -o "$BRIDGE" -m conntrack', script)
        self.assertIn('iptables -t nat -C POSTROUTING -s "$BRIDGE_NETWORK"', script)
        self.assertIn('ip link show dev "$BRIDGE"', script)
        self.assertIn("sleep 2", script)
        self.assertIn("did not become available within 60 seconds", script)
        self.assertIn("tsw-apply-incus-forwarding.sh", service)
        self.assertIn("TimeoutStartSec=75s", service)
        self.assertIn("RemainAfterExit=yes", service)
        self.assertIn("Restart=no", service)
        self.assertNotIn("RestartSec=", service)
        self.assertNotIn("StartLimitIntervalSec=0", service)
        self.assertIn("Wants=network-online.target incus.service", service)

    def test_forwarding_script_recovers_on_retry_after_bridge_appears(self):
        # Execute only stub commands, never host networking tools.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commands = {
                "ip": '#!/bin/bash\nif [ "$1" = link ]; then test -e "$TEST_BRIDGE"; else echo "inet 10.0.0.1/24"; fi\n',
                "sleep": "#!/bin/bash\nexit 0\n",
                "iptables": '#!/bin/bash\necho "$*" >> "$TEST_RULES"\n',
                # Drain the producer so pipefail does not depend on process scheduling.
                "sed": "#!/bin/bash\nwhile IFS= read -r _line; do :; done\necho 10.0.0.1/24\n",
            }
            for name, content in commands.items():
                path = root / name
                path.write_text(content)
                path.chmod(0o755)
            env = dict(os.environ, PATH=directory, TEST_BRIDGE=str(root / "bridge"),
                       TEST_RULES=str(root / "rules"))
            script = host_network_repair._forwarding_script()
            failed = subprocess.run(["/bin/bash", "-c", script], env=env,
                                    capture_output=True, text=True, timeout=5)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("did not become available", failed.stderr)
            self.assertFalse((root / "rules").exists())
            (root / "bridge").touch()
            recovered = subprocess.run(["/bin/bash", "-c", script], env=env,
                                       capture_output=True, text=True, timeout=5)
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertIn("FORWARD -i incusbr0", (root / "rules").read_text())

    def test_incus_runtime_file_guard_accepts_only_expected_pid_path(self):
        self.assertTrue(
            host_network_repair._inside_incus_network_dir(
                "/var/lib/incus/networks/incusbr0/dnsmasq.pid"
            )
        )

    def test_dnsmasq_pid_parser_rejects_incus_metadata(self):
        self.assertEqual("12345", host_network_repair._parse_numeric_pid(" 12345\n"))
        self.assertIsNone(
            host_network_repair._parse_numeric_pid(
                "name: dnsmasq\nargs: --keep-in-foreground\n"
            )
        )
        self.assertFalse(host_network_repair._inside_incus_network_dir("/tmp/dnsmasq.pid"))
        self.assertFalse(
            host_network_repair._inside_incus_network_dir(
                "/var/lib/incus/networks/other/dnsmasq.pid"
            )
        )

    def test_wslconfig_path_guard_reconstructs_only_windows_user_profile_path(self):
        self.assertEqual(
            Path("/mnt/c/Users/micro/.wslconfig"),
            host_network_repair._wslconfig_path_from_mapped_profile("/mnt/c/Users/micro"),
        )
        self.assertIsNone(host_network_repair._wslconfig_path_from_mapped_profile("/tmp/user"))
        self.assertIsNone(
            host_network_repair._wslconfig_path_from_mapped_profile(
                "/mnt/c/Users/micro/../../Windows"
            )
        )

    def test_wsl_nat_repair_blocks_untrusted_mapped_profile_path(self):
        executor = _SequenceExecutor(
            (
                _ok(
                    "powershell.exe -NoProfile -Command",
                    "C:\\Users\\micro",
                ),
                _ok("wslpath -u", "/tmp/micro"),
            )
        )
        repair = SubprocessNetworkRepair(executor=executor)

        result = repair._apply_wsl2_nat_runtime()

        self.assertFalse(result.success)
        self.assertIn("Refused to update .wslconfig", result.message)

    def test_incus_repair_restarts_without_stale_pid_file(self):
        executor = _MappingExecutor(
            {
                "test -e /var/lib/incus/networks/incusbr0/dnsmasq.pid": _failed(
                    "test -e /var/lib/incus/networks/incusbr0/dnsmasq.pid"
                ),
                "systemctl restart incus": _ok("systemctl restart incus"),
                "incus network list": _ok("incus network list", "incusbr0"),
                "incus network info incusbr0": _ok("incus network info incusbr0", "State: up"),
            }
        )
        repair = SubprocessNetworkRepair(executor=executor)

        result = repair._apply_incus_repair()

        self.assertTrue(result.success)
        self.assertIn("No stale Incus dnsmasq.pid file was present.", result.details)

    def test_incus_repair_removes_stale_pid_file_after_guard_checks(self):
        executor = _MappingExecutor(
            {
                "test -e /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok("test -e"),
                "realpath -m -- /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok(
                    "realpath",
                    "/var/lib/incus/networks/incusbr0/dnsmasq.pid",
                ),
                "cat /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok("cat", "12345"),
                "pgrep -x dnsmasq": _failed("pgrep"),
                "ps -p 12345": _failed("ps"),
                "rm -f -- /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok("rm"),
                "systemctl restart incus": _ok("systemctl restart incus"),
                "incus network list": _ok("incus network list", "incusbr0"),
                "incus network info incusbr0": _ok("incus network info incusbr0", "State: up"),
            }
        )
        repair = SubprocessNetworkRepair(executor=executor)

        result = repair._apply_incus_repair()

        self.assertTrue(result.success)
        self.assertIn("About to remove stale Incus runtime file:", result.details)

    def test_incus_repair_refuses_when_dnsmasq_process_is_running(self):
        executor = _MappingExecutor(
            {
                "test -e /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok("test -e"),
                "realpath -m -- /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok(
                    "realpath",
                    "/var/lib/incus/networks/incusbr0/dnsmasq.pid",
                ),
                "cat /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok("cat", "12345"),
                "pgrep -x dnsmasq": _ok("pgrep"),
                "ps -p 12345": _failed("ps"),
            }
        )
        repair = SubprocessNetworkRepair(executor=executor)

        result = repair._apply_incus_repair()

        self.assertFalse(result.success)
        self.assertIn("dnsmasq process is running", result.message)

    def test_incus_repair_refuses_non_numeric_pid_without_process_command(self):
        executor = _MappingExecutor(
            {
                "test -e /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok("test -e"),
                "realpath -m -- /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok(
                    "realpath",
                    "/var/lib/incus/networks/incusbr0/dnsmasq.pid",
                ),
                "cat /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok(
                    "cat", "name: dnsmasq\nargs: --keep-in-foreground"
                ),
                "pgrep -x dnsmasq": _failed("pgrep"),
            }
        )
        repair = SubprocessNetworkRepair(executor=executor)

        result = repair._apply_incus_repair()

        self.assertFalse(result.success)
        self.assertIn("does not contain a numeric PID", result.message)
        self.assertFalse(any(command.startswith("ps -p") for command in executor.calls))

    def test_incus_repair_refuses_when_pid_path_is_outside_incus_network_dir(self):
        executor = _MappingExecutor(
            {
                "test -e /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok("test -e"),
                "realpath -m -- /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok(
                    "realpath",
                    "/tmp/dnsmasq.pid",
                ),
                "cat /var/lib/incus/networks/incusbr0/dnsmasq.pid": _ok("cat", "12345"),
                "pgrep -x dnsmasq": _failed("pgrep"),
                "ps -p 12345": _failed("ps"),
            }
        )
        repair = SubprocessNetworkRepair(executor=executor)

        result = repair._apply_incus_repair()

        self.assertFalse(result.success)
        self.assertIn("outside the incusbr0 directory", result.message)

    def test_linux_forwarding_repair_installs_service_and_verifies_node_egress(self):
        executor = _DefaultOkExecutor()
        repair = SubprocessNetworkRepair(executor=executor)

        result = repair._apply_linux_forwarding("incusbr0", "swarm-manager")

        self.assertTrue(result.success)
        commands = tuple(command.command for command in result.commands)
        self.assertTrue(any("install -m 0755" in command for command in commands))
        self.assertTrue(any("systemctl enable tsw-incus-forwarding.service" in command for command in commands))
        self.assertTrue(any("incus exec swarm-manager -- curl" in command for command in commands))
        self.assertTrue(any("systemctl restart tsw-incus-forwarding.service" in command for command in commands))
        self.assertTrue(any("--fail" in command and "--max-time" in command for command in commands))

    def test_linux_forwarding_repair_does_not_claim_success_when_restart_or_http_fails(self):
        for failed_command in ("systemctl restart", "curl"):
            with self.subTest(failed_command=failed_command):
                def executor(command, timeout):
                    if failed_command in command:
                        return _failed(command)
                    return _ok(command)

                result = SubprocessNetworkRepair(executor=executor)._apply_linux_forwarding(
                    "incusbr0", "swarm-manager"
                )
                self.assertFalse(result.success)

    def test_linux_forwarding_repair_reports_failed_install(self):
        executor = _MappingExecutor(
            {
                "install -m 0755": _failed("install script"),
                "install -m 0644": _ok("install service"),
            }
        )
        repair = SubprocessNetworkRepair(executor=executor)

        with patch.object(host_network_repair, "_protected_forwarding_install", return_value=_failed("protected install")):
            result = repair._apply_linux_forwarding("incusbr0", "swarm-manager")

        self.assertFalse(result.success)
        self.assertEqual(result.message, "Failed to install forwarding persistence files.")

    def test_windows_scripts_read_ports_from_registry(self):
        root = Path(__file__).resolve().parents[6]
        repair_script = root / "modules/tsw_windows_wsl/bootstrap" / "repair-wsl-portproxy.ps1"
        doctor_script = root / "modules/tsw_windows_wsl/bootstrap" / "doctor-portproxy.ps1"

        for script in (repair_script, doctor_script):
            text = script.read_text(encoding="utf-8")
            self.assertIn("modules/tsw_core/infra/config/ports.yaml", text)
            self.assertIn("Get-TswBridgePorts", text)
            self.assertNotIn("$ports = @(", text)


class TestWslConfigConfinement(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.profile = self.root / "Users" / "test user"
        self.profile.mkdir(parents=True)
        self.config = self.profile / ".wslconfig"
        self.original = "[wsl2]\nmemory=8GB\nnetworkingMode=mirrored\n"
        clock = patch.object(wslconfig_files, "datetime")
        self.clock = clock.start()
        self.addCleanup(clock.stop)
        self.clock.now.return_value.strftime.return_value = "20261110220000"
        self.backup = self.profile / ".wslconfig.bak-20261110220000"

    def repair(self, path=None):
        executor = _SequenceExecutor((
            _ok("profile", "C:\\Users\\test user"),
            _ok("mapped profile", "/mnt/c/Users/test user"),
        ))
        with patch.object(host_network_repair, "_wslconfig_path_from_mapped_profile",
                          return_value=self.config if path is None else path):
            return SubprocessNetworkRepair(executor=executor)._apply_wsl2_nat_runtime()

    def assert_refused(self, result):
        self.assertFalse(result.success)
        self.assertFalse(result.applied)

    def test_parent_name_cannot_escape_windows_users_directory(self):
        for mapped in ("/mnt/c/Users/..", "/mnt/c/Users/../Windows"):
            with self.subTest(mapped=mapped):
                self.assertIsNone(host_network_repair._wslconfig_path_from_mapped_profile(mapped))
        for name in ("test user", "micro.admin", "_micro"):
            with self.subTest(name=name):
                self.assertEqual(host_network_repair._wslconfig_path_from_mapped_profile(
                    f"/mnt/c/Users/{name}"), Path(f"/mnt/c/Users/{name}/.wslconfig"))

    def test_windows_trailing_aliases_and_unexpected_path_whitespace_are_refused(self):
        for mapped in ("/mnt/c/Users/demo.", "/mnt/c/Users/demo ", "/mnt/c/Users/demo /",
                       "/mnt/c/Users/.. .", " /mnt/c/Users/demo", "/mnt/c/Users/demo\t"):
            with self.subTest(mapped=mapped):
                self.assertIsNone(host_network_repair._wslconfig_path_from_mapped_profile(mapped))
        for name in ("test user", "micro.admin"):
            self.assertEqual(host_network_repair._wslconfig_path_from_mapped_profile(
                f"/mnt/c/Users/{name}\r\n"), Path(f"/mnt/c/Users/{name}/.wslconfig"))

    def test_supported_existing_config_retains_exact_backup_and_other_settings(self):
        self.config.write_text(self.original)
        before = self.config.stat()
        result = self.repair()
        self.assertTrue(result.success)
        self.assertTrue(result.applied)
        self.assertEqual(self.backup.read_text(), self.original)
        self.assertEqual(self.config.read_text(), self.original.replace("mirrored", "nat"))
        self.assertEqual((self.config.stat().st_ino, self.config.stat().st_mode),
                         (before.st_ino, before.st_mode))

    def test_supported_missing_config_does_not_invent_a_backup(self):
        result = self.repair()
        self.assertTrue(result.success)
        self.assertIn("networkingMode=nat", self.config.read_text())
        self.assertFalse(self.backup.exists())

    def test_existing_and_dangling_config_symlinks_preserve_outside_target(self):
        outside = self.root / "outside.ini"
        for present in (True, False):
            with self.subTest(present=present):
                if present:
                    outside.write_text(self.original)
                self.config.symlink_to(outside)
                try:
                    self.assert_refused(self.repair())
                    self.assertTrue(self.config.is_symlink())
                    self.assertEqual(outside.read_text() if present else None,
                                     self.original if present else None)
                    self.assertEqual(outside.exists(), present)
                    self.assertFalse(self.backup.exists())
                finally:
                    self.config.unlink(missing_ok=True)
                    outside.unlink(missing_ok=True)
                    self.backup.unlink(missing_ok=True)

    def test_symlinked_profile_directory_is_never_followed(self):
        outside = self.root / "other profile"
        outside.mkdir()
        target = outside / ".wslconfig"
        target.write_text(self.original)
        alias = self.profile.parent / "profile alias"
        alias.symlink_to(outside, target_is_directory=True)
        self.assert_refused(self.repair(alias / ".wslconfig"))
        self.assertEqual(target.read_text(), self.original)
        self.assertEqual(sorted(p.name for p in outside.iterdir()), [".wslconfig"])

    def test_existing_backup_entries_are_not_overwritten_or_followed(self):
        self.config.write_text(self.original)
        outside = self.root / "backup target"
        outside.write_text("retained external backup")
        for linked in (False, True):
            with self.subTest(linked=linked):
                if linked:
                    self.backup.symlink_to(outside)
                else:
                    self.backup.write_text("retained existing backup")
                try:
                    self.assert_refused(self.repair())
                    self.assertEqual(self.config.read_text(), self.original)
                    self.assertEqual(outside.read_text(), "retained external backup")
                    self.assertEqual(self.backup.is_symlink(), linked)
                    self.assertEqual(self.backup.read_text(),
                                     "retained external backup" if linked else "retained existing backup")
                finally:
                    self.backup.unlink(missing_ok=True)

    def test_nonregular_or_oversize_config_is_refused_without_backup_or_write(self):
        for kind in ("directory", "fifo", "oversize", "hardlink"):
            with self.subTest(kind=kind):
                outside = self.root / "unrelated hardlink target"
                if kind == "directory":
                    self.config.mkdir()
                elif kind == "fifo":
                    os.mkfifo(self.config)
                elif kind == "oversize":
                    self.config.write_bytes(b"x" * 65537)
                else:
                    outside.write_text(self.original)
                    os.link(outside, self.config)
                before = self.config.lstat()
                try:
                    self.assert_refused(self.repair())
                    self.assertFalse(self.backup.exists())
                    after = self.config.lstat()
                    self.assertEqual((after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns),
                                     (before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns))
                    if kind == "oversize":
                        self.assertEqual(self.config.read_bytes(), b"x" * 65537)
                    if kind == "hardlink":
                        self.assertEqual(outside.read_text(), self.original)
                finally:
                    if kind == "directory":
                        self.config.rmdir()
                    else:
                        self.config.unlink(missing_ok=True)
                    outside.unlink(missing_ok=True)

    def test_config_replacement_after_read_is_not_modified(self):
        self.config.write_text(self.original)
        outside = self.root / "replacement target"
        outside.write_text("unrelated external state")
        transform = host_network_repair._set_wsl_networking_mode

        def replace(content, mode):
            self.config.unlink()
            self.config.symlink_to(outside)
            return transform(content, mode)

        with patch.object(host_network_repair, "_set_wsl_networking_mode", side_effect=replace):
            self.assert_refused(self.repair())
        self.assertEqual(outside.read_text(), "unrelated external state")
        self.assertTrue(self.config.is_symlink())

    def test_backup_replacement_blocks_config_write_and_reports_the_created_effect(self):
        self.config.write_text(self.original)
        outside = self.root / "replacement backup"
        outside.write_text("unrelated external backup")
        sync = os.fsync

        def replace(descriptor):
            sync(descriptor)
            self.backup.unlink()
            self.backup.symlink_to(outside)

        with patch.object(wslconfig_files.os, "fsync", side_effect=replace):
            result = self.repair()
        self.assertFalse(result.success)
        self.assertTrue(result.applied)
        self.assertEqual(self.config.read_text(), self.original)
        self.assertEqual(outside.read_text(), "unrelated external backup")
        self.assertTrue(self.backup.is_symlink())

    def test_same_inode_backup_tamper_blocks_config_write(self):
        self.config.write_text(self.original)
        tampered = self.original.encode().replace(b"mirrored", b"external")
        sync = os.fsync

        def tamper_backup(descriptor):
            sync(descriptor)
            opened = os.fstat(descriptor)
            backup = self.backup.stat()
            if (opened.st_dev, opened.st_ino) == (backup.st_dev, backup.st_ino):
                self.backup.write_bytes(tampered)

        with patch.object(wslconfig_files.os, "fsync", side_effect=tamper_backup):
            result = self.repair()
        self.assertFalse(result.success)
        self.assertTrue(result.applied)
        self.assertEqual(self.config.read_text(), self.original)
        self.assertEqual(self.backup.read_bytes(), tampered)

    def test_failed_config_sync_retains_exact_backup_and_reports_partial_effect(self):
        self.config.write_text(self.original)
        sync = os.fsync
        identity = (self.config.stat().st_dev, self.config.stat().st_ino)

        def fail_config_sync(descriptor):
            observed = os.fstat(descriptor)
            if (observed.st_dev, observed.st_ino) == identity:
                raise OSError("synthetic config sync failure")
            sync(descriptor)

        with patch.object(wslconfig_files.os, "fsync", side_effect=fail_config_sync):
            result = self.repair()
        self.assertFalse(result.success)
        self.assertTrue(result.applied)
        self.assertEqual(self.backup.read_text(), self.original)
        self.assertIn("networkingMode=nat", self.config.read_text())

    def test_backup_directory_sync_failure_preserves_config_and_reports_created_backup(self):
        self.config.write_text(self.original)
        sync = os.fsync
        directories = []

        def fail_directory_sync(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directories.append(descriptor)
                raise OSError("synthetic directory sync failure")
            sync(descriptor)

        with patch.object(wslconfig_files.os, "fsync", side_effect=fail_directory_sync):
            result = self.repair()
        self.assertFalse(result.success)
        self.assertTrue(result.applied)
        self.assertTrue(directories)
        self.assertEqual(self.config.read_text(), self.original)
        self.assertEqual(self.backup.read_text(), self.original)

    def tamper_after_config_sync(self, change):
        sync = os.fsync
        identity = (self.config.stat().st_dev, self.config.stat().st_ino)

        def tamper(descriptor):
            sync(descriptor)
            observed = os.fstat(descriptor)
            if (observed.st_dev, observed.st_ino) == identity:
                change(descriptor)

        return patch.object(wslconfig_files.os, "fsync", side_effect=tamper)

    def test_same_inode_content_change_after_write_is_not_reported_success(self):
        self.config.write_text(self.original)
        before = self.config.stat().st_ino
        tampered = "[wsl2]\nnetworkingMode=mirrored\n"
        with self.tamper_after_config_sync(lambda _descriptor: self.config.write_text(tampered)):
            result = self.repair()
        self.assertFalse(result.success)
        self.assertTrue(result.applied)
        self.assertEqual(self.config.stat().st_ino, before)
        self.assertEqual(self.config.read_text(), tampered)
        self.assertEqual(self.backup.read_text(), self.original)

    def test_file_metadata_change_after_write_is_not_reported_success(self):
        self.config.write_text(self.original)
        before = self.config.stat().st_mode
        with self.tamper_after_config_sync(lambda descriptor: os.fchmod(descriptor, before ^ 0o100)):
            result = self.repair()
        self.assertFalse(result.success)
        self.assertTrue(result.applied)
        self.assertNotEqual(self.config.stat().st_mode, before)
        self.assertIn("networkingMode=nat", self.config.read_text())
        self.assertEqual(self.backup.read_text(), self.original)

    def test_parent_replacement_after_read_cannot_redirect_the_write(self):
        self.config.write_text(self.original)
        outside = self.root / "replacement profile"
        outside.mkdir()
        target = outside / ".wslconfig"
        target.write_text("unrelated external state")
        retained = self.root / "retained profile"
        transform = host_network_repair._set_wsl_networking_mode

        def replace(content, mode):
            self.profile.rename(retained)
            self.profile.symlink_to(outside, target_is_directory=True)
            return transform(content, mode)

        with patch.object(host_network_repair, "_set_wsl_networking_mode", side_effect=replace):
            self.assert_refused(self.repair())
        self.assertEqual(target.read_text(), "unrelated external state")
        self.assertEqual((retained / ".wslconfig").read_text(), self.original)


class _SequenceExecutor:
    def __init__(self, observations: tuple[CommandObservation, ...]) -> None:
        self.observations = list(observations)

    def __call__(self, command: str, _timeout: int) -> CommandObservation:
        observation = self.observations.pop(0)
        return CommandObservation(
            command=command,
            return_code=observation.return_code,
            stdout=observation.stdout,
            stderr=observation.stderr,
        )


class _MappingExecutor:
    def __init__(self, observations: dict[str, CommandObservation]) -> None:
        self.observations = observations
        self.calls: list[str] = []

    def __call__(self, command: str, _timeout: int) -> CommandObservation:
        self.calls.append(command)
        for expected, observation in self.observations.items():
            if expected in command:
                return CommandObservation(
                    command=command,
                    return_code=observation.return_code,
                    stdout=observation.stdout,
                    stderr=observation.stderr,
                )
        return _failed(command, "unexpected command")


class _DefaultOkExecutor:
    def __call__(self, command: str, _timeout: int) -> CommandObservation:
        return _ok(command, "HTTP/1.1 200 OK" if "curl" in command else "")


def _ok(command: str, stdout: str = "") -> CommandObservation:
    return CommandObservation(command=command, return_code=0, stdout=stdout)


def _failed(command: str, stderr: str = "failed") -> CommandObservation:
    return CommandObservation(command=command, return_code=1, stderr=stderr)


if __name__ == "__main__":
    unittest.main()


class TestForwardingOwnerCollisions(unittest.TestCase):
    def test_byte_compatible_owner_requires_exact_mode_and_never_replaces_w06(self):
        from tiny_swarm_world.infrastructure.adapters.network_preparation.files import FileObservation

        def compatible(path):
            script = path == host_network_repair.FORWARDING_SCRIPT_PATH
            content = host_network_repair._forwarding_script() if script else host_network_repair._forwarding_service()
            return FileObservation(True, content.encode(), "observed", 0o755 if script else 0o644, 0, 0)

        with patch("tiny_swarm_world.infrastructure.adapters.network_preparation.files.observe", side_effect=compatible):
            self.assertEqual(host_network_repair._forwarding_write_targets(), ())
        for content, mode in ((host_network_repair._forwarding_script().encode(), 0o644), (b"W06 scoped owner", 0o755)):
            observed = FileObservation(True, content, "observed", mode, 0, 0)
            with patch("tiny_swarm_world.infrastructure.adapters.network_preparation.files.observe", return_value=observed):
                with self.assertRaises(RuntimeError):
                    host_network_repair._forwarding_write_targets()
