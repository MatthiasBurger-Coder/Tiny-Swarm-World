import subprocess
import unittest
from unittest.mock import patch

from tiny_swarm_world.application.ports.network import CommandObservation
from tiny_swarm_world.infrastructure.adapters.network.host_network_probe import (
    SubprocessNetworkProbe,
    _run_shell_command,
)


class TestHostNetworkProbe(unittest.IsolatedAsyncioTestCase):
    async def test_runtime_detects_wsl2_nat_and_eth0_address(self):
        probe = SubprocessNetworkProbe(
            executor=_MappingExecutor(
                {
                    "grep -Eqi": _ok("grep"),
                    "hostname -I": _ok("hostname", "172.22.1.20"),
                    "wslinfo --networking-mode": _ok("wslinfo", "nat"),
                    "ip -4 -o addr show dev eth0": _ok(
                        "ip",
                        "2: eth0 inet 172.22.1.20/20 brd 172.22.15.255 scope global eth0",
                    ),
                }
            )
        )

        runtime = await probe.runtime()

        self.assertEqual("wsl2", runtime.runtime)
        self.assertEqual("nat", runtime.networking_mode)
        self.assertEqual("172.22.1.20", runtime.wsl_ipv4)

    async def test_incus_unavailable_skips_dependent_network_commands(self):
        probe = SubprocessNetworkProbe(
            executor=_MappingExecutor({"incus version": _failed("incus version")})
        )

        incus = await probe.incus()

        self.assertFalse(incus.version.ok)
        self.assertEqual("skipped", incus.network_list.command)

    async def test_lxc_node_uses_gateway_probe_when_gateway_is_known(self):
        probe = SubprocessNetworkProbe(executor=_DefaultOkExecutor())

        node = await probe.lxc_node("swarm-manager", "10.85.194.1")

        self.assertEqual("swarm-manager", node.node_name)
        self.assertTrue(node.ping_gateway.ok)
        self.assertIn("10.85.194.1", node.ping_gateway.command)

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

        self.assertEqual(124, result.return_code)
        self.assertTrue(result.timed_out)
        self.assertEqual("out", result.stdout)
        self.assertEqual("err", result.stderr)


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
        return _ok(command)


def _ok(command: str, stdout: str = "") -> CommandObservation:
    return CommandObservation(command=command, return_code=0, stdout=stdout)


def _failed(command: str, stderr: str = "failed") -> CommandObservation:
    return CommandObservation(command=command, return_code=1, stderr=stderr)
