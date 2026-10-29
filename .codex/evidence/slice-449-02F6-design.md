# S449-02F6 — bounded Snap drop-in form diagnosis

Status: PLANNED. Native F5 source 04a0c3cf3b641775cad59da12a7951e0eb5035cc
returned BLOCKED_UNKNOWN / DROPIN_CONTENT, exit 2. This reveals no contents
and is not inventory, identity, ownership, support, safety or host admission.
The private F5 plan, GO and result remain on native ext4 and must be
independently reviewed before any F6 host phase.

## Requirement-to-verification matrix

| ID | Requirement | Verification |
|---|---|---|
| D01 | Bind native F5 result, host, source and existing active fixed service. | Private F5 records, independently reviewed exact-source JIT. |
| D02 | Only fixed F5 unit queries and F4 UNIT_FILE and DROP_IN; no derived path or /etc/environment read. | Exact fixed-argv and file-access assertions. |
| D03 | Preserve root ownership, no-follow, descriptor identity, file bounds and cooperative deadlines; stable recheck each read. | Untrusted/symlink/I-O/size/timeout/identity/bytes drift tests. |
| D04 | Closed structural categories only; no values, paths, PIDs, exceptions or secret hashes. | Every enum/priority and synthetic secret leakage tests. |
| D05 | Always BLOCKED_UNKNOWN and exit 2; unverified/unstable/invalid context is UNKNOWN. | CLI, all error paths and recheck tests. |
| D06 | No service/socket activation, clients, endpoints, resources, inventory artifact or host mutation. | Mock call and no-write tests. |
| D07 | Preserve normal F4 and F5 acceptance, failure and output semantics. | Parity and regression tests. |
| D08 | Cover every category, priority, mixed faults, trusted-file, encoding and budget cases. | SSH-PC-WSL focused tests and direct Ruff. |
| D09 | Six same-hash reviews/S3D and exact-source full PC-WSL QUALITY; separate post-commit native plan/GO. | Reviews, hashes, actual gate and private host evidence. |
| D10 | No observation alone permits a guard change, inventory rerun or host qualification. | Independent result and separately governed next decision. |

## Closed CLI and grammar contract

Only python3 tools/qualification/native_runtime_inventory.py
--diagnose-snap-dropin is valid. The flag must be the sole argument; invalid
combinations, duplicates, values or help return exactly one constant JSON object
with status BLOCKED_UNKNOWN and reason UNKNOWN and exit 2, without argparse,
argument reflection or host access. Valid invocation always returns the same
two-key schema and exit 2. Never output tracebacks or arbitrary errors.

F5 DROPIN_CONTENT must reproduce using F4's accepted-input predicate on a
trusted stable snapshot; otherwise return UNKNOWN. After exact F4 blank/comment
filtering, CR, NUL, any backslash escape or continuation, invalid UTF-8,
ambiguous syntax and all trust, I/O, state, size, deadline and drift failures
take priority as UNKNOWN. With confirmed stable valid text, use this order:

1. SECTION_SHAPE: significant lines do not begin with exactly one [Unit]
   section, or another syntactically section-shaped line appears.
2. UNKNOWN_DIRECTIVE: section shape passes but subsequent significant lines
   are not exactly one After= line; duplicate or other lines are included.
3. DEPENDENCY_VARIANT: exactly [Unit] plus one After= line, whose complete
   text differs from F4's exact accepted After= line.
4. UNKNOWN: no reproducible rejection or any precondition cannot be verified.

The result does not reveal lines, names, values or contents. An After= variant
may be unsafe; a category cannot admit it. Uncertain syntax returns UNKNOWN.

## Fixed collection sequence and bounds

Use exactly the initial fixed F5 five-property unit snapshot and at most two
F4 detailed fixed unit queries defined in
.codex/evidence/slice-449-02F5-design.md. Snapshot requires loaded, active,
running and positive PID. Validate F4 unit-level fields before file reads.
Read only the fixed F4 UNIT_FILE and, after the exact permitted reference and
same no-follow/root-ownership/mode trust checks, fixed DROP_IN. Never open a
path from input data; explicitly never read /etc/environment, including on
an accepted drop-in. Do not use a helper that implicitly proceeds to that
file. No client, socket, resource, service activation, extra systemd query,
network or host mutation is permitted.

Before category output, repeat the second F4 detailed query and re-observe
each actually read file with identical descriptor trust checks. Compare
identity-driving unit fields and descriptor identities and bytes in memory.
No file content, raw value or secret-bearing hash may be retained or emitted.
Drift, ambiguity, errors or exceeded limits return UNKNOWN without guessing.
Do not perform lower-priority collection after a precondition fails.

Use existing _Proof 60-second cooperative aggregate deadline, 64 KiB per
context text and 16 MiB aggregate byte budget. Outer Runner limits each command
to 30 seconds, each output stream to 2 MiB, all commands to 16 MiB, maximum
256 commands and 300 seconds total; count rechecks and use the stricter limit.
Filesystem deadlines are cooperative, not preemptive syscall guarantees.

## Tests, dependencies and release

Test each category, all multi-fault priorities, accepted exact lines,
blank/comments, extra/duplicate/unknown sections or directives and values,
CR/NUL/backslash/invalid UTF-8, secrets in data, exceptions and both output
streams, no derived or environment path reads, unsafe owner/mode/symlink,
missing and I/O/size/deadline failures, identity/unit/bytes drift, all invalid
CLI combinations, exact argv and no extra calls, artifacts or host changes.
Demonstrate normal F4/F5 behavior unchanged.

Serial F4 -> F5 commit 04a0 -> bounded F5 native result -> F6 same-hash
six-role review and S3D -> F6 implementation -> exact-source SSH PC WSL
targeted tests, direct Ruff and full QUALITY -> separate post-commit
six-role plan/S3D/host GO -> one native diagnosis. A separately reviewed
evidence-backed correction and S449-02F inventory plan remain future decisions.
S449-02G and 02H retain their existing dependencies. F6 is not a fixture,
runtime, ownership or support GO. Private host records require owner-controlled
ext4 directories 0700 and files 0600. F5 testing did not verify Python 3.12.
