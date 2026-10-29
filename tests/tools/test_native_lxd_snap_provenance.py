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


if __name__ == "__main__":
    unittest.main()
