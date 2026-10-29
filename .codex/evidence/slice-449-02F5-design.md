# S449-02F5 — bounded Snap context diagnosis

Status: **PLANNED**. This document defines a diagnostic contract; it is not an
implementation, test result, identity proof, host admission or live GO.

The 2026-10-29 native S449-02F inventory at source
`1ec15b3e9f7f943cdde85e43d00ec01ff9c7e9fd` exited 2 with
`BLOCKED:SNAP_WRAPPER_CONTEXT_BLOCKED`. No inventory artifact was created.
The cause is unknown. No host, service, network, storage, profile or instance
mutation was performed. The private plan and result remain on the native ext4
test checkout under the issue-449 private evidence directory.

## Requirements and acceptance

| ID | Requirement | Verification |
|---|---|---|
| D01 | Diagnose only the fixed, already active Snap LXD service and the existing F4 proof inputs; preserve existing bounds and trust checks. | Fixed-call and unit-state regression tests. |
| D02 | Return only the closed symbolic result below; never emit raw values, paths, PIDs, arguments, environment, file bytes, exceptions or hashes of secret-bearing data. | Synthetic secret and output/exception leakage tests. |
| D03 | Reuse F4's exact fixed systemctl property queries, allowed root-owned drop-in and environment file reads. Never open a path supplied by unit data; preserve descriptor/no-follow, size, aggregate and cooperative deadline checks. | Fixed-argv, trusted-file, invalid reference, size and deadline tests. |
| D04 | No service/socket activation, client/endpoint/resource request, inventory artifact or host/configuration mutation. | Mock call and no-artifact assertions. |
| D05 | All outputs remain `BLOCKED_UNKNOWN`, exit 2. Invalid prerequisites/schema, ambiguity, unverified I/O, drift, limits or no reproducible rejection return `UNKNOWN`. No identity, ownership or support admission. | Failure, ambiguity, recheck and successful-context tests. |
| D06 | Preserve F4's normal acceptance and failure behavior. Produce the first applicable category in the defined priority order only after its prerequisites are proven. | F4/diagnostic parity, each category, all multiple-error priorities, malformed inputs and drift regressions. |
| D07 | Require separate same-hash six-role review, S3D, exact-source PC WSL focused and full quality gates before a separately reviewed post-commit native diagnostic plan and host GO. | Review, source-hash and test evidence; separate native record. |
| D08 | Treat diagnosis as a bounded observation only; any correction, rerun and 02G/02H admission remain independent. | Consolidation and fresh independently reviewed decisions. |

## Closed result contract

The only invocation is `python3 tools/qualification/native_runtime_inventory.py
--diagnose-snap-context`, with that flag as the sole argument. Handle this mode
before argparse and before any source, output, host or filesystem operation.
Any invocation containing the flag in another combination, including a value,
duplicate, `--diagnose-units`, help or unknown arguments, returns the same
fixed `UNKNOWN` JSON and exit 2; it must not print argv, usage or argparse
errors. Calls without this mode retain their existing behavior.

The diagnostic returns exactly one fixed JSON object with keys
`status` and `reason`; status is always `BLOCKED_UNKNOWN`, exit code is always
2. The only reason values, in priority order, are
`EXECSTART_FORMAT_OR_TIME`, `CONTROL_GROUP`, `FRAGMENT_OR_HOOK`,
`DROPIN_OR_ENV_SETTING`, `ENVIRONMENT_FILE_SPEC`, `DROPIN_CONTENT`,
`ENVIRONMENT_FILE_CONTENT`, and `UNKNOWN`. If a higher-priority check or its
prerequisites cannot be evaluated reliably, return `UNKNOWN`, not a guessed
later cause. If no reproducible context rejection exists, return `UNKNOWN`.
Structural, I/O, malformed Unicode, timeout, output-cap and recheck/drift
failures return `UNKNOWN`. Never output tracebacks or arbitrary exception text.

### Exact collection sequence and bounds

The existing outer runner `_systemctl_show` obtains a five-field snapshot with
argv `/usr/bin/systemctl show snap.lxd.daemon.service --property=LoadState
--property=ActiveState --property=SubState --property=UnitFileState
--property=MainPID --no-pager`. This snapshot must show loaded, active,
running and a positive PID. Unlike full inventory, F5 queries no other units
and does not call readlink or the executable resolver. If snapshot parsing or
state validation fails, return `UNKNOWN` without a detailed query.

F4's helper `UNIT_ARGV` then performs up to two identical detailed queries:
`/usr/bin/systemctl show snap.lxd.daemon.service --property=LoadState,ActiveState,SubState,UnitFileState,MainPID,ExecStart,ControlGroup,FragmentPath,DropInPaths,ExecCondition,ExecStartPre,ExecStartPost,RootDirectory,RootImage,BindPaths,BindReadOnlyPaths,Environment,EnvironmentFiles --no-pager`.
The initial detailed query must match the five-field snapshot. Its structurally
valid fields are classified in the declared priority order in memory; the
first rejected predicate is the only candidate category. If unit-level checks
pass, inspect the fixed trusted unit file and, only when its exact F4 reference
is admitted, the fixed F4 drop-in and `/etc/environment` using the existing
descriptor and content rules. A rejected unit reference must never be opened;
do not inspect lower-priority context after the first rejected predicate.

Before emitting any category, issue the second identical detailed query and
re-observe every file actually read, using the same trust checks, to prove that
the first observation and identity-driving fields remain stable. Compare
F4-normalized unit identity fields and descriptor/file identities and bytes in
memory; do not output or hash those bytes. If the second query, reread or
comparison fails, return `UNKNOWN`. Otherwise emit only the candidate category;
if no rejection reproduced, return `UNKNOWN`. Invalid structure, inactive or
drifting state, untrusted file, failed read, command error or exceeded limit
stops subsequent collection and returns `UNKNOWN`; the only allowed continuation
after a context rejection is the bounded recheck just described.

F4 `_Proof` has a 60-second aggregate cooperative deadline, 64 KiB per
context text, and 16 MiB aggregate byte budget; the outer `Runner` additionally
limits each command to 30 seconds, each stream to 2 MiB, all command output to
16 MiB, command count to 256 and total runner time to 300 seconds. Use the
stricter applicable limits, reusing the existing runner and accounting for
rechecks. File deadline checks are cooperative, not a claim that a filesystem
syscall can be preempted. No additional systemctl, shell, client, endpoint,
socket, network or resource command is admitted by this contract.

The F4 design's statement that no new CLI or diagnostic schema was needed
remains historically correct for F4. F5 is an explicit narrow extension for
this diagnostic only; it does not broaden F4's proof or inventory behavior.
Prefer shared predicates where they preserve F4 behavior, with tests proving
equivalence. A diagnostic category cannot establish that a rejected value is
safe or justify an automatic allowlist change.

## Sequence and controls

F4 checkpoint -> F5 implementation review and PC-WSL quality -> separate
post-commit native diagnosis plan/GO -> independently reviewed observation ->
separate correction decision if evidence supports it -> new S02F inventory
plan/GO. S449-02G remains conditional on a successful complete inventory and
exclusive ownership; S449-02H retains its own prerequisites. No diagnostic
result admits a listener fixture, runtime mutation, support version or issue
completion. The current F4 test results are historical and are not F5 tests.

The workspace-private issue matrix `.tiny-swarm/evidence/issue-449/requirement_matrix.md`
remains the issue-level authority; D01–D08 refine its R449-18, R449-19 and
R449-22 evidence and safety obligations without reducing other requirements.
Private S02 result, GO and review records must be kept in owner-controlled
POSIX ext4 directories (0700) with files 0600, not under DrvFS.
