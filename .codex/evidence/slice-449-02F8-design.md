# S449-02F8 — bounded F7 failure-stage diagnosis

Status: PLANNED. Native F7 source fd8dd1478329ee00a907822b4e43b19efc14a631
returned BLOCKED_UNKNOWN / UNKNOWN and exit 2. The result identifies no cause
and private host evidence requires independent review before the F8 host phase.

## Requirements and verification

| ID | Requirement | Verification |
|---|---|---|
| D01 | Bind F7 observation, target, source and fixed active Snap unit. | Independent private evidence and exact host JIT. |
| D02 | Use only existing F7 fixed unit queries, trusted unit/drop-in, validated PID/process/shell and revision-bound script pair. | Fixed argv/path and no-environment/client/socket tests. |
| D03 | Preserve F7 30 s command, 60 s cooperative proof, 300 s runner, 2 MiB stream, 16 MiB aggregate, 64 KiB context and 1 MiB script limits. | Boundary, progressing-clock and no-later-call regressions. |
| D04 | Closed fixed JSON/enum/exit 2; no raw values, PID, argv, environment, secret hash, exception or traceback on either stream. | Synthetic secret, output and CLI tests. |
| D05 | Classify only explicit typed deterministic negative predicates after relevant prior trusted observations have been stably rechecked. | Per-stage, priority, stability and short-circuit tests. |
| D06 | Parse/schema, IO/permission, timeout/limit, ambiguity or incomplete recheck => UNKNOWN; RECHECK_DRIFT only for two successful trusted comparable observations that differ. | Error injection, limits, trust, drift and incomplete-recheck tests. |
| D07 | Share F7 predicates without changing normal F4–F7 behavior; no extra host commands/files, environment-file read, artifact or mutation. | F4–F7 parity and no-write/call-count tests. |
| D08 | Recheck only previously acquired trusted data within F7 budgets; do not access an unvisited unsafe later phase to force a reason. | Snapshot, TOCTOU, no-later-read and limit tests. |
| D09 | Six same-hash reviews and serial S3D; exact-source SSH PC WSL targeted/direct Ruff/full QUALITY; separate post-commit host plan/JIT/GO. | Review, hash and quality evidence. |
| D10 | A result is only a bounded stage observation, not safety, identity, ownership, support or inventory admission. F02 correction/retry is separate. | Independent decision and consolidation. |

## Exact CLI and failure-stage contract

Only --diagnose-snap-generator-stage as sole argument is valid. Invalid,
duplicate, combined, equals-value and help inputs return fixed two-key JSON
status BLOCKED_UNKNOWN/reason UNKNOWN and exit 2 before argparse or host I/O.
All valid outputs likewise have only status BLOCKED_UNKNOWN and one reason
from this closed list, exit 2. Priority follows existing F7 execution:

1. UNIT_CONTEXT: explicit closed negative for a fully parsed and validated
   fixed unit context predicate; malformed/inconsistent snapshots => UNKNOWN.
2. DROPIN_TRUST_OR_FORM: explicit negative of F6/F7 form predicate using
   complete successfully trust-checked fixed unit and drop-in snapshots.
   Missing/untrusted/unreadable/ambiguous observations => UNKNOWN.
3. PROCESS_BINDING: explicit deterministic closed negative after completely
   observed and unambiguously parsed F7 process/cgroup/Snap prerequisites.
   Existing mixed error codes may not be guessed; undifferentiated => UNKNOWN.
4. REVISION_BINDING: successfully validated main_environment returns a valid
   base unequal to the pinned 40958 base. Invalid/mixed/denied => UNKNOWN.
5. SHELL_BINDING: explicit negative of fully observed trusted shell identity
   comparison. Failed access or noncomparable data => UNKNOWN.
6. SCRIPT_PAIR_OR_DIGEST: explicit negative after completely observed trusted
   host/process-root script pair identity comparison or fixed digest mismatch;
   missing/denied/unverifiable pair => UNKNOWN.
7. RECHECK_DRIFT: only two successfully collected, independently trusted and
   semantically comparable observations that differ; failed/partial recheck
   => UNKNOWN.
8. UNKNOWN: every other case including successful F7 MATCH, I/O, permission,
   parsing, unexpected exception, limits, ambiguous multi-error or unstable
   prior observation.

Existing F7 execution order is fixed: outer unit snapshot, detailed unit/context,
fixed trusted UNIT_FILE and DROP_IN, F6 form then F7 generator grammar, process,
in-memory main_environment/revision, shell, pinned script pair/digest, and
unit/process/shell/script/context rechecks. A stage label requires preceding
trusted relevant snapshots to be rechecked and stable before output. An
independently successful comparable difference yields RECHECK_DRIFT. Do not
read an unvisited later unsafe stage solely to force a label; if stability
cannot be established within original F7 query/byte/time bounds return UNKNOWN.
Do not map arbitrary exception strings or errno into stage names. Mixed F7
exceptions must remain UNKNOWN unless refactored into shared typed predicates
that do not change F7 public MATCH/UNKNOWN semantics or F4–F6 APIs/behavior.

No /etc/environment, new subprocess/systemctl query, arbitrary derived path,
client/socket/network, host mutation, service activation, script execution,
inventoried artifact or public raw data. Process environment/argv remain
bounded and in-memory only; no raw data or secret-bearing hashes persist.
Filesystem deadlines are cooperative, not preemptive. Stage names are merely
bounded failure observations and do not establish a cause, security, identity,
actual producer, service ownership, version support or host readiness.

## Ordering

F7 checkpoint -> independent review of private F7 UNKNOWN evidence -> six-role
exact-hash review and serial S3D -> F8 implementation -> SSH PC WSL targeted,
direct Ruff and full QUALITY on exact candidate -> separate post-commit
source/host-specific reviews, S3D/JIT/GO -> at most one read-only native F8
diagnostic. Any correction or S449-02F inventory retry is separately scoped.
02F remains BLOCKED; 02G/02H retain successful-inventory prerequisites.
Private records require an owner-only ext4 directory (0700) with files 0600.
Python 3.12 was not separately verified by the previous F7 gate.
