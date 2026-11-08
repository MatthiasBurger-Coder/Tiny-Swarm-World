# EPIC 440: Three-Amigos review of the WSL registration blocker

Decision: **READY_FOR_WORKFLOW** for the bounded service-quiescence prerequisite
and ordering below. Actual registration remains **LIVE_BLOCKED_BEFORE_MUTATION**;
WSL S02 and EPIC acceptance remain OPEN. This report grants no host execution GO.

Inspected source: `ac28c5b13d011abd4c2efc111aefe9fecdb5d3ac`. Author/reviewer:
`/root/architecture_review`, the single analysis subagent explicitly requested by
the user. Requirements, architecture, automation and test/evidence are separate
role passes by this same agent, **not four independent reviewers**. Root remains
integrator/executor and must independently review any authored effect helper.

Applied skill: [three-amigos-requirement-gatekeeper](/home/micro/.codex/skills/three-amigos-requirement-gatekeeper/SKILL.md).
Read repository AGENTS, the canonical issue-completion and verification-state
policies, preserving-host/product-acceptance ADRs, current workflow, registration,
bridge binding, guest switch, service runner and relevant tests. The earlier
connected #440/#449 acceptance review remains the parent scope. No extra host,
profile or Cartesian product matrix is introduced.

## Actual state and evidence limits

- Actual W05 completed on this source: private
  `wsl-parent-duplex-usedby/event-0004.json` binds 21 GiB / 8 CPU / 6 GiB swap;
  `event-0006.json` records MAINTENANCE_COMPLETE, resource_verified, shutdown,
  relaunch and bridge restoration, zero route changes, no uncertain actions.
  Result SHA256 `737238f3e7a2354874f074f0d7c3e730e122f490f3ec1cf59357a5c5bdcd1cfc`.
  This is host-resource maintenance, not listener/product/service qualification.
- Original R9 returned RESTORED under its existing identity-bound journal,
  retaining the original two Running managers and two Stopped workers, graph
  and 35 normalized detail records. Private `wsl-runtime-r9-prepared/restore-transport2-stdout.json`,
  SHA256 `099d0f91dac3f86fc15084b18dc79fe8a93f807c3aed935ee0b2e8d19d1ba1cb`.
  That completed quiesce journal must not be replayed for the next switch.
- Registration R4 failed during Observe/GlobalProof, before import:
  `registration-plan-readonly-r4/raw-result.json`, SHA256
  `f067d432b3c1be37146d1fd14839ef0fb87e7466ea9db37d67d6b4561811327d`.
  Error BRIDGE_FILE_DRIFT points to the initial expected-length equality in
  BridgeFileHash at registration source line 224. Thus a collected file length
  differed from its opened stream length. It does not identify the file,
  direction of length change, writer, or an unauthorized edit.
- The separate ten-second metadata observation found the same 14 paths and no
  length/mtime change in its own interval; raw SHA256
  `a2c0444ad3a9c074232fa965ffdce14292389c65a97e8164d693c8a36bbc2f2c`.
  That does not invalidate the earlier refusal or attribute it to any log.
- Root reports a healthy bounded resource-parent lease still holds the original
  guest. No new registration has been imported. No host diagnostic, service
  operation, source implementation, test or state change was performed by this
  review; only this report is authored. The tracked master checkpoint predates
  the actual W05 success and must not override the linked actual results.

All private paths above are relative to Root's ignored
`.tiny-swarm/evidence/issue-449/continuation-20261107/`. No protected payload,
credentials, SID, IP or raw log content is copied into this tracked report.

## Requirement-to-delivery matrix

| ID | Requirement/source | Production owner/path | Actual evidence/dependency | State |
| --- | --- | --- | --- | --- |
| REG-01 | W05 capacity before qualification | resource maintenance + preparation application | Actual 21/8/6 maintenance and original restoration above | VERIFIED, bounded host prerequisite |
| REG-02 | #440/449 preserve originals; no adoption/reset | registration inventory and original runtime driver | R9 RESTORED; GUID/VHD/default/runtime checks retained | VERIFIED prior restoration; future preservation required |
| REG-03 | Complete stable registration preservation proof | registration GlobalProof/BridgeFileHash | Actual collected-length refusal; exact member unknown | BLOCKED live registration |
| REG-04 | Maintenance can stop only the owned bridge | existing bridge ownership + checked stop/start | Concrete primitives exist; registration Plan does not stop it | PARTIAL, task ordering/receipt needed |
| REG-05 | Preserve all logs and immutable service assets | registration full hashes + protected archive | Existing 14-path snapshot includes current/old logs and wrapper log | PARTIAL, stopped archive/readback not run |
| REG-06 | Import one new registration Stopped, exact original default unchanged | registration Plan/Import/Verify | Durable pending/CAS/no-replay/actual receipt implemented; no import yet | OPEN, applicable live |
| REG-07 | Preserve stopped-baseline validity through consuming checks | registration Verify + guest-switch receipt path | Verify compares global hash; switch validates receipt/GUID/VHD without rerunning global proof | VERIFIED source contract; integration live OPEN |
| REG-08 | Restore initial Running bridge truthfully | checked start + real expected-bundle heartbeat | Restore must precede binding Archive, which requires actual Running | OPEN, applicable live |
| REG-09 | Fresh guest is safe before Incus initialization | guest-switch/reset/network absence + bootstrap | Import alone provides neither machine/boot nor shared-kernel isolation | OPEN downstream prerequisite |
| REG-10 | WSL S02 profile/listener/HTTP and both-host capability proof | existing fixture + matrix admission | Native proof exists; actual WSL fixture/capability acceptance still absent | OPEN, no matrix promotion |

## Requirements role pass

The user has explicitly authorized completing the remaining work on both named
hosts, including necessary preserving maintenance. A finite owned bridge pause
is not resource adoption, deletion, a default-distro switch or a new project.
No additional generic permission question is needed. Fresh source-bound reviewed
execution evidence remains required; broad authorization is not proof of a pass.

The registration Plan must remain read-only. The pause is a separately named,
journaled maintenance operation surrounding Plan/Import/Verify, never an implicit
side effect of preview. All original service configuration, payload, account,
ACL, logon rights, rules, hosts and original registrations remain protected.
Temporary service state and ordinary stop/start logging are explicit maintenance
transitions; they cannot be described as byte-identical runtime transparency.

## Architecture role pass: precise defect and data flow

`GlobalProof` first inventories every bridge file into cached FileInfo objects,
then calls `BridgeFileHash(path, cap, collected Length)` over that inventory.
The hash reader permits concurrent sharing but requires the cached length,
opened length, consumed bytes and final length/mtime to agree. Refusal on an
inconsistent observation is correct. The missing prerequisite is a stable
observation window; increasing bounds or retrying the same live baseline does
not establish one.

The service is an actual writer. `Invoke-BridgeReconcile` releases Reconcile at
bridge script line 3941; refresh emits completion output after it returns at
line 4576. `tws-wsl-bridge-service.ps1` buffers child output at lines 24-31, then
re-emits it at line 35 and writes errors at lines 40/44/60 outside that mutex.
WinSW also writes wrapper logs. Therefore neither Update nor Reconcile alone
freezes all log producers. Waiting two minutes on a mutex can itself cause more
out-of-lock error output. This proves a synchronization mismatch in the design,
not the identity of the file/writer responsible for R4.

The installed definition is pinned WinSW 2.12.0 with `<log mode="roll">`.
Its primary [RollingLogAppender](https://raw.githubusercontent.com/winsw/winsw/v2.12.0/src/WinSW.Core/LogAppenders.cs)
(lines 278-298) rolls stdout/stderr to `.old` when starting; its
[MoveOrReplaceFile](https://raw.githubusercontent.com/winsw/winsw/v2.12.0/src/WinSW.Core/Util/FileHelper.cs)
replaces an existing destination. Consequently every stopped current/old log
and wrapper log must be copied completely to a hash-verified protected archive
before restart. The archive must be outside ServiceRoot so it does not modify
the very GlobalProof baseline being compared. Do not restore archived old bytes
over newly generated logs; preserve the archive and the actual new observations.

### Downstream contract verified, not assumed

Registration Verify calls Assert-AcceptanceRegistrationInventory, which compares
baseline/global/running/default preservation. It would correctly reject a
Stopped baseline after service resume/log rotation. Do not rerun that historical
Verify after the maintenance window and call its failure a new import failure.

At the inspected revision, GuestSwitch `Ports.Registration` (line 704) calls
`RegistrationState` (592) and `Observe` (601). It **does not call registration
Verify** or compare `baseline.global_sha256`. It validates the hash-bound
registered receipt, scenario, exact new name/GUID/VHD, actual registration values,
original default and allowed Running set. Source/Load/Observe/QuiesceOriginal do
not read a bridge archive. The binding adapter is used lazily by EnterNew.
Thus a bridge archive need not preexist when the new actual registration receipt
is consumed or when Original is quiesced. Binding Archive later requires the
bridge actually Running and records that actual state; no fabricated
`originalWasRunning` value or stopped-to-running baseline rewrite is necessary.

## Automation role pass: minimum executable order

Prefer a closed task coordinator over any public production guard change:

1. Keep the existing verified bounded guest lease alive. Capture source, actual
   original registrations/GUID/VHD/default, immutable service policy/payload and
   initial Running state. Verify owned/no-adoption, trusted bundle/wrapper,
   original account, no pending payload transaction and no dependent service.
   Journal the exact pause/restoration obligation before stopping anything.
2. Serialize registration against competing imports; acquire existing bridge
   Update then Reconcile in a documented consistent order. Reuse the concrete
   ownership and checked-stop logic; do **not** call binding StopOriginal with
   invented new GUID/quiesce input. Its present phase contract is not this pause.
   Stop only the proved service, bound its exit/child settlement and refuse if
   the log/file set still changes. `Stop-BridgeServiceChecked` uses `-Force`;
   the no-dependent-service admission must remain before invoking that primitive.
3. With the bridge actually Stopped, preserve every immutable payload/config/
   manifest/definition/ACL hash. Keep all current, old and wrapper logs included
   in the existing strict full-file GlobalProof. No log truncation, exclusion,
   cap relaxation, live-log restoration or writer suspension is allowed.
4. Generate a **new** actual stopped preservation baseline and registration Plan.
   Produce fresh exact registration GO from that baseline. Invoke the unchanged
   Import once, then unchanged Verify while still Stopped. Retain its pending/
   receipt bytes and raw outcome; ambiguous import is RECOVERY_REQUIRED, never
   replayed/unregistered automatically. Verify actual new GUID/VHD and Stopped
   state, original default/values/VHD/running set and full global equality.
5. Archive all existing stopped logs outside ServiceRoot with complete bytes,
   hash, path/file identity, metadata and private permissions, then read back the
   archive before any restart that can roll `.old`. The returned real GUID/VHD
   now permits building genuine bridge/switch scenarios. All standalone
   registration Verify calls must precede resume. No original workload stop or
   new guest start is needed for this registration maintenance window.
6. Resume the same original bridge in the maintenance `finally`, even if a prior
   step failed, after JIT immutable owner/payload/default/GUID/sole-original checks.
   Release Reconcile before starting so the real service can obtain it; retain
   the appropriate outer owner serialization until recovery completes. Start
   only if initially Running, then require the actual original-bundle fresh
   heartbeat, unchanged firewall/foreign routes/hosts and preserved log archive.
   Do not alter credentials, service policy or registration metadata to repair it.
   A failure is durable RECOVERY_REQUIRED, not a new registration/stop replay.
7. Only after actual Running restoration, perform binding Prepare/Archive so its
   original descriptor truthfully records Running. Continue the normal guest-
   switch Prepare/QuiesceOriginal/EnterNew sequence. R9 is already RESTORED and
   cannot be replayed: Root's next fresh original-runtime window (designated R7)
   needs its own source-bound prepare/proposal/journal/GO. Stop only the two
   admitted manager UUIDs; preserve the workers. EnterNew separately performs
   StopOriginal, original termination, all-stopped reset, changed boot and actual
   shared-kernel absence proof. Bootstrap and S02 retain their own identity/GO.

Steps 4-6 can be bounded and resumed as explicit task phases; do not hold one
thread-affine mutex across unrelated remote sessions or extend a spent deadline.
If the implementation holds the registration mutex across its own nested Import,
prove same-thread named-mutex reentrancy or expose the existing owned lock
explicitly; do not replace production ports with successful mocks. Every exit
retains the original Running restoration obligation. If failure occurs after
Original quiesce, also invoke its identity-bound restoration; bridge restore
alone does not restore the guest workloads.

No registration receipt/global-baseline schema amendment or looser hash
predicate is required by the current source. If a separate external caller truly
requires an extra standalone Verify immediately before QuiesceOriginal, the
source also permits consuming that Verify and QuiesceOriginal while the bridge
is still Stopped, then resuming/heartbeating it and creating the genuine Running
binding archive before EnterNew. That is an optional ordering alternative, not
a requirement or permission to stop original workloads during registration.

### Alternatives considered

- Append/prefix preservation can theoretically preserve live log history, but
  requires explicit file identity/rotation semantics, prefix and suffix evidence,
  foreign-writer handling and a new global-proof contract. It is larger and is
  not needed for the supported owned-service pause. Not selected.
- Moving one Write-Host under Reconcile is insufficient: the parent runner and
  WinSW write independently. A comprehensive new cross-writer locking protocol
  changes the installed bundle and vendor boundary. Not selected.
- Omit logs, ignore length/mtime, accept a changed global hash, normalize arbitrary
  metadata or relabel an unobserved stopped/running state: rejected.

## Tester/evidence role pass

APPLICABLE_LOCAL, not run by this reviewer:

- Actual file transport fixture appends between enumeration/open; production
  BridgeFileHash still rejects, records a private fixed file class/relative name
  and expected/opened lengths, and never claims Plan PASS.
- Running producer emits after Reconcile release; mutex-only control does not
  claim to freeze it. Stopped writer plus full file readback produces a stable
  full hash; hash/cap/reparse/unknown-file denials remain intact.
- Ownership/adoption/account/payload/transaction/dependency drift refuses before
  stop. Stop timeout, post-stop writer and unexpected restart refuse Import;
  prior Running restoration is attempted in every relevant finally path.
- Log archive readback includes current, `.old` and wrapper files; simulated
  WinSW restart replacing `.old` cannot lose the original archived history.
- Composed unchanged registration Plan/Import/Verify with Stopped service passes
  only the new paused baseline; later standalone Verify after resume fails rather
  than rewriting history. Actual coordinator receipt verification is exercised.
- Trace paused Import/Verify -> complete log archive -> resume/heartbeat ->
  binding Archive captures actual Running -> normal guest-switch QuiesceOriginal
  and EnterNew. Verify that GuestSwitch consumes identity receipts and never
  compares the stale stopped GlobalProof after resume. Failure before/after import
  restores the service; later quiesce failures retain both restoration obligations.
  Uncertain import/stop/start is observed without effect replay or deletion.

Root should run the nearest registration/bridge-binding/guest-switch/resource
fixtures on the authorized PC/WSL host, then applicable repository gates against
integrated exact source. Existing mock registration and real-file hash tests do
not prove live service quiescence or actual import. Browser/application checks
are NOT_APPLICABLE to this source-ordering prerequisite; actual listener/HTTP
checks remain APPLICABLE_LIVE for subsequent S02, not silently dropped.

Required new live evidence, currently NOT_RUN: exact pause intent/owner/source,
actual stopped service and settled writer, stable full preserve baseline,
complete private log archive/readback, attributable Plan/one Import/Verify,
new Stopped GUID/VHD receipt, original bridge Running heartbeat and payload/
rule/hosts preservation, truthful binding archive and normal guest-switch receipt
consumption. Later original quiesce/restoration belongs to that subsequent phase. Registration success does not establish
Ubuntu/Incus/bootstrap or S02 success.

## Remaining qualification and effort

Next acyclic dependencies are Import+receipt -> safe guest switch/reset/network
absence -> new machine/boot/source-bound bootstrap and pinned Incus/images/Python
-> actual WSL scoped-profile/listener/nonce-HTTP fixture -> independently accepted
paired native/WSL capability matrix. Original restoration and preserved Issue447
state are required throughout. No product acceptance case or EPIC closure follows
from W05, a registration Plan or a successful import alone.

Estimate, not a wall-clock commitment: 0.25-0.75 engineer-days for the closed
maintenance helper/order/receipt and focused regressions, plus 0.25-0.5 for its
actual qualified run/evidence if ownership and image prerequisites remain valid.
This excludes later bootstrap/S02/product cases. Confidence is medium because
live file-writer settlement and restoration have not been exercised in this
registration window. No filename-attribution probe was run: it is not required
to select this all-writer quiescence design, and another full firewall capture
would add cost without resolving the writer boundary.
