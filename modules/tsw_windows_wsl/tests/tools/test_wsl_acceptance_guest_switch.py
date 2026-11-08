"""Closed handoff dispatch plus real NETLINK parser with synthetic OS boundaries."""
from __future__ import annotations

import json
import ast
from pathlib import Path
import re
import socket
import struct
import subprocess
import tempfile
import unittest
from typing import Any
from unittest.mock import patch

from modules.tsw_windows_wsl.tests.test_prepare_windows import _powershell, _runtime_path

ROOT = Path(__file__).resolve().parents[4]
CONTROLLER = ROOT / "modules/tsw_windows_wsl/tools/qualification/wsl_acceptance_guest_switch.ps1"


class UpgradeLedgerTests(unittest.TestCase):
    def test_actual_promoted_case_source_preserves_unexecuted_recovery_without_checkout(self):
        source = CONTROLLER.read_text()
        start = source.index('def verify_case_checkout(')
        end = source.index("if kind=='prepared':", start)
        def need(value):
            if not value:
                raise ValueError('CASE_SOURCE_DENIED')
        namespace: dict[str, Any] = {'need': need, 're': re}
        exec(compile(ast.parse(source[start:end]), str(CONTROLLER), 'exec'), namespace)
        required = namespace['case_requires_checkout']
        outcome = {'status': 'CASE_NOT_EXECUTED', 'run_id': 'a' * 32, 'source_commit': 'b' * 40,
            'case': 'minimal', 'epic_complete': False}
        readonly_child = {'argv_sha256': 'c' * 64, 'timeout': 10, 'public': False}
        # This branch must not touch or require a checkout at all.
        self.assertFalse(required(outcome, [], []))
        self.assertFalse(required(outcome | {'status': 'CASE_NOT_IMPLEMENTED'}, [], [readonly_child]))
        self.assertTrue(required(outcome, [], [readonly_child | {'public': True}]))
        for status in ('CASE_PASS_DISPOSED', 'CASE_FAILED_DISPOSED', 'CASE_RECOVERED', 'CASE_NOT_EXERCISED'):
            self.assertTrue(required(outcome | {'status': status}, [], []))
        for changed, effects, children in (({'epic_complete': True}, [], []), ({}, ['execution-intent.json'], []),
                                            ({}, [], [{'public': False}])):
            with self.subTest(changed=changed, effects=effects, children=children), self.assertRaises(ValueError):
                required(outcome | changed, effects, children)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = root / 'cases/minimal/checkout'
            (checkout / '.git').mkdir(parents=True)
            cap = checkout / 'modules/tsw_core/infra/config/incus-profile-capabilities.json'
            cap.parent.mkdir(parents=True)
            cap.write_bytes(b'approved-matrix')
            for fault in ('valid', 'head', 'dirty', 'filter', 'matrix'):
                def git(args, exits=(0,), directory=None):
                    del exits, directory
                    if args[0] == 'config':
                        return b'filter.bad' if fault == 'filter' else b''
                    if args[0] == 'rev-parse':
                        return ('c' * 40 if fault == 'head' else 'b' * 40).encode()
                    return b'changed' if fault == 'dirty' else b''
                namespace.update(root=root, git=git, trusted=lambda *a: None, product_source='b' * 40)
                with self.subTest(checkout=fault):
                    if fault == 'valid':
                        namespace['verify_case_checkout']('minimal', b'approved-matrix')
                    else:
                        with self.assertRaises(ValueError):
                            namespace['verify_case_checkout']('minimal', b'wrong' if fault == 'matrix' else b'approved-matrix')
            checkout.rename(checkout.with_name('partial-staging'))
            self.assertFalse(required(outcome, [], []))
            if required(outcome, [], [readonly_child | {'public': True}]):
                with self.assertRaises(FileNotFoundError):
                    namespace['verify_case_checkout']('minimal', b'approved-matrix')

    def test_actual_embedded_promotion_gate_refuses_code_merge_and_grandchild(self):
        source = CONTROLLER.read_text()
        start = source.index('def admitted_product_revision(')
        end = source.index("path=root/('preparation.json'", start)
        def need(value):
            if not value:
                raise ValueError('PROMOTION_DENIED')
        namespace: dict[str, Any] = {'need': need, 're': re}
        exec(compile(ast.parse(source[start:end]), str(CONTROLLER), 'exec'), namespace)
        gate = namespace['admitted_product_revision']
        q, r = 'a' * 40, 'b' * 40
        matrix = 'modules/tsw_core/infra/config/incus-profile-capabilities.json'
        self.assertEqual(gate(q, q, [], []), q)
        self.assertEqual(gate(q, r, [r, q], [matrix]), r)
        for parents, changes in (([r, q, 'c' * 40], [matrix]), ([r, 'c' * 40], [matrix]),
                                 ([r, q], [matrix, 'code.py']), ([r, q], []), ([r, q], ['other.json'])):
            with self.subTest(parents=parents, changes=changes), self.assertRaises(ValueError):
                gate(q, r, parents, changes)
        for bad in ('main', 'a' * 39):
            with self.assertRaises(ValueError):
                gate(q, bad, [bad, q], [matrix])

    def test_actual_embedded_promotion_requires_paired_host_proof_and_fixture_bytes(self):
        from modules.tsw_native_linux.tools.qualification import preserving_product_acceptance as proof_module
        from modules.tsw_native_linux.tests.tools.test_preserving_product_acceptance import altered_capability
        source = CONTROLLER.read_text()
        start = source.index('def validate_promoted_capability(')
        end = source.index("path=root/('preparation.json'", start)
        code = b'fixed-real-fixture-source-for-unit-test'
        matrix = {'schema_version': 1, 'capability': 'installation-scoped-incus-manager-profile',
            'admitted_versions': [{'client_version': '6.0.5', 'server_version': '6.0.5',
                'fixture_source_revision': 'b' * 40, 'fixture_sha256': proof_module.native.digest(code)}]}
        capraw = proof_module.native.canonical(matrix)
        for kind in ('valid', 'copied-native', 'wrong-host', 'missing-host', 'source', 'fixture', 'fixture-code'):
            proof, artifacts, _ = altered_capability(kind, proof_module.native.digest(capraw))
            def private(path, limit=65536):
                del limit
                if path.name == 'both-host-profile-capability.json':
                    return proof_module.native.canonical(proof)
                return artifacts[path.name.removeprefix('profile-capability-').removesuffix('.json')]
            def git(args):
                if args[-1].endswith('incus-profile-capabilities.json'):
                    return capraw
                return b'changed-fixture' if kind == 'fixture-code' else code
            def need(value):
                if not value:
                    raise ValueError('PROMOTION_DENIED')
            namespace: dict[str, Any] = {'need': need, 're': re, 'git': git, 'private': private,
                'strict': json.loads, 'root': Path('/never-accessed'), 'product_source': 'c' * 40,
                'hashlib': __import__('hashlib')}
            exec(compile(ast.parse(source[start:end]), str(CONTROLLER), 'exec'), namespace)
            with self.subTest(kind=kind), patch.dict('sys.modules', {'preserving_product_acceptance': proof_module}):
                if kind == 'valid':
                    self.assertEqual(namespace['validate_promoted_capability'](), capraw)
                else:
                    with self.assertRaises(ValueError):
                        namespace['validate_promoted_capability']()

    def test_actual_embedded_ledger_parser_preserves_v1_and_closes_v2(self):
        from modules.tsw_native_linux.tools.qualification import product_upgrade_cases as cases
        source = CONTROLLER.read_text()
        start = source.index('def case_ledger_names(')
        end = source.index("if kind=='prepared':", start)
        tree = ast.parse(source[start:end])
        def need(value):
            if not value:
                raise ValueError('LEDGER_DENIED')
        namespace: dict[str, Any] = {'need': need, 're': re}
        exec(compile(tree, str(CONTROLLER), 'exec'), namespace)
        parse = namespace['case_ledger_names']
        ledger = {'schema_version': 2, 'run_id': 'run', 'source_commit': 'source',
            'cases': [{'case': name, 'outcome_sha256': 'a' * 64} for name in cases.ALL_NAMES]}
        self.assertEqual(parse(ledger, 'run', 'source'), cases.ALL_NAMES)
        directories = namespace['case_ledger_directory_names']
        directories(ledger, list(cases.ALL_NAMES), cases.ALL_NAMES)
        for names in (list(cases.ALL_NAMES[:-1]), [*cases.ALL_NAMES, 'unknown'], [*cases.ALL_NAMES, cases.ALL_NAMES[0]]):
            with self.assertRaises(ValueError):
                directories(ledger, names, cases.ALL_NAMES)
        self.assertEqual(parse(ledger | {'schema_version': 1, 'cases': ledger['cases'][:8]}, 'run', 'source'), cases.FRESH_NAMES)
        for change in ({'schema_version': 1}, {'schema_version': True}, {'run_id': 'foreign'},
                       {'source_commit': 'foreign'}, {'cases': ledger['cases'][::-1]},
                       {'cases': ledger['cases'] + ledger['cases'][:1]},
                       {'cases': [{'case': 'arbitrary', 'outcome_sha256': 'a' * 64}]},
                       {'cases': [{'case': cases.ALL_NAMES[0], 'outcome_sha256': 'broken'}]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                parse(ledger | change, 'run', 'source')


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
             _runtime_path(ROOT / "modules/tsw_core/tests/fixtures/wsl_acceptance_guest_switch.ps1", executable),
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
