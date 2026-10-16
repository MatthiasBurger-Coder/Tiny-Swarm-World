"""Root-anchored Incus proxy identity regressions; no live processes or Incus."""
from __future__ import annotations

import copy
import json
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.network_preparation import trusted_process as subject


def probe_namespace():
    namespace = {"__name__": "identity_test"}
    exec(subject.PROBE, namespace)
    return namespace


def process(pid, mapped=0):
    return dict(pid=pid, owner=mapped, credentials={"Uid": [mapped]*4, "Gid": [mapped]*4},
                maps={"uid_map": [[0, mapped, 1000000000]], "gid_map": [[0, mapped, 1000000000]]},
                namespaces={"user": f"user:[{100 if mapped else 1}]", "net": "net:[101]"},
                executable=["/usr/libexec/incus/incusd", 8, 42, 0, stat.S_IFREG | 0o755], start="10")


class ProcessIdentityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.namespace = probe_namespace()
        self.namespace["host_user_namespace"] = lambda: "user:[1]"
        self.observed = {10: process(10, 1000000), 20: process(20), 30: process(30, 1000000)}
        self.namespace["snapshot"] = lambda pid, trusted=False: copy.deepcopy(self.observed[pid])

    def test_complete_mapping_root_is_derived(self):
        self.assertEqual(self.namespace["mapped_root"]([[0, 1000000, 1000000000]]), 1000000)
        self.assertEqual(self.namespace["mapped_root"]([[5, 20, 2], [0, 10, 2]]), 10)

    def test_mapped_and_host_root_keep_complete_proof(self):
        for mapped in (1000000, 0):
            with self.subTest(mapped=mapped):
                self.observed[10] = process(10, mapped)
                proof = self.namespace["prove"](10, 20, 30)
                self.assertEqual(proof, dict(listener=self.observed[10], daemon=self.observed[20],
                                             manager=self.observed[30]))

    def test_invalid_maps_fail_closed(self):
        invalid = ([], [[1, 5, 2]], [[0, -1, 2]], [[0, 3, 0]], [[0, 3, -1]],
                   [[0, 3]], [[0, 3, 2**32]], [[0, 3, 10], [5, 50, 10]],
                   [[0, 3, 10], [30, 5, 10]], [[0, 3, 10], [0, 30, 1]],
                   [[False, 3, 10]], [[0, 2**32-2, 2]])
        for rows in invalid:
            with self.subTest(rows=rows), self.assertRaises(RuntimeError):
                self.namespace["mapped_root"](rows)

    def test_all_listener_manager_daemon_credential_fields_are_required(self):
        for pid in (10, 20, 30):
            for kind in ("Uid", "Gid"):
                for field in range(4):
                    with self.subTest(pid=pid, kind=kind, field=field):
                        original = copy.deepcopy(self.observed[pid])
                        self.observed[pid]["credentials"][kind][field] += 1
                        with self.assertRaises(RuntimeError):
                            self.namespace["prove"](10, 20, 30)
                        self.observed[pid] = original

    def test_foreign_namespaces_full_maps_owner_and_inode_are_rejected(self):
        for field in ("user", "net", "uid_map", "gid_map", "owner", "inode"):
            with self.subTest(field=field):
                original = copy.deepcopy(self.observed[10])
                if field in ("user", "net"):
                    self.observed[10]["namespaces"][field] = "foreign:[999]"
                elif field in ("uid_map", "gid_map"):
                    self.observed[10]["maps"][field].append([2000000000, 2000000000, 2])
                elif field == "owner":
                    self.observed[10]["owner"] += 1
                else:
                    self.observed[10]["executable"][2] += 1
                with self.assertRaises(RuntimeError):
                    self.namespace["prove"](10, 20, 30)
                self.observed[10] = original

    def test_nonhost_daemon_is_rejected(self):
        self.observed[20] = process(20, 1000000)
        with self.assertRaises(RuntimeError):
            self.namespace["prove"](10, 20, 30)

    def test_mapped_listener_cannot_share_daemon_user_namespace(self):
        for pid in (10, 30):
            self.observed[pid]["namespaces"]["user"] = self.observed[20]["namespaces"]["user"]
        with self.assertRaises(RuntimeError):
            self.namespace["prove"](10, 20, 30)

    def test_daemon_is_bound_to_observed_host_user_namespace(self):
        self.observed[20]["namespaces"]["user"] = "user:[999]"
        with self.assertRaises(RuntimeError):
            self.namespace["prove"](10, 20, 30)

    def test_host_root_listener_must_share_daemon_user_namespace(self):
        self.observed[10] = process(10)
        self.observed[10]["namespaces"]["user"] = "user:[999]"
        with self.assertRaises(RuntimeError):
            self.namespace["prove"](10, 20, 30)

    def test_mapped_uid_with_host_gid_is_rejected(self):
        for pid in (10, 30):
            self.observed[pid]["maps"]["gid_map"] = [[0, 0, 1000000000]]
            self.observed[pid]["credentials"]["Gid"] = [0]*4
        with self.assertRaises(RuntimeError):
            self.namespace["prove"](10, 20, 30)

    def test_host_namespace_change_during_proof_blocks(self):
        observations = iter(("user:[1]", "user:[2]"))
        self.namespace["host_user_namespace"] = lambda: next(observations)
        with self.assertRaises(RuntimeError):
            self.namespace["prove"](10, 20, 30)

    def test_every_process_snapshot_change_is_rejected(self):
        for pid in (10, 20, 30):
            for field in ("start", "credentials", "maps", "namespaces", "executable", "owner"):
                with self.subTest(pid=pid, field=field):
                    counts = {}

                    def snapshot(current, trusted=False):
                        counts[current] = counts.get(current, 0) + 1
                        result = copy.deepcopy(self.observed[current])
                        if current == pid and counts[current] == 2:
                            result[field] = "changed"
                        return result

                    self.namespace["snapshot"] = snapshot
                    with self.assertRaises(RuntimeError):
                        self.namespace["prove"](10, 20, 30)

    def test_safe_executable_and_all_ancestors(self):
        safe = SimpleNamespace(st_mode=stat.S_IFREG | 0o755, st_uid=0)
        ancestor = Mock()
        ancestor.stat.return_value = SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0)
        path = SimpleNamespace(parents=[ancestor])
        self.namespace["safe_executable"](path, safe)
        for mode, uid in ((stat.S_IFREG | 0o777, 0), (stat.S_IFREG | 0o755, 1000),
                          (stat.S_IFDIR | 0o755, 0)):
            with self.subTest(mode=mode, uid=uid), self.assertRaises(RuntimeError):
                self.namespace["safe_executable"](path, SimpleNamespace(st_mode=mode, st_uid=uid))
        for mode, uid in ((stat.S_IFDIR | 0o775, 0), (stat.S_IFDIR | 0o755, 1000)):
            ancestor.stat.return_value = SimpleNamespace(st_mode=mode, st_uid=uid)
            with self.assertRaises(RuntimeError):
                self.namespace["safe_executable"](path, safe)

    def test_snapshot_records_credentials_maps_namespaces_and_executable(self):
        namespace = probe_namespace()
        info = SimpleNamespace(st_uid=0, st_mode=stat.S_IFREG | 0o755, st_dev=8, st_ino=42)
        status = "Uid:\t1000000 1000000 1000000 1000000\nGid:\t1000000 1000000 1000000 1000000\n"

        def read_text(path):
            if path.name == "status":
                return status
            if path.name in ("uid_map", "gid_map"):
                return "0 1000000 1000000000\n"
            return "10 (name with ) space) " + " ".join(["0"]*19 + ["1234"])

        with patch.object(Path, "stat", return_value=info), patch.object(Path, "resolve", return_value=Path("/incusd")), \
                patch.object(Path, "read_text", read_text), patch("os.open", return_value=7), \
                patch("os.fstat", return_value=info), patch("os.close") as close, \
                patch("os.readlink", side_effect=lambda path: f"{path.name}:[100]"):
            result = namespace["snapshot"](10, True)
        self.assertEqual(result["start"], "1234")
        self.assertEqual(result["credentials"]["Uid"], [1000000]*4)
        self.assertEqual(result["maps"]["gid_map"], [[0, 1000000, 1000000000]])
        self.assertEqual(result["namespaces"], {"user": "user:[100]", "net": "net:[100]"})
        close.assert_called_once_with(7)

    def test_manager_executable_is_observed_through_proc_not_host_filesystem(self):
        namespace = probe_namespace()
        info = SimpleNamespace(st_uid=1000000, st_mode=stat.S_IFREG | 0o755, st_dev=99, st_ino=501)

        def read_text(path):
            if path.name == "status":
                return "Uid: 1000000 1000000 1000000 1000000\nGid: 1000000 1000000 1000000 1000000\n"
            if path.name in ("uid_map", "gid_map"):
                return "0 1000000 1000000000\n"
            return "30 (init) " + " ".join(["0"]*19 + ["15"])

        def observe_stat(path):
            if path != Path("/proc/30"):
                raise FileNotFoundError("Container executable does not exist in host namespace")
            return info

        with patch.object(Path, "stat", observe_stat), patch.object(Path, "resolve", side_effect=AssertionError), \
                patch.object(Path, "read_text", read_text), patch("os.open", return_value=7), \
                patch("os.fstat", return_value=info), patch("os.close"), \
                patch("os.readlink", side_effect=lambda path: "/container/sbin/init" if path.name == "exe" else f"{path.name}:[100]"):
            result = namespace["snapshot"](30)
        self.assertEqual(result["executable"], ["/container/sbin/init", 99, 501, 1000000, stat.S_IFREG | 0o755])

    def test_missing_or_unreadable_proc_fails_closed(self):
        namespace = probe_namespace()
        for error in (FileNotFoundError, PermissionError):
            with self.subTest(error=error), patch.object(Path, "stat", side_effect=error):
                with self.assertRaises(error):
                    namespace["snapshot"](10, True)


class ProcessIdentityApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.device = {"type": "proxy", "listen": "tcp:0.0.0.0:443", "connect": "tcp:127.0.0.1:443"}
        self.state = {"pid": 30}
        self.instance = {"expanded_devices": {"https": self.device}}
        self.proof = dict(listener=process(10, 1000000), daemon=process(20), manager=process(30, 1000000))
        self.query = AsyncMock(side_effect=[self.state, self.instance, self.state, self.instance])
        self.command = AsyncMock(return_value="20\n")
        self.privileged = AsyncMock(return_value=json.dumps(self.proof))
        for name, mock in (("incus.query", self.query), ("runtime.command", self.command),
                           ("runtime.privileged", self.privileged)):
            patcher = patch(f"{subject.__name__}.{name}", mock)
            patcher.start()
            self.addCleanup(patcher.stop)

    async def test_positive_wrapper_requeries_and_fingerprints_complete_proof(self):
        result = await subject.verify(10, self.device)
        self.assertEqual(json.loads(result[1]), self.proof)
        self.assertEqual(self.query.await_count, 4)
        self.assertEqual(self.privileged.call_args.args[0][-3:], ("10", "20", "30"))

    async def test_invalid_api_pid_is_rejected_before_privileged_probe(self):
        for pid in (None, True, "30", 0, -1, 1.5):
            self.query.side_effect = [{"pid": pid}, self.instance]
            with self.subTest(pid=pid), self.assertRaises(NetworkPreparationFailure):
                await subject.verify(10, self.device)
        self.privileged.assert_not_awaited()

    async def test_device_drift_duplicate_and_missing_expanded_devices_block(self):
        for devices in ({}, {"one": {**self.device, "connect": "tcp:127.0.0.1:444"}},
                        {"one": self.device, "two": self.device}, None):
            self.query.side_effect = [self.state, {"expanded_devices": devices}]
            with self.subTest(devices=devices), self.assertRaises(NetworkPreparationFailure):
                await subject.verify(10, self.device)
        self.privileged.assert_not_awaited()

    async def test_custom_credentials_binding_and_nat_block(self):
        for key, value in (("security.uid", "0"), ("security.gid", ""), ("bind", "guest"), ("nat", "true")):
            with self.subTest(key=key), self.assertRaises(NetworkPreparationFailure):
                await subject.verify(10, {**self.device, key: value})
        self.query.assert_not_awaited()

    async def test_manager_pid_or_proxy_changes_after_proof_block(self):
        for state, instance in (({"pid": 31}, self.instance), (self.state, {"expanded_devices": {}})):
            self.query.side_effect = [self.state, self.instance, state, instance]
            with self.subTest(state=state, instance=instance), self.assertRaises(NetworkPreparationFailure):
                await subject.verify(10, self.device)

    async def test_daemon_change_after_proof_blocks(self):
        self.command.side_effect = ["20", "21"]
        with self.assertRaises(NetworkPreparationFailure):
            await subject.verify(10, self.device)

    async def test_missing_or_malformed_proof_blocks(self):
        incomplete = dict(listener={}, daemon={}, manager={})
        wrong_pid = copy.deepcopy(self.proof)
        wrong_pid["manager"]["pid"] = 31
        for value in ("invalid", "[]", '{}', json.dumps(incomplete), json.dumps(wrong_pid)):
            self.query.side_effect = [self.state, self.instance, self.state, self.instance]
            self.privileged.return_value = value
            with self.subTest(value=value), self.assertRaises(NetworkPreparationFailure):
                await subject.verify(10, self.device)
