"""Closed handoff dispatch plus real NETLINK parser with synthetic OS boundaries."""
from __future__ import annotations

import json
from pathlib import Path
import re
import socket
import struct
import subprocess
import unittest
from unittest.mock import patch

from tests.test_prepare_windows import _powershell, _runtime_path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "tools/windows/qualification/wsl_acceptance_guest_switch.ps1"


def network_probe() -> dict:
    source = CONTROLLER.read_text()
    match = re.search(r"function Get-WslSwitchNetworkProbe \{.*?return @'\n(.*?)\n'@\n\}", source, re.S)
    if match is None:
        raise AssertionError("Actual fixed network probe was not found")
    namespace = {"__name__": "closed_network_fixture"}
    exec(compile(match[1], str(CONTROLLER), "exec"), namespace)
    return namespace


def frame(kind: int = 3, flags: int = 2, seq: int = 1, port: int = 44, body: bytes = b"\0\0\0\0") -> bytes:
    return struct.pack("=IHHII", 16 + len(body), kind, flags, seq, port) + body


class ClosedGuestSwitchTests(unittest.TestCase):
    @unittest.skipUnless(_powershell(), "PowerShell test runtime unavailable")
    def test_actual_coordinator_with_fake_host_boundaries(self):
        executable = _powershell()
        assert executable is not None
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
             _runtime_path(ROOT / "tests/fixtures/wsl_acceptance_guest_switch.ps1", executable),
             "-RepositoryRoot", _runtime_path(ROOT, executable)],
            capture_output=True, text=True, check=False, timeout=90,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertGreaterEqual(report["cases"], 30)
        self.assertEqual(report["actual_guest_effects"], 0)
        self.assertFalse(report["actual_preparation"])
        self.assertFalse(report["originals_touched"])
        self.assertFalse(report["application_ready"])


class NetfilterReadParserTests(unittest.TestCase):
    def test_only_complete_unfiltered_kernel_dump_can_prove_empty(self):
        probe = network_probe()
        self.assertTrue(probe["nft_messages"](frame(), 1, 44))
        self.assertFalse(probe["nft_messages"](b"", 1, 44))
        for data in (
            b"x", frame()[:-1], struct.pack("=IHHII", 15, 3, 2, 1, 44),
            frame(seq=2), frame(port=0), frame(flags=0), frame(flags=0x12),
            frame(flags=0x22), frame(kind=2), frame(kind=4), frame(body=b"x"),
            frame(body=struct.pack("=i", -1)), frame() + frame(),
        ):
            with self.subTest(frame=data.hex()), self.assertRaises(probe["Unknown"]):
                probe["nft_messages"](data, 1, 44)
        with self.assertRaises(probe["Residue"]):
            probe["nft_messages"](frame(kind=0xA00), 1, 44)

    def test_missing_module_never_opens_a_netfilter_socket(self):
        probe = network_probe()
        with (patch.object(Path, "is_dir", return_value=False),
              patch.object(socket, "socket") as opened,
              self.assertRaises(probe["Unknown"])):
            probe["nft_empty"]()
        opened.assert_not_called()

    def test_closed_gettable_dump_checks_real_transport_metadata_and_closes(self):
        probe = network_probe()

        class WireSocket:
            def __init__(self, rows):
                self.rows = list(rows)
                self.sent = []
                self.closed = False
                self.timeout = None

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                self.closed = True

            def settimeout(self, value):
                self.timeout = value

            def bind(self, address):
                self.address = address

            def getsockname(self):
                return (44, 0)

            def sendto(self, data, address):
                self.sent.append((data, address))
                return len(data)

            def recvmsg(self, _size):
                if not self.rows:
                    raise TimeoutError
                row = self.rows.pop(0)
                if isinstance(row, Exception):
                    raise row
                return row

        good = (frame(), [], 0, (0, 0))
        cases = [([good], None),
                 ([(frame(), [], 0, (123, 0))], probe["Unknown"]),
                 ([(frame(), [], 0, (0, 1))], probe["Unknown"]),
                 ([(frame(), ["unexpected"], 0, (0, 0))], probe["Unknown"]),
                 ([(frame(), [], socket.MSG_TRUNC, (0, 0))], probe["Unknown"]),
                 ([(frame(kind=0xA00), [], 0, (0, 0))], probe["Residue"]),
                 ([TimeoutError()], TimeoutError),
                 ([(b"", [], 0, (0, 0))], probe["Unknown"])]
        for rows, error in cases:
            with self.subTest(rows=rows):
                wire = WireSocket(rows)
                with (patch.object(Path, "is_dir", return_value=True),
                      patch.object(socket, "socket", return_value=wire) as create):
                    if error is None:
                        probe["nft_empty"]()
                    else:
                        with self.assertRaises(error):
                            probe["nft_empty"]()
                create.assert_called_once_with(socket.AF_NETLINK, socket.SOCK_RAW, 12)
                self.assertTrue(wire.closed)
                self.assertEqual(wire.timeout, 2)
                self.assertEqual(wire.address, (0, 0))
                self.assertEqual(wire.sent, [(struct.pack("=IHHII", 20, 0xA01, 0x301, 1, 44) + b"\0\0\0\0", (0, 0))])

    def test_initial_network_probe_refuses_both_owned_and_foreign_service_sockets(self):
        probe = network_probe()
        reads = {
            "/proc/sys/kernel/osrelease": b"6.6.87-microsoft-standard-WSL2\n",
            "/etc/machine-id": b"1234567890abcdef1234567890abcdef\n",
            "/proc/net/route": b"Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT\n",
            "/proc/net/tcp": b"header\n", "/proc/net/tcp6": b"header\n",
            "/proc/net/udp": b"header\n", "/proc/net/udp6": b"header\n",
            "/proc/net/unix": b"header\n0000: 0000 0000 0000 0001 01 123 /var/lib/incus/unix.socket\n",
        }
        probe["read"] = lambda path, limit=65536: reads[str(path)]
        probe["nft_empty"] = lambda: None
        with (patch.object(probe["os"], "geteuid", return_value=0),
              patch.object(probe["os"], "listdir", return_value=["lo", "eth0"]),
              patch.object(Path, "exists", return_value=False),
              patch.object(probe["os"].path, "lexists", side_effect=lambda path: path == "/var/lib/incus/unix.socket")):
            with self.assertRaises(probe["Residue"]):
                probe["inspect"]()
            reads["/proc/net/unix"] = b"header\n0000: 0000 0000 0000 0001 01 123 /foreign/incus.socket\n"
            with self.assertRaises(probe["Residue"]):
                probe["inspect"]()
