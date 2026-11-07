# S449-02F4 — normalize the verified Snap wrapper and direct LXD child

## 2026-11-07 ordinary Instance collection transport

The exact f495969e normal native collector returned RESOURCE_SCHEMA_INVALID,
no artifact, at 14:27:38 UTC. Separate approved schema-only diagnosis at
14:29:56 UTC identifies _only_keys on an Instance-shaped object with three
unknown fields, last query lxd_profile_show exit 0, command count 197. The
previous nil-collection hypothesis is not established and grants no coercion.

Pinned LXD5.21.9 lxc/list.go renders []api.InstanceFull, whose extra state,
backups and snapshots are outside this collector's closed ordinary Instance
DTO. Their actual unknown names were not emitted by the diagnostic and are
not claimed as observed. This independently known CLI/DTO mismatch is enough
to replace the collection transport; no unknown field is admitted or dropped.
https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxc/list.go
https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/shared/api/instance.go
https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/instance.go

Serial F4 collector/test and normative/workflow/evidence authoring locks remain.
Extend the existing closed URI template set by ONLY instance-list, arity zero:
/1.0/instances?project={encoded_validated_project}&recursion=1. Fixed request GET,
--raw, fixed local client/--force-local and explicit selected socket. No caller
URI, recursion override, filter, all-projects, method, data or remote option.
Recursion 1 requests ordinary Instance objects, not full runtime/snapshot data.
Validate the same exact typed synchronous seven-key success envelope. Require
metadata to be an actual list of at most MAX_ENTITIES; detail-kind metadata
must still be a dict. Reuse strict JSON duplicate/constant/UTF-8 rejection.
Every member then passes existing closed Instance DTO/schema/ownership checks.

Replace only the current instance collection CLI list command; preserve its
command ID/safe arguments, before_query position, all detail observations,
identity/reciprocity/redaction and command/time/byte/entity limits. Other CLI
list/version commands remain unchanged. No normalization or budget increase.
Tests independently assert exact fixed collection GET/raw URI on both client
paths, positive complete ordinary API rows, malformed/error/duplicate envelope,
wrong/oversized metadata, and that full Instance DTO extra fields are rejected
rather than discarded. Keep all existing graph/drift/refusal regressions.
Focused then all seven PC-WSL gates on exact source. No live release until a
new committed-source normal capture phase is independently reviewed.

## 2026-11-07 exact CLI read-only detail API compatibility

Current a0ee2ccd normal capture returns COMMAND_FAILED. The separately reviewed
command-ID-only diagnostic at 14:13:12 UTC identifies lxd_project_show, exit 1,
command count 71. Exact LXD 5.21.9 project.go implements YAML-only project show,
with no --format. Existing mocked tests wrongly accepted this syntax.

Primary contracts (version-pinned upstream source):
- https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxc/project.go
- https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxc/query.go
- https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/shared/api/response.go
- https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/shared/api/instance.go
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/query.go
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/response.go
- https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/instance.go

Serial source locks: native_runtime_inventory.py and its test module only;
workflow/context, F4 normative design/consolidation and master evidence are
authoring locks. No provenance-helper changes. This amendment changes only
read-only detail transport and the instance detail DTO's known API shape.

Replace every unsupported detail show --format json with exactly the existing
fixed local binary + --force-local + query --request GET --raw + one internally
constructed URI. No --project CLI flag (query explicitly rejects it), data,
wait, remote, caller-provided URI or method. Closed resource templates:
projects/{project}, profiles/{name}, instances/{name}, networks/{name},
storage-pools/{pool}, storage-pools/{pool}/volumes/{type}/{name}, all below /1.0.
Validate each component with existing _name or _volume_type before URI quoting
safe=''; explicit ?project={encoded_project} for each scoped detail, project
identity is also explicit in its path. Reject unknown kind/arity, malformed
identifiers or nonfixed prefix before any runner call. The normal list/version
commands remain unchanged. Command IDs and sanitized argument records remain
unchanged. Per-query before_query, socket environment, no-shell execution,
command/time/stream/aggregate limits and final checks remain unchanged.

Use --raw because normal query unmarshals metadata into a generic map before
rendering. The raw response preserves metadata as json.RawMessage. Parse the
returned JSON with existing strict duplicate-key/constant/UTF-8 guards. Require
exact envelope keys type,status,status_code,operation,error_code,error,metadata;
require type='sync', status='Success', integer (not bool) status_code=200,
operation='', integer (not bool) error_code=0, error=''. Reject async/error/null,
extra/missing keys and failed envelopes even when Incus --raw exits zero.
Validate metadata with existing closed DTO/identity/relationship rules before
redacted projection. This guards the CLI output, not original wire envelope
keys already decoded by the CLI. No YAML or permissive fallback.

Instance GET returns the complete known Instance API DTO. Permit only the
existing list DTO fields; require identity, local config/devices, profile list,
boolean ephemeral/stateful, and validate every present metadata/expanded field.
The exact upstream omitempty contract allows absent expanded_config and
expanded_devices to mean empty maps; reject null/wrongly typed present values.
Validate the complete object before deriving the existing local or expanded
config/devices projection. Keep two separately rechecked instance GETs for the
two existing observations; neither local nor expanded state may be inferred
from the other. Compare the complete normalized instance DTOs across the two
reads, excluding only status, status_code and last_used_at; configuration,
identity, creation, location and device drift blocks before projection. A
missing expanded map is only its exact upstream omitempty empty-map contract,
not a fallback to local or list data. Unknown API fields remain blocking.

Tests: independently enumerated literal new argv and real API envelope/DTO
fixtures for both LXD and Incus; historical unsupported syntax explicitly
rejected. Retain all current graph/identity/redaction/drift regressions. Cover
all closed path templates, plus escaping; deny injected path/method/remote,
unknown kind/arity/prefix before command execution; envelope missing/extra/
coerced/error/async/duplicate metadata; full instance known fields, omission
semantics, typed and unknown fields, independent local/expanded device maps.
Focused inventory/provenance/fixture tests then all seven QUALITY gates run
only on exact-hash PC WSL candidate; no live fixtures in these tests.

Architecture/security and tester/DevOps review this exact amendment before
implementation and exact final source afterward. Commit only this F4 correction.
Any new normal native capture requires its own committed-source, protected-root
one-shot plan and review. No budget enlargement, maintenance, runtime mutation,
capability admission or issue/epic completion is released by this amendment.


## 2026-11-07 bounded shutdown dependency compatibility

This extension supersedes only the historical two-unit-only drop-in grammar
below; every other proof requirement remains authoritative.

## 2026-11-07 bounded escaped-root wrapper proof

This extension additionally supersedes only the historical universal
same-systemd-cgroup assumption for the exact installed wrapper below. The
current native candidate passes context but returns `SNAP_WRAPPER_PROC_INVALID`:
root UID/stat predicates pass, while the wrapper reports exactly `0::/`.
Canonical's wrapper intentionally moves itself to the cgroup-v2 root:
https://raw.githubusercontent.com/canonical/lxd-pkg-snap/latest-edge/snapcraft/commands/daemon.start.
The installed bounded script was inspected; it is a root-owned, non-writable,
read-only regular file of 35,348 bytes with SHA-256
`7ecbe39a07dc02666af544327dbaf5cfbe9967868bfb9d7c627061f14916b562`.
The digest binds those installed bytes; moving upstream is not installed proof.

Keep the existing exact effective-systemd-ControlGroup mode. Add only exact
root `0::/` (with the existing optional final LF) as a preliminary process
observation. Bind original cgroup bytes in the Process equality snapshot.
All inspected direct children must have exactly the same observed cgroup bytes
as the main process. Mixed groups, arbitrary paths, v1/multiple records and
`/.lxc` remain unsupported. Do not infer namespace identity or call root
membership proof of systemd-unit membership.

Root mode can produce the existing identity tuple only after every unchanged
systemctl MainPID/ExecStart/context/root UID/shell/package/unique direct-child
PPID/start/inode proof succeeds, and the paired immutable installed wrapper
matches that literal full SHA-256. Read both wrapper views with a 1-MiB limit
per read, charged to the existing 16-MiB aggregate and deadline. Preserve paired
inode/byte equality and exact second-pass equality, including raw cgroup and
wrapper bytes. Unit-group mode has no new digest pin but also retains bounded
script observations. No substring/shell parser or command execution is added.

Tests must retain legacy unpinned success and exercise known pinned root mode,
unknown/changed/mismatched/oversized script, mixed or malformed groups,
root-to-unit and unit-to-root drift (main and child), cgroup LF-byte drift,
and unchanged denial of UID/PPID/package/child ambiguity violations. Test-only
synthetic script digests may be patched; the production digest remains the
literal inspected value. Source review and exact-source PC-WSL focused/full
gates precede any new native invocation.

Architecture/security and tester/DevOps accepted this bounded design as the
same qualification adapter, not a new product capability. No namespace read,
privileged invocation or host mutation is released here. Standard-user reads
of the root process executable/environment are unavailable. A future elevated
read-only capture requires a separate exact-source plan with root-private
evidence; never change proc permissions or claim the unavailable reads passed.

### Pinned-root split server/stop-hook layout

The separately approved privileged capture and one proof diagnostic remained
non-pass. The last entered stage was package identity. Bounded inspection of
the active numeric Snap package confirmed the exact pinned wrapper and two
distinct root-owned, non-writable, read-only regular files at `sbin/lxd` and
`bin/lxd`. Canonical packaging explicitly builds the actual server at `sbin/lxd`
and maps the stop-hook wrapper to `bin/lxd`:
https://raw.githubusercontent.com/canonical/lxd-pkg-snap/latest-edge/snapcraft.yaml.
That establishes package roles, not authenticity of the installed revision.

For observed-root mode only, the full paired wrapper digest must match the
literal approved pin before binary selection. Require both fixed paths as
distinct no-follow root-owned regular read-only executables, with matching
host/process views. Select ONLY `sbin/lxd` as the unique direct-child executable
authority. Retain both pairs in the package snapshot and stable rereads. Never
infer authority from PATH, argv, a filename alone, or either-inode fallback.
The exact script/package/metadata/MainPID/shell/UID/PPID/start/cgroup proof is
still required. Debug/unrelated or stop-hook-only children cannot qualify.

Derive root mode only from the already observed main cgroup in `run()` and
reuse that bound mode during rechecks. Traditional unit-group mode retains the
original one-inode/alias algorithm. Unknown wrapper pins, missing files,
symlinks/aliases, same-inode root layouts, untrusted/mismatched views and any
drift remain blocked. Snapshotting the stop-hook must not be omitted just
because only the server is the authority. Binary identity observations remain
protected by their paired readonly package mounts; no unbounded binary-content
read is introduced.

Architecture/security and tester/DevOps accepted this bounded same-slice
compatibility decision before code. Required regressions include known-root
split success, stop-hook-only/debug/missing/ambiguous children, same-inode or
alias root layouts, either missing/untrusted/mismatched file, server/stop-hook
inode drift, and all earlier unknown-pin/group/process failures. Preserve
legacy unpinned alias success and separate-inode refusal. Exact source review,
focused/full PC-WSL verification and a new host plan precede another capture.

### Exact server-version LTS label

The next separately approved normal capture at `a09d104f` passed wrapper
provenance and reached local version discovery, then returned
`VERSION_SCHEMA_INVALID` without an inventory artifact. The fixed local CLI
reports `Client version: 5.21.9 LTS` and `Server version: 5.21.9 LTS`.

Extend only the closed server-version token with an optional literal single
ASCII-space plus uppercase `LTS`. Preserve the complete observed string,
including the label, in the existing string field; do not strip it or infer
supported transitions. Existing unlabelled tokens remain valid. Require exactly
one `Server version:` record and a complete valid parse of that record; a valid
record plus a malformed second record is still a duplicate and must fail.
Reject doubled/tab separators within the LTS suffix, lowercase/unknown suffixes,
extra words, malformed/empty records and duplicate records before project or
resource queries. Retain strict UTF-8, read-only command/budget, artifact schema
and all service/socket/provenance checks.

Requirements/root, architecture/security and tester/DevOps accepted this
inventory-format correction before implementation. Tests must traverse the
real mocked `_inventory_client` flow, retain plain and exact LTS versions and
prove rejected versions issue no later resource queries. Focused/full gates
and a fresh exact-source capture plan remain required.

The current exact-source native read-only attempt at `b87fe5c9` returned
`SNAP_WRAPPER_CONTEXT_BLOCKED` before inventory/artifact creation. Effective
unit checks and the canonical environment passed. The installed read-only LXD
wrapper generates a larger shutdown-order drop-in than the historical two-unit
form. Inspection of the bounded installed generator establishes this shape;
the moving upstream branch still showing the older generator is not proof of
the installed revision. No host file or service was changed.

Keep the exact legacy `[Unit]` and
`After=snap.microceph.daemon.service snap.microovn.daemon.service` form.
Also accept exactly `[Unit]` and one `After=` line with the following ordered
static prefix, separated by one ASCII space:

```text
snap.microceph.daemon.service
snap.microceph.mds.service
snap.microceph.mgr.service
snap.microceph.mon.service
snap.microceph.nfs.service
snap.microceph.osd.service
snap.microceph.rgw.service
snap.microceph.rbd-mirror.service
snap.microceph.cephfs-mirror.service
snap.microovn.daemon.service
snap.microovn.ovn-ovsdb-server-nb.service
snap.microovn.ovn-ovsdb-server-sb.service
snap.microovn.ovn-northd.service
snap.microovn.chassis.service
snap.microovn.switch.service
snap.microovn.bird.service
```

The prefix may be followed by zero to sixteen runtime tokens from this same
closed list, sorted lexicographically and unique within the runtime suffix.
One ASCII space separates tokens. The new static16 form additionally accepts
exactly one optional final ASCII space, as emitted by the installed generator's
newline-to-space runtime list. Remove at most that single terminal space before
validation; never normalize the retained observation. Leading/doubled spaces,
tabs, continuations and inline comments are unsupported. The legacy two-unit
form remains exact and does not accept a terminal space. Repetition between the
static prefix and runtime suffix is expected. Preserve full-line comments and
blank lines, existing UTF-8/LF/CR/NUL checks, root ownership, no-follow opens,
byte limits and exact observation equality across rechecks. Do not normalize
accepted bytes or inode identity. Reject any other unit/directive/section.

This same-slice extension adds no host command, executable allowance, runtime
capability, schema or maintenance permission. Reviews: requirements by
`requirements_audit`, architecture/security boundary by `architecture_review`,
test/DevOps by `preflight_review`, automation and integration by root. Review
messages accept the contract; exact source review and PC-WSL gates follow.
The current execution record is `.codex/evidence/epic440-20261107.md`.

Current execution, review, verification and checkpoint state is recorded only in `.codex/evidence/slice-449-02F4-consolidation.md`; historical observations below do not grant a new release or native invocation.

The normative proof below defines the S449-02F4 v1.41 corrective checkpoint on the same slice; its release state is recorded in consolidation. No signatures, REST API, package downloads or general mount-namespace framework are added.

## Requirement and supported contract

The native F3 result was SNAP_EXECUTABLE_OUTSIDE_ROOT for snap.lxd.daemon.service. Canonical's packaging launches commands/daemon.start as a simple service; the shell wrapper launches LXD as a direct background child and waits. MainPID can therefore be the trusted shell, and must not be accepted merely because it is a shell. The whole wrapper/child relation below replaces that false assumption for this one fixed service.

Primary source: https://github.com/canonical/lxd-pkg-snap/blob/latest-edge/snapcraft.yaml and https://raw.githubusercontent.com/canonical/lxd-pkg-snap/latest-edge/snapcraft/commands/daemon.start . These establish the packaging design only. Installed metadata and file identity establish the host relationship; moving upstream bytes are never treated as installed-revision proof.

Outcome: _resolve_executable may normalize to existing lxd_snap / snap:lxd only after every proof condition passes. The proved child path remains internal to the helper and is never returned, logged or persisted. _resolve_executable returns only the existing pair (lxd_snap, snap:lxd); the inventory artifact schema is unchanged. Existing inventory then performs its normal socket/client/resource/coexistence checks. The proof alone does not establish ownership, authorize maintenance, run inventory or qualify #449. F3 diagnostic behavior remains byte-for-byte unchanged.

## Closed proof algorithm

Implement a small qualification-only helper with injected bounded filesystem reads and existing Runner. Invoke it only from _resolve_executable when the fixed unit is snap.lxd.daemon.service and the existing direct executable identity check fails with EXECUTABLE_IDENTITY_BLOCKED. Preserve existing direct identity handling for already-supported Snap executables and all other units. Do not broaden executable_identity's path allowlist.

1. Query only snap.lxd.daemon.service using /usr/bin/systemctl show with explicit properties and --no-pager under the existing sanitized C locale. Properties are existing unit state plus ExecStart, ControlGroup, FragmentPath, DropInPaths, ExecCondition, ExecStartPre, ExecStartPost, RootDirectory, RootImage, BindPaths, BindReadOnlyPaths, Environment, EnvironmentFiles. Keep requesting every listed property. Reject duplicate, unknown or malformed property keys/records. Normalize omission of only ExecCondition, ExecStartPre, ExecStartPost and EnvironmentFiles to the empty string before validation/rechecks; an explicitly empty value is equivalent. Every other property, including ExecStart, remains mandatory. Nonempty execution hooks remain blocked and the existing closed EnvironmentFiles allowlist remains unchanged. Require the loaded/active/running state and same positive ASCII MainPID as the supplied unit snapshot.
2. ExecStart is one anchored record with exactly these ordered fields: `{ path=/usr/bin/snap ; argv[]=/usr/bin/snap run lxd.daemon ; ignore_errors=no ; start_time=[T] ; stop_time=[T] ; pid=P ; code=C ; status=S }`. Whitespace separators are exactly one ASCII space as shown; no second record, brace nesting, escape or newline. P is ASCII decimal including zero. C is exactly one of `(null)`, `exited`, `killed`, `dumped`; S is an ASCII signed decimal, optionally followed by `/` and an ASCII unsigned decimal or one of SUCCESS, FAILURE, CHDIR, EXEC, SIGNAL, EXIT_CODE; reject other forms. T is exactly `n/a` or `Day YYYY-MM-DD HH:MM:SS ZONE`, Day from Mon..Sun and ZONE a bounded 2–8 uppercase ASCII timezone abbreviation or signed four-digit numeric offset; validate calendar/time ranges. The accepted local serialization is intentionally narrow: any other serialization blocks rather than guessing. Compare identity-driving parsed fields across rechecks; volatile timestamps/P/C/S do not drive identity or equality. Never execute the parsed value.
3. FragmentPath must be exactly /etc/systemd/system/snap.lxd.daemon.service. Open it read-only with O_NOFOLLOW; descriptor fstat must prove root-owned regular file, no group/world write. Require no nonempty ExecCondition/ExecStartPre/ExecStartPost/RootDirectory/RootImage/BindPaths/BindReadOnlyPaths. Require DropInPaths empty, except the single canonical root-owned /run/systemd/system/snap.lxd.daemon.service.d/lxd-shutdown.conf may be accepted only with this complete grammar: strict UTF-8 with LF newlines; blank lines and full-line # comments allowed; exactly one [Unit] section followed by exactly one After=snap.microceph.daemon.service snap.microovn.daemon.service assignment; no other section/key, duplicate or inline comment. Do not execute or source files.
4. Environment and EnvironmentFiles are not banned wholesale. Accept Environment as empty or only the exact fixed key/value `SNAPD_DEBUG=0`; accept EnvironmentFiles as empty or exactly the canonical optional `/etc/environment (ignore_errors=yes)` serialization. If optional /etc/environment exists, read it bounded/no-follow/root-owned regular/no group-world write. Its complete supported contents are blank lines, lines whose first non-whitespace character is #, and at most one exact assignment `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin` or `PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"`. Assignment lines permit no extra whitespace, escapes, variable references, single quotes or inline comments. Reject duplicate PATH and every other assignment, malformed line or non-comment content, including LD_AUDIT and all loader variables. There is no denylist or arbitrary key/value acceptance. Any unsupported effective environment serialization/value blocks. These are the complete supported contexts; do not infer a different distro default. Tests cover both literal PATH forms and near misses, duplicate assignments and LD_AUDIT rejection.
5. Snapshot MainPID starttime and parent from bounded /proc/P/stat (parse the final closing parenthesis correctly), effective UID from /proc/P/status, /proc/P/cgroup, and executable descriptor fstat. Require UID 0. Support only a single cgroup-v2 `0::<absolute normalized path>` record and require it equals the effective ControlGroup; unsupported v1/mixed schemas block. Keep starttime and all raw values memory-only.
6. Read bounded NUL-separated main cmdline and environ. Only selected SNAP_NAME/SNAP_REVISION/SNAP entries participate in identity proof; reject duplicate selected keys. Other bounded NUL-delimited process-environment entries are discarded without interpretation, logging or persistence. This is not a blanket prohibition on normal Snap-injected runtime keys: the closed environment-file/effective-unit rules in step 4 govern configured injection separately. Require SNAP_NAME=lxd, revision positive ASCII decimal and SNAP exactly /snap/lxd/<revision>. Require main argv exactly two entries: an absolute shell path and /snap/lxd/<revision>/commands/daemon.start; the shell path must resolve to the same inode as /proc/P/root/bin/sh and /proc/P/exe. Require that trusted shell descriptor is root-owned regular executable with no group/world write. Never treat process-supplied strings alone as proof.
7. Open fixed script and metadata paths /snap/lxd/<revision>/commands/daemon.start and /snap/lxd/<revision>/meta/snap.yaml through host and /proc/P/root views. fstat each descriptor: root-owned regular, no group/world write; corresponding host/process views must have identical device/inode. Require os.fstatvfs(...).f_flag & ST_RDONLY for all package descriptors. Safe YAML parse with duplicate-key rejection; require name=lxd, apps.daemon.command=commands/daemon.start and apps.daemon.daemon=simple. Do not parse shell code or run it. A missing field, unsupported YAML type/size or mismatch blocks. Package file identities and metadata bytes are pinned in memory during this observation.
8. Open fixed candidate paths /snap/lxd/<revision>/sbin/lxd and /snap/lxd/<revision>/bin/lxd through host and process-root views. Missing candidates are allowed only if exactly one distinct candidate inode exists; both paths may identify the same inode via regular files/hardlinks or one supported final symlink: bin/lxd -> ../sbin/lxd or sbin/lxd -> ../bin/lxd. Its target must be a regular file, with no second symlink or escape from the revision root; reject every other symlink. All present candidates must meet the package-descriptor ownership, regular-executable, ST_RDONLY and host/process device/inode requirements. More than one distinct inode blocks. This is the complete supported binary set.
9. Read exactly /proc/P/task/P/children, limit 64 unique positive ASCII IDs. No global /proc scan, pgrep, PID file, child execution or client call. Snapshot each direct child's stat/status/cgroup/exe using the same bounds. Select exactly one child with PPID=P, root effective UID, same unit cgroup, stable starttime and executable inode equal to the unique package binary. No child or multiple matching children blocks. Writable lxd.debug and an unrelated shell/process do not match the immutable package inode and cannot be normalized.
10. Re-read effective unit identity/context fields, main/selected-child stat/status/cgroup/exe, trusted shell inode, package script/metadata/binary descriptor identities, metadata bytes and direct-child set. Require equality in all identity-driving observations. Unit drift, exec, PID reuse, revision/environment change, file replacement or ambiguity blocks without retry. Close descriptors on every path. Root is the accepted host trust boundary; concurrent malicious root kernel/mount subversion is not claimed detectable by this tool.

All unsupported conditions raise a fixed InventoryError code without raw values: SNAP_WRAPPER_UNIT_INVALID, SNAP_WRAPPER_CONTEXT_BLOCKED, SNAP_WRAPPER_PROC_INVALID, SNAP_WRAPPER_FILE_UNVERIFIED, SNAP_WRAPPER_METADATA_INVALID, SNAP_WRAPPER_CHILD_ABSENT, SNAP_WRAPPER_CHILD_AMBIGUOUS, SNAP_WRAPPER_DRIFT, SNAP_WRAPPER_LIMIT_EXCEEDED. Existing outer inventory failure/redaction and no-artifact-on-failure behavior applies. No new CLI, diagnostic result schema or proof artifact is necessary.

## Bounds and tests

Exactly two additional fixed systemctl calls inside this proof; existing outer inventory calls and their aggregate command budget remain unchanged. No other new command or socket/network/client operation. At most 64 direct child candidates; 64 KiB per proc text read, 256 KiB main environ, 1 MiB snap metadata, 16 MiB total read bytes, 60-second aggregate proof deadline and existing per-command Runner caps. Every read uses limit+1 and every descriptor close is deterministic. The local read deadline is cooperative: check it before and after every proc or read-only package operation; do not claim hard preemption of filesystem syscalls. Existing Runner subprocess timeouts remain hard limits. The main environ 256 KiB bound is the explicit exception to the ordinary 64 KiB proc-text bound. File opening uses no final-symlink following for script/metadata/unit; candidate aliases follow only the two exact single-hop relative final aliases specified above and must satisfy descriptor identity. /proc exe and trusted /bin/sh symlinks are intentional but always compared through opened descriptors. No raw path/PID/revision/argv/env/output/file bytes or hashes reach logs, error text or persisted command records.

Meaningful tests: genuine wrapper+directchild normalizes only to the existing (lxd_snap, snap:lxd) pair with no child-path output; MainPID shell alone fails; forged process environment/argv fails without immutable installed-file relation; wrong effective ExecStart/context, unknown or malformed environment-file assignment (including LD_AUDIT), duplicate selected process keys while unrelated Snap-injected keys remain permitted, unit or file writable, metadata duplicate/oversize, host/process inode mismatch, non-readonly package, two binary inodes, missing/ambiguous children, wrong child cgroup/PPID/UID, debug binary, PID reuse/exec/refresh/unit drift, command/read/deadline limits and secret-token non-disclosure. Preserve current F3 output tests and direct-executable inventory tests; add integration-with-mocked-ports coverage proving failed proof prevents every client/socket/resource/artifact call and successful proof still runs existing coexistence checks. Mock all host operations.

## Slice contract and publication

slice_id: S449-02F4
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester
dependencies: S449-02F3
parallel_group: sequential
allowed files and matching file locks:
- tools/qualification/native_runtime_inventory.py
- tools/qualification/native_lxd_snap_provenance.py
- tests/tools/test_native_runtime_inventory.py
- tests/tools/test_native_lxd_snap_provenance.py
- documentation/workflow/issues/issue-449/workflow.md
- documentation/workflow/issues/issue-449/context-pack.md
- documentation/workflow/issues/issue-449/context-pack.json
- documentation/workflow/workflow.index.md
- .codex/evidence/slice-449-02F4-design.md
- .codex/evidence/slice-449-02F4-distribution.md
- .codex/evidence/slice-449-02F4-consolidation.md
module lock: bounded native Snap wrapper/child normalization
contract lock: exact wrapper relation before existing lxd_snap identity; unchanged F3 and normal inventory checks
architecture lock: qualification tooling only, no product runtime/host mutation
required targeted gate: PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance
required full gate: python3 tools/quality_gate.py quality
required diff gate: git diff --check
All Python gates run via SSH in approved PC WSL on verified exact candidate bytes.

Amend the existing issue workflow on the verified dedicated branch, preserving its structure and unrelated changes. Record the requirement/finding, same-hash six-role review, S3D, serial distribution record, implementation, focused/full quality and consolidation. Commit exactly S449-02F4 with one Slice-ID, active workflowVersion and CP_RECORD, then checkpoint push. A separate post-commit exact-hash S3D plan and exact-host GO is mandatory before any native full inventory capture. F4 implementation does not run capture. Inventory must prove coexistence/ownership; historical unrelated project resources forbid an exclusive-TSW assumption. Conditional maintenance still needs its separate evidence and five-role host/scenario GO. No #449 completion or live-scenario success is claimed by F4.





## Historical requirement clarification and authoring release snapshot

- Original Request: execute the authorized S02 path quickly, preserve all pending work, merge reviewed changes and end with a clean main branch.
- Interpreted Intent: repair the Snap wrapper identity assumption without bypassing ownership, resource, route, qualification or merge gates.
- Change Type: targeted issue-workflow amendment; no workflow-tree regeneration.
- Affected Process Strand: workflow execution planning and qualification tooling.
- Affected Architecture Area: native read-only inventory adapter; no product runtime change.
- Explicit Requirements: exact wrapper/direct-child relation, existing identity pair only, unchanged artifact schema and F3 diagnostic; PC WSL quality gates.
- Implicit Requirements: preserve unrelated pending files and historical provenance; no maintenance or exclusive-ownership inference.
- Assumptions: trusted local host root is the accepted baseline; unsupported serialization/context blocks.
- Non-Goals: signatures/REST, full namespace framework, resource mutation, issue completion.
- Risks: stock unit/schema differences may produce a safe blocker; cooperative filesystem deadlines cannot preempt blocked syscalls.
- Open Questions: none in the closed proposal.
- Blocking Questions: none for authoring; exact-hash review and S3D remain execution prerequisites.
- Confidence Level: 92 percent for the bounded contract; no implemented behavior or host success claimed.
- Historical Decision at authoring time: READY_FOR_WORKFLOW authoring; NOT_RELEASED_FOR_IMPLEMENTATION until same-hash role review and S3D. Superseded by the achieved implementation release and verification in the current consolidation record.

Historical authoring-role snapshot (superseded by all six exact-hash APPROVED decisions recorded in consolidation): Requirement, Architecture and Security accepted the narrow trusted-host-root design subject to the recorded corrections. Tester accepted the return-pair and additional-command wording corrections. Python Automation required the closed drop-in grammar, candidate alias policy and cooperative deadline wording now incorporated; its final exact-hash decision is pending. DevOps final exact-hash decision is pending. These are design-status records, not invented implementation or same-hash approvals. All six exact-hash decisions remain required before S3D releases implementation.

## v1.41 same-slice corrective contract — omitted empty array properties

The historical native read-only inventory attempt at commit 45c56359c9d18b1dd5f2dbdbd8e05fb81c5d646b returned SNAP_WRAPPER_UNIT_INVALID and produced no artifact. A separately authorized three-query schema diagnosis found exactly the three omitted empty execution-hook arrays and no other property mismatch. These are observations, not admission or success. No raw values are recorded here.

Official systemd prints EnvironmentFiles and Exec* array records only while array entries exist; an empty array can therefore emit no property line. Primary source: https://github.com/systemd/systemd/blob/main/src/systemctl/systemctl-show.c#L1303-L1318 and https://github.com/systemd/systemd/blob/main/src/systemctl/systemctl-show.c#L1408-L1455 . This supports only the four fixed optional-empty array properties specified in step 1; it does not permit missing scalar/identity properties or relaxed mandatory ExecStart.

Regression requirements: all 16 omission/presence combinations of the four optional-empty arrays normalize identically; explicit empty and omitted values compare equal across unit rechecks. Nonempty ExecCondition/ExecStartPre/ExecStartPost, duplicate keys, unknown keys, malformed records and each missing mandatory property remain blocked. EnvironmentFiles nonempty values still require its existing exact allowlist. F3, outer inventory budgets, ownership checks and every other proof constraint remain unchanged. This corrective checkpoint uses the same S449-02F4 ownership, files/locks, serial execution and focused/full PC WSL gates; it creates no diagnostic slice and grants no native execution.
