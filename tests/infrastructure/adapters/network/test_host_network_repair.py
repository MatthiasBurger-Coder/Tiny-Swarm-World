import unittest
from pathlib import Path

from tiny_swarm_world.application.ports.network import CommandObservation
from tiny_swarm_world.infrastructure.adapters.network import host_network_repair
from tiny_swarm_world.infrastructure.adapters.network.host_network_repair import (
    SubprocessNetworkRepair,
)


class TestHostNetworkRepair(unittest.TestCase):
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
        self.assertIn("tsw-apply-incus-forwarding.sh", service)
        self.assertIn("RemainAfterExit=yes", service)

    def test_incus_runtime_file_guard_accepts_only_expected_pid_path(self):
        self.assertTrue(
            host_network_repair._inside_incus_network_dir(
                "/var/lib/incus/networks/incusbr0/dnsmasq.pid"
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
        self.assertTrue(any("systemctl enable --now tsw-incus-forwarding.service" in command for command in commands))
        self.assertTrue(any("incus exec swarm-manager -- curl" in command for command in commands))

    def test_linux_forwarding_repair_reports_failed_install(self):
        executor = _MappingExecutor(
            {
                "install -m 0755": _failed("install script"),
                "install -m 0644": _ok("install service"),
            }
        )
        repair = SubprocessNetworkRepair(executor=executor)

        result = repair._apply_linux_forwarding("incusbr0", "swarm-manager")

        self.assertFalse(result.success)
        self.assertEqual("Failed to install forwarding persistence files.", result.message)

    def test_windows_scripts_read_ports_from_registry(self):
        root = Path(__file__).resolve().parents[4]
        repair_script = root / "tools" / "windows" / "repair-wsl-portproxy.ps1"
        doctor_script = root / "tools" / "windows" / "doctor-portproxy.ps1"

        for script in (repair_script, doctor_script):
            text = script.read_text(encoding="utf-8")
            self.assertIn("infra\\config\\ports.yaml", text)
            self.assertIn("Get-TswBridgePorts", text)
            self.assertNotIn("$ports = @(", text)


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

    def __call__(self, command: str, _timeout: int) -> CommandObservation:
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
