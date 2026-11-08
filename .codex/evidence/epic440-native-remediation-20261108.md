# Native S02 actual-failure remediation

Source-only implementation authorized by Root, based on clean
`7643c68e576dda388151cd34cd48c6cbf4dc545f`. Scope: the native maintenance
controller, existing listener fixture, their two existing test modules, this
record. No host actions, tests, runtime imports or commits by this author.

## Actual result and limits of inference

Root reported one real maintenance attempt stopped its three original Running
LXD nodes gracefully, shut down the verified Snap daemon and captured actual
paused resource admission with all twelve checks passing. The fixture's JIT then
failed after six reads, before any fixture resource write: its image-info CLI
used unsupported `--format json` on Incus6.0.5. No successful fixture or supported
runtime capability is inferred from this failed attempt.

Automatic recovery started the daemon, then full binding failed before node
starts. Its exact cause was not retained. A later read-only full binding and
three node UUID checks passed, and a separately approved explicit recovery
restored all three Running states, the original inactive socket and full
preservation comparison. A startup readiness race is a hypothesis, not an
observed cause. This patch does not retroactively classify that error.

## Corrections

The JIT image metadata read now uses the existing guarded `incus query` GET
transport at exactly `/1.0/images/<64-lowerhex>?project=default`. The URI parser
admits that bounded form only, with no alternate project, extra query, selector,
fragment or write option. The unsupported image-info CLI form is removed from
the inventory allowlist; there is no CLI-format fallback. Existing literal JIT
fixtures, read-prefix assertions and allowlist tests use the actual API path.
The existing strict duplicate-key JSON reader and exact Alpine3.21 policy remain.

After exactly one admitted daemon start, the production port waits for complete
installed/process/endpoint proof, then reads the fixed existing `/1.0` API through
the collector's guarded protocol, validates the complete pinned root DTO and
matches the saved trusted/default/noncluster/family/version authority projection.
Full binding is repeated around that GET. Only daemon-not-active, absent wrapper
child, absent LXD socket and root-GET command-unavailable outcomes are eligible
for bounded retry; installed/Incus/source/process/schema/authority drift fails
immediately. This is stricter than treating systemd active as API readiness.

The native Unix SIGALRM handler is scoped to this read-only wait and restored in
finally. Its 25-second timer reserves the existing maximum five seconds for
owned-client kill/reap, keeping the complete wait within thirty seconds. A
preexisting real timer is refused; no global timer is overwritten. At least
thirty seconds of the unchanged independent 600-second recovery reserve must
remain before waiting. A timed-out proof is not accepted, no service start is
repeated, and no node starts before successful proof. The final full snapshot
and original-state preservation comparison remain mandatory.

Failure records are exclusive owner-private durable journal files with only
fixed stage, safe symbolic reason and UTC time. Qualification, automatic or
explicit recovery, and per-node recovery failures retain trusted symbolic codes;
unknown/raw exception text is replaced by a fixed redacted code. Fixture child
failure codes are read only from the fixed private result with the exact source
and final GO hash, fixed blocked status and symbolic-code grammar. An unrelated,
unbound or malformed result cannot replace the original controller failure.
No raw exception, streams, process IDs, addresses, configs or environment values
are added to failure records. The original failed evidence remains historical.

## Authored regression coverage and validation

New tests exercise the actual production start/wait path (active before proof,
transient then ready, exactly one start), hard wait expiry, immediate permanent
drift refusal, fixed API/root-authority recheck and endpoint binding. They also
exercise real private failure journal serialization, retained qualification and
recovery reasons, raw-text redaction and bound versus foreign fixture results.
Existing JIT literal/prefix regressions and URI allowlist tests are updated;
retired CLI syntax and malformed image query variants are explicitly denied.
All external observations/processes are mocked in these authored tests.

Author checks: AST parsing of all four modified Python files and
`git diff --check` only. Root must independently review exact bytes, run PC
focused/typecheck/all quality gates, then commit and stage a fresh clean source.
Any new native attempt requires a new intent, fresh read-only proposal and
separate concrete maintenance/final paused approvals. Previous approvals are not
reused. No live success, capability qualification or EPIC closure is claimed.

Root PC R1 combined8pins type912 PASS78bfef797f4b5390ab28ea0515177bdea203faeba408e175651c866f15ed5f97. Focused295/5.285s failed1 PRIVATE_DIRECTORY_UNSAFE for real failurejournal test using /tmp with non-rootordinaryuser; fullNOTRUN. Loga5342d4e879de02f96ba8d231f676160e0a811b9d4fede06263a6337c02f429d. Root test-only correction follows existingJournal unitfixture convention: replace only constructor ancestor-provenance port with mock, assert invokedexactroot; actual0700/0600 file/fsync/serialization/readback staysreal. Production private_directory unchanged. R2pending.

## Root independent review and actual PC R2 qualification

Root independently reviewed exact guardedImageGET/queryallowlist, actualfullAPI/startup wait/timer/cleanup safety and trusted symbolicfailure persistence. Narrowfixture constructor-provenance mock independently reviewed by original author; productionguard unchanged. Combined8assets PC596base includesacceptedabsencecollector/helper. Typecheck912 PASS78bfef797f4b5390ab28ea0515177bdea203faeba408e175651c866f15ed5f97; focused295/6.153s PASS35960de9c9390f6d377dc70372707c1c3c737d78f12ccde635176daa35cb450e; all7 QUALITY PASS3401/225.999s/36skips, quality97fd5cc89b1e6bbe8b8c402b087564e40812d08e2c5fc2b04b526b759e5d3c77. Logs retained PC privateext4. Exactsource/test copied to Root; resultprose appendedafterward. No new nativefixture/maintenance effect yet; previous failedrun andsuccessful recovery preserved.
