"""Mocked proof-boundary tests; no process, package or service reads occur."""
from __future__ import annotations

from dataclasses import replace
import errno
import os
from pathlib import Path
import stat
import tempfile
import unittest
from typing import Any
from unittest.mock import Mock, patch

from tools.qualification import native_lxd_snap_provenance as proof


def regular(inode: int, data: bytes = b"", *, executable: bool = False, readonly: bool = True) -> proof.Observation:
    return proof.Observation(1, inode, stat.S_IFREG | (0o555 if executable else 0o444), 0, readonly, data)


def proc_stat(pid: int, parent: int, started: int) -> bytes:
    # The command name contains a closing parenthesis: split at the final one.
    fields = ["S", str(parent)] + ["0"] * 17 + [str(started)]
    return f"{pid} (worker ) name) {' '.join(fields)}\n".encode()


class MemoryFS:
    def __init__(self) -> None:
        self.files: dict[str, proof.Observation] = {}
        self.links: dict[str, str] = {}
        self.sequences: dict[str, list[proof.Observation]] = {}
        self.calls: list[tuple[str, int | None, bool]] = []

    def observe(self, path: str, *, limit: int | None = None, follow: bool = False) -> proof.Observation:
        self.calls.append((path, limit, follow))
        if path in self.links and not follow:
            raise OSError(errno.ELOOP, "secret-value")
        if path in self.sequences:
            sequence = self.sequences[path]
            return sequence.pop(0) if len(sequence) > 1 else sequence[0]
        if path not in self.files:
            raise FileNotFoundError("secret-value")
        return self.files[path]

    def final_link(self, path: str) -> str | None:
        if path in self.links:
            return self.links[path]
        if path not in self.files:
            raise FileNotFoundError("secret-value")
        return None


class WrapperProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fs = MemoryFS()
        self.row = {"unit": proof.UNIT, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                    "unit_file_state": "enabled", "main_pid": 101}
        self.values = dict.fromkeys(proof.PROPERTIES, "")
        self.values.update(LoadState="loaded", ActiveState="active", SubState="running", UnitFileState="enabled",
                           MainPID="101", ControlGroup="/system.slice/" + proof.UNIT, FragmentPath=proof.UNIT_FILE,
                           ExecStart="{ path=/usr/bin/snap ; argv[]=/usr/bin/snap run lxd.daemon ; ignore_errors=no ; "
                                     "start_time=[Wed 2026-10-28 10:00:00 UTC] ; stop_time=[n/a] ; pid=101 ; code=(null) ; status=0/0 }")
        self.runner = Mock()
        self.runner.run.side_effect = lambda *_a, **_kw: (0, self.unit_bytes(), b"")
        self.fs.files[proof.UNIT_FILE] = regular(10, readonly=False)
        self.add_process(101, 1, 11, 20)
        self.add_process(202, 101, 22, 30)
        self.fs.files["/proc/101/root/bin/sh"] = regular(20, executable=True)
        self.fs.files["/proc/101/cmdline"] = regular(40, b"/bin/sh\x00/snap/lxd/123/commands/daemon.start\x00")
        self.fs.files["/proc/101/environ"] = regular(41, b"SNAP_NAME=lxd\x00SNAP_REVISION=123\x00SNAP=/snap/lxd/123\x00LD_LIBRARY_PATH=/snap/extra\x00")
        self.fs.files["/proc/101/task/101/children"] = regular(42, b"202 ")
        self.pair("commands/daemon.start", regular(50, executable=True))
        self.pair("meta/snap.yaml", regular(51, b"name: lxd\napps:\n  daemon:\n    command: commands/daemon.start\n    daemon: simple\n"))
        self.pair("sbin/lxd", regular(30, executable=True))

    def unit_bytes(self) -> bytes:
        return "".join(f"{key}={value}\n" for key, value in self.values.items()).encode()

    def add_process(self, pid: int, parent: int, started: int, executable: int) -> None:
        self.fs.files[f"/proc/{pid}/stat"] = regular(1000 + pid, proc_stat(pid, parent, started), readonly=False)
        self.fs.files[f"/proc/{pid}/status"] = regular(2000 + pid, b"Name:\tignored\nUid:\t0\t0\t0\t0\n", readonly=False)
        self.fs.files[f"/proc/{pid}/cgroup"] = regular(3000 + pid, ("0::" + self.values["ControlGroup"] + "\n").encode(), readonly=False)
        self.fs.files[f"/proc/{pid}/exe"] = regular(executable, executable=True)

    def pair(self, relative: str, value: proof.Observation) -> None:
        self.fs.files["/snap/lxd/123/" + relative] = value
        self.fs.files["/proc/101/root/snap/lxd/123/" + relative] = value

    def run_proof(self, *, clock=lambda: 0.0) -> tuple[str, str]:
        return proof.prove_snap_wrapper(self.runner, self.row, fs=self.fs, clock=clock)

    def assert_blocked(self, code: str | None = None) -> None:
        with self.assertRaises(proof.ProvenanceError) as caught:
            self.run_proof()
        self.assertTrue(str(caught.exception).startswith("SNAP_WRAPPER_"))
        self.assertNotIn("secret-value", str(caught.exception))
        if code is not None:
            self.assertEqual(str(caught.exception), code)

    def test_full_relation_returns_pair_only_with_two_fixed_additional_commands(self) -> None:
        self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))
        self.assertEqual(self.runner.run.call_count, 2)
        for call in self.runner.run.call_args_list:
            self.assertEqual(call.args, (proof.UNIT_ARGV,))
            self.assertEqual(call.kwargs, {"command_id": "systemctl_show_unit", "safe_args": [proof.UNIT]})
        self.assertLessEqual(len(proof.UNIT_ARGV), 16)

    def test_wrapper_without_child_cannot_establish_identity(self) -> None:
        self.fs.files["/proc/101/task/101/children"] = regular(42)
        self.assert_blocked("SNAP_WRAPPER_CHILD_ABSENT")

    def test_duplicate_or_missing_unit_properties_are_rejected(self) -> None:
        for raw in (self.unit_bytes() + b"MainPID=101\n", self.unit_bytes().replace(b"MainPID=101\n", b""),
                    self.unit_bytes() + b"Unexpected=secret-value\n"):
            with self.subTest(raw=raw[:20]):
                self.runner.run.side_effect = None
                self.runner.run.return_value = (0, raw, b"")
                self.assert_blocked("SNAP_WRAPPER_UNIT_INVALID")

    def test_all_optional_empty_omission_combinations_are_logically_equivalent(self) -> None:
        optional = ("ExecCondition", "ExecStartPre", "ExecStartPost", "EnvironmentFiles")
        complete = self.unit_bytes()
        for mask in range(16):
            omitted = {key for index, key in enumerate(optional) if mask & (1 << index)}
            partial = b"".join(line for line in complete.splitlines(keepends=True)
                               if line.partition(b"=")[0].decode() not in omitted)
            for first, last in ((complete, partial), (partial, complete)):
                with self.subTest(mask=mask, omitted_first=first == partial):
                    self.runner.reset_mock()
                    self.runner.run.side_effect = [(0, first, b""), (0, last, b"")]
                    self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))
                    self.assertEqual(self.runner.run.call_count, 2)
                    self.assertIn("--property=" + ",".join(proof.PROPERTIES), self.runner.run.call_args.args[0])

    def test_every_other_property_remains_mandatory(self) -> None:
        optional = {"ExecCondition", "ExecStartPre", "ExecStartPost", "EnvironmentFiles"}
        complete = self.unit_bytes()
        for key in set(proof.PROPERTIES) - optional:
            raw = b"".join(line for line in complete.splitlines(keepends=True)
                           if line.partition(b"=")[0] != key.encode())
            with self.subTest(key=key):
                self.runner.run.side_effect = None
                self.runner.run.return_value = (0, raw, b"")
                self.assert_blocked("SNAP_WRAPPER_UNIT_INVALID")

    def test_optional_properties_still_reject_duplicates_and_malformed_rows(self) -> None:
        for key in ("ExecCondition", "ExecStartPre", "ExecStartPost", "EnvironmentFiles"):
            for suffix in ((key + "=\n").encode(), (key + "\n").encode(), (key + " =\n").encode()):
                with self.subTest(key=key, suffix=suffix):
                    self.runner.run.side_effect = None
                    self.runner.run.return_value = (0, self.unit_bytes() + suffix, b"")
                    self.assert_blocked("SNAP_WRAPPER_UNIT_INVALID")

    def test_present_optional_properties_keep_their_closed_context_policy(self) -> None:
        for key in ("ExecCondition", "ExecStartPre", "ExecStartPost", "EnvironmentFiles"):
            with self.subTest(key=key):
                self.values[key] = "secret-value"
                self.assert_blocked("SNAP_WRAPPER_CONTEXT_BLOCKED")
                self.values[key] = ""

    def test_closed_execstart_record_rejects_extra_argv_or_records_and_invalid_time(self) -> None:
        original = self.values["ExecStart"]
        for value in (original.replace("run lxd.daemon", "run lxd.daemon secret-value"), original + original,
                      original.replace("2026-10-28", "2026-02-31"), original.replace("ignore_errors=no", "ignore_errors=yes")):
            with self.subTest(value=value[:20]):
                self.values["ExecStart"] = value
                self.assert_blocked("SNAP_WRAPPER_CONTEXT_BLOCKED")

    def test_volatile_execstart_fields_do_not_drive_snapshot_equality(self) -> None:
        initial = self.unit_bytes()
        final = initial.replace(b"pid=101 ; code=(null) ; status=0/0", b"pid=0 ; code=exited ; status=0/SUCCESS")
        self.runner.run.side_effect = [(0, initial, b""), (0, final, b"")]
        self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))

    def test_unsupported_effective_context_blocks(self) -> None:
        for key in ("RootDirectory", "RootImage", "BindPaths", "BindReadOnlyPaths", "ExecCondition", "ExecStartPre", "ExecStartPost", "Environment"):
            with self.subTest(key=key):
                self.values[key] = "secret-value"
                self.assert_blocked("SNAP_WRAPPER_CONTEXT_BLOCKED")
                self.values[key] = ""

    def test_environment_file_closed_to_comments_and_blank_lines(self) -> None:
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        self.fs.files["/etc/environment"] = regular(60, b"# canonical optional file\n  # comment\n\n", readonly=False)
        self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))
        for content in (b"LD_AUDIT=secret-value\n", b"PATH=/usr/bin\n", b"UNKNOWN=1\n", b"# comment\r\n"):
            with self.subTest(content=content[:10]):
                self.fs.files["/etc/environment"] = regular(60, content, readonly=False)
                self.assert_blocked("SNAP_WRAPPER_CONTEXT_BLOCKED")

    def test_optional_missing_environment_file_and_fixed_unit_environment(self) -> None:
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        self.values["Environment"] = "SNAPD_DEBUG=0"
        self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))

    def test_only_the_two_exact_canonical_path_assignments_are_supported(self) -> None:
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        plain = "PATH=" + proof.CANONICAL_PATH
        quoted = 'PATH="' + proof.CANONICAL_PATH + '"'
        for assignment in (plain, quoted):
            with self.subTest(assignment=assignment[:6]):
                self.fs.files["/etc/environment"] = regular(60, ("# supported\n" + assignment + "\n").encode(), readonly=False)
                self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))
        for content in (plain + "\n" + plain, plain + " ", " " + plain, plain + ":/extra",
                        "PATH='" + proof.CANONICAL_PATH + "'", plain + " # comment", 'PATH="${PATH}"',
                        plain + "\nLD_AUDIT=secret-value"):
            with self.subTest(content=content[:10]):
                self.fs.files["/etc/environment"] = regular(60, content.encode(), readonly=False)
                self.assert_blocked("SNAP_WRAPPER_CONTEXT_BLOCKED")

    def test_dropin_has_closed_dependency_only_grammar(self) -> None:
        self.values["DropInPaths"] = proof.DROP_IN
        valid = b"# generated\n[Unit]\nAfter=snap.microceph.daemon.service snap.microovn.daemon.service\n"
        self.fs.files[proof.DROP_IN] = regular(61, valid, readonly=False)
        self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))
        for content in (valid + b"[Service]\nExecStart=secret-value\n", valid + b"[Unit]\n", valid.replace(b"After=", b"Before=")):
            with self.subTest(content=content[-20:]):
                self.fs.files[proof.DROP_IN] = regular(61, content, readonly=False)
                self.assert_blocked("SNAP_WRAPPER_CONTEXT_BLOCKED")

    def test_forged_or_duplicate_selected_environment_cannot_establish_identity(self) -> None:
        original = self.fs.files["/proc/101/environ"]
        for raw in (original.data + b"SNAP_NAME=lxd\x00", original.data.replace(b"SNAP_NAME=lxd", b"SNAP_NAME=other"),
                    original.data.replace(b"SNAP_REVISION=123", b"SNAP_REVISION=../123"), original.data[:-1]):
            with self.subTest(raw=raw[:20]):
                self.fs.files["/proc/101/environ"] = replace(original, data=raw)
                self.assert_blocked("SNAP_WRAPPER_PROC_INVALID")

    def test_main_argv_must_bind_the_canonical_wrapper(self) -> None:
        self.fs.files["/proc/101/cmdline"] = regular(40, b"/bin/sh\x00secret-value\x00")
        self.assert_blocked("SNAP_WRAPPER_PROC_INVALID")

    def test_metadata_requires_unique_keys_and_exact_daemon_contract(self) -> None:
        for raw in (b"name: lxd\nname: lxd\n", b"name: secret-value\n", b"apps: [daemon]\n", b"\xff"):
            with self.subTest(raw=raw[:20]):
                self.pair("meta/snap.yaml", regular(51, raw))
                self.assert_blocked("SNAP_WRAPPER_METADATA_INVALID")

    def test_package_file_must_be_root_owned_regular_readonly_and_same_object(self) -> None:
        path = "/snap/lxd/123/commands/daemon.start"
        original = self.fs.files[path]
        for changed in (replace(original, uid=1000), replace(original, mode=stat.S_IFREG | 0o777),
                        replace(original, mode=stat.S_IFDIR | 0o555), replace(original, readonly=False), replace(original, inode=99)):
            with self.subTest(changed=changed):
                self.fs.files[path] = changed
                self.assert_blocked("SNAP_WRAPPER_FILE_UNVERIFIED")

    def test_trusted_interpreter_inode_must_match_main_executable(self) -> None:
        self.fs.files["/proc/101/root/bin/sh"] = regular(99, executable=True)
        self.assert_blocked("SNAP_WRAPPER_FILE_UNVERIFIED")

    def test_only_one_distinct_installed_binary_inode_is_supported(self) -> None:
        self.pair("bin/lxd", regular(31, executable=True))
        self.assert_blocked("SNAP_WRAPPER_FILE_UNVERIFIED")

    def test_hardlink_or_exact_one_hop_final_alias_is_supported(self) -> None:
        self.pair("bin/lxd", regular(30, executable=True))
        self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))
        for prefix in ("", "/proc/101/root"):
            self.fs.links[prefix + "/snap/lxd/123/bin/lxd"] = "../sbin/lxd"
        self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))

    def test_alias_escape_loop_or_host_process_mismatch_blocks(self) -> None:
        for target in ("/usr/bin/secret-value", "../../secret-value", "../bin/lxd"):
            with self.subTest(target=target):
                for prefix in ("", "/proc/101/root"):
                    self.fs.links[prefix + "/snap/lxd/123/bin/lxd"] = target
                self.assert_blocked("SNAP_WRAPPER_FILE_UNVERIFIED")

    def test_missing_all_binary_candidates_blocks(self) -> None:
        for prefix in ("", "/proc/101/root"):
            del self.fs.files[prefix + "/snap/lxd/123/sbin/lxd"]
        self.assert_blocked("SNAP_WRAPPER_FILE_UNVERIFIED")

    def test_wrong_child_parent_uid_group_or_debug_executable_blocks(self) -> None:
        changes = (("stat", proc_stat(202, 999, 22)), ("status", b"Uid:\t1000\t1000\t1000\t1000\n"),
                   ("cgroup", b"0::/other\n"))
        for suffix, raw in changes:
            path = "/proc/202/" + suffix
            original = self.fs.files[path]
            with self.subTest(suffix=suffix):
                self.fs.files[path] = replace(original, data=raw)
                self.assert_blocked()
                self.fs.files[path] = original
        self.fs.files["/proc/202/exe"] = regular(999, executable=True)
        self.assert_blocked("SNAP_WRAPPER_CHILD_ABSENT")

    def test_two_matching_children_are_ambiguous(self) -> None:
        self.add_process(203, 101, 23, 30)
        self.fs.files["/proc/101/task/101/children"] = regular(42, b"202 203")
        self.assert_blocked("SNAP_WRAPPER_CHILD_AMBIGUOUS")

    def test_pid_reuse_or_exec_during_recheck_blocks(self) -> None:
        path = "/proc/202/stat"
        first = self.fs.files[path]
        self.fs.sequences[path] = [first, replace(first, data=proc_stat(202, 101, 999))]
        self.assert_blocked("SNAP_WRAPPER_DRIFT")

    def test_unit_context_or_package_refresh_during_recheck_blocks(self) -> None:
        initial = self.unit_bytes()
        final = initial.replace(b"Environment=\n", b"Environment=SNAPD_DEBUG=0\n")
        self.runner.run.side_effect = [(0, initial, b""), (0, final, b"")]
        self.assert_blocked("SNAP_WRAPPER_DRIFT")

    def test_metadata_bytes_and_child_set_are_rechecked(self) -> None:
        path = "/snap/lxd/123/meta/snap.yaml"
        first = self.fs.files[path]
        self.fs.sequences[path] = [first, replace(first, data=first.data + b"# refresh\n")]
        self.assert_blocked()

    def test_proc_schema_requires_cgroup_v2_and_root_uid(self) -> None:
        for raw in (b"1:legacy:/system.slice/test\n", b"0::/other\n", b"0::/a\n0::/a\n"):
            self.fs.files["/proc/101/cgroup"] = regular(3101, raw)
            self.assert_blocked("SNAP_WRAPPER_PROC_INVALID")

    def test_child_limit_and_duplicate_ids_block_before_process_reads(self) -> None:
        for raw in (b" ".join(str(value).encode() for value in range(1, 66)), b"202 202", b"secret-value"):
            self.fs.files["/proc/101/task/101/children"] = regular(42, raw)
            self.assert_blocked()

    def test_exact_child_count_limit_preserves_the_unique_match(self) -> None:
        children = [202] + list(range(203, 266))
        self.assertEqual(len(children), proof.MAX_CHILDREN)
        for child in children[1:]:
            self.add_process(child, 101, child, 999)
        self.fs.files["/proc/101/task/101/children"] = regular(42, " ".join(map(str, children)).encode())
        self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))

    def test_per_read_limit_and_cooperative_deadline_are_enforced(self) -> None:
        original = self.fs.files["/proc/101/environ"]
        self.fs.files["/proc/101/environ"] = replace(original, data=b"x" * (proof.ENV_LIMIT + 1))
        self.assert_blocked("SNAP_WRAPPER_LIMIT_EXCEEDED")
        with self.assertRaisesRegex(proof.ProvenanceError, "^SNAP_WRAPPER_LIMIT_EXCEEDED$"):
            self.run_proof(clock=Mock(side_effect=[0.0, 60.0]))

    def test_aggregate_budget_is_independent_of_per_read_limit(self) -> None:
        with patch.object(proof, "TOTAL_LIMIT", 1):
            self.assert_blocked("SNAP_WRAPPER_LIMIT_EXCEEDED")

    def test_exact_main_environment_limit_tolerates_unrelated_runtime_values(self) -> None:
        original = self.fs.files["/proc/101/environ"]
        padding = b"PADDING=" + b"x" * (proof.ENV_LIMIT - len(original.data) - 9) + b"\x00"
        self.fs.files["/proc/101/environ"] = replace(original, data=original.data + padding)
        self.assertEqual(len(self.fs.files["/proc/101/environ"].data), proof.ENV_LIMIT)
        self.assertEqual(self.run_proof(), ("lxd_snap", "snap:lxd"))

    def test_oversize_metadata_blocks_before_yaml_parsing(self) -> None:
        self.pair("meta/snap.yaml", regular(51, b"x" * (proof.METADATA_LIMIT + 1)))
        self.assert_blocked("SNAP_WRAPPER_LIMIT_EXCEEDED")

    def test_unexpected_os_error_is_redacted_and_does_not_retry(self) -> None:
        with patch.object(self.fs, "observe", side_effect=PermissionError("secret-value")):
            self.assert_blocked("SNAP_WRAPPER_FILE_UNVERIFIED")
        self.assertEqual(self.runner.run.call_count, 1)

    def test_wrong_unit_never_issues_a_command(self) -> None:
        self.row["unit"] = "incus.service"
        self.assert_blocked("SNAP_WRAPPER_UNIT_INVALID")
        self.runner.run.assert_not_called()


class DescriptorAdapterTests(unittest.TestCase):
    def test_real_directory_walk_pins_the_package_and_reads_normal_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "snap/lxd/123/commands"
            package.mkdir(parents=True)
            (package / "daemon.start").write_bytes(b"installed-wrapper")
            filesystem = proof.LocalReadOnlyFS()
            mapped = (temporary, ("snap", "lxd", "123", "commands"), "daemon.start")
            with patch.object(filesystem, "package_parts", return_value=mapped), \
                    patch.object(proof.os, "fstatvfs", return_value=Mock(f_flag=os.ST_RDONLY)):
                result = filesystem.observe("/snap/lxd/123/commands/daemon.start", limit=100)
            self.assertEqual(result.data, b"installed-wrapper")

    def test_real_parent_symlink_cannot_redirect_to_external_readonly_inode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as external:
            package = Path(temporary) / "snap/lxd/123"
            package.mkdir(parents=True)
            outside = Path(external) / "daemon.start"
            outside.write_bytes(b"external-wrapper")
            outside.chmod(0o444)
            (package / "commands").symlink_to(external, target_is_directory=True)
            filesystem = proof.LocalReadOnlyFS()
            mapped = (temporary, ("snap", "lxd", "123", "commands"), "daemon.start")
            with patch.object(filesystem, "package_parts", return_value=mapped), \
                    patch.object(proof.os, "fstatvfs", return_value=Mock(f_flag=os.ST_RDONLY)):
                with self.assertRaises(OSError):
                    filesystem.observe("/snap/lxd/123/commands/daemon.start", limit=100)
                with self.assertRaises(OSError):
                    filesystem.final_link("/snap/lxd/123/commands/daemon.start")

    def test_child_directory_cannot_cross_the_pinned_package_device(self) -> None:
        directory = Mock(st_mode=stat.S_IFDIR | 0o755, st_dev=1)
        other = Mock(st_mode=stat.S_IFDIR | 0o755, st_dev=2)
        with patch.object(proof.os, "open", side_effect=[10, 11, 12, 13, 14]), \
                patch.object(proof.os, "fstat", side_effect=[directory, directory, directory, other]), \
                patch.object(proof.os, "fstatvfs", return_value=Mock(f_flag=os.ST_RDONLY)), \
                patch.object(proof.os, "close") as closed:
            with self.assertRaisesRegex(proof.ProvenanceError, "^SNAP_WRAPPER_FILE_UNVERIFIED$"):
                with proof.LocalReadOnlyFS.contained_parent("/", ("snap", "lxd", "123", "commands")):
                    self.fail("cross-device package directory was admitted")
        self.assertEqual([call.args[0] for call in closed.call_args_list], [14, 13, 12, 11, 10])

    def test_open_and_close_are_readonly_and_final_symlink_safe(self) -> None:
        metadata = Mock(st_dev=1, st_ino=2, st_mode=stat.S_IFREG | 0o444, st_uid=0,
                        st_size=3, st_mtime_ns=4, st_ctime_ns=5)
        with patch.object(proof.os, "open", return_value=7) as opened, \
                patch.object(proof.os, "fstat", return_value=metadata), \
                patch.object(proof.os, "fstatvfs", return_value=Mock(f_flag=os.ST_RDONLY)), \
                patch.object(proof.os, "read", side_effect=[b"abc", b""]), \
                patch.object(proof.os, "close") as closed:
            result = proof.LocalReadOnlyFS().observe("/fixed", limit=3)
        self.assertEqual(result.data, b"abc")
        flags = opened.call_args.args[1]
        self.assertFalse(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
        self.assertTrue(flags & os.O_NOFOLLOW)
        closed.assert_called_once_with(7)

    def test_limit_plus_one_or_changed_descriptor_closes_before_failure(self) -> None:
        metadata = Mock(st_dev=1, st_ino=2, st_mode=stat.S_IFREG | 0o444, st_uid=0,
                        st_size=3, st_mtime_ns=4, st_ctime_ns=5)
        with patch.object(proof.os, "open", return_value=7), \
                patch.object(proof.os, "fstat", return_value=metadata), \
                patch.object(proof.os, "fstatvfs", return_value=Mock(f_flag=os.ST_RDONLY)), \
                patch.object(proof.os, "read", return_value=b"abcd"), \
                patch.object(proof.os, "close") as closed:
            with self.assertRaisesRegex(proof.ProvenanceError, "^SNAP_WRAPPER_LIMIT_EXCEEDED$"):
                proof.LocalReadOnlyFS().observe("/fixed", limit=3)
        closed.assert_called_once_with(7)


class ContextDiagnosticTests(unittest.TestCase):
    fs: MemoryFS
    row: dict[str, Any]
    values: dict[str, str]
    runner: Mock

    def setUp(self) -> None:
        self.fs = MemoryFS()
        self.row = {"unit": proof.UNIT, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                    "unit_file_state": "enabled", "main_pid": 101}
        self.values = dict.fromkeys(proof.PROPERTIES, "")
        self.values.update(LoadState="loaded", ActiveState="active", SubState="running", UnitFileState="enabled",
                           MainPID="101", ControlGroup="/system.slice/" + proof.UNIT, FragmentPath=proof.UNIT_FILE,
                           ExecStart="{ path=/usr/bin/snap ; argv[]=/usr/bin/snap run lxd.daemon ; ignore_errors=no ; "
                                     "start_time=[Wed 2026-10-28 10:00:00 UTC] ; stop_time=[n/a] ; pid=101 ; code=(null) ; status=0/0 }")
        self.runner = Mock()
        self.runner.run.side_effect = lambda *_a, **_kw: (0, self.unit_bytes(), b"")
        self.fs.files[proof.UNIT_FILE] = regular(10, readonly=False)
        self.add_process(101, 1, 11, 20)
        self.add_process(202, 101, 22, 30)
        self.fs.files["/proc/101/root/bin/sh"] = regular(20, executable=True)
        self.fs.files["/proc/101/cmdline"] = regular(40, b"/bin/sh\x00/snap/lxd/123/commands/daemon.start\x00")
        self.fs.files["/proc/101/environ"] = regular(41, b"SNAP_NAME=lxd\x00SNAP_REVISION=123\x00SNAP=/snap/lxd/123\x00LD_LIBRARY_PATH=/snap/extra\x00")
        self.fs.files["/proc/101/task/101/children"] = regular(42, b"202 ")
        self.pair("commands/daemon.start", regular(50, executable=True))
        self.pair("meta/snap.yaml", regular(51, b"name: lxd\napps:\n  daemon:\n    command: commands/daemon.start\n    daemon: simple\n"))
        self.pair("sbin/lxd", regular(30, executable=True))

    def unit_bytes(self) -> bytes:
        return "".join(f"{key}={value}\n" for key, value in self.values.items()).encode()

    def add_process(self, pid: int, parent: int, started: int, executable: int) -> None:
        self.fs.files[f"/proc/{pid}/stat"] = regular(1000 + pid, proc_stat(pid, parent, started), readonly=False)
        self.fs.files[f"/proc/{pid}/status"] = regular(2000 + pid, b"Name:\tignored\nUid:\t0\t0\t0\t0\n", readonly=False)
        self.fs.files[f"/proc/{pid}/cgroup"] = regular(3000 + pid, ("0::" + self.values["ControlGroup"] + "\n").encode(), readonly=False)
        self.fs.files[f"/proc/{pid}/exe"] = regular(executable, executable=True)

    def pair(self, relative: str, value: proof.Observation) -> None:
        self.fs.files["/snap/lxd/123/" + relative] = value
        self.fs.files["/proc/101/root/snap/lxd/123/" + relative] = value

    def run_proof(self, *, clock=lambda: 0.0) -> tuple[str, str]:
        return proof.prove_snap_wrapper(self.runner, self.row, fs=self.fs, clock=clock)

    def assert_blocked(self, code: str | None = None) -> None:
        with self.assertRaises(proof.ProvenanceError) as caught:
            self.run_proof()
        self.assertTrue(str(caught.exception).startswith("SNAP_WRAPPER_"))
        self.assertNotIn("secret-value", str(caught.exception))
        if code is not None:
            self.assertEqual(str(caught.exception), code)

    def diagnose(self) -> str:
        return proof.diagnose_context(self.runner, self.row, fs=self.fs, clock=lambda: 0.0)

    def test_unit_categories_and_normal_proof_parity(self) -> None:
        cases = (("ExecStart", "secret-token", "EXECSTART_FORMAT_OR_TIME"),
                 ("ControlGroup", "secret-token", "CONTROL_GROUP"),
                 ("FragmentPath", "secret-token", "FRAGMENT_OR_HOOK"),
                 ("DropInPaths", "secret-token", "DROPIN_OR_ENV_SETTING"),
                 ("EnvironmentFiles", "secret-token", "ENVIRONMENT_FILE_SPEC"))
        for field, value, reason in cases:
            with self.subTest(field=field):
                original = self.values[field]
                self.values[field] = value
                self.runner.reset_mock()
                self.fs.calls.clear()
                self.assertEqual(self.diagnose(), reason)
                self.assertEqual(self.runner.run.call_count, 2)
                self.assertEqual(self.fs.calls, [])
                self.assert_blocked("SNAP_WRAPPER_CONTEXT_BLOCKED")
                self.values[field] = original

    def test_priority_and_no_lower_file_reads(self) -> None:
        self.values.update(ExecStart="secret", ControlGroup="secret", EnvironmentFiles="secret")
        self.assertEqual(self.diagnose(), "EXECSTART_FORMAT_OR_TIME")
        self.assertEqual(self.fs.calls, [])

    def test_pairwise_unit_priority(self) -> None:
        cases = (("ExecStart", "EXECSTART_FORMAT_OR_TIME"), ("ControlGroup", "CONTROL_GROUP"),
                 ("FragmentPath", "FRAGMENT_OR_HOOK"), ("DropInPaths", "DROPIN_OR_ENV_SETTING"),
                 ("EnvironmentFiles", "ENVIRONMENT_FILE_SPEC"))
        original = dict(self.values)
        for index, (field, reason) in enumerate(cases):
            for later_field, _ in cases[index + 1:]:
                with self.subTest(first=field, second=later_field):
                    self.values = dict(original)
                    self.values[field] = self.values[later_field] = "secret-token"
                    self.assertEqual(self.diagnose(), reason)
                    self.assertEqual(self.fs.calls, [])

    def test_unit_rejection_precedes_each_rejected_context_file(self) -> None:
        cases = (("ExecStart", "EXECSTART_FORMAT_OR_TIME"), ("ControlGroup", "CONTROL_GROUP"),
                 ("FragmentPath", "FRAGMENT_OR_HOOK"), ("DropInPaths", "DROPIN_OR_ENV_SETTING"),
                 ("EnvironmentFiles", "ENVIRONMENT_FILE_SPEC"))
        original = dict(self.values)
        good_drop = b"[Unit]\nAfter=snap.microceph.daemon.service snap.microovn.daemon.service\n"
        for field, reason in cases:
            for rejected_file in ("dropin", "environment"):
                with self.subTest(field=field, rejected_file=rejected_file):
                    self.values = dict(original)
                    self.values["DropInPaths"] = proof.DROP_IN
                    self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
                    self.fs.files[proof.DROP_IN] = regular(7, b"secret\n" if rejected_file == "dropin" else good_drop)
                    self.fs.files["/etc/environment"] = regular(8, b"SECRET=value\n" if rejected_file == "environment" else b"")
                    self.values[field] = "secret-token"
                    self.fs.calls.clear()
                    self.runner.reset_mock()
                    self.assertEqual(self.diagnose(), reason)
                    self.assertEqual(self.fs.calls, [])
                    self.assertEqual(self.runner.run.call_count, 2)

    def test_malformed_duplicate_timeout_and_second_query_error_are_unknown(self) -> None:
        valid = self.unit_bytes()
        for raw in (valid + b"MainPID=101\n", valid + b"NotAllowed=secret\n", b"\xff"):
            self.runner.run.side_effect = None
            self.runner.run.return_value = (0, raw, b"")
            self.assertEqual(self.diagnose(), "UNKNOWN")
        self.values["ControlGroup"] = "secret"
        self.runner.run.side_effect = [(0, self.unit_bytes(), b""), OSError("secret")]
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.runner.run.side_effect = None
        self.runner.run.return_value = (0, self.unit_bytes(), b"")
        self.assertEqual(proof.diagnose_context(self.runner, self.row, fs=self.fs,
                                                clock=iter([0.0, 61.0]).__next__), "UNKNOWN")

    def test_dropin_and_environment_categories_reobserve_only_trusted_fixed_files(self) -> None:
        self.values["DropInPaths"] = proof.DROP_IN
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        self.fs.files[proof.DROP_IN] = regular(7, b"secret-content\n")
        self.fs.files["/etc/environment"] = regular(8, b"SECRET=secret-content\n")
        self.assertEqual(self.diagnose(), "DROPIN_CONTENT")
        self.assertNotIn("/etc/environment", [item[0] for item in self.fs.calls])
        self.fs.files[proof.DROP_IN] = regular(7, b"[Unit]\nAfter=snap.microceph.daemon.service snap.microovn.daemon.service\n")
        self.fs.calls.clear()
        self.assertEqual(self.diagnose(), "ENVIRONMENT_FILE_CONTENT")
        self.assertEqual([item[0] for item in self.fs.calls], [proof.UNIT_FILE, proof.DROP_IN, "/etc/environment"] * 2)

    def test_content_rejections_match_original_proof_and_do_not_read_later_files(self) -> None:
        unit = {"DropInPaths": proof.DROP_IN, "EnvironmentFiles": "/etc/environment (ignore_errors=yes)"}
        self.values.update(unit)
        self.fs.files[proof.DROP_IN] = regular(7, b"[Unit]\nsecret-token\n")
        with self.assertRaisesRegex(proof.ProvenanceError, "^SNAP_WRAPPER_CONTEXT_BLOCKED$"):
            proof._Proof(self.runner, self.fs, lambda: 0.0).context(unit)
        self.fs.calls.clear()
        self.assertEqual(self.diagnose(), "DROPIN_CONTENT")
        self.assertNotIn("/etc/environment", [call[0] for call in self.fs.calls])
        self.fs.files[proof.DROP_IN] = regular(7, b"[Unit]\nAfter=snap.microceph.daemon.service snap.microovn.daemon.service\n")
        self.fs.files["/etc/environment"] = regular(8, b"SECRET=secret-token\n")
        with self.assertRaisesRegex(proof.ProvenanceError, "^SNAP_WRAPPER_CONTEXT_BLOCKED$"):
            proof._Proof(self.runner, self.fs, lambda: 0.0).context(unit)
        self.assertEqual(self.diagnose(), "ENVIRONMENT_FILE_CONTENT")

    def test_invalid_properties_and_untrusted_paths_stop_before_context_reads(self) -> None:
        self.values["EnvironmentFiles"] = "/tmp/secret-token"
        self.assertEqual(self.diagnose(), "ENVIRONMENT_FILE_SPEC")
        self.assertEqual(self.fs.calls, [])
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        self.fs.links["/etc/environment"] = "/tmp/secret-token"
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.assertNotIn("/tmp/secret-token", [call[0] for call in self.fs.calls])

    def test_no_rejection_and_invalid_unicode_return_unknown(self) -> None:
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        self.fs.files["/etc/environment"] = regular(8, b"\xffsecret")
        self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_execstart_calendar_validation_and_drift_never_leak(self) -> None:
        valid = self.values["ExecStart"]
        first_invalid = valid.replace("2026-10-28", "2026-02-31")
        second_invalid = valid.replace("2026-10-28", "2026-02-30")
        valid_other = valid.replace("2026-10-28", "2026-02-28").replace("Wed ", "Sat ")
        for first, second, expected in (
            (first_invalid, valid_other, "UNKNOWN"),
            (valid_other, first_invalid, "UNKNOWN"),
            (first_invalid, second_invalid, "UNKNOWN"),
            (first_invalid, first_invalid, "EXECSTART_FORMAT_OR_TIME"),
        ):
            with self.subTest(expected=expected, first_valid=first == valid_other, second_valid=second == valid_other):
                self.values["ExecStart"] = first
                initial = self.unit_bytes()
                self.values["ExecStart"] = second
                final = self.unit_bytes()
                self.runner.run.side_effect = [(0, initial, b"secret-token"), (0, final, b"secret-token")]
                result = self.diagnose()
                self.assertEqual(result, expected)
                self.assertNotIn("secret-token", result)
                self.assertNotIn(first, result)
                self.assertNotIn(second, result)

    def test_unit_and_file_drift_and_recheck_failure_return_unknown(self) -> None:
        self.values["ControlGroup"] = "secret"
        first = self.unit_bytes()
        self.values["ControlGroup"] = "other-secret"
        self.runner.run.side_effect = [(0, first, b""), (0, self.unit_bytes(), b"")]
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.runner.run.side_effect = lambda *_a, **_kw: (0, self.unit_bytes(), b"")
        self.values["ControlGroup"] = "/system.slice/" + proof.UNIT
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        self.fs.sequences["/etc/environment"] = [regular(8, b"SECRET=one\n"), regular(8, b"SECRET=two\n")]
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.runner.run.side_effect = OSError("secret-token")
        self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_untrusted_files_and_invalid_unit_never_emit_values(self) -> None:
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        self.fs.files["/etc/environment"] = replace(regular(8, b"SECRET=value"), uid=1000)
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.runner.run.side_effect = None
        self.runner.run.return_value = (0, self.unit_bytes() + b"SECRET=secret-token\n", b"")
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.assertEqual(self.runner.run.call_args.args, (proof.UNIT_ARGV,))

    def dropin_diagnose(self) -> str:
        return proof.diagnose_dropin(self.runner, self.row, fs=self.fs, clock=lambda: 0.0)

    def test_dropin_form_categories_and_no_environment_read(self) -> None:
        self.values["DropInPaths"] = proof.DROP_IN
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        cases = ((b"[Other]\nAfter=secret-token\n", "SECTION_SHAPE"),
                 (b"[Unit]\nAfter=secret-token\n[Other]\n", "SECTION_SHAPE"),
                 (b"[Unit]\n", "UNKNOWN_DIRECTIVE"),
                 (b"[Unit]\nOther=secret-token\n", "UNKNOWN_DIRECTIVE"),
                 (b"[Unit]\nAfter=one\nAfter=two\n", "UNKNOWN_DIRECTIVE"),
                 (b"# comment\n[Unit]\n\nAfter=secret-token\n", "DEPENDENCY_VARIANT"),
                 (b"[Unit]\nAfter=snap.microceph.daemon.service snap.microovn.daemon.service\n", "UNKNOWN"),
                 (b"[Unit]\nAfter=secret-token\r\n", "UNKNOWN"),
                 (b"[Unit]\nAfter=secret\x00\n", "UNKNOWN"),
                 (b"[Unit]\nAfter=secret\\\n continuation\n", "UNKNOWN"),
                 (b"[Unit]\nAfter=\xff\n", "UNKNOWN"),
                 (b"[Unit\nAfter=secret\n", "UNKNOWN"))
        for raw, expected in cases:
            with self.subTest(expected=expected, raw=raw):
                self.fs.files[proof.DROP_IN] = regular(7, raw)
                self.fs.calls.clear()
                self.runner.reset_mock()
                result = self.dropin_diagnose()
                self.assertEqual(result, expected)
                self.assertNotIn("secret-token", result)
                invalid_utf8 = raw == b"[Unit]\nAfter=\xff\n"
                self.assertEqual(self.runner.run.call_count, 1 if invalid_utf8 else 2)
                expected_paths = [proof.UNIT_FILE, proof.DROP_IN]
                self.assertEqual([item[0] for item in self.fs.calls],
                                 expected_paths if invalid_utf8 else expected_paths * 2)
                self.assertNotIn("/etc/environment", [item[0] for item in self.fs.calls])

    def test_dropin_unit_failures_stop_before_files(self) -> None:
        self.values["DropInPaths"] = "secret-token"
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.assertEqual(self.fs.calls, [])
        self.assertEqual(self.runner.run.call_count, 1)
        self.values["DropInPaths"] = ""
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.assertEqual(self.fs.calls, [])

    def test_dropin_trust_missing_size_and_drift_fail_closed(self) -> None:
        self.values["DropInPaths"] = proof.DROP_IN
        for value in (replace(regular(7, b"[Unit]\nAfter=secret\n"), uid=1000),
                      regular(7, b"x" * (proof.PROC_LIMIT + 1))):
            with self.subTest(value=value):
                self.fs.files[proof.DROP_IN] = value
                self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.fs.files.pop(proof.DROP_IN)
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.fs.links[proof.DROP_IN] = "/tmp/secret-token"
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.fs.links.clear()
        self.fs.sequences[proof.DROP_IN] = [regular(7, b"[Unit]\nAfter=one\n"),
                                              regular(7, b"[Unit]\nAfter=two\n")]
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")

    def test_dropin_unit_drift_and_io_failure_are_unknown(self) -> None:
        self.values["DropInPaths"] = proof.DROP_IN
        self.fs.files[proof.DROP_IN] = regular(7, b"[Unit]\nAfter=secret-token\n")
        initial = self.unit_bytes()
        self.values["ControlGroup"] = "/different"
        self.runner.run.side_effect = [(0, initial, b""), (0, self.unit_bytes(), b"")]
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.runner.run.side_effect = OSError("secret-token")
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.assertEqual(proof.diagnose_dropin(self.runner, self.row, fs=self.fs,
                                               clock=iter([0.0, 61.0]).__next__), "UNKNOWN")

    def test_dropin_categories_reproduce_f5_rejection(self) -> None:
        self.values["DropInPaths"] = proof.DROP_IN
        self.values["EnvironmentFiles"] = "/etc/environment (ignore_errors=yes)"
        cases = ((b"[Other]\nAfter=secret\n", "SECTION_SHAPE"),
                 (b"[Unit]\nOther=secret\n", "UNKNOWN_DIRECTIVE"),
                 (b"[Unit]\nAfter=secret\n", "DEPENDENCY_VARIANT"))
        for raw, reason in cases:
            with self.subTest(reason=reason):
                self.fs.files[proof.DROP_IN] = regular(7, raw)
                self.fs.calls.clear()
                self.assertEqual(self.diagnose(), "DROPIN_CONTENT")
                self.assertNotIn("/etc/environment", [item[0] for item in self.fs.calls])
                self.fs.calls.clear()
                self.assertEqual(self.dropin_diagnose(), reason)
                self.assertNotIn("/etc/environment", [item[0] for item in self.fs.calls])

    def test_dropin_identity_mode_and_unit_failure_cannot_be_classified(self) -> None:
        self.values["DropInPaths"] = proof.DROP_IN
        raw = b"[Unit]\nAfter=secret-token\n"
        self.fs.files[proof.DROP_IN] = replace(regular(7, raw), mode=stat.S_IFREG | 0o666)
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.fs.files[proof.DROP_IN] = regular(7, raw)
        self.fs.sequences[proof.DROP_IN] = [regular(7, raw), regular(8, raw)]
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.fs.sequences.clear()
        self.fs.sequences[proof.UNIT_FILE] = [regular(10), regular(11)]
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")
        self.fs.sequences.clear()
        self.runner.run.side_effect = [(0, self.unit_bytes(), b""), OSError("secret-token")]
        self.assertEqual(self.dropin_diagnose(), "UNKNOWN")

    def test_dropin_unsafe_syntax_overrides_structural_categories(self) -> None:
        self.values["DropInPaths"] = proof.DROP_IN
        for raw in (b"[Other]\nAfter=secret\\\n", b"[Unit]\nOther=secret\r\n",
                    b"[Other]\nAfter=secret\x00\n", b"[Unit]\nAfter=\xff\n"):
            with self.subTest(raw=raw):
                self.fs.files[proof.DROP_IN] = regular(7, raw)
                self.assertEqual(self.dropin_diagnose(), "UNKNOWN")

    def test_dropin_malformed_lines_never_report_structural_category(self) -> None:
        self.values["DropInPaths"] = proof.DROP_IN
        cases = (b"[Unit]\nnot-an-assignment secret-token\n",
                 b"[broken\nAfter=secret-token\n",
                 b"[Unit]\n[broken\nAfter=secret-token\n",
                 b"[Other]\nnot-an-assignment secret-token\n",
                 b"[Unit]\nInvalid Name=secret-token\n",
                 b'[Unit]\nAfter="secret-token\n',
                 b'[Unit]\nAfter="secret-token"\n',
                 b"[Unit]\nAfter='secret-token'\n",
                 b'[Other]\nAfter="secret-token\n',
                 b"[Unit]\nOther='secret-token'\n")
        for raw in cases:
            with self.subTest(raw=raw):
                self.fs.files[proof.DROP_IN] = regular(7, raw)
                result = self.dropin_diagnose()
                self.assertEqual(result, "UNKNOWN")
                self.assertNotIn("secret-token", result)


class GeneratorFormTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = WrapperProofTests("runTest")
        fixture.setUp()
        self.fixture = fixture
        self.fs = fixture.fs
        self.row = fixture.row
        self.runner = fixture.runner
        fixture.values["DropInPaths"] = proof.DROP_IN
        self.fs.files[proof.DROP_IN] = regular(999, proof._GENERATOR_PREFIX + b"\n", readonly=False)
        base = "/snap/lxd/40958"
        self.fs.files["/proc/101/cmdline"] = regular(40, b"/bin/sh\x00" + (base + "/commands/daemon.start").encode() + b"\x00")
        self.fs.files["/proc/101/environ"] = regular(41, b"SNAP_NAME=lxd\x00SNAP_REVISION=40958\x00SNAP=/snap/lxd/40958\x00")
        script = regular(50, b"source fixture", executable=True)
        self.fs.files[base + "/commands/daemon.start"] = script
        self.fs.files["/proc/101/root" + base + "/commands/daemon.start"] = script

    def diagnose(self) -> str:
        # Synthetic script bytes are not the public package; simulate only the
        # pinned digest so every other proof boundary runs through MemoryFS.
        digest = Mock()
        digest.hexdigest.return_value = proof._GENERATOR_DIGEST
        with patch.object(proof.hashlib, "sha256", return_value=digest):
            return proof.diagnose_generator_form(self.runner, self.row, fs=self.fs, clock=lambda: 0.0)

    def test_public_source_static_literals_and_script_digest_input(self) -> None:
        # Independent, source-pinned fixture: Canonical LXD 3a06799 daemon.start.
        source_tokens = (
            "snap.microceph.daemon.service", "snap.microceph.mds.service",
            "snap.microceph.mgr.service", "snap.microceph.mon.service",
            "snap.microceph.nfs.service", "snap.microceph.osd.service",
            "snap.microceph.rgw.service", "snap.microceph.rbd-mirror.service",
            "snap.microceph.cephfs-mirror.service", "snap.microovn.daemon.service",
            "snap.microovn.ovn-ovsdb-server-nb.service", "snap.microovn.ovn-ovsdb-server-sb.service",
            "snap.microovn.ovn-northd.service", "snap.microovn.chassis.service",
            "snap.microovn.switch.service", "snap.microovn.bird.service",
        )
        self.assertEqual(proof._GENERATOR_TOKENS, source_tokens)
        self.assertEqual(proof._GENERATOR_PREFIX, ("[Unit]\nAfter=" + " ".join(source_tokens) + " ").encode("ascii"))
        digest = Mock()
        digest.hexdigest.return_value = "7ecbe39a07dc02666af544327dbaf5cfbe9967868bfb9d7c627061f14916b562"
        with patch.object(proof.hashlib, "sha256", return_value=digest) as hasher:
            self.assertEqual(proof.diagnose_generator_form(self.runner, self.row, fs=self.fs, clock=lambda: 0.0), "MATCH")
        hasher.assert_called_once_with(b"source fixture")

    def test_static_form_and_all_dynamic_members_duplicates_and_bounds(self) -> None:
        members = [item.encode() for item in proof._GENERATOR_TOKENS]
        suffixes = [b"", *(item + b" " for item in members), members[0] + b"  " + members[0] + b" ",
                    (members[0] + b" ") * 256]
        for suffix in suffixes:
            with self.subTest(length=len(suffix)):
                self.fs.files[proof.DROP_IN] = regular(999, proof._GENERATOR_PREFIX + suffix + b"\n", readonly=False)
                self.assertEqual(self.diagnose(), "MATCH")
                self.assertNotIn("/etc/environment", [call[0] for call in self.fs.calls])
        self.fs.files[proof.DROP_IN] = regular(999, proof._GENERATOR_PREFIX + (members[0] + b" ") * 257 + b"\n")
        self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_every_static_position_cannot_be_replaced_removed_or_shifted(self) -> None:
        tokens = list(proof._GENERATOR_TOKENS)
        for index in range(len(tokens)):
            for kind in ("replace", "remove", "reverse"):
                changed = tokens.copy()
                if kind == "replace":
                    changed[index] = "secret-value.service"
                elif kind == "remove":
                    del changed[index]
                else:
                    changed[index], changed[(index + 1) % len(tokens)] = changed[(index + 1) % len(tokens)], changed[index]
                raw = ("[Unit]\nAfter=" + " ".join(changed) + " \n").encode()
                with self.subTest(index=index, kind=kind):
                    self.assertFalse(proof._generator_form(raw))

    def test_unsafe_forms_and_foreign_tokens_never_match(self) -> None:
        prefix = proof._GENERATOR_PREFIX
        for raw in (prefix + b"evil.service \n", prefix + b" secret-value \n", prefix + b"\n[Service]\n",
                    prefix + b"\r\n", prefix + b"\x00\n", prefix + b"\t\n", prefix + b"'x' \n",
                    prefix + b"\\x \n", prefix + b"%x \n", prefix + b"\xff\n", prefix[:-1] + b"\n",
                    prefix + b"snap.microceph.daemon.service\n", prefix + b"\nX"):
            with self.subTest(case=len(raw)):
                self.assertFalse(proof._generator_form(raw))

    def test_wrong_revision_or_script_digest_remains_unknown(self) -> None:
        self.fs.files["/proc/101/environ"] = regular(41, b"SNAP_NAME=lxd\x00SNAP_REVISION=123\x00SNAP=/snap/lxd/123\x00")
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.setUp()
        digest = Mock()
        digest.hexdigest.return_value = "0" * 64
        with patch.object(proof.hashlib, "sha256", return_value=digest):
            self.assertEqual(proof.diagnose_generator_form(self.runner, self.row, fs=self.fs, clock=lambda: 0.0), "UNKNOWN")

    def test_trust_process_and_script_pair_fail_closed(self) -> None:
        script_path = "/snap/lxd/40958/commands/daemon.start"
        for path, changed in ((proof.DROP_IN, regular(999, proof._GENERATOR_PREFIX + b"\n", readonly=False)),
                              (script_path, regular(50, b"other", executable=True))):
            with self.subTest(path=path):
                if path == proof.DROP_IN:
                    changed = replace(changed, uid=123)
                self.fs.files[path] = changed
                self.assertEqual(self.diagnose(), "UNKNOWN")
                self.setUp()
        self.fs.files["/proc/101/status"] = regular(2101, b"Uid:\t1\t1\t1\t1\n", readonly=False)
        self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_unit_process_script_and_dropin_drift_are_unknown(self) -> None:
        script_path = "/snap/lxd/40958/commands/daemon.start"
        original = self.fs.files[script_path]
        self.fs.sequences[script_path] = [original, replace(original, inode=51)]
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.setUp()
        drop = self.fs.files[proof.DROP_IN]
        self.fs.sequences[proof.DROP_IN] = [drop, replace(drop, data=drop.data + b"secret-value")]
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.setUp()
        proc = self.fs.files["/proc/101/stat"]
        self.fs.sequences["/proc/101/stat"] = [proc, replace(proc, data=proc_stat(101, 1, 12))]
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.setUp()
        before = self.fixture.unit_bytes()
        self.runner.run.side_effect = [(0, before, b""), (0, before.replace(b"MainPID=101", b"MainPID=102"), b"")]
        self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_missing_symlink_timeout_and_input_errors_do_not_leak(self) -> None:
        self.fs.links["/snap/lxd/40958/commands/daemon.start"] = "secret-path"
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.setUp()
        del self.fs.files[proof.DROP_IN]
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.runner.run.side_effect = ValueError("secret-value")
        self.assertEqual(self.diagnose(), "UNKNOWN")


    def test_cooperative_deadline_stops_before_unit_or_file_access(self) -> None:
        times = iter((0.0, float(proof.MAX_SECONDS)))
        self.runner.reset_mock()
        self.fs.calls.clear()
        result = proof.diagnose_generator_form(self.runner, self.row, fs=self.fs, clock=lambda: next(times))
        self.assertEqual(result, "UNKNOWN")
        self.runner.run.assert_not_called()
        self.assertEqual(self.fs.calls, [])

    def test_script_and_dropin_exact_bounds_and_overflow(self) -> None:
        host = "/snap/lxd/40958/commands/daemon.start"
        proc = "/proc/101/root" + host
        for size, expected in ((proof.METADATA_LIMIT, "MATCH"), (proof.METADATA_LIMIT + 1, "UNKNOWN")):
            with self.subTest(kind="script", size=size):
                self.setUp()
                script = regular(50, b"x" * size, executable=True)
                self.fs.files[host] = self.fs.files[proc] = script
                self.assertEqual(self.diagnose(), expected)
        member = proof._GENERATOR_TOKENS[0].encode()
        for size, expected in ((proof.PROC_LIMIT, "MATCH"), (proof.PROC_LIMIT + 1, "UNKNOWN")):
            with self.subTest(kind="dropin", size=size):
                self.setUp()
                tail = member + b" " * (size - len(proof._GENERATOR_PREFIX) - len(member) - 1) + b"\n"
                self.fs.files[proof.DROP_IN] = regular(999, proof._GENERATOR_PREFIX + tail, readonly=False)
                self.assertEqual(self.diagnose(), expected)

    def test_each_script_pair_trust_and_identity_failure_is_unknown(self) -> None:
        host = "/snap/lxd/40958/commands/daemon.start"
        proc = "/proc/101/root" + host
        original = regular(50, b"source fixture", executable=True)
        cases = ((host, replace(original, readonly=False)),
                 (host, replace(original, uid=1000)),
                 (host, replace(original, mode=stat.S_IFREG | 0o777)),
                 (proc, replace(original, inode=51)),
                 (proc, replace(original, device=2)),
                 (proc, replace(original, data=b"secret mismatch")))
        for path, value in cases:
            with self.subTest(path=path, mode=value.mode):
                self.setUp()
                self.fs.files[path] = value
                self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_wrong_argv_and_rechecked_process_context_remain_unknown(self) -> None:
        for path, data in (("/proc/101/cmdline", b"/bin/sh\x00/snap/lxd/123/commands/daemon.start\x00"),
                           ("/proc/101/environ", b"SNAP_NAME=lxd\x00SNAP_REVISION=40958\x00SNAP=/snap/lxd/123\x00")):
            with self.subTest(path=path):
                self.setUp()
                self.fs.files[path] = regular(40, data)
                self.assertEqual(self.diagnose(), "UNKNOWN")
        self.setUp()
        path = "/proc/101/environ"
        initial = self.fs.files[path]
        altered = replace(initial, data=b"SNAP_NAME=lxd\x00SNAP_REVISION=123\x00SNAP=/snap/lxd/123\x00")
        self.fs.sequences[path] = [initial, altered]
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.setUp()
        path = "/proc/101/cmdline"
        initial = self.fs.files[path]
        altered = replace(initial, data=b"/bin/sh\x00/snap/lxd/123/commands/daemon.start\x00")
        self.fs.sequences[path] = [initial, altered]
        self.assertEqual(self.diagnose(), "UNKNOWN")


class GeneratorStageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = GeneratorFormTests("runTest")
        self.fixture.setUp()
        self.fs = self.fixture.fs
        self.row = self.fixture.row
        self.runner = self.fixture.runner
        self.values = self.fixture.fixture.values

    def stage(self, *, digest_value: str = proof._GENERATOR_DIGEST) -> str:
        digest = Mock()
        digest.hexdigest.return_value = digest_value
        with patch.object(proof.hashlib, "sha256", return_value=digest):
            return proof.diagnose_generator_stage(self.runner, self.row, fs=self.fs, clock=lambda: 0.0)

    def test_successful_generator_proof_remains_blocked_unknown(self) -> None:
        self.assertEqual(self.stage(), "UNKNOWN")
        self.assertNotIn("/etc/environment", [call[0] for call in self.fs.calls])
        self.assertEqual(self.runner.run.call_count, 2)

    def test_stable_unit_and_dropin_rejections_report_only_first_stage(self) -> None:
        self.values["FragmentPath"] = "/private-secret"
        self.assertEqual(self.stage(), "UNIT_CONTEXT")
        self.assertEqual(self.fs.calls, [])
        self.assertEqual(self.runner.run.call_count, 2)
        self.setUp()
        self.fs.files[proof.DROP_IN] = regular(999, b"[Unit]\nAfter=private-secret.service\n", readonly=False)
        self.assertEqual(self.stage(), "DROPIN_TRUST_OR_FORM")
        self.assertEqual([item[0] for item in self.fs.calls], [proof.UNIT_FILE, proof.DROP_IN] * 2)
        self.assertEqual(self.runner.run.call_count, 2)

    def test_explicit_process_cgroup_mismatch_requires_identical_rejection(self) -> None:
        path = "/proc/101/cgroup"
        self.fs.files[path] = regular(3101, b"0::/other-group\n", readonly=False)
        self.assertEqual(self.stage(), "PROCESS_BINDING")
        self.assertNotIn("/proc/101/environ", [call[0] for call in self.fs.calls])
        self.setUp()
        self.fs.sequences[path] = [regular(3101, b"0::/other-group\n", readonly=False),
                                   regular(3101, b"0::/different-group\n", readonly=False)]
        self.assertEqual(self.stage(), "UNKNOWN")

    def test_revision_and_shell_rejections_require_valid_prior_snapshots(self) -> None:
        self.fs.files["/proc/101/environ"] = regular(41, b"SNAP_NAME=lxd\x00SNAP_REVISION=124\x00SNAP=/snap/lxd/124\x00")
        self.fs.files["/proc/101/cmdline"] = regular(40, b"/bin/sh\x00/snap/lxd/124/commands/daemon.start\x00")
        self.assertEqual(self.stage(), "REVISION_BINDING")
        self.assertNotIn("/snap/lxd/124/commands/daemon.start", [call[0] for call in self.fs.calls])
        self.setUp()
        self.fs.files["/proc/101/root/bin/sh"] = regular(21, executable=True)
        self.assertEqual(self.stage(), "SHELL_BINDING")
        self.assertNotIn("/snap/lxd/40958/commands/daemon.start", [call[0] for call in self.fs.calls])

    def test_script_identity_or_digest_rejections_are_rechecked(self) -> None:
        self.fs.files["/proc/101/root/snap/lxd/40958/commands/daemon.start"] = regular(51, b"source fixture", executable=True)
        self.assertEqual(self.stage(), "SCRIPT_PAIR_OR_DIGEST")
        self.setUp()
        self.assertEqual(self.stage(digest_value="0" * 64), "SCRIPT_PAIR_OR_DIGEST")

    def test_trusted_comparable_drift_is_distinct_from_io_or_untrusted_failure(self) -> None:
        original = self.fs.files[proof.DROP_IN]
        self.fs.sequences[proof.DROP_IN] = [original, replace(original, inode=1234)]
        self.assertEqual(self.stage(), "RECHECK_DRIFT")
        self.setUp()
        del self.fs.files["/proc/101/environ"]
        self.assertEqual(self.stage(), "UNKNOWN")
        self.setUp()
        self.fs.files[proof.DROP_IN] = replace(self.fs.files[proof.DROP_IN], uid=1000)
        self.assertEqual(self.stage(), "UNKNOWN")

    def test_missing_or_denied_recheck_is_unknown_not_drift(self) -> None:
        for target in (proof.UNIT_FILE, proof.DROP_IN, "/proc/101/environ",
                       "/snap/lxd/40958/commands/daemon.start"):
            with self.subTest(target=target):
                self.setUp()
                original_observe = self.fs.observe
                visits = 0

                def observe(path: str, *, limit: int | None = None, follow: bool = False) -> proof.Observation:
                    nonlocal visits
                    if path == target:
                        visits += 1
                        if visits == 2:
                            raise FileNotFoundError("private-secret")
                    return original_observe(path, limit=limit, follow=follow)

                with patch.object(self.fs, "observe", side_effect=observe):
                    self.assertEqual(self.stage(), "UNKNOWN")
                self.assertNotIn("/etc/environment", [call[0] for call in self.fs.calls])
        self.setUp()
        original = self.fs.files[proof.DROP_IN]
        self.fs.sequences[proof.DROP_IN] = [original, replace(original, inode=1234)]
        self.assertEqual(self.stage(), "RECHECK_DRIFT")

    def test_failed_or_expired_early_recheck_is_unknown_without_later_reads(self) -> None:
        self.values["FragmentPath"] = "/private-secret"
        initial = self.fixture.fixture.unit_bytes()
        for failure in (PermissionError("secret-token"), OSError("private-secret")):
            with self.subTest(failure=type(failure).__name__):
                self.setUp()
                self.values["FragmentPath"] = "/private-secret"
                initial = self.fixture.fixture.unit_bytes()
                self.runner.run.side_effect = [(0, initial, b""), failure]
                self.assertEqual(self.stage(), "UNKNOWN")
                self.assertEqual(self.fs.calls, [])
        self.setUp()
        self.values["FragmentPath"] = "/private-secret"
        clock = iter([0.0, 0.0, 0.0, 60.0])
        result = proof.diagnose_generator_stage(self.runner, self.row, fs=self.fs, clock=lambda: next(clock))
        self.assertEqual(result, "UNKNOWN")
        self.assertEqual(self.runner.run.call_count, 1)
        self.assertEqual(self.fs.calls, [])

    def test_unknown_for_malformed_and_unstable_inputs_and_all_stages_remain_redacted(self) -> None:
        self.values["ExecStart"] = "secret-token"
        self.assertEqual(self.stage(), "UNKNOWN")
        self.setUp()
        initial = self.fixture.fixture.unit_bytes()
        changed = initial.replace(b"FragmentPath=", b"FragmentPath=/private-secret")
        self.runner.run.side_effect = [(0, initial, b""), (0, changed, b"")]
        self.assertEqual(self.stage(), "UNKNOWN")
        self.setUp()
        self.runner.run.side_effect = PermissionError("secret-token /private/path")
        self.assertEqual(self.stage(), "UNKNOWN")
        self.assertNotIn("/etc/environment", [call[0] for call in self.fs.calls])


class CgroupRelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = GeneratorStageTests("runTest")
        self.fixture.setUp()
        self.fs = self.fixture.fs
        self.row = self.fixture.row
        self.runner = self.fixture.runner
        self.values = self.fixture.values

    def diagnose(self) -> str:
        return proof.diagnose_cgroup_relation(self.runner, self.row, fs=self.fs, clock=lambda: 0.0)

    def test_component_relations_and_prefix_collisions(self) -> None:
        cases = (
            ("/a/b", b"0::/\n", "PROC_ROOT"),
            ("/a/b", b"0::/a\n", "PROC_STRICT_ANCESTOR"),
            ("/a", b"0::/a/b\n", "PROC_STRICT_DESCENDANT"),
            ("/", b"0::/a/b\n", "PROC_STRICT_DESCENDANT"),
            ("/a", b"0::/ab\n", "DISJOINT"),
            ("/a/b", b"0::/a/c", "DISJOINT"),
            ("/équipe/service unit", "0::/équipe\n".encode(), "PROC_STRICT_ANCESTOR"),
            ("/a\tb/child", b"0::/a\tb\n", "PROC_STRICT_ANCESTOR"),
            ("/a\u00a0b", "0::/a\u00a0b/child\n".encode(), "PROC_STRICT_DESCENDANT"),
            ("/équipe", "0::/équipe/子 group\n".encode(), "PROC_STRICT_DESCENDANT"),
            ("/équipe/service", "0::/équipe-other\n".encode(), "DISJOINT"),
            ("/a", b"0::/a\n", "UNKNOWN"),
        )
        for unit, raw, expected in cases:
            with self.subTest(expected=expected, unit=unit):
                self.assertEqual(proof._cgroup_relation(unit, raw), expected)

    def test_invalid_and_noncanonical_paths_are_unknown(self) -> None:
        for raw in (b"0::/a//b\n", b"0::/a/./b\n", b"0::/a/../b\n", b"0::/a/\n",
                    b"0::relative\n", b"0::/a\n0::/b\n", b"0::/a\r\n",
                    b"0::/a\x00\n", b"0::/\xff\n", b"1::/a\n"):
            with self.subTest(raw=raw):
                self.assertEqual(proof._cgroup_relation("/system.slice/example", raw), "UNKNOWN")
        for unit in ("/a/./b", "//a", "/a/", "/a/../b", "relative", "/a\nsecret"):
            with self.subTest(unit=unit):
                self.assertEqual(proof._cgroup_relation(unit, b"0::/other\n"), "UNKNOWN")

    def test_stable_root_mismatch_is_classified_without_later_reads(self) -> None:
        path = "/proc/101/cgroup"
        self.fs.files[path] = regular(3101, b"0::/\n", readonly=False)
        self.assertEqual(self.diagnose(), "PROC_ROOT")
        reads = [call[0] for call in self.fs.calls]
        self.assertEqual(self.runner.run.call_count, 2)
        self.assertNotIn("/proc/101/environ", reads)
        self.assertNotIn("/etc/environment", reads)
        self.assertNotIn("/proc/101/exe", reads)
        self.assertEqual(reads.count(path), 2)

    def test_stable_ancestry_and_disjoint_are_reported_from_existing_snapshots(self) -> None:
        path = "/proc/101/cgroup"
        group = self.values["ControlGroup"]
        cases = (
            (b"0::/system.slice\n", "PROC_STRICT_ANCESTOR"),
            (("0::" + group + "/child\n").encode(), "PROC_STRICT_DESCENDANT"),
            (b"0::/system.slice-other\n", "DISJOINT"),
        )
        for raw, reason in cases:
            with self.subTest(reason=reason):
                self.setUp()
                self.fs.files[path] = regular(3101, raw, readonly=False)
                self.assertEqual(self.diagnose(), reason)
                self.assertEqual(self.runner.run.call_count, 2)
                self.assertNotIn("/proc/101/environ", [call[0] for call in self.fs.calls])

    def test_malformed_or_unstable_process_identity_never_produces_relation(self) -> None:
        cgroup = "/proc/101/cgroup"
        for raw in (b"0::/x\n0::/y\n", b"0::/x\r\n", b"0::/x\x00\n", b"0::/\xff\n"):
            with self.subTest(raw=raw):
                self.setUp()
                self.fs.files[cgroup] = regular(3101, raw, readonly=False)
                self.assertEqual(self.diagnose(), "UNKNOWN")
        for path, mutate in (
            ("/proc/101/stat", lambda item: replace(item, data=proc_stat(101, 1, 12))),
            ("/proc/101/status", lambda item: replace(item, data=b"Uid:\t1000\t1000\t1000\t1000\n")),
            (proof.DROP_IN, lambda item: replace(item, inode=item.inode + 1)),
        ):
            with self.subTest(path=path):
                self.setUp()
                self.fs.files[cgroup] = regular(3101, b"0::/\n", readonly=False)
                original = self.fs.files[path]
                changed = mutate(original)
                self.assertNotEqual(original, changed)
                self.fs.sequences[path] = [original, changed]
                self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_unit_root_is_rejected_before_relation(self) -> None:
        self.values["ControlGroup"] = "/"
        self.fs.files["/proc/101/cgroup"] = regular(3101, b"0::/a\n", readonly=False)
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.assertNotIn("/proc/101/cgroup", [call[0] for call in self.fs.calls])

    def test_unstable_or_missing_prior_observations_are_unknown(self) -> None:
        path = "/proc/101/cgroup"
        first = regular(3101, b"0::/a\n", readonly=False)
        for second in (regular(3101, b"0::/b\n", readonly=False), replace(first, inode=999)):
            with self.subTest(second=second):
                self.setUp()
                self.fs.sequences[path] = [first, second]
                self.assertEqual(self.diagnose(), "UNKNOWN")
                self.assertNotIn("/proc/101/environ", [call[0] for call in self.fs.calls])
        self.setUp()
        self.fs.files[path] = first
        original = self.fs.observe
        visits = 0

        def observe(name: str, *, limit: int | None = None, follow: bool = False) -> proof.Observation:
            nonlocal visits
            if name == path:
                visits += 1
                if visits == 2:
                    raise PermissionError("secret /private/path")
            return original(name, limit=limit, follow=follow)

        with patch.object(self.fs, "observe", side_effect=observe):
            self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_deadline_expires_without_later_reads(self) -> None:
        self.fs.files["/proc/101/cgroup"] = regular(3101, b"0::/\n", readonly=False)

        def clock() -> float:
            return 60.0 if self.runner.run.call_count >= 2 else 0.0

        reason = proof.diagnose_cgroup_relation(self.runner, self.row, fs=self.fs, clock=clock)
        self.assertEqual(reason, "UNKNOWN")
        self.assertEqual(self.runner.run.call_count, 2)
        self.assertNotIn("/proc/101/environ", [call[0] for call in self.fs.calls])

    def test_non_process_failures_and_matching_cgroup_never_admit_relation(self) -> None:
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.assertNotIn("/proc/101/environ", [call[0] for call in self.fs.calls])
        self.setUp()
        self.values["FragmentPath"] = "/private-secret"
        self.assertEqual(self.diagnose(), "UNKNOWN")
        self.assertEqual(self.fs.calls, [])


class ReaderNamespaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = CgroupRelationTests("runTest")
        self.fixture.setUp()
        self.fixture.fs.files["/proc/101/cgroup"] = regular(3101, b"0::/\n", readonly=False)

    def diagnose(self) -> str:
        fixture = self.fixture
        return proof.diagnose_reader_namespace(fixture.runner, fixture.row, fs=fixture.fs, clock=lambda: 0.0)

    def test_comparison_requires_stable_f9_root_and_revalidation(self) -> None:
        for result in ("SAME", "DIFFERENT"):
            with self.subTest(result=result):
                self.setUp()
                with patch.object(proof, "_compare_reader_namespace",
                                  side_effect=lambda _proof, check: result if check() else "UNKNOWN") as compare:
                    self.assertEqual(self.diagnose(), result)
                compare.assert_called_once()
                self.assertEqual(self.fixture.runner.run.call_count, 2)
                self.assertNotIn("/etc/environment", [call[0] for call in self.fixture.fs.calls])
                self.assertNotIn("/proc/101/environ", [call[0] for call in self.fixture.fs.calls])

    def test_non_root_and_ambiguous_result_never_admit(self) -> None:
        self.fixture.fs.files["/proc/101/cgroup"] = regular(3101, b"0::/other\n", readonly=False)
        with patch.object(proof, "_compare_reader_namespace") as compare:
            self.assertEqual(self.diagnose(), "UNKNOWN")
            compare.assert_not_called()
        self.setUp()
        with patch.object(proof, "_compare_reader_namespace", return_value="private secret"):
            self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_process_negative_snapshot_drift_during_revalidation_is_rejected(self) -> None:
        path = "/proc/101/cgroup"
        first = regular(3101, b"0::/\n", readonly=False)
        changed = regular(3101, b"0::/other\n", readonly=False)
        self.fixture.fs.sequences[path] = [first, changed]
        with patch.object(proof, "_compare_reader_namespace",
                          side_effect=lambda _proof, check: "SAME" if check() else "UNKNOWN") as compare:
            self.assertEqual(self.diagnose(), "UNKNOWN")
        compare.assert_called_once()
        self.assertEqual(self.fixture.runner.run.call_count, 2)

    def test_unit_drift_during_comparison_fails_closed(self) -> None:
        def change(_proof: Any, check: Any) -> str:
            self.fixture.values["FragmentPath"] = "/secret"
            return "SAME" if check() else "UNKNOWN"
        with patch.object(proof, "_compare_reader_namespace", side_effect=change):
            self.assertEqual(self.diagnose(), "UNKNOWN")

    def test_unsupported_abi_and_hostile_self_fail_closed(self) -> None:
        instance = proof._Proof(Mock(), MemoryFS(), lambda: 0.0)
        with patch("platform.machine", return_value="unsupported"):
            self.assertEqual(proof._compare_reader_namespace(instance, lambda: True), "UNKNOWN")
        with patch("os.readlink", return_value="../private"):
            self.assertEqual(proof._compare_reader_namespace(instance, lambda: True), "UNKNOWN")

    def test_real_namespace_probe_closes_descriptors_and_compares(self) -> None:
        import ctypes
        import fcntl
        import platform
        import sys

        if sys.platform != "linux" or platform.machine() != "x86_64" or ctypes.sizeof(ctypes.c_long) != 8:
            self.skipTest("F10 supports Linux x86_64 LP64 only")
        opened = []
        libc = ctypes.CDLL(None, use_errno=True)
        libc.syscall.restype = ctypes.c_long
        try:
            try:
                procfd = os.open("/proc", os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
                opened.append(procfd)
                own = os.readlink("self", dir_fd=procfd)
                if own != str(os.getpid()):
                    self.skipTest("procfs PID view does not match this reader")
                for path in ("/proc/self/ns/cgroup", "/proc/1/ns/cgroup"):
                    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
                    opened.append(fd)
                    if fcntl.ioctl(fd, 0xB703) != 0x02000000:
                        self.skipTest("cgroup namespace descriptor type unavailable")
                how = (ctypes.c_uint64 * 3)(os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC, 0, 0x0D)
                probe = libc.syscall(ctypes.c_long(437), ctypes.c_int(procfd), ctypes.c_char_p(own.encode()),
                                     ctypes.byref(how), ctypes.c_size_t(24))
                if probe < 0:
                    self.skipTest("openat2 with required resolution flags unavailable")
                opened.append(probe)
                statx = (ctypes.c_ubyte * 256)()
                rc = libc.syscall(ctypes.c_long(332), ctypes.c_int(procfd), ctypes.c_char_p(b""),
                                  ctypes.c_int(0x1000), ctypes.c_uint(0x1000), ctypes.byref(statx))
                if rc != 0 or not ctypes.c_uint32.from_buffer(statx).value & 0x1000:
                    self.skipTest("statx mount ID unavailable")
                first, second = (os.fstat(fd) for fd in opened[1:3])
                expected = "SAME" if (first.st_dev, first.st_ino) == (second.st_dev, second.st_ino) else "DIFFERENT"
            except (OSError, PermissionError):
                self.skipTest("procfs namespace descriptors inaccessible")
        finally:
            for fd in reversed(opened):
                os.close(fd)
        instance = proof._Proof(Mock(), MemoryFS(), lambda: 0.0)
        before = set(os.listdir("/proc/self/fd"))
        self.assertEqual(proof._compare_reader_namespace(instance, lambda: True), expected)
        self.assertEqual(set(os.listdir("/proc/self/fd")), before)


class NamespaceDescriptorFixtureTests(unittest.TestCase):
    """Exercise descriptor identity and error paths without changing namespaces."""

    def setUp(self) -> None:
        import ctypes
        from types import SimpleNamespace

        self.ctypes = ctypes
        self.SimpleNamespace = SimpleNamespace
        self.next_fd = 10
        self.handles: dict[int, tuple[str, int]] = {}
        self.bytes_read: set[int] = set()
        self.closed: set[int] = set()
        self.reader_inode = 200
        self.init_inode = 201
        self.mount_id = 11
        self.mask = 0x1000
        self.ioctl_result = 0x02000000
        self.fail_openat = False
        self.fail_link = False
        self.self_link = "123"
        self.bad_procfs = False
        self.bad_nsfs = False
        self.bad_statfs = False
        self.substitute_stat = False
        self.stat_open_count = 0
        self.change_mount_after = 0
        self.statx_calls = 0
        self.stat_read_count = 0
        self.change_start = False
        self.proc = proof._Proof(Mock(), MemoryFS(), lambda: 0.0)
        self.libc = SimpleNamespace(syscall=Mock(side_effect=self.syscall),
                                    fstatfs=Mock(side_effect=self.fstatfs))

    def allocate(self, kind: str, pid: int = 0) -> int:
        self.next_fd += 1
        self.handles[self.next_fd] = (kind, pid)
        return self.next_fd

    def syscall(self, number: Any, *args: Any) -> int:
        if number.value == 437:
            parent, name, _how, _size = args
            if self.fail_openat:
                return -1
            kind, pid = self.handles[parent.value]
            value = name.value.decode()
            if kind == "proc" and value in {"123", "1"}:
                return self.allocate("process", int(value))
            if kind == "process" and value == "ns":
                return self.allocate("nsdir", pid)
            if kind == "process" and value == "stat":
                self.stat_open_count += 1
                item = self.allocate("stat", pid)
                if self.substitute_stat and self.stat_open_count == 2:
                    self.handles[item] = ("substituted_stat", pid)
                return item
            return -1
        if number.value == 332:
            fd, _path, _flags, _mask, buffer = args
            if fd.value not in self.handles:
                return -1
            self.statx_calls += 1
            self.ctypes.memset(buffer, 0, 256)
            self.ctypes.cast(buffer, self.ctypes.POINTER(self.ctypes.c_uint32))[0] = self.mask
            address = self.ctypes.addressof(buffer._obj)
            drift = self.change_mount_after and self.statx_calls > self.change_mount_after
            self.ctypes.c_uint64.from_address(address + 144).value = self.mount_id + bool(drift)
            return 0
        return -1

    def fstatfs(self, fd: Any, buffer: Any) -> int:
        kind, _pid = self.handles[fd]
        value = 0x6E736673 if kind == "namespace" else 0x9FA0
        if ((kind == "namespace" and self.bad_nsfs) or (kind != "namespace" and self.bad_procfs)
                or (kind in {"stat", "substituted_stat"} and self.bad_statfs)):
            value = 0
        self.ctypes.cast(buffer, self.ctypes.POINTER(self.ctypes.c_long))[0] = value
        return 0

    def open(self, path: str, flags: int, *, dir_fd: int | None = None) -> int:
        if path == "/proc" and dir_fd is None:
            return self.allocate("proc")
        if dir_fd is None:
            raise OSError("missing parent descriptor")
        kind, pid = self.handles[dir_fd]
        if path == "stat" and kind == "process":
            return self.allocate("stat", pid)
        if path == "cgroup" and kind == "nsdir":
            if self.fail_link:
                raise PermissionError("secret")
            return self.allocate("link" if flags & os.O_NOFOLLOW else "namespace", pid)
        raise OSError("unexpected open")

    def fstat(self, fd: int) -> Any:
        kind, pid = self.handles[fd]
        if kind in {"proc", "process", "nsdir"}:
            mode = stat.S_IFDIR | 0o555
            inode = {"proc": 1, "process": 10 + pid, "nsdir": 20 + pid}[kind]
        elif kind == "link":
            mode, inode = stat.S_IFLNK | 0o777, 30 + pid
        elif kind in {"stat", "substituted_stat"}:
            mode, inode = stat.S_IFREG | 0o444, 40 + pid + (kind == "substituted_stat")
        else:
            mode = stat.S_IFREG | 0o444
            inode = self.reader_inode if pid == 123 else self.init_inode
        return self.SimpleNamespace(st_dev=1, st_ino=inode, st_mode=mode, st_uid=0)

    def read(self, fd: int, _size: int) -> bytes:
        if fd in self.bytes_read:
            return b""
        self.bytes_read.add(fd)
        self.stat_read_count += 1
        started = 43 if self.change_start and self.stat_read_count > 2 else 42
        return proc_stat(self.handles[fd][1], 1, started)

    def close(self, fd: int) -> None:
        if fd in self.closed:
            raise OSError("duplicate close")
        self.closed.add(fd)

    def run_probe(self, revalidate: Any = lambda: True) -> str:
        with patch("platform.machine", return_value="x86_64"), \
                patch("ctypes.CDLL", return_value=self.libc), \
                patch("os.open", side_effect=self.open), \
                patch("os.fstat", side_effect=self.fstat), \
                patch("os.read", side_effect=self.read), \
                patch("os.close", side_effect=self.close), \
                patch("os.readlink", side_effect=lambda *_a, **_kw: self.self_link), \
                patch("os.getpid", return_value=123), \
                patch("fcntl.ioctl", side_effect=lambda *_a: self.ioctl_result):
            return proof._compare_reader_namespace(self.proc, revalidate)

    def test_same_and_different_require_full_revalidation_and_cleanup(self) -> None:
        for same in (True, False):
            with self.subTest(same=same):
                self.setUp()
                self.init_inode = self.reader_inode if same else self.reader_inode + 1
                seen = []
                def revalidate() -> bool:
                    seen.append(len(self.handles) - len(self.closed))
                    return True
                self.assertEqual(self.run_probe(revalidate), "SAME" if same else "DIFFERENT")
                self.assertGreater(seen[0], 0)
                self.assertEqual(set(self.handles), self.closed)

    def test_unsupported_syscall_missing_mount_id_or_wrong_namespace_type(self) -> None:
        for failure in ("openat", "mask", "type", "permission", "recheck"):
            with self.subTest(failure=failure):
                self.setUp()
                self.fail_openat = failure == "openat"
                self.mask = 0 if failure == "mask" else 0x1000
                self.ioctl_result = 0 if failure == "type" else 0x02000000
                self.fail_link = failure == "permission"
                self.assertEqual(self.run_probe(lambda: failure != "recheck"), "UNKNOWN")
                self.assertEqual(set(self.handles), self.closed)

    def test_self_procfs_namespace_mount_and_start_identity_are_bound(self) -> None:
        for failure in ("self", "procfs", "nsfs", "mount", "start", "statfs", "stat-retarget"):
            with self.subTest(failure=failure):
                self.setUp()
                self.self_link = "124" if failure == "self" else "123"
                self.bad_procfs = failure == "procfs"
                self.bad_nsfs = failure == "nsfs"
                self.change_mount_after = 3 if failure == "mount" else 0
                self.change_start = failure == "start"
                self.bad_statfs = failure == "statfs"
                self.substitute_stat = failure == "stat-retarget"
                self.assertEqual(self.run_probe(), "UNKNOWN")
                self.assertEqual(set(self.handles), self.closed)

    def test_changing_namespace_identity_on_reopen_fails_closed(self) -> None:
        original = self.open
        count = 0
        def changing(path: str, flags: int, *, dir_fd: int | None = None) -> int:
            nonlocal count
            if path == "cgroup" and not flags & os.O_NOFOLLOW:
                count += 1
                if count == 3:
                    self.reader_inode += 1
            return original(path, flags, dir_fd=dir_fd)
        with patch.object(self, "open", side_effect=changing):
            self.assertEqual(self.run_probe(), "UNKNOWN")
        self.assertEqual(set(self.handles), self.closed)

if __name__ == "__main__":
    unittest.main()
