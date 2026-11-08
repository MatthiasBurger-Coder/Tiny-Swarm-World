# Preserving WSL acceptance bridge binding: design before implementation

Status: DESIGN_ONLY, submitted for independent Root review. Inspected base:
`10aa0a57ec92f3b4341c25ac41dda701cf652fc5`. No new production/test code,
PowerShell execution, host observation, service action or commit in this agent.
The accepted preserving-product-acceptance ADR and renewed user instruction
authorize source engineering; they do not make this unimplemented transaction
or a future guest switch qualified.

The Three Amigos requirement gatekeeper skill was applied as requirement,
architecture, automation and tester role passes by this one author. Root's
independent design/code review and actual PC gates remain separate.

## Requirements and actual delivered path

| ID | Required outcome | Existing production owner / source fact | Planned evidence / state |
|---|---|---|---|
| WB01 | Preserve original registration/VHD/nodes and service identity | Coordinator owns guest handoff; this module never imports, terminates, unregisters or selects a default distro | Exact registry GUID/VHD identity and authoritative Running set per phase; OPEN |
| WB02 | Change only binding of already owned protected service | `Get-BridgeServiceOwnership`, canonical ACL, account/SID, XML, pinned WinSW and bundle guards | Before/after complete identity; refuse absent/adoption/migration/legacy task; OPEN |
| WB03 | Restore exact original payload even after transaction completion | `Complete-BridgePayloadTransaction` deletes staging AND rollback | Independent immutable original archive before Bind; OPEN |
| WB04 | Use real transaction and heartbeat | Existing New/Write/Switch/Protect/Start/Wait/Complete payload primitives | Actual generated heartbeat, exact bundle ID and fresh timestamp; OPEN |
| WB05 | Keep existing routes, foreign firewall/hosts untouched | Existing reconcile has exact previous-state tuple authority; noncanonical firewall/hosts must block | Full all-family PortProxy registry + netsh bijection, complete firewall snapshot, raw hosts identity; OPEN |
| WB06 | Admit existing-route exposure to new guest | Old wildcard forwards can expose fresh guest even without a tuple addition | Exact union exposure in each GO; no new product routes in this module; OPEN |
| WB07 | Remain recoverable across guest switch/controller loss | Old active ext4 may be unavailable while original guest is stopped | Protected native operational archive/descriptor; workflow GOs remain ext4 or in RAM; OPEN |
| WB08 | Respect shared-kernel/network handoff | Stopped/no Running does not prove kernel interface absence | Coordinator owns actual network absence before Incus init; never inferred here; OPEN |
| WB09 | Bounded no-replay recovery | Existing payload journal records individual Active/Backup/Staged move intent | Explicit fixed-phase recovery; unknown active bytes/partial tuple state refused; OPEN |
| WB10 | No new account/right/policy/service installation | High install can create service or migrate ACLs; these branches are outside scope | Neither registration nor rights/runtime-policy helpers called; OPEN |

## Source findings that determine ordering

`Get-BridgeDiscovery` checks PortProxy, firewall, hosts and owned running service.
It does NOT test a manager, Incus API, TCP backend or application login.
`Write-StateFile` derives `agentStatus=ready` from those routing checks.
`Wait-BridgeServiceHeartbeat` requires a later generated timestamp, service agent
mode, ready status, expected bundle ID and protected config/registry paths.
`Get-WslIp` obtains only the selected guest's address with `hostname -I`.
Consequently a genuine fresh routing heartbeat can be produced after the new
registration is the sole Running guest and has an observed address, BEFORE
Incus initialization or a product manager exists. It is never evidence of
application readiness. Backend endpoint/login remain UNVERIFIED.

The new module must prove the selected registration is already Running before
letting the existing hostname observation execute: it must not wake a stopped
original/new guest just to obtain an address, evidence or heartbeat.

`New-BridgeInstallationManifestText` contains contractVersion, serviceName,
accountSid/serviceAccount, pinned wrapperSha256, the two logon-right provenance
Booleans and installedAt. At this inspected source it contains NO bundleId,
config hash or source hash. `Get-BridgeServiceOwnership` validates those account,
wrapper/provenance fields and the canonical registration/ACL/XML separately;
`Get-BridgeBundleIdentity` independently validates the bundle manifest hashes
and derived bundle ID. Thus keeping the original installation manifest exact
does not falsely assert the new bundle identity. Unknown manifest fields or a
future relation require explicit source-contract review, not silent omission.

Calling high-level `Install-BridgeService` directly would copy current source
scripts and regenerate XML/installation-manifest, potentially exceeding an
exact distro-only binding. Both directions instead use its SAME transaction
primitives with an exact clone of the original payload, as Root requested.
No generic alternative mover/installer is introduced.

## Closed source scope and authority

Proposed four locks only:

1. `tools/windows/qualification/wsl_acceptance_bridge_binding.ps1`.
2. `tests/tools/test_wsl_acceptance_bridge_binding.py`.
3. `tests/fixtures/wsl_acceptance_bridge_binding.ps1`.
4. This evidence/design record, later appended with exact authored pins.

No existing bridge, shared firewall asset, controller, product configuration,
service registration or capability file is edited. In particular the mutable
shared Windows firewall snapshot implementation is not copied or hardcoded.
Production loads the eventual committed source-bound asset with its exact
reviewed hash; a missing/mismatched asset blocks. Tests use the same loader and
real helper bodies, with transport-only replacement of SCM/WSL/registry/netsh
and firewall observations. Dot sourcing the new module performs no host action.
The executable path constructs fixed production ports, never caller callbacks.

The typed scenario binds source/pins, physical Windows host and actor identity,
original and new names/GUIDs/VHD identities, original active payload and bundle
fingerprints, exact mappings/hosts/service policy, declared exposure union,
run ID and recovery descriptor. Paths are derived from the canonical protected
root and run ID, not arbitrary input. Duplicate/unknown keys and noncanonical
wire representations are rejected before effects; canonical round-trip
comparison can reject duplicate JSON properties without another JSON engine.
Raw GO bytes are hash-bound. Each phase binds an actual before-proposal hash,
exact effect set and five role decisions with finite expiry. No old resource
GO or stale heartbeat is reused.

## Archive and native operational recovery classification

Before Bind, archive the exact active bundle tree, pinned wrapper, exact XML and
installation-manifest into a separate canonical-ACL-protected
`.staging-acceptance-<runid>-original` directory below the existing ServiceRoot.
The archive is not a transaction RollbackRoot and cannot be removed by Complete.
Record every relative member/hash/size, original payload fingerprints and ACL
identity; reject reparse points, missing/extra files, noncanonical ACLs and
unrecognized layouts. Limit files/count/total bytes before copying. Flush and
verify the exact archive readback before any active payload effect. Preserve
the archive and a minimal operational phase/move descriptor after success.
Neither logs nor unrelated ProgramData files are archived or exported.

This is a narrow NEW native product-recovery artifact classification, not a
claim that the existing W05-only exception already names these files. Root must
record the specific bridge archive/descriptor boundary in the operative
workflow/context before code/live acceptance. Raw payload, ACL/SID and archive
metadata stay exclusively in the protected Windows operational store. They
are not workflow approvals, are not exported as evidence and grant no mutation
authority. Canonical GO/review/result records remain private ext4; a source-bound
coordinator may pass already loaded, hash-checked GO bytes in RAM. No stopped
guest may be auto-started merely to read authority. The same procedure works
with phase evidence in the currently selected already Running guest or the
independent review checkout, avoiding an evidence/guest-start cycle.

## Exact phase protocol

Prepare is read-only apart from separately admitted source-owned private result
storage. It requires canonical fully owned existing service, no pending payload
transaction, no legacy task, no adoption/ACL migration, preserved account/right
provenance, known complete original bundle, no dependent service that could be
stopped by the existing Stop helper, and complete route/firewall/hosts snapshot.
Original/new registration identities and new Stopped state are captured. No
archive or service stop is inferred authorized by a mere Prepare.

Archive requires its explicit source/host/proposal GO. Under ServiceUpdate then
Reconcile mutexes, recheck original active fingerprints and snapshots, write
durable operational intent, copy/verify original payload into the independent
archive and release locks. It creates only the exact protected native archive
and descriptor. The original service may still run; payload files must match
before/after. Runtime heartbeat drift is not mistaken for payload identity.

The COORDINATOR then quiesces the exact original guest nodes, stops the owned
bridge BEFORE terminating original, proves only original Running, terminates
ONLY original, proves none Running, starts ONLY new, and proves actual shared
kernel/network absence before initializing its Incus. None of those guest
effects belongs to this binding module. Ordering can Bind immediately after
the new guest has its real address, before manager creation: no heartbeat cycle.

Bind requires the existing service Stopped and new registration sole Running;
original must be Stopped. Its actual fresh address and admitted exposure union
are bound. Clone the verified archive into a fresh canonical `.staging-*`
payload. Retain scripts/runner/ports/XML/wrapper/installation-manifest exactly.
Change ONLY config.distro, require all other parsed config properties identical,
and derive only the config hash and bundle ID/hash manifest through the existing
bundle helpers. An explicitly allowed `auto` original binding is restored as
those exact bytes, never replaced by a guessed original distro config.

Construct `StagedPayload` with Root, Bundle, Wrapper, Definition,
InstallationManifest and BundleId, and call `Test-BridgeStagedPayload`.
Create the existing `New-BridgePayloadTransaction` with service/root existing,
serviceWasRunning=false and actual previous bundle ID. Persist its journal.
Under the normal mutex order, recheck complete active/staged/archive identities,
registration and route snapshots, invoke the existing checked Stop and Switch,
then Protect. Release Reconcile before Start so real service reconcile can take
its own mutex. Start the SAME registration, require actual fresh ready heartbeat
for the new bundle and actual address, exact sole-new registration, preserved
account/startup/XML/right/ACL identities and unchanged foreign firewall/hosts.
Complete only after all readbacks. The independent original archive remains.

Only the existing owned v4tov4 destination address may follow the selected new
guest. Listen address/port, protocol, connect port, rule identity and all other
family tuples stay exact. Reconciliation's delete/add behavior is explicitly
accounted as a possible uncertain intermediate state, not presented as atomic
netsh set. Service refresh must already have exactly canonical firewall/hosts,
so it has no permission to create/remove/repair them. Additional product routes
remain a separate exact product-route transaction/GO; no route builder is hidden
in this module. The exposure GO includes ALL existing forwards that may now
reach the guest even when no tuple changes.

StageRestore requires product workers settled and all exact new owned guest
nodes stopped by the coordinator. Stop the NEW-bound bridge before terminating
new. Clone the immutable original archive into another StagedPayload, with its
exact original BundleId and exact original installation-manifest. Use the same
New/Write/Switch/Protect primitives against the known current binding while
keeping the service Stopped. Do not regenerate XML or installation-manifest.
Keep the restore transaction pending until original heartbeat succeeds.

The coordinator terminates ONLY new, proves no Running registrations, then
starts ONLY original. ResumeOriginal requires authoritative original-only
Running and exact original GUID/VHD, restored original payload identities and
fresh observed original address. Release Reconcile, start the same service,
require a later real heartbeat for the ORIGINAL bundle plus exact routing
readback. Only old owned destination addresses may follow that fresh original
IP. Complete the restore transaction, preserve archive/descriptor, then the
coordinator restores only its original two Running managers and verifies its
full original preserve graph. New registration remains Stopped and retained.

Failure/explicit Recover never registers/unregisters a service or guest,
changes account/right/startup policy, downloads a wrapper, performs global WSL
shutdown, creates routes or starts an unproven guest. Existing journal move
intent is reconciled against exact Active/Backup/Staged fingerprints. Missing
required members/unknown active bytes/uncertain route state remain
RECOVERY_REQUIRED. Payload may be restored while service stays Stopped. Do not
call generic interrupted recovery that could automatically start old binding
while the fresh guest runs. ResumeOriginal remains a separately gated phase.

## Bounds and test matrix

Each phase has a fresh monotonic aggregate: Prepare180s, Archive180s, Bind300s,
StageRestore180s, ResumeOriginal180s; explicit recovery300s independently.
Use existing finite mutex waits, service start/stop30s and heartbeat45s within
those aggregates; fixed child probes at most15s, owned child-tree settlement
reserve10s. An exhausted phase cannot continue effects or borrow another GO.
Cap command count256, aggregate output64MiB, per stream2MiB, scenario/GO64KiB,
archive4096 members/32MiB, and reject larger layouts before a payload stop.
No uncertain effect is automatically retried. A following explicit recovery
re-observes, while locks are released only after owned workers settle.

Tests must exercise real transaction helpers and real protected temporary
payload trees through Windows PowerShell on Root's SSH test host. Include exact
original/new/original bytes and installation-manifest equality; bundleId/config
digest correctness; actual helper-generated heartbeat positive and stale/wrong
bundle/missing heartbeat negatives; existing original archive survives Complete;
failure after each item move; interrupted journal recovery; unknown active or
archive bytes refused; no credential/right/registration/policy calls; foreign
route/all-family registry/firewall/hosts drift refusal; only owned IP delta;
wrong/new GUID/VHD, original/new/both/third/no Running phases; new-manager absent
with genuine routing heartbeat; stale/incorrect app readiness never claimed;
mutex release before heartbeat; process budget expiry and worker settlement;
legacy task/dependent service/ACL/reparse/source/hash/unknown-JSON negatives.

This is READY_FOR_ROOT_DESIGN_REVIEW, not code GO, not independent source GO,
not an executed test matrix and not permission for one service/guest effect.
Implementation estimate1–2 engineer-days including real-helper fixtures and PC
failure correction; actual staging/source gate/live windows are additional and
depend on the separate fresh-guest coordinator and eventual firewall asset.

## Authored candidate: 2026-11-08 (not executed)

The approved design above is historical. Root subsequently approved the following
concrete ABI refinements before implementation; they supersede its preliminary
phase names, timeout estimates and generic testing description.

- Exact registration name: `TSW-Q440-<run_id>`, matching the frozen registration
  helper. Both VHD identity hashes encode that helper's `vhd_identity` string;
  running VHD contents are never hashed. Global registration metadata (excluding
  runtime `State`), GUIDs, DWord WSL2 versions and unique names remain bound.
- `Prepare -PrepareFor Archive|StopOriginal|Bind|StageRestore|ResumeOriginal|Recover`
  produces an actual proposal for that phase with no locks or mutation. The
  executable takes canonical JSON/Base64 scenario and GO with independent raw
  hashes. Scenario/source/host and actual locked before-proposal are checked.
- New `StopOriginal` is the narrow coordinator boundary: existing ownership,
  full preservation observation, durable intent, Update then Reconcile locks,
  checked stop of the owned service with no dependent services. Its GO includes
  `guest_quiesce_sha256`; the coordinator independently verifies that actual
  receipt before issuing this GO. The digest is not independently a guest probe.
  `StageRestore` similarly requires the actual new-guest quiesce receipt.
- Prepare/Archive/StopOriginal/StageRestore cap 180s; Bind/ResumeOriginal cap
  360s; explicit Recover cap 300s. The same complete fresh firewall query has a
  120s child cap at each checkpoint. Bind/Resume reserve both complete queries,
  service start, real 45s heartbeat and cleanup; insufficient remaining time
  refuses before active payload change/start. Recovery stages only Stopped
  original payload; it never starts a service or guest.
- Certificate dependency: isolated full dot-source of the committed controller,
  parameterless `Get-WslMaintenanceFirewallCertificateCommand` and strict
  `ConvertFrom-WslMaintenanceFirewallCertificate`. The exact eight-key v1 DTO
  binds the source query, complete snapshot SHA/bytes, ActiveStore, schema2,
  provider-identity association model and all counts. No raw snapshot fallback,
  truncated hash, incomplete provider query or cross-checkpoint reuse exists.
  The inspected base lacks this new producer/loader; executable admission must
  fail until Root integrates and qualifies those separately authored assets.
- Existing bridge installation manifest has no bundle/config hash relation;
  its exact bytes, wrapper and XML stay unchanged. Only cloned config `distro`
  and its derived bundle manifest/ID change. Whole active/archive/staged member
  hashes and exact transaction paths bind CAS and recovery. Original archive
  survives normal transaction cleanup. Archive/staged files and native descriptor
  are flushed; all use canonical protected bridge ACLs.
- Original config `auto`/empty is accepted only when Windows default-distribution
  GUID is the bound original GUID. No global default setting changes. Recover
  permits zero or one of the two known Running registrations, never both or a
  foreign Running registration. Resume requires original sole Running, and Bind
  requires new sole Running; bounded address observation rechecks that set.
- Partial payload recovery uses the existing recovery ownership proof, exact
  native transaction journal and observed known-member fingerprints. Missing
  required member backups refuse before the existing wrapper-download fallback.
  No service creation, account/right/policy change, route creation capability,
  automatic original service start, guest lifecycle command or host adoption.

Production statuses are `PREPARED_READ_ONLY`, `ORIGINAL_ARCHIVED`,
`ORIGINAL_BRIDGE_STOPPED`, `NEW_BINDING_READY`,
`ORIGINAL_PAYLOAD_STAGED_STOPPED`, `ORIGINAL_BINDING_RESTORED`,
`RECOVERED_STOPPED`. All report `application_ready=false`. Failed phases retain
native intent/journal and a redacted symbolic error; no application readiness or
complete recovery is inferred from a routing heartbeat.

### Authored verification and its limits

The Python wrapper invokes a new PowerShell fixture on Root's approved PC.
Authored cases cover canonical wire/registration denial, exact certificate
schema/count/hash bounds, all six phases, actual proposal CAS, lock ordering,
quiesce receipt/expiry, failure at each active phase, and no automatic service
restart during recovery. Host ports in these phase tests are synthetic.

Separate fixture sections invoke the **actual existing** New/Write/Switch/
Restore/Complete payload primitives on new disposable files, including exact
original restoration, independent archive survival after both commit and
rollback cleanup, and foreign active-byte refusal. The ACL boundary alone is
replaced for those disposable test files; no SCM, WSL, registry or firewall
operation occurs. The actual heartbeat validator receives explicitly synthetic
fixture JSON and rejects stale timestamp/wrong bundle/status/path; this tests
validation only, not a genuine service heartbeat. Production adapter/source/
certificate integration and actual native ACL/SCM behavior are NOT qualified by
these unit fixtures. The earlier design paragraph describing transport-only
full-adapter tests is therefore a planned later evidence requirement, not a
claim that such tests ran or are included here.

Author checks: Python test AST parse and `git diff --check` only. No PowerShell
parse/execution, Python test execution, production import, PC/host operation,
commit or live qualification occurred. No tests or host readiness claimed.
Root independent source review, exact integrated dependency pins, PC focused/
full gates and phase-specific actual source/host GOs remain mandatory.

### R2: actual firewall command transport correction

Independent Root/preflight review found a concrete pre-execution defect in R1:
shared producer command length 22,397 characters becomes 59,728 characters with
UTF16 Base64, exceeding Windows CreateProcess's 32,767-character command-line
limit. R1 was not executed or qualified. The certificate child now uses the
same trusted plain `-Command` transport as other shared consumers, with the
complete hash-verified command as one final argument and `UseShellExecute=false`.
A pure production argument builder applies Windows native quoting and rejects
NUL or a final executable+quoted-arguments+separator+terminator length greater
than 32,767 before starting any child. There is no shell interpolation, shorter
alternate query, source truncation or fallback to raw firewall output.

The fixture now obtains the actual producer command from the separately
integrated source-pinned loader, without running its firewall query. It checks
the exact returned source string, actual native command construction, native
Windows CommandLineToArgvW round-trip, old Base64 overflow, exact last permitted
command-line length and first rejected length, quote-expansion overflow, and NUL
refusal. A tiny fake command cannot satisfy the actual-producer regression.
These construction tests require the real new shared loader/producer dependency;
missing assets fail, rather than skipping or substituting synthetic payload.

R2 author checks remain Python AST parse and whitespace/diff only. No production
import, PowerShell parse/execution, tests, hosts or commit. Independent review
and PC gates remain pending; no phase or live capability GO is implied.

### R3: immediate pre-start active-payload CAS

Independent preflight review found that R2 rechecked registrations and sole
Running guest before StartService but left active payload identity to the later
final observation. An outside payload/config writer could therefore cause the
service to use changed or auto-original binding before that final refusal.

`StartOwned` now reads actual protected payload plus native descriptor immediately
before SCM start. Its production guard requires Stopped, exact full member hash
map (`bound_hashes` for Bind, `archive_hashes` for ResumeOriginal), unchanged
service policy and full registration digest, sole correct Running guest, and
exact effective distro. Original config is additionally equal to the archived
config; auto/empty original binding requires the exact original default GUID.
The Running probe returns ordinary pipeline strings for callers' explicit array
capture, so zero/one/multiple cardinality is preserved without a nested array.
No stop/start retry, original wake-up or payload repair is added.

The new test extracts the actual nested StartOwned definition from the source
AST and executes that exact body in an isolated module with only observation and
SCM transports replaced. It proves positive new/original-auto paths and zero
SCM start calls for changed active member, status, config, policy, registration,
Running guest and auto-default GUID. This is a production-body unit regression,
not a full native adapter or live service qualification. Python wrapper minimum
case count includes these new cases. Author checks remain AST/whitespace only;
all actual test execution remains Root's pending PC responsibility.

## Root integration verification

PC SSH/WSL `epic440-bridge-20261108-r1`, base176e38e7 with exact shared
certificate18 R2 paths and bridge4 R3: nearest real PowerShell fixture PASS
(1 Python test,7.868s), typecheck978 PASS; all seven quality gates PASS,
3619 tests/36 skipped/264.238s. Full quality log SHA256
`f1e6582246a8cf850d256687ede871bea42973533d9653ec45d48cf034c5efc0`.
Independent reviewer preflight_review confirmed both P1 full command transport
and P2 immediate active-payload CAS fixes. Actual host bridge phases, real SCM
mutation and actual heartbeat remain NOT_RUN; no scenario GO is granted here.
