# Epic 440 — WSL version checkpoint compatibility

Status: CODE_VERIFIED by root on PC WSL; no live Apply or host changes.
The worker performed no tests or host actions.
Baseline: `635e67f067183738579701b6e12263d727746e46` (the commit matching the
parent's `635e` abbreviation; that shorter name also matched an unrelated blob).
Branch: `fix/epic440-wsl-state-20261107`; isolated Linux worktree.

## Problem and bounded requirement matrix

Actual WSL observation preserves `3.0.3.0`, while Assert-PreparationState accepts
only three components. Application validates/writes the pending checkpoint
before invoking Execute, so current resource Apply would block before changing
configuration. Do not truncate the observed revision or bypass durable state.

| ID | Requirement | Implementation | Meaningful verification | State |
| --- | --- | --- | --- | --- |
| WSTATE-01 | Preserve complete three/four-component WSL version in existing checkpoints | Assert-PreparationState WSL field predicate only | Actual pending/effect serialization, validation and file roundtrip for 3.0.1 and 3.0.3.0 | OPEN |
| WSTATE-02 | Preserve null/empty-string unknown behavior; reject nonstrings and malformed known values | Same typed predicate | Null/empty roundtrips; malformed/fifth-component/newline/whitespace/nonstring refusals | OPEN |
| WSTATE-03 | Invalid checkpoint versions cannot reach privileged execution or replace valid state | Existing application ReadState and WriteState boundaries | Actual Assert validation through mocked checkpoint port blocks Execute; invalid real WritePreparationState leaves valid file unchanged | OPEN |
| WSTATE-04 | Preserve schema, identity, types, provenance, consent and state lifecycle | No changes outside WSL version predicate | Existing W08 identity/state regressions plus exact-source preparation/quality checks | NOT_RUN |

## Proposed exact contract before code

Known WSL values must be strings with exactly three or four dot-separated,
nonempty ASCII decimal components, anchored with `\A` and `\z`:
`\A[0-9]+(?:\.[0-9]+){2,3}\z`.

The predicate preserves the literal full value; it does not trim, normalize,
parse to a different version type, impose a new support matrix/minimum version,
or remove an explicit revision. Existing numeric three-component strings remain
accepted. Existing null and empty-string unknown observations remain accepted.
Booleans, numbers, arrays and maps are not version strings even if false-like;
reject them explicitly. Reject fifth components, missing components, nonnumeric
characters, whitespace, embedded/trailing line breaks and non-ASCII digits.

Only Assert-PreparationState's WSL field condition changes. All existing schema,
state/operation IDs, status, identity equality, Windows-build type, Ubuntu,
timestamp, observation, recovery-command, provenance and consent gates remain.
No schema bump, journal override or migration/adoption path is introduced.

## Concrete tests and execution plan

Extend the current actual durable checkpoint fixture (mock only its ACL/path
boundary) with both pending and effect records. Serialize, validate, write,
read JSON and revalidate known legacy/new and null/empty unknown values; compare
type and exact value including the fourth component. Existing create/replace
behavior and single checkpoint file remain required.

Add actual application-path controls for valid four-part runtime facts with
resource-only plans: pending/effect checkpoint writes validate through the real
state parser before fake Execute, retaining full version. Malformed persisted
checkpoint versions loaded through ReadState must add bootstrap_state_invalid
and leave Execute untouched. Invalid real file writes must preserve the previous
valid checkpoint bytes and leave no temporary file. Keep all earlier W08 tests.

Root owns all remote verification. No test/PowerShell/Python/host invocation by
this worker. After root's design GO, implement serially within:

- bootstrap/windows/preparation/Adapters.ps1
- tests/windows/prepare-windows.Tests.ps1
- this record

Parent owns workflow/context integration. Independent source review, targeted
PC-WSL preparation tests and full QUALITY precede acceptance. Any source commit
changes the live plan fingerprint, so resource Apply still requires a fresh
same-source preflight and phase-specific GO.

## Maintenance boundaries remain separate

Native NTFS product recovery metadata versus ext4-only workflow evidence still
needs explicit classification. Root's latest actual inventory also confirms
TinySwarmWorldWslBridge is Running, its legacy task is Absent and native Windows
sshd is Running. A WSL restart can therefore let the active bridge rewrite
PortProxy. Owner-verified quiescence and preservation require a separate decision
before resource Apply; this checkpoint correction authorizes neither that
service change nor a restart or network edit.

## Implementation handoff

Root and two independent reviewers approved the exact pre-code design. The only
production change computes the typed WSL predicate inside Assert-PreparationState
and substitutes it for the old three-part regex condition. It does not change
any other field, state identity or write/execute ordering.

The application regression validates actual serialized pending/effect records
with `3.0.3.0` around a mocked resource action. Fifteen malformed/nonstring
checkpoint values exercise the actual state validator in ReadState before
Execute, with checkpoint/execution counters unchanged. These are mocked effects,
not live configuration operations.

The existing durable filesystem fixture now performs ten pending/effect
roundtrips across legacy/new/legacy-numeric/null/empty values, verifies exact
types/values, and requires all malformed actual write attempts to leave the
previous checkpoint bytes unchanged with no temporary file. Only its existing
ACL/path safety boundary is mocked. All earlier W08 tests remain.

| File | SHA-256 |
| --- | --- |
| bootstrap/windows/preparation/Adapters.ps1 | `cc5cb90940696571d4cfa89e260851e7671150043a1c28833cc5e7b347618f70` |
| tests/windows/prepare-windows.Tests.ps1 | `3f208a2638594282ad554df8736de4f42e0a78d6b1b0dcc81a25ed7f7030c1be` |

Static `git diff --check`: PASS. No PowerShell/Python/test/host execution, commit,
push or publication by this worker. Runtime behavior and WSTATE-01–04 remain
unverified pending root's independent exact-source review and PC-WSL results.
The pending maintenance-storage and active bridge decisions remain separate.


## Root integration and verification

Root copied the three reviewed worker files byte-for-byte into the continuation
worktree. Independent architecture/security and tester/DevOps review approved
Adapters SHA-256 `cc5cb90940696571d4cfa89e260851e7671150043a1c28833cc5e7b347618f70`
and PS tests `3f208a2638594282ad554df8736de4f42e0a78d6b1b0dcc81a25ed7f7030c1be`.
Root's exact combined F4-locations/S02I candidate passed 266 focused tests and all
seven QUALITY gates on the authorized PC WSL host: 43 architecture tests,
3,262 discovery tests/36 skipped, exit 0. The actual checkpoint IO/application
boundary tests run within the mocked PowerShell preparation contract; no live
product state/resource was written. Focused log
`2a361815f4be6fdee794a8c97ac1611a092859030ca540ab5a3a856e38dc1f69`, full log
`582a5eef5cfb33082a13f2c2d6b8f2897b83fdb4ad66e76fd1ea6bd13ea038af`.
Root's private copied logs matched both hashes. This is code verification only;
fresh committed-source preflight/fingerprint and separate maintenance admission
remain required, including active bridge preservation.
