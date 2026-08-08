import subprocess
import unittest
from unittest.mock import Mock

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.common import (
    local_service_url,
    lxc_manager_ip,
    validate_local_http_scheme,
)


class TestLxcServiceCommon(unittest.TestCase):
    def test_validate_scheme_normalizes_supported_values(self):
        self.assertEqual(validate_local_http_scheme(" HTTPS "), "https")
        self.assertEqual(local_service_url("http", "127.0.0.1", 8081), "http://127.0.0.1:8081")

    def test_validate_scheme_rejects_unsupported_value(self):
        with self.assertRaisesRegex(ValueError, "http.*https"):
            validate_local_http_scheme("ftp")

    def test_manager_ip_retries_transient_failure(self):
        transient = subprocess.CompletedProcess(
            [],
            255,
            stdout="",
            stderr="Failed to retrieve PID of executing child process",
        )
        success = subprocess.CompletedProcess([], 0, stdout="10.0.0.8\n", stderr="")
        run = Mock(side_effect=(transient, success))
        sleep = Mock()

        self.assertEqual(
            lxc_manager_ip(
                ManagedLxcBackend.INCUS,
                "swarm-manager",
                30,
                run=run,
                sleep=sleep,
            ),
            "10.0.0.8",
        )
        self.assertEqual(run.call_args.args[0][:3], ["incus", "exec", "swarm-manager"])
        sleep.assert_called_once_with(0.5)

    def test_manager_ip_rejects_command_failure_and_missing_address(self):
        failed = Mock(
            return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="failure")
        )
        with self.assertRaisesRegex(RuntimeError, "lookup failed"):
            lxc_manager_ip(ManagedLxcBackend.LXD, "swarm-manager", 30, run=failed)

        missing = Mock(
            return_value=subprocess.CompletedProcess([], 0, stdout="hostname\n", stderr="")
        )
        with self.assertRaisesRegex(RuntimeError, "no IPv4"):
            lxc_manager_ip(ManagedLxcBackend.LXD, "swarm-manager", 30, run=missing)

    def test_manager_ip_rejects_timeout(self):
        run = Mock(side_effect=subprocess.TimeoutExpired("lxc", 30))

        with self.assertRaisesRegex(RuntimeError, "timed out"):
            lxc_manager_ip(ManagedLxcBackend.LXD, "swarm-manager", 30, run=run)
