# S449-02F4 — normalize the verified Snap wrapper and direct LXD child

Status: IMPLEMENTED_PC_WSL_VERIFIED_READY_FOR_CHECKPOINT. Implementation is complete and independently reviewed; the exact approved-PC-WSL candidate passed 105 focused tests and all seven quality gates (3,100 discovered tests, 18 skipped). Ready for the single-slice checkpoint. Native inventory has NOT executed and requires separate post-commit exact-source S3D and host GO. The current execution/review evidence and original approved release tuple are preserved in `.codex/evidence/slice-449-02F4-consolidation.md`; subsequent status-only updates do not rewrite that historical tuple.

The normative proof below is the approved implemented contract. No signatures, REST API, package downloads or general mount-namespace framework are added.

## Requirement and supported contract

The native F3 result was SNAP_EXECUTABLE_OUTSIDE_ROOT for snap.lxd.daemon.service. Canonical's packaging launches commands/daemon.start as a simple service; the shell wrapper launches LXD as a direct background child and waits. MainPID can therefore be the trusted shell, and must not be accepted merely because it is a shell. The whole wrapper/child relation below replaces that false assumption for this one fixed service.

Primary source: https://github.com/canonical/lxd-pkg-snap/blob/latest-edge/snapcraft.yaml and https://raw.githubusercontent.com/canonical/lxd-pkg-snap/latest-edge/snapcraft/commands/daemon.start . These establish the packaging design only. Installed metadata and file identity establish the host relationship; moving upstream bytes are never treated as installed-revision proof.

Outcome: _resolve_executable may normalize to existing lxd_snap / snap:lxd only after every proof condition passes. The proved child path remains internal to the helper and is never returned, logged or persisted. _resolve_executable returns only the existing pair (lxd_snap, snap:lxd); the inventory artifact schema is unchanged. Existing inventory then performs its normal socket/client/resource/coexistence checks. The proof alone does not establish ownership, authorize maintenance, run inventory or qualify #449. F3 diagnostic behavior remains byte-for-byte unchanged.

## Closed proof algorithm

Implement a small qualification-only helper with injected bounded filesystem reads and existing Runner. Invoke it only from _resolve_executable when the fixed unit is snap.lxd.daemon.service and the existing direct executable identity check fails with EXECUTABLE_IDENTITY_BLOCKED. Preserve existing direct identity handling for already-supported Snap executables and all other units. Do not broaden executable_identity's path allowlist.

1. Query only snap.lxd.daemon.service using /usr/bin/systemctl show with explicit properties and --no-pager under the existing sanitized C locale. Properties are existing unit state plus ExecStart, ControlGroup, FragmentPath, DropInPaths, ExecCondition, ExecStartPre, ExecStartPost, RootDirectory, RootImage, BindPaths, BindReadOnlyPaths, Environment, EnvironmentFiles. Reject duplicate, absent or unknown property keys. Require the loaded/active/running state and same positive ASCII MainPID as the supplied unit snapshot.
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
