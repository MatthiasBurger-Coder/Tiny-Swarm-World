import subprocess
import unittest
from unittest.mock import patch

from tiny_swarm_world.application.ports.network import CommandObservation
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    SetupPath,
)
from tiny_swarm_world.infrastructure.adapters.network.host_network_probe import (
    SubprocessNetworkProbe,
    _run_shell_command,
)


class TestHostNetworkProbe(unittest.IsolatedAsyncioTestCase):
    async def test_runtime_detects_wsl2_nat_and_eth0_address(self):
        probe = SubprocessNetworkProbe(
            executor=_MappingExecutor(
                {
                    "hostname -I": _ok("hostname", "172.22.1.20"),
                    "wslinfo --networking-mode": _ok("wslinfo", "nat"),
                    "ip -4 -o addr show dev eth0": _ok(
                        "ip",
                        "2: eth0 inet 172.22.1.20/20 brd 172.22.15.255 scope global eth0",
                    ),
                }
            ),
            host_environment_detector=_Detector(
                _host_report(HostEnvironmentKind.WSL2, SetupPath.WSL2)
            ),
        )

        runtime = await probe.runtime()

        self.assertEqual(runtime.runtime, "wsl2")
        self.assertEqual(runtime.networking_mode, "nat")
        self.assertEqual(runtime.wsl_ipv4, "172.22.1.20")

    async def test_incus_unavailable_skips_dependent_network_commands(self):
        probe = SubprocessNetworkProbe(
            executor=_MappingExecutor({"incus version": _failed("incus version")})
        )

        incus = await probe.incus()

        self.assertFalse(incus.version.ok)
        self.assertEqual(incus.network_list.command, "skipped")

    async def test_runtime_detects_native_linux_and_host_address(self):
        executor = _MappingExecutor(
                {
                    "hostname -I": _ok("hostname", "192.168.1.25 10.0.0.2"),
                    "ip route": _ok("ip route", "default via 192.168.1.1"),
                }
            )
        probe = SubprocessNetworkProbe(
            executor=executor,
            host_environment_detector=_Detector(
                _host_report(
                    HostEnvironmentKind.NATIVE_LINUX,
                    SetupPath.NATIVE_LINUX,
                )
            ),
        )

        runtime = await probe.runtime()

        self.assertEqual(runtime.runtime, "native-linux")
        self.assertEqual(runtime.host_ipv4, "192.168.1.25")
        self.assertFalse(any("wslinfo" in command for command in executor.commands))
        self.assertFalse(any("eth0" in command for command in executor.commands))
        self.assertFalse(any("grep -Eqi" in command for command in executor.commands))

    async def test_runtime_never_reports_wsl1_or_ambiguous_as_wsl2(self):
        for report in (
            _host_report(
                HostEnvironmentKind.WSL1_UNSUPPORTED,
                SetupPath.UNSUPPORTED,
            ),
            _host_report(
                HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
                SetupPath.UNSUPPORTED,
            ),
        ):
            with self.subTest(environment=report.environment.value):
                executor = _MappingExecutor({})
                probe = SubprocessNetworkProbe(
                    executor=executor,
                    host_environment_detector=_Detector(report),
                )

                runtime = await probe.runtime()

                self.assertEqual(report.environment.value, runtime.runtime)
                self.assertFalse(runtime.is_wsl2)
                self.assertEqual(executor.commands, [])

    async def test_incus_success_parses_gateway_from_network_show(self):
        probe = SubprocessNetworkProbe(
            executor=_MappingExecutor(
                {
                    "incus version": _ok("incus version", "6.0"),
                    "incus network list": _ok("incus network list", "incusbr0"),
                    "incus network show incusbr0": _ok(
                        "incus network show",
                        "config:\n  ipv4.address: 10.85.194.1/24",
                    ),
                    "incus network info incusbr0": _ok("incus network info", "State: up"),
                    "ip addr show incusbr0": _ok("ip addr", "inet 10.85.194.1/24"),
                    "journalctl -u incus": _ok("journalctl"),
                    "cat /var/log/incus/dnsmasq.incusbr0.log": _ok("cat"),
                }
            )
        )

        incus = await probe.incus()

        self.assertTrue(incus.version.ok)
        self.assertEqual(incus.gateway_ipv4, "10.85.194.1")

    async def test_lxc_node_uses_gateway_probe_when_gateway_is_known(self):
        probe = SubprocessNetworkProbe(executor=_DefaultOkExecutor())

        node = await probe.lxc_node("swarm-manager", "10.85.194.1")

        self.assertEqual(node.node_name, "swarm-manager")
        self.assertTrue(node.ping_gateway.ok)
        self.assertIn("10.85.194.1", node.ping_gateway.command)

    async def test_lxc_node_reports_unknown_gateway_without_ping_command(self):
        probe = SubprocessNetworkProbe(executor=_DefaultOkExecutor())

        node = await probe.lxc_node("swarm-manager", "")

        self.assertFalse(node.ping_gateway.ok)
        self.assertIn("incusbr0 gateway unknown", node.ping_gateway.command)

    async def test_forwarding_collects_kernel_and_firewall_state(self):
        probe = SubprocessNetworkProbe(executor=_DefaultOkExecutor())

        forwarding = await probe.forwarding()

        self.assertTrue(forwarding.ip_forward.ok)
        self.assertIn("sysctl", forwarding.ip_forward.command)

    async def test_service_ports_reads_listening_tcp_sockets(self):
        probe = SubprocessNetworkProbe(
            executor=_MappingExecutor({"ss -ltnH": _ok("ss", "LISTEN 0 4096 *:10000 *:*")})
        )

        service_ports = await probe.service_ports()

        self.assertIn(":10000", service_ports.listeners.stdout)

    def test_shell_command_reports_timeout_without_raising(self):
        with patch(
            "tiny_swarm_world.infrastructure.adapters.network.host_network_probe.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["bash"], 5, output=b"out", stderr=b"err"),
        ):
            result = _run_shell_command("sleep 10", 5)

        self.assertEqual(result.return_code, 124)
        self.assertTrue(result.timed_out)
        self.assertEqual(result.stdout, "out")
        self.assertEqual(result.stderr, "err")

    def test_shell_command_reports_os_error_without_raising(self):
        with patch(
            "tiny_swarm_world.infrastructure.adapters.network.host_network_probe.subprocess.run",
            side_effect=OSError("missing bash"),
        ):
            result = _run_shell_command("echo ok", 5)

        self.assertEqual(result.return_code, 127)
        self.assertIn("missing bash", result.stderr)

    def test_shell_command_strips_successful_stdout_and_stderr(self):
        completed = subprocess.CompletedProcess(
            ["bash"],
            0,
            stdout=" out \n",
            stderr=" err \n",
        )
        with patch(
            "tiny_swarm_world.infrastructure.adapters.network.host_network_probe.subprocess.run",
            return_value=completed,
        ):
            result = _run_shell_command("echo ok", 5)

        self.assertTrue(result.ok)
        self.assertEqual(result.stdout, "out")
        self.assertEqual(result.stderr, "err")


class _MappingExecutor:
    def __init__(self, observations: dict[str, CommandObservation]) -> None:
        self.observations = observations
        self.commands: list[str] = []

    def __call__(self, command: str, _timeout: int) -> CommandObservation:
        self.commands.append(command)
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
        if "incusbr0 gateway unknown" in command:
            return _failed(command, "incusbr0 gateway unknown")
        return _ok(command)


def _ok(command: str, stdout: str = "") -> CommandObservation:
    return CommandObservation(command=command, return_code=0, stdout=stdout)


def _failed(command: str, stderr: str = "failed") -> CommandObservation:
    return CommandObservation(command=command, return_code=1, stderr=stderr)


class _Detector:
    def __init__(self, report: HostEnvironmentReport) -> None:
        self.report = report

    def detect(self) -> HostEnvironmentReport:
        return self.report


def _host_report(
    environment: HostEnvironmentKind,
    setup_path: SetupPath,
) -> HostEnvironmentReport:
    return HostEnvironmentReport(
        environment=environment,
        setup_path=setup_path,
        remediation=("Inspect the host classification.",),
        evidence={"classification": environment.value},
    )
