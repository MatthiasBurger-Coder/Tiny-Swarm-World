# S449-02G — preserving native maintenance controller

Status: ROOT_SOURCE_REVIEWED_PC_WSL_ALL_SEVEN_QUALITY_PASS; NATIVE_HOST_PHASE_NOT_RUN.
Base 9a81972cd722a759ccd4d7118fe5eec833bf075e; isolated worktree
/home/micro/tsw440-native-maintenance. Root authorized this implementation after
its practical plan and the preserving-maintenance ADR/workflow decision review.
Root integrates accepted v1.49 policy separately. This record grants no host GO.

The initial three-file/schema5/final-GO notes below are historical checkpoints.
The final bootstrap amendment at the end supersedes those specific claims;
no earlier test result qualifies the amended bytes.

## Scope and traceability

| ID | Requirement | Concrete implementation | Verification state |
| --- | --- | --- | --- |
| N1 | Maintenance permission distinct from adoption | Exact three default-project node names, Snap service/socket; no create/delete/config/profile/pool/network operation | Tests authored, NOT_RUN |
| N2 | Fresh exact source/host/scenario binding | prepare proposal; strict current approval with expiry/reviews/source pins/host machine identity/fixture GO; pre-effect re-observation | Tests authored, NOT_RUN |
| N3 | No systemd force escalation | Graceful no-force node stop, optional socket stop, verified Snap shutdown; never systemctl stop live daemon | Fixed argv and failure tests authored |
| N4 | Always restore prior runtime state | Independent recovery reserve, intent-before-effect, original Running-only starts, original socket state, explicit recover mode | Failure/interruption/idempotence tests authored |
| N5 | Existing resource preservation | Validated full schema5 before/after, immutable instance UUID/config identity, configuration metadata hashes, complete Incus projections/units | Drift/canary projection tests authored |
| N6 | Fixed qualification window and honest result | Existing fixed listener-fixture CLI/GO/result; no arbitrary callback/command argument; PASS requires fixture and recovery | Source review pending |

Only three locks are changed: tools/linux/qualification/native_lxd_maintenance.py,
tests/tools/test_native_lxd_maintenance.py and this record. No existing collector,
provenance helper, fixture, policy or application behavior is edited here.

## Concrete staged protocol

The CLI supports prepare, execute and recover, with a validated 32-hex run ID.
The evidence parent is the existing fixed owner-only issue449 ext4 directory;
proposal, approval, started intent and unique events/results stay private0600.
Prepare is read-only with respect to runtime/host configuration: it creates only
its fresh private evidence directory/proposal after source and fixture-GO checks.
It does not acquire/create the host mutation lock or run the fixture.

Execute/recover require an exact expected approval SHA256; a closed approval
binds proposal/source pins/host ID/fixture GO and all five reviewer decisions,
with a fresh finite expiry. Validate before even creating the host lock, then
recheck under that lock. The singleton private /run host lock serializes distinct
root checkouts. Existing or unsafe lock paths are never repaired or unlinked.
Execute creates an exclusive durable started record; a second execute refuses.
Recovery uses the same immutable proposal and a newly fresh current approval;
it cannot run a fixture or reconstruct missing prestate from current selection.

The adapter checks the same complete existing collector/Snap provenance before
client operations. Shutdown additionally binds the actual readonly numeric Snap
revision, strict app command commands/lxd with no command-chain, script/metadata
hashes and paired process-root/host descriptors; bin/lxd authority uses its
root-owned readonly descriptor identity rather than pretending to hash its data.
Any lxd.debug file blocks. Fixed root unit/drop-in contents and closed known
ExecStop/Restart/timeout/KillMode/SendSIGKILL semantics are bound. The initial
LXD MainPID is stable until the controller enters recovery; a restarted daemon
must pass full package/process proof before any instance recovery.

Preserve a socket already inactive/dead. For an active socket, stop it before
graceful daemon shutdown. The only node effects are no-force stop/start of the
three exact names on the fixed local Snap endpoint/default project. Node identity
includes the actual immutable UUID, creation/type/profiles and stable config/
device metadata. Stop workers before manager; restore manager before workers.
The only daemon shutdown invocation is /snap/bin/lxd shutdown --timeout 60,
with controlled environment and no LXD_DIR override. No live-daemon systemctl
stop, masking, disabling, package action, force option, host reboot or object
replacement is present. Owned subprocess cleanup signals are not daemon signals.

Qualification uses only the existing fixed Python listener-fixture file and its
existing validated GO; the fixed result must already be reserved NOT_RUN before
maintenance. Recheck source binding before spawning that child and require its
actual PASS result/digest. On its deadline, signal only the owned child tree with
SIGINT and give a finite 120-second cleanup reserve before owned-client teardown;
any deadline remains failed qualification even if cleanup completes. The fixture
retains its own cleanup protocol; residual objects fail final preservation.

Every normal/error/interruption path enters recovery. A separate 600-second
recovery budget cannot be exhausted by the qualification phase's 1200-second
budget; client/process/proof/output bounds remain finite. Read back uncertain
outcomes; do not replay commands blindly. No start for an originally Stopped
instance. If the daemon is already active, no extra start is sent. Restore socket
runtime state only if needed. Compare complete normalized configuration/consumer
identities and states after full source-bound schema5 recapture; unchanged Incus
unit PIDs/state and LXD unit enablement are included. Recovery failure is explicit
RECOVERY_REQUIRED, never PASS, and no automatic deletion fallback exists.

Additional configuration projections hash full stable returned metadata, omit
only separately canonicalized used_by and instance operational status/last-use
fields. Instance runtime volatile keys are excluded except volatile.uuid and
volatile.uuid.generation; user settings and full local/expanded devices remain.
No raw config/description/UUID values are persisted by this projection. These
hashes are private identity evidence, not confidentiality. Guest filesystem
contents naturally change during orderly shutdown/start; API comparisons do not
claim bitwise disk-data equality or historical instance safety.

## Authored verification and actual state

Tests cover successful inactive/active socket restoration; mixed original states;
each before/after uncertain stop/shutdown failure; fixture refusal/interruption;
reactivation; Incus drift; failed/resumed/idempotent recovery; no effects before
prestate/intent/approval admission; exact no-force/fixed endpoint argv; expired/
wrong source/host/fixture/reviews; strict prestate names; exclusive durable private
journal IO and symlink refusal; real cross-process host-lock contention; stable
configuration projection and immutable UUID retention.

Worker performed AST syntax parsing only (no imports/execution) and
`git diff --check`, both PASS. Tests, typecheck and full quality NOT_RUN. No host,
service, node, fixture, data, package, Windows or network action; no commit or
publication. Root owns independent source review, exact-source PC WSL gates,
policy/source integration, committed-source execution/fixture GO and all live
observations. These mocked tests do not qualify Incus support or complete S02.

Frozen candidate SHA256:

- controller 100a9ae4c8c7304ff99416070842f4dffcff1245086fc04fa9eb78d813badf6f
- tests bc939d823d7157de2e5db3b8e9f46c03deb5d0c1fc1bf12cc58a2d1b0f19c71d


## Root static review corrections before PC verification

Root independently identified two concurrency gaps before any test or host run.
The first candidate accepted a Running/Stopped state different from baseline
before first acting on a node; recovery could then overwrite operator intent.
The controller now requires exact baseline status before its first stop attempt
and restores only nodes with a durable own stop intent. Recovery continues for
other own nodes even when a foreign/drifted node cannot be restored, then reports
RECOVERY_REQUIRED without changing the foreign node. A fresh controller obtains
the same finite stop-intent set from private event files rather than guessing.

Root also required a complete recapture after the three graceful node stops and
before socket/global daemon shutdown. That full source-bound snapshot must equal
baseline with only the three intended instance status changes to Stopped; no
resource/config/consumer/Incus objects are ignored or filtered. A fourth instance,
new project or other preserve-set drift blocks global shutdown and qualification;
finally restores only this transaction's own node stops. This is a final checked
precondition, not an atomic guarantee against uncooperative external writers.

Regression tests now cover both concurrent state-change directions, late fourth
node/project/resource/Incus changes, durable new-controller recovery and raw
secret canary exclusion from captured configuration hash evidence.
Source and tests remain unexecuted; AST parsing and diff check only.

Superseding frozen SHA256:

- controller 46103eab22cdb6a8d59b26ad462985dd57201075f952d5c07ce29b4edbb1f34c
- tests 86558fd8893e5e3bcbe2e2acc956c43f1556a90fed130edcf2d9474047838e86

## PC r1 typecheck failure and typing-only correction

Root reports exact PC native-r1 nearest typecheck failed with 16 errors in the
two new files: six standalone-import/no-redefinition diagnostics, six Optional
baseline arguments after existing require guards, and four mixed fixture
inference/annotation diagnostics. Focused/full quality NOT_RUN. Failed private
log SHA256 a47fb208864cd31ab0ccf47cefcedfdc245164f9f263da7dfdb3db5b77a6a4cd
is retained on PC; an initial root fetch timed out, then root read the PTY error
log successfully. No test or quality success follows from that failed attempt.

Correction supplies TYPE_CHECKING relative imports and equivalent importlib
runtime imports for the same package/standalone module names. Six casts follow
the unchanged existing baseline guards; no guard is removed or weakened. Test
proposal/raw maps and the unchanged malformed-map tuple gain explicit types.
No literal, assertion, effect, command, budget or recovery behavior changes.

Superseding frozen SHA256:

- controller 2a7460f6daa9406e3bd24eb0ec1eb9a2db080807be72cb75e57d6d84cb181911
- tests d2ce9c6937606d6552fb1952277a1625ddc968abb7d15bdbfc6d3548adb4d873

Worker AST syntax parse and diff checks PASS only; no worker imports, tests,
hosts or commits. Independent delta review and fresh root PC gates remain.

## Initial stopped-node restart admission correction

Root identified a preservation gap after the earlier PC verification: daemon
restart can autostart a previously stopped node. The controller now checks the
validated raw Instance configuration during initial snapshot preparation and
again on each read of a node whose admitted baseline was stopped. It accepts
expanded boot.autostart exactly `false`, or missing/empty boot.autostart with
missing or `STOPPED` volatile.last_state.power. Other cases fail closed
with STOPPED_NODE_AUTOSTART_UNSAFE before maintenance admission/effects; no
configuration is changed. An originally running node stopped by this transaction
is exempt from this initial-stopped policy, preserving normal recovery.

Tests cover explicit/implicit autostart rejection, safe stopped configurations,
actual adapter reads during preparation and revalidation, and the originally
running/own-stop case. Existing command, approval, snapshot and recovery guards
remain. Root reports the previous native candidate passed PC checks; that result
is historical for these changed bytes. New source/test execution remains pending.
Worker AST parsing and diff check PASS only; no worker tests, imports or hosts.
An attempted `python` syntax command was unavailable; the syntax-only check was
then completed using python3, without importing or executing product code.

Superseding frozen SHA256:

- controller 8b944d7d691c45f077a2f8713c9a29b6b2687c505fb6365882e50e28a060bb29
- tests 54a677ed9d1b1e4eef093ec6f57936dd46de339604ab02a2c259dee8af71eb35

## Root-authorized concrete S02 bootstrap correction

Root explicitly authorized the image-aware preserve inventory, actual read-only
resource/route adapters and bounded PAUSED_ADMISSION_PENDING implementation.
The exact normative delta is the accompanying
`epic440-native-bootstrap-contract-20261107.md`; it supersedes the initial
three-file-only scope, schema5-only preservation and final-GO-before-pause
requirement, without changing the existing fixture final17-key GO or JIT.

Concrete eight-file handoff: controller/resource adapter/collector, their three
test files, this record and that explicit contract. No provenance helper,
listener fixture, product service/apply path or host configuration was edited.
Root integrates the operative workflow/context reference separately after this
exact contract review; this worktree's older workflow is not silently rewritten.
All other root/network/profile/storage/returned-owner guards remain binding.

The actual resource adapter uses the real product Inspector and qualification
function, strict source-bound actual17GiB override bytes and honest structured
facts. A config-only admission precedes every complete snapshot and therefore
proposal creation/first effect. It cannot label the active-LXD prestate PASS.
The source-bound dependency-qualified controller interpreter runs it in a
bounded isolated child; no global dependency install or arbitrary callback CLI.
The final GO binds only post-pause actual files, static intent, exact source and
fresh reviewer decisions. The fixed fixture remains unreachable on capture/
resource/route/approval/expiry failure and finally recovery always runs.

Root's early read-only review identified the former1200s aggregate-minus1020s
formula could exhaust approval time before waiting. That exact candidate was
not tested or executed. Explicit preparation1200/capture360/approval180/
fixture1025 phases now provide complete named budgets; commands refuse before
spawn instead of shortening timeout. Fresh initial authority must cover1740s
of pre-fixture admission and final authority1025s. Recovery600s remains separate.
Tests directly demonstrate a late preparation/capture cannot steal the next
180s approval or900+120s fixture budget, and insufficient fixed-command reserve
causes no spawn. Source/phase/timeout refusal still restores own changes.

Image-aware capture is explicit schema6 opt-in. New project image and pool cache
rows retain actual identities, metadata digests and complete validated returned
edges. They are never dropped to make schema5 pass. Both pinned primary API
sources were inspected for DTO and UsedBy behavior. Reader tests include real
client flow, exact fixed argv, strict malformed metadata/selector/ownership
refusal, cache counterpart/source drift, full schema6 artifact validation and
missing/failed/duplicate command proof. A previously malformed `/images/image`
negative now expects IMAGE_IDENTITY_INVALID; it remains a failure. No raw image
metadata, secret canary, paths or update source is exported in the inventory.
Only last_used_at is omitted from stable image preservation; the documented
optional actual fixture-cache addition is retained in the expected full graph.
Foreign/new unrelated caches, existing changes and all other drift still fail.

The autostart-only predecessor remains byte-preserved in root-private local
`/tmp/epic440-native-autostart-freeze` (700/files600). Source/test were reconstructed
from the already retained preceding root candidate plus their exact reviewed
patch, then all three bytes matched the previously published8b944d7d/54a677ed/
e2592130 hashes before exclusive archive creation. This is preservation of
known exact bytes, not a test/commit or claim they were archived before editing.
The autostart safety fix is included unchanged in the amended controller.

Final source/test SHA256:

- controller d1291c83cb66b575372fd046d971aa5421c8db55174cd86bfff53fe0e8386aef
- resource adapter 0d6fc43a920774a88be57714f1d9d4eea1e430ba7a14a126bc1d0b7f44b86e7d
- collector 1c6e62b8c3553d1d185ff3243770f28d16583cb5ffc01e4662a76c620edbaccf
- controller tests 6be60a597836a38714a0976e78e311b344ce6fd0954ff21f92e153a90968b0aa
- resource tests 5039e973921c7103486116c36bb18576189d3dcd2787549e350459e41460bd43
- collector tests eca1de20a56fff81b394ee88b8f8aa5e96e6b8739ee616db9f5d020ce86fc5ed
- normative contract 174a38a866e5eba772f90b4a1a9d2b9b15741106f49d5f892e91bedbca399525

Worker performed six-file AST syntax parsing and git diff --check: PASS only.
Worker did not import product/runtime modules, execute tests/lint/typechecks,
SSH/access hosts, import images, mutate service/resource/rules or commit. Prior
native PC passes remain historical. Independent exact source/security/contract
review, fresh root PC gates, committed-source staging and separately approved
actual host phases remain required. No live/capability completion is claimed.

## PC bootstrap R1 typing correction

Root independently reviewed source/contract and staged86 exact combined assets on PC WSL. Typecheck910 files found four static typing issues: optional baseline narrowing and three heterogeneous test-table annotations. LogSHA e8c53965b4555a5bcb99d289bf3eb65c1e8787e1289e83336bcdb9e5cea1d684 retained privately on PC. Focus/full NOT_RUN. Root added an explicit cast after existing baseline admission and concrete table annotations only. No command, image/schema projection, phase/expiry/host effect or assertion changes. PC rerun pending; worker independent delta review requested.

## Historical initial controller root verification (pre-bootstrap bytes)


Root read the concrete source/IO/provenance/transaction/recovery and new tests,
separately from the implementer. Two concrete pretest findings were corrected:
per-node initial state must still equal the baseline before its first stop,
and a complete paused-state snapshot must reject late fourth nodes/projects or
other resource drift before global shutdown. Recovery starts only nodes whose
own durable stop-intent exists, without changing a concurrently drifted node.
New regressions retain these denials; no ownership adoption or broad exception.

First PC candidate nearest typecheck failed16errors in controller/tests; focused
and full were NOT_RUN. Complete log remains PC private ext4 with SHA256
`a47fb208864cd31ab0ccf47cefcedfdc245164f9f263da7dfdb3db5b77a6a4cd`.
Root pipe read timed out; later PTY read showed all errors. No root byte-identical
copy is claimed. Minimal reviewed typing delta changed package/typechecking
imports, narrowed after unchanged baseline guards and annotated identical test
values. Frozen source `2a7460f6daa9406e3bd24eb0ec1eb9a2db080807be72cb75e57d6d84cb181911`,
tests `d2ce9c6937606d6552fb1952277a1625ddc968abb7d15bdbfc6d3548adb4d873`.

PC Ubuntu WSL native-maintenance-r2 matched all13 asset pins before tests.
Typecheck PASS902; focused332 PASS in7.936s; all7 gates PASS;
discovery3330 in195.123s with36skipped, overall exit0. Retained PC logs:
typecheck `59c24a52f4b83285296e29c3b006e69556cd62672739c5397604f44d6c51cf6d`,
focused `c57114cb770d9133fc24ef8657badb903ba4de08fbb0c6b8d4e94f3dda65ea5a`,
quality `4f59e5c02be505230aa9d59b3e8b7d2c582229327f8dac4d6fed49e279849f49`.
Logs are private0600 on PC ext4; tests used isolated HOME and normal umask022.
No tests ran locally or on native Linux. Root integrated exact code/test bytes;
only this actual-result prose and root execution record differ afterward.

This code-only pass does not authorize a host action or qualify Incus. Concrete
fresh committed-source fixture/image/resource/proposal/scenario approvals remain
required before maintenance; no runtime action has occurred. Alpine3.20 is not
cached on either host and the current official image server no longer publishes
it. An independently reviewed fixture-only baseline refresh to a fixed official
Alpine3.21 artifact is being prepared separately; no floating alias or custom
image build and no unsupported capability claim. No host image import yet.

## Final amended bootstrap root integration

Root independently inspected actual image graph/cache DTO/command closure, metadata preservation, intent/capture/final-GO binding, fixed source/config/interpreter paths, autostart and recovery. Root found/corrected the original clamped approval-window reserve; author added actual distinct1200/360/180/1025s phases and600s recovery. Independent author review verified root typing corrections reconstruct the previous exact bytes when removed; Collector1c6e62b8… unchanged. Candidate8-pin manifest206dbfa5c535fe0b41e5bfa1fd8b5a7464c9df6f203be664c99f0dd4c382ccea accepted for PC checks.

PC Ubuntu WSL R2 verified86 exact combined assets (current integrated S03/network/fixture plus amended bootstrap). Typecheck910 PASS log395641543e9a804f55c27427f2361b7aa5dbfe0cc0f5f7a569d3254a8e773a23; focused345 in5.388s PASS log23d99b15275a0a0874c255218a29a7d6b3dac597fe6f2232d7f0be38480233f2; all seven QUALITY gates PASS,43 architecture and3381 discovery in189.490s/36skips, exit0, log747510340bafa6ebba96f11674172ff1d83074257823e01bdf2afd562a9f780c. Logs remain PC private ext4/0600. Root integrated these exact source/test bytes; final record/normative reference prose updated afterward. No native pause, image import or capability acceptance yet; fresh exact committed-source host intent/proposal/GO remains required.
