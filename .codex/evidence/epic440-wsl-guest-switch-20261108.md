# WSL closed guest-switch coordinator: source plan and authoring locks

Base ce21098c90e3d81672e2ee7637feeadbef5f0ce5. Root released SOURCE ONLY,
no tests/hosts/commits, four exclusive locks: this record,
`tools/windows/qualification/wsl_acceptance_guest_switch.ps1`,
`tests/fixtures/wsl_acceptance_guest_switch.ps1`, and
`tests/tools/test_wsl_acceptance_guest_switch.py`.

## Requirements before implementation

Implement a qualification-only closed phase coordinator, never a package/product
engine. Exact current source, signed-image registration receipt, original/new
registry GUID and VHD file-identity bindings are mandatory. Phase decisions derive
from current actual observation, never success-looking flags or saved running/PID
values. Root-owned original task driver SHA256
71d2d3c213766ebe424486acb6ec3554c08f3b22ede5c89d64fdda328dcef34a
and its df30e7d451eaea9f4b2ec4028bd40378654dee18 checkout/journals remain immutable.
Only that driver's exact two manager UUIDs may be stopped/restored.

Plan: explicit Prepare/QuiesceOriginal/EnterNew/VerifyPrepared/ReturnOriginal
phases with no automatic rollback/replay. Per-phase GO binds current proposal,
source and scenario; bridge GOs remain independently hash-bound and checked by
existing owner. Every external effect has a durable phase intent before dispatch.
Uncertain intent is recovered through actual observation; it is never resent.

QuiesceOriginal calls the unchanged original driver. EnterNew requires its actual
fresh RealPort full-snapshot comparison of all four stopped originals before
StopOriginal and again before original termination. StopOriginal is exclusively
the bridge owner's new phase under its canonical locks. Then only original is
terminated; authoritative running set must become empty before explicit root
first boot of only new. Once new is sole Running, inspect actual kernel interfaces,
routes and nft/iptables rules BEFORE package/service/network initialization.
Finite idle re-observation may prove absence; residual owners mean refusal,
never flush/delete/adoption/global WSL shutdown. Return safe-for-preparation;
fixed new-guest package/source/venv/bootstrap is a separate prerequisite, not an
arbitrary callback. Actual fresh prepared proof is required before resuming.

ReturnOriginal requires actual fresh closed new-case-owned node identities and
Stopped state, and operations settled. StageRestore exclusively stops the new
bridge and restores archived original bytes while stopped. Then only new is
terminated; authoritative running set must be empty before only original starts.
ResumeOriginal must complete actual original bridge heartbeat before unchanged
original task-driver restore restarts only its two stopped managers. Final proof
must show original full graph/config/resources/statuses unchanged; new remains
registered Stopped. Failures retain state and require explicit reconciliation.

## Persistence classification released by Root

Root approved EXACT new NativeOperational bookmark:
`CommonApplicationData/TinySwarmWorld/maintenance/acceptance-<runid>/guest-switch.json`.
Only schema/run/source/scenario hashes, registration GUID+VHD identity digests,
closed phase/action/intent names and hashed receipt references are allowed.
No raw firewall/ACL/SID/config/baseline/secrets/GO authority are persisted there.
Raw original baseline remains in original private ext4, never fetched while the
original guest is stopped. Unknown existing maintenance namespace/owner/ACL must
refuse without repair. Own new run directory uses existing exact ACL primitive;
no ServiceRoot rebinding. Existing bookmark is CAS and no-replay, not actual-state
proof. Root owns normative publication before live use.

## Known prerequisite owners and boundaries

- Root: unchanged OriginalRuntimeWindowDriver, actual node evidence, image repin,
  separate signed package/source/venv provisioning, source integration and gates.
- Architecture worker: bridge StopOriginal/Bind/StageRestore/ResumeOriginal ABI,
  truthful heartbeat, exact owned routes and archival preservation.
- Firewall/preflight worker: complete actual provider certificate and bounded
  native collector; coordinator cannot replace either with a Boolean stub.
- Registration helper: exact run-derived TSW-Q440 name, verified image receipt,
  GUID/VHD identity and stopped state. Image repin to verified official26.04.1
  is separate Root-owned work; Noble container fingerprint stays unchanged.
- This coordinator: only finite phase state, trusted wsl.exe start/terminate for
  exact registrations, actual no-overlap predicates and current guest probes.

Missing source assets, proof functions, receipts or ABI fields fail closed.
No arbitrary URL, executable, directory, command, callback or selected distro is
accepted from CLI. Dot sourcing is inert. Production entry always constructs real
ports; injected ports exist only in the fixture seam. Incus capability matrix and
product acceptance remain separate, unmodified and unclaimed.

## Frozen implementation contract

The production entry constructs only real ports. Its exact modes are Prepare,
QuiesceOriginal, EnterNew, VerifyPrepared, BindNew, ReturnOriginal,
RestoreOriginal and read-only Reconcile. ReturnOriginal yields
ORIGINAL_READY_FOR_BRIDGE_RESUME after starting only original: the caller then
collects an actual fresh ResumeOriginal proposal/GO before RestoreOriginal.
This split avoids pre-authorizing an invented future bridge proposal.

Scenario exact keys: schema_version, run_id, host, source_commit, pins,
original_machine_sha256, original_proposal_sha256, registration_scenario,
registration_state_sha256, bridge_scenario, linux_pins. The nested registration
scenario and whole original durable registration file must match. Bridge scenario
is the exact architecture-owned14-field contract with TSW-Q440 name and canonical
scalar VHD identity hashes. Source pins have an exact closed19-asset list including
all transitive Preparation imports; Linux pins name exactly the existing inventory
and provenance collectors. Native source root derives from this script, not CLI.

Coordinator GO exact keys: schema_version, decision, phase, scenario_sha256,
source_commit, proposal_sha256, expires_at_utc, evidence_sha256. Prepare proposal
hash binds actual fresh registration/running observation plus current minimal
bookmark. Before effects it is re-observed under the task mutex and compared.
Bridge GOs are independently passed to the existing owner, never replaced with
coordinator GO. StopOriginal uses the actual unchanged driver's QUIESCED receipt
hash; fresh RealPort settle/full-snapshot compare runs both before StopOriginal
and immediately before TerminateOriginal. No access to original ext4 occurs while
original is stopped. Original/new start/terminate ports recheck registration and
sole-running/no-running predicates independently. Only trusted native Windows
wsl.exe can dispatch fixed argv; source/bridge helpers are source-pinned.

Absolute monotonic per-phase limits (seconds): Prepare180, QuiesceOriginal1500,
EnterNew1800, VerifyPrepared600, BindNew960, ReturnOriginal1800,
RestoreOriginal2200, read-only Reconcile300. GO lifetime covers the entire phase
and at most300s additional. These are finite wrapper envelopes, not extensions of
existing child budgets: unchanged original driver650, original actual read proof300,
new actual proof240, bounded source proof60, WSL start/terminate30, kernel read15;
bridge owner's StopOriginal180, Bind/ResumeOriginal360, StageRestore180 remain
unchanged. Remaining budget is checked before every owned child and bridge phase;
aggregate command count256 / output8MiB are hard refusal bounds.

Fresh successful bookmark stage commits permit continuation from completed
boundaries. Uncertain intent is never replayed, including start/terminate calls
that may already have succeeded. Read-only Reconcile reports its exact pending
closed action and stage; it does not erase uncertainty or claim recovery. Explicit
owner/Root reconciliation is required for pending external effects. There is no
automatic rollback, daemon retry, adoption, forced stop or broad shutdown.

## Actual probes and separate receipt prerequisites

The image contains Python3.14 and ip, but no nft/iptables executable. The fixed
stdlib NETLINK_NETFILTER probe first requires already-present /sys/module/nf_tables
AND /sys/module/nfnetlink, so a missing subsystem cannot trigger autoload. Missing
prerequisite returns NEW_GUEST_NETWORK_PREREQUISITE_REQUIRED with new sole Running;
separate closed module/tool preparation may then run before any Incus/Docker/network
init, followed by explicit EnterNew observation resume without replaying first boot.
No prerequisite install loop or package operation is in this coordinator.

The actual probe reads bounded interfaces, IPv4/IPv6 routes, legacy table names,
TCP/UDP/UNIX listeners and fixed Incus/LXD/Docker sockets, then only an unfiltered
GETTABLE dump (AF_UNSPEC; subsystem10/operation1; REQUEST|DUMP). Only a complete
kernel-origin unfiltered dump with matching sender/port/sequence, bounded aligned
frames and successful DONE can prove no table. Any table is conservative residue;
malformed, interrupted/filtered/error/truncated/timeout observations are unknown.
Socket is always closed. Observed bytes are reduced to digests; no raw kernel or
host state is persisted in the Windows bookmark. Primary UAPI checked:

- https://www.kernel.org/doc/html/latest/userspace-api/netlink/intro.html
- https://raw.githubusercontent.com/torvalds/linux/v6.6/include/uapi/linux/netlink.h
- https://raw.githubusercontent.com/torvalds/linux/v6.6/include/uapi/linux/netfilter/nfnetlink.h
- https://raw.githubusercontent.com/torvalds/linux/v6.6/include/uapi/linux/netfilter/nf_tables.h

Separate new-guest preparation must populate fixed root-owned private directory
/root/tsw440-acceptance/<runid>/checkout (clean complete source clone) and its
.venv, then /root/tsw440-acceptance/<runid>/preparation.json (0600, regular, one link).
Its exact fields are schema_version1, run_id, source_commit,
kind NEW_GUEST_PREPARATION, package_versions (incus/incus-base/incus-client6.0.5-8),
python_version. VerifyPrepared compares its actual bytes with GO evidence hash,
rechecks clean source/blobs/no filters, actual package versions, actual mandatory
venv imports and every runtime/build locked distribution version, and actual Incus
client/server6.0.5 through trusted executable/unit/endpoint/root-API proof.
The receipt alone is never readiness. Missing producer output refuses; this worker
did not provision a guest or fabricate preparation evidence.

Separate closed product case recipe must produce
/root/tsw440-acceptance/<runid>/new-case-stop.json (same private file contract).
Exact fields: schema_version1, run_id, source_commit,
kind NEW_OWNED_NODES_STOPPED, canonical installation_id,32hex operation_id,
derived tsw-manager-<24hex> profile_name, actual full-profile SHA256, nodes map
for exactly swarm-manager/swarm-worker-1/swarm-worker-2 with distinct actual UUIDs.
Before return this is compared with actual fresh all-project inventory: only default
project, no pending operations, exactly those three instances, canonical UUIDs,
Stopped/status102, actual managed/node markers, exact profile hash/installation and
operation markers and actual manager profile attachment. This proves actual current
state, not a status Boolean from the receipt.

Root identified a reverse shared-kernel hazard: stopped nodes do not imply a clean
network. Therefore production Stopped proof ALSO requires actual kernel absence
before StageRestore and again before new termination. Only the two exact already
unit/peer/API-verified owned Incus UNIX socket paths are tolerated on that reverse
probe; foreign Incus/LXD/Docker listeners still refuse. All interfaces/routes/tables
checks remain strict. The separate preserving case recipe must already have removed
only its owned new network state; this coordinator does not detach, delete, flush
or stop a network/service to achieve that condition. If that prerequisite cannot be
proved, return is BLOCKED. Root is independently assessing an alternative all-stopped
VM-reset boundary; it is NOT implemented or authorized by this candidate, and the
current prohibition on global WSL shutdown is retained.

NativeOperational bookmark contains only the approved minimal identity/hash/phase
fields. Existing parent/namespace/file ACL or owner uncertainty refuses without
repair. Only its own absent run directory receives the canonical actor/SYSTEM/admin
DACL; only its own bounded ephemeral atomic-write temporary is removed. Existing
file uses canonical JSON validation and CAS before replacement. No bridge descriptor,
service identity variables, original journal or original approval is rewritten.
The unchanged original driver alone appends its own canonical intent/result records.

## Authored delivery checks and actual verification state

PowerShell fixture exercises actual coordinator core with fake OS boundaries:
full switch/return ordering, actual fresh old-proof sequencing, no overlap, writeahead
intent, source/registration/GUID/running drift denial, missing receipts, partial/timeout
non-replay, network prerequisite observation resume, foreign/running new-node refusal,
canonical wire/duplicate denial, GO expiry/source/scenario/proposal/evidence bindings
and bookmark mismatch. Python tests run that fixture and exercise the ACTUAL embedded
GETTABLE parser and socket-boundary logic with synthetic kernel frames, module absence
(no socket call), sender/groups/sequence/port/flags/error/truncation/timeout denial,
context closure and exact preverified return-socket allowance. No fake production
ports are selectable from CLI and no host command is invoked by the fixtures.

Worker checks: AST parsed all three embedded Python probes and Python test; Git
whitespace check only. PowerShell parse, tests, typecheck, quality gates, hosts,
imports/start/terminate/apt/bootstrap/product cases/commits are NOT_RUN by worker.
Root must independently review exact frozen4 hashes, integrate final registration
repin/certificate/bridge prerequisites, run PC parse/focused/full checks and separately
release any live phase. This source candidate is not acceptance or Epic completion.

## R2 plan recorded before edits: v1.56 cold-kernel boundary

Root released narrow R2 after committing normative39f7533f. Read the complete
v1.56 first section in issue-449/workflow.md. R1 exact4 source files are retained
privately in /tmp/epic440-wsl-guest-switch-r1; original manifest is also retained
as /tmp/epic440-wsl-guest-switch-r1-candidate-hashes.json (original SHAad714fbb...).
R1 statements forbidding any shutdown/requiring reverse empty netfilter are
historical and superseded ONLY by the explicit bounded R2 protocol below.

R2 requires exactly original+campaign registrations, no third registration even
Stopped, all registered distributions Stopped, exact existing actor/source/GUID/VHD
and actual pretermination UUID-bound quiescence. Capture the last ACTUAL kernel
boot ID in the currently already Running guest, hash it, and never wake a stopped
guest for evidence. Existing original RealPort snapshot independently proves all
four boot.autostart false/absent and last power STOPPED before cold boot.

For each direction, after that guest is terminated and all registrations Stopped,
acquire existing bridge Update→Reconcile locks, execute fresh full owner observation
and Stopped proof, recheck entire registration/empty-Running set and no unsettled
WSL/test child JIT, flush one reset intent. Invoke ONLY trusted wsl.exe --shutdown
once (60s), immediately flush command-return outcome, then verify exact empty
running/registration state within30s. No unknown/partial reset outcome is replayed.
After the next sole selected root launch, require a valid DIFFERENT actual kernel
boot ID plus registration/source/machine binding before any next transition.

Minimal bookmark adds only closed reset action identity/outcome and previous/next
boot-ID hashes. Fresh source/registration/current-runtime checks remain necessary;
bookmark flags/PIDs are not proofs. The task/bridge locks exclude controlled known
launchers only: Windows registry inspection plus shutdown is not atomic against an
outside user's/manual/automatic WSL launch. No Windows-wide lock or cross-user
visibility is claimed. Exact check-to-use limitation remains explicit.

Keep initial full kernel-absence check before packages/Incus. Return no longer
requires speculative network deletion: the case engine's truthful
OWNED_CASES_DISPOSED variant must prove actual zero case instances/root volumes/
generated profiles/no operations and source/machine/boot binding, allowing retained
network/pool/images. Then new bridgeStopped→terminateNew→allStopped reset→sole
Original changed boot→separate fresh ResumeOriginalGO→existing manager restore.
Only this fixed all-stopped reset replaces the reverse kernel-residue prerequisite;
no flush, module unload, foreign stop, unregistration or default change is added.

## R2 released implementation and frozen handoff

Current R2 supersedes only the explicitly identified historical R1 statements.
Scenario/bookmark schema is2 with explicit handoff_policy
ALL_STOPPED_COLD_KERNEL_V1; R1 scenarios/GOs cannot be reinterpreted. Nested existing
registration/bridge and coordinator GO contracts retain their own existing schema.
Bookmarked resets.new / resets.original contain exactly action,
previous_boot_sha256, next_boot_sha256, machine_sha256 and outcome
(captured/intent/command-returned/all-stopped/changed-boot). No raw boot ID or PID is
stored. Last actual original boot/machine proof is part of the existing full
quiescent RealPort probe immediately before termination. Last actual new boot/
machine proof comes from the current actual stopped/disposed proof before its
termination. Next root sole-launch reads a valid canonical actual kernel UUID,
requires its digest different, and binds original known/fresh new machine identity.
Subsequent phases also recheck the same boot/machine context before continuing.

All observations require exactly2 registrations. Initial entry compares every full
registry-row digest with the original immutable registration receipt. The admitted
complete stable registry/root-values digest is then retained only as a minimal
receipt hash: skip ONLY the transient per-distro State field, matching the frozen
bridge R3 rule. Every other registry field, root value/default, name, version,
BasePath and handle-derived VHD file identity remains bound. This lets actual
Running/Stopped state change without accepting a configuration change.

Actual reset reuses the architecture-confirmed READ-ONLY bridge port combination:
Begin Recover; canonical Update→Reconcile locks; Observe Recover (including fresh
complete preservation certificate); Stopped ResetBoundary (does not write the
bridge descriptor). It calls NO bridge Recover/Stop/Start effect. Under those
locks it rechecks complete registered-set/empty Running state and current-actor
actual WSL clients/test workers through bounded native process metadata. No PID
from a document is signalled. A separate shared pure boundary validator checks
these same required observations, exact reset action and captured context.
After final JIT check the same minimal intent is flushed again under the locks.
The single fixed trusted wsl.exe --shutdown has60s; command-return outcome is
flushed immediately; actual unchanged registration/empty Running and settled
clients are then rechecked within30s. Owner prelude must leave90 of its original
Recover300 budget (elapsed<210 before dispatch); total owner elapsed<=300 and
reset+verify<=90. Owner clocks are never restarted to multiply budget.
Uncertain/partial intent remains blocked, not automatically replayed or erased.

Finite wrapper phase envelopes now include this source/owner90s handoff boundary:
Prepare180, QuiesceOriginal1500, EnterNew2400, VerifyPrepared600, BindNew960,
ReturnOriginal2400, RestoreOriginal2200, read-only Reconcile300. Existing driver650,
actual old probe300, new proof240, source60, start/terminate30 and bridge owner's
own180/360/300 budgets are unchanged. The extra wrapper headroom includes actual
source/registry/probe/owner preconditions; it does not widen any child's effect.
GO expiry still covers the entire exact phase and at most300s additional.

Reset is not atomic against an outside manual/automatic WSL launch. Task and bridge
locks cover cooperating known launchers, not all Windows users or applications.
This is an explicit check-to-use limitation, never a claim of a global host lock
or other-user visibility. Live controller must run natively in Windows independently
of the guest it terminates. No source evidence is fetched by waking stopped guests.

The new R2 OWNED_CASES_DISPOSED variant matches the independently authored producer:
new-case-stop.json exact7 fields schema_version1,run_id,source_commit,
kind OWNED_CASES_DISPOSED,case_journal_sha256,machine_id_sha256,boot_id_sha256.
Read actual private product-case-ledger.json and compare its exact byte hash;
validate its exact schema/run/source and unique ordered subset of the closed recipe
sequence minimal,swagger-internal,swagger-published,swagger-traefik-swarm,
swagger-traefik-portainer,swagger-add-traefik,full-swarm,full-portainer. Every listed
actual outcome digest must match exactly one bounded root-owned case journal
outcome file in its fixed directory. Failed-but-disposed/recovered outcomes permit
safe return without claiming a case PASS. Actual current Incus trusted unit/local
API/client/server6.0.5 proof must then show default project only, zero instances,
zero container/VM root volumes/snapshot names, no generated tsw-manager profiles,
no operations and no known live case/test worker. Current actual machine/boot hashes
must match the receipt. Retained networks, pool and images are allowed. This is
truthful disposal, never fabricated three-node Stopped evidence. The previous
three-actual-Stopped-node proof is still strictly supported as a distinct variant.

Return's reverse empty-netfilter/socket allowance was removed: the approved
all-stopped cold-VM reset now handles the kernel boundary. Initial new guest still
requires the unchanged strict bounded kernel-absence proof BEFORE packages or
Incus/network initialization, with module-missing UNKNOWN and no autoload.

A narrow native-executable trust correction accompanies actual use: private-evidence
ACL policy must not reject legitimate TrustedInstaller-owned fixed System32 binary
leaves. Only wsl.exe/powershell.exe from the existing fixed native executable
resolver are accepted, on fixed local NTFS, no reparse ancestors, trusted system/
admin/TrustedInstaller owners and no untrusted replacement/write ACLs, plus valid
Microsoft Corporation organization Authenticode signature. No ACL is repaired.
Private evidence/namespace/file policy is unchanged. UTC GO parsing now explicitly
assumes UTC for the literal Z format, avoiding caller-local-time reinterpretation.

R2 tests extend the actual pure core fixture: exactly one reset each direction,
changed/unchanged boot, reset timeout never replayed, third Stopped registration
refusal, and the SAME production boundary validator under running/registration/
service/client/worker/intent/boot/action denial cases. Real embedded netlink-parser
and synthetic socket-boundary tests remain; no return-only parser relaxation is
retained. Author checks are Python AST for all FOUR actual embedded probes and
test (SyntaxWarning treated as error) plus Git whitespace. PowerShell parse/tests,
typecheck, hosts/effects/bootstrap/cases/commits remain NOT_RUN by this worker.
Root owns exact independent review, PC gates and separately approved live phases.

## R3: independent P1 correction — disposal-only ReturnOriginal

Independent Store review of exact R2 manifest51b0eef8 identified one P1: historical
NEW_OWNED_NODES_STOPPED fallback still allowed return with three existing nodes.
Root authorized only this narrow correction. R2 exact4 source bytes are retained
privately in /tmp/epic440-wsl-guest-switch-r2, alongside the unchanged named R2
manifest; its previous supporting-variant statement is historical and superseded.

ReturnOriginal and its production NewProof consumer now accept ONLY
OWNED_CASES_DISPOSED. The entire three-existing-Stopped-node branch is removed.
The exact seven-field disposed receipt, actual private case ledger and ordered
closed eight-recipe subset, referenced outcome files, actual zero instances/root
volumes/generated profiles/no operations and current machine/boot/source proofs
remain mandatory. v1.56 reset, owner locks, all other phases and existing limits
are unchanged. No stopped-only receipt is relabelled or synthesized as disposal.

The actual core fixture supplies the old NEW_OWNED_NODES_STOPPED result at the
ReturnOriginal seam and asserts BLOCKED while stage stays bound, no pending
intent, no extra bridge/guest/reset effect and new remains sole Running. Existing
full successful flow continues to exercise truthful OWNED_CASES_DISPOSED.

Worker checks remain source-only AST of actual embedded probes/Python test with
SyntaxWarning as error, exact historical R2 hash verification and whitespace.
No PowerShell parse, tests, hosts, commits or live acceptance were executed.
Independent Root review and exact PC gates remain required.

## Root serial v1.57 original-runtime source repin

The historical71d2/df30 driver stays immutable. The NEW92b4a45ccb2838f52b8f3b16428386ae15a5c2f412ce29e0e003ab41bc38abe7
driver uses sourcea81456f0e46dede2e717df899daf19cf9486d4b3 and private
root`/root/tsw440-wsl-r4-20261108`; only SOURCE/ROOT/reader pin changed. Root
serially repins the three exact adapter invocation paths and two source hashes.
No driver control flow, scenario authority, budgets or target identities changed.
Independent Store source delta review passed; exact14 fake tests are rerun on PC
before deployment. This is not a quiescence/restore result or host GO.

Root PC R4 nearest gate caught the PowerShell builtin Copy alias taking
precedence over the fixture's Copy function. Root R5 gives only the fixture
clone helper a unique name; production handoff behavior is unchanged. The
failed R4 log remains historical, not a host result.

## Root PC integration verification

GuestSwitch R5 (R3 disposed-only policy + v1.57 fixed driver repin + unique
fixture clone helper), PC SSH/WSL `epic440-guest-switch-20261108-r5`,basea81456f0:
5 focused tests PASS11.272s,type979 PASS,all7 quality PASS,3637 tests,36 skips,
268.277s. Full quality log SHA256
`3609d6cc22bb2c3179b6ec066c622a30d8c4cc3077ba000ec3bde2ad2b0b6274`.
The versioned original driver passed14 unchanged fake contracts on PC/WSL
0.400s; logSHA`6aa3c8aed855b0538ede8a17382dee00daeb70b64002be34b847caece08fe282`.
Store independently reviewed disposed-only and literal3-change driver source.
Actual registrations/guest switch/VM reset/bridge phases remain NOT_RUN.
The actual new-driver read-only prepare refused before runtime effects and
needs diagnosis; neither the old nor new proposal grants live authority here.
