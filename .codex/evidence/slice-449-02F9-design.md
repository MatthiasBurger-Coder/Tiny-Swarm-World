# S449-02F9 — bounded Snap cgroup relation diagnosis

Status: **PLANNED**; no implementation, native result, inventory admission or
host GO is established by this document.

The 2026-10-29 native S449-02F8 diagnosis on source
`7615a29962b0fd3ae2d44e4246893335ad9fadd3` returned
`BLOCKED_UNKNOWN / PROCESS_BINDING`, exit 2. The F8 code assigns this stage
only to a repeatedly observed, valid cgroup-v2 process path differing from
the systemd unit ControlGroup; it does not reveal either path or establish
process identity, namespace, ownership or safety. Protected native F8 plan and
result remain on owner-private ext4 and require independent review before F9
host execution. No runtime mutation or inventory pass is claimed.

## Requirements and acceptance

| ID | Requirement | Verification |
|---|---|---|
| D01 | Bind the F8 observation, exact source and fixed active unit/PID inputs; require the F8 cgroup mismatch to be reproduced. | Synthetic unit/process proof and early-abort tests. |
| D02 | Reuse only F8's fixed unit and trusted unit/drop-in/process observations, queries and bounded rechecks; do not add host reads, commands, client/socket/network calls or environment-file access. | Fixed-call/no-extra-read and parity tests. |
| D03 | Compare canonical absolute paths by complete components in memory. Do not normalize invalid paths or treat a string prefix as ancestry. | Root, nested ancestry, sibling/prefix-collision and invalid path tests. |
| D04 | Apply the closed priority and UNKNOWN rules below; never infer a common namespace or an identity/safety decision. | Reason and mixed-input/namespace-nonclaim tests. |
| D05 | Before an explicit relation result, recheck the previously trusted unit/drop-in and the same process PID, start-time, UID, cgroup and other F8-consumed snapshots; all observations must be complete, trusted and stable. | Per-snapshot drift, missing, IO and permission tests. |
| D06 | Emit only the closed two-field JSON object and exit 2; never emit path/components, names, PID, argv, environment, raw data, exceptions or sensitive hashes. | CLI, stdout/stderr/exception secret-leak tests. |
| D07 | Never mutate host state, create inventory, activate service/socket or weaken F4–F8 behavior. | Mock call, no-artifact and F4–F8 parity regression tests. |
| D08 | Preserve F8 command, byte and cooperative deadline budgets; classify partial, uncertain or over-budget checks as UNKNOWN. | Limits, progressing clock, short circuit and no-later-read tests. |
| D09 | Perform six same-hash role reviews and S3D before implementation; run exact-source focused tests, direct tool Ruff and full QUALITY via the designated SSH PC WSL host. | Hash-bound role, S3D and gate evidence. |
| D10 | Require separate post-commit host plan/JIT/GO before one native run; later fix or S449-02F retry requires independent evidence and review. | Separate private host evidence; no implied admission. |

## Closed contract

The only standalone invocation is
`python3 tools/qualification/native_runtime_inventory.py --diagnose-snap-cgroup-relation`.
If the F9 flag is present with any other argument, value or duplicate, output
UNKNOWN without argparse text or host I/O. Invocations not using the F9 flag
retain existing F4–F8 behavior. Emit exactly one JSON object with keys
`status` and `reason`; status is always `BLOCKED_UNKNOWN`, exit is always 2.

Read the F8 systemd ControlGroup and valid cgroup-v2 process observation only
in memory. Require exactly one `0::<absolute-path>` line with at most one
final LF, strict UTF-8, no CR/NUL or extra lines; both paths must pass the
existing F8 absolute canonical path validation without normalizing input.
Reject empty components, repeated slashes, dot/dot-dot components and trailing
slash except for root. Use complete components, not a text prefix. Relative
comparison classifies syntax only, even if the two paths originate in different
namespace views; no common namespace is assumed.

Require a reproducible F8 PROCESS_BINDING cgroup mismatch and stable trusted
unit, PID/start-time/UID/cgroup and already consumed file snapshots before a
category. With unit components U and process components P, use this priority:

1. `PROC_ROOT` iff process path is exactly `/` and unit path is not `/`.
2. `PROC_STRICT_ANCESTOR` iff P is a nonempty strict initial component
   sequence of U.
3. `PROC_STRICT_DESCENDANT` iff U is a strict initial component sequence of P
   and process is not root. The pure component-comparison helper may define
   and test this mathematical relation for unit root; the F9 diagnostic must
   return UNKNOWN for unit root because the unchanged F8 `_context_reason`
   rejects `ControlGroup=/` before PROCESS_BINDING. Never relax F8 admission.
4. `DISJOINT` iff neither is equal nor ancestor of the other.
5. `UNKNOWN` for equality, invalid/multiple/ambiguous cgroup data, failed
   F8 reproduction, missing/untrusted observation, IO, permissions, incomplete
   recheck, drift, timeout or limit.

Thus `/a` and `/ab` are disjoint, while `/a` and `/a/b` are not.
Ambiguous or unequal observations never imply a cgroup namespace cause, process
membership, executable provenance, ownership, safety or admission. Repeated
observations are not an atomic snapshot.

Use F8's existing fixed outer and detailed unit queries, process observations,
trust checks and cooperative deadlines without extending their query, byte or
wall-clock budgets. No data-derived file path, additional host command,
resource/client/socket/network query, `/etc/environment` read or write is
allowed. A condition that cannot be securely reproduced within the existing
budget returns UNKNOWN; do not visit an otherwise unvisited unsafe phase to
obtain a reason. Preserve F4–F8 public results and fail-closed behavior. This
F9-only CLI is an explicit bounded extension of F8's sole-CLI contract.

## Sequence and boundaries

F8 checkpoint and bounded native PROCESS_BINDING observation -> independent
review of private F8 evidence -> F9 six-role same-hash review and S3D -> F9
serial implementation -> exact-source PC WSL targeted tests, direct Ruff and
full QUALITY -> separate post-commit host-specific same-hash plan, S3D, JIT and
GO -> at most one native read-only F9 invocation. An F9 observation is not a
correction or authorization to retry S449-02F. Any F4 correction requires a
separate source-backed architecture/security decision, implementation and
quality evidence. S449-02F remains BLOCKED until a new complete inventory
passes; 02G and 02H retain their existing S449-02F prerequisites.

Keep host records in the verified private POSIX ext4 directory (0700,
files 0600). Preserve historical failures and distinguish local/mock, native
diagnostic and live qualification. The issue-level requirement matrix remains
`.tiny-swarm/evidence/issue-449/requirement_matrix.md`; D01–D10 refine its
R449-18, R449-19 and R449-22 without reducing #440 or #449 requirements.
