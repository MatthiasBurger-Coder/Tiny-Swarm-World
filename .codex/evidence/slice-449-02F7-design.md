# S449-02F7 — source-bound Snap generator-form diagnosis

Status: PLANNED. Native F6 at source 4f52873330b665ab013b607c26d7172194ff375b
returned BLOCKED_UNKNOWN / DEPENDENCY_VARIANT, exit 2. This is a form
observation only; private F6 host evidence must be independently reviewed
before F7 host execution. No inventory, identity, ownership or safety is
admitted. The user requested continued investigation.

## Public source and exact grammar

Canonical [LXD source commit 3a06799](https://github.com/canonical/lxd/blob/3a06799e5f5d144a8e778ea4909ef463df828c28/snapcraft/commands/daemon.start)
has script SHA-256 7ecbe39a07dc02666af544327dbaf5cfbe9967868bfb9d7c627061f14916b562.
Preliminary native observations report LXD 5.21.8-3a06799, revision 40958,
and matching installed script bytes. This does not prove that script generated
the drop-in. Independently recheck the package, process binding and host facts.

The sixteen exact public static source literals in their required order are:

```text
snap.microceph.daemon.service snap.microceph.mds.service snap.microceph.mgr.service snap.microceph.mon.service snap.microceph.nfs.service snap.microceph.osd.service snap.microceph.rgw.service snap.microceph.rbd-mirror.service snap.microceph.cephfs-mirror.service snap.microovn.daemon.service snap.microovn.ovn-ovsdb-server-nb.service snap.microovn.ovn-ovsdb-server-sb.service snap.microovn.ovn-northd.service snap.microovn.chassis.service snap.microovn.switch.service snap.microovn.bird.service
```

Require exact bytes `[Unit]`, LF, `After=`, these sixteen literals joined
by single ASCII spaces, one literal ASCII space, then zero or more optional
tokens from the same sixteen literals, each followed by one or more ASCII
spaces, followed by one LF and EOF. At most 256 dynamic tokens; maximum
drop-in bytes 64 KiB. Duplicate dynamic tokens are allowed. Unknown tokens,
different static order, missing separator/newline, tabs, CR, NUL, quotes,
backslash, specifiers, Unicode ambiguity, extra directives or malformed
syntax return UNKNOWN. This is deliberately only a closed subset of possible
generator output; an UNKNOWN token is not a claim upstream rejects it.

## Requirements and verification

| ID | Requirement | Verification |
|---|---|---|
| F7-R01 | Bind F6 observation, named host, source, active fixed unit, PID and numeric revision. | Private F6 record review and post-commit host JIT. |
| F7-R02 | Read only fixed UNIT_FILE, DROP_IN and script pair from validated revision; no environment file. | Fixed path and no-environment tests. |
| F7-R03 | Verify fixed host/process-root script pair via existing `_Proof.pair` containment, no-follow, root-owned, mode, read-only package device, inode/byte equality, 1 MiB cap and pinned digest. | Forged revision, path, hash, mode, symlink, device and bytes tests. |
| F7-R04 | Bind active PID/cgroup/start, Snap name, numeric revision, argv and shell through existing bounded process identity checks in memory. | Invalid process, binding and drift tests. |
| F7-R05 | Reproduce F6 rejection and recheck unit, PID, process inputs, both script views and actual trusted files/bytes before MATCH. | Identity/bytes/race/timeout and recheck ordering tests. |
| F7-R06 | Fixed JSON only; no value, path, PID, argv, exception or secret-bearing hash leaks. | Synthetic secret tests on stdout/stderr/errors. |
| F7-R07 | No extra systemctl, client, socket, network, script execution, host mutation or inventory artifact; F4/F5/F6 remain unchanged. | Exact argv, no-write and regression parity tests. |
| F7-R08 | Test all token positions, spaces, dynamic members, duplicates, unknowns, malformed data, limits and trust. | PC WSL exact-source targeted tests and direct Ruff. |
| F7-R09 | Six same-hash role reviews/S3D, exact-source full QUALITY, separate post-commit host plan/JIT/GO. | Review, hash and quality evidence. |
| F7-R10 | MATCH is only bounded form correlation, not authorship, identity, safety or inventory admission. | Independent decision and separately scoped correction. |

## CLI and bounded collection

Only `python3 tools/qualification/native_runtime_inventory.py
--diagnose-snap-generator-form` with this sole argument is valid.
Every result is exactly `{"status":"BLOCKED_UNKNOWN","reason":"MATCH"}` or
`{"status":"BLOCKED_UNKNOWN","reason":"UNKNOWN"}`, exit 2. Invalid
combinations, duplicates, values and help return UNKNOWN before argparse or
host access. Errors, drift, missing prerequisites and non-reproducible F6
rejection return UNKNOWN without exception text, traceback or sensitive hashes.

Use the fixed F5 initial five-property unit snapshot and at most two F4
detailed unit queries, same argv/order/state checks and caps. Require active
fixed Snap service and positive PID. Reuse existing `_Proof.process`,
`_Proof.main_environment` and `_Proof.shell` to validate process identity,
cgroup, SNAP name/revision and command-line in memory. The only admitted
revision for this source profile is 40958. Never emit, retain or hash raw
environment, command-line or drop-in bytes. Do not call `_Proof.context` or
other helpers that read `/etc/environment`.

Only added package read: fixed
`/snap/lxd/<validated-revision>/commands/daemon.start` and its fixed
`/proc/<pid>/root` view through `_Proof.pair`. Both must be root-owned,
non-group/world-writable, read-only on the package device and match both
descriptor identity and bytes. Pin the public script digest above; never
execute the script. Pin fixed trusted UNIT_FILE and DROP_IN, re-establish F6
DEPENDENCY_VARIANT on that snapshot, compare the closed grammar, and recheck
unit, PID/process/cgroup/start, memory-only Snap context, shell, both script
views, and actually read trusted context identities and bytes before output.
Any uncertainty or change is UNKNOWN.

Include every read/recheck within existing 60-second cooperative aggregate,
16 MiB aggregate, 64 KiB context and 1 MiB per script bounds. Fixed Runner
bounds still apply. Filesystem deadlines are cooperative, not preemptive.
No extra systemctl, list-units, client, socket, network, script execution,
host mutation or inventory artifact. F7 explicitly extends F6's historical
no-additional-package-file contract solely for this script pair and necessary
bounded in-memory process identity inputs; F4/F5/F6 behavior stays unchanged.

MATCH does not prove script execution, drop-in origin or safety, F4 identity,
ownership, supported version, listener capability or host admission.

## Ordering

F6 commit 4f528733 and its bounded native result -> F7 six-role same-hash
review/S3D -> one serial implementation -> SSH PC WSL targeted/direct Ruff
and full QUALITY on exact candidate -> separate post-commit host review,
S3D/JIT/GO -> at most one read-only native observation. A guard correction
and S449-02F retry are separate reviewed phases. S449-02F remains BLOCKED;
02G/02H retain their successful-inventory prerequisites. Private host records
must use owner-controlled ext4 directory 0700 and file 0600. Python 3.12
was not independently tested for F6. No F7 implementation or host GO claimed.
