# S449-04 scoped manager profile — implementation contract

Status: implementation design for independent review. Root authorizes the isolated
source-only stream parallel to S02; no host/test/commit or version admission.
Worktree /home/micro/tsw440-scoped-profile, baseline9a81972c plus exact 57-file S03
overlay486cb4296c6e6e535d465ec621c07357ede6510462a85a0e3913fb51f6efb571.
No inherited S03 file is edited in the S03 worktree. If S03 changes, rebase its
exact pins explicitly before integrating this stream.

Authority: accepted installation-scoped-incus-profile ADR and root's current
source-only routing decision. Supported-version matrix stays EMPTY. S04 cannot
silently make the existing S03 legacy runtime guard permissive. Actual version
admission and host execution require independently accepted S02 evidence.

## Requirement matrix and operational decisions

| ID | Required behavior | Implementation and authored proof |
|---|---|---|
| C1 | Exact admitted client/server versions only | Strict capability asset/repository with empty admitted tuple; deny absent/malformed/unknown/version drift before mutation; test no effects |
| O1 | Installation + operation ownership, not names | Persist exact stopped-create intent and owner markers; inventory every project/profile/consumer/local+expanded device; collision/foreign/inheritance denials |
| S1 | Profile before stopped init, exact effective routes before start | Existing provider delegates to new guarded lifecycle; no launch for scoped manager; test actual production command order/argv |
| J1 | Intent before first effect; immutable recovery | Durable typed checkpoint CAS on S03 anchor under explicit lease + one component journal claim; unknown old payload is not retrofitted |
| F1 | Four write outcomes and interruption | Fresh readback after every mutation; read-proven postcondition only, no blind retries or uncertain cleanup; fault matrix |
| P1 | Preserve default/shared/issue447/Windows/unselected state | Complete preservation projection before every effect; dedicated profile only; no shared edits/legacy adoption or Windows commands |
| W1 | Real composition, no hidden enablement | Private operation context passed through setup/platform/provider/exposure; empty production matrix always refuses scoped execution |

Capability asset: infra/config/incus-profile-capabilities.json, schema_version=1,
capability='installation-scoped-incus-manager-profile', admitted_versions=[].
A later reviewed entry must name exact client/server versions plus controller and
accepted fixture provenance. No environment variable, major-version match or
mock success populates this asset. A supplied mutable JSON object is revalidated.

Introduce focused typed models alongside S03, without changing its legacy
serialization: immutable manager-create intent binds installation UUID,
operation hex identity, default project, node name, exact source image fingerprint,
ordered non-routing base profiles plus dedicated exposure profile, resolved
network/storage/resource settings, full desired profile config/devices and the
S03 route/selection binding. New profile and instance configs include explicit
user.tiny_swarm_world.installation_id and operation_id markers; current generic
managed/node/image_alias remain compatible data, not ownership proof.

Profile identity must equal S03 installation_profile_name; project fixed default.
Profile config is bounded own markers only, devices exactly the canonical route
map. Base profiles must be fully observed and have only admitted safe non-routing
config/devices; all attached profiles and instance-level and expanded devices are
compared. No hidden/profile property merge engine. Complete observed expanded
Incus DTO remains authoritative. Preserve the shared manager profile; replace it
in the new manager's attachment list rather than adding another routing profile.

Inventory includes complete projects/profiles/instances within existing finite
budgets. Inherited profile consumers must resolve to their actual owner: projects
without features.profiles=true can consume default profiles and cannot be hidden
by filtering to default instances. Foreign/unknown consumers or changed project
feature flags block. Unknown device keys/options/types and route-affecting config
block. Compare complete raw validated observation projections in RAM, retain only
bounded typed safe checkpoint identity/digests, never raw credential/config logs.

Durable checkpoint stages: intent, profile-configured, instance-initialized,
routes-verified, instance-started, completed, recoverable, cleaned. Capture the
exact read-before-write expectation and intent before any effect. Journal uses
S03 owner-private repository/CAS and an explicit active lease journal claim; a
new source operation cannot reinterpret an old checkpoint. Recovery accepts only
the exact intent and actual state matching a recorded pre/postcondition.

Sequence: capability+lease+consent admission -> complete initial inventory ->
durable intent -> fresh inventory -> atomic full dedicated profile create or
exact owned configuration -> readback -> stage -> fresh inventory -> incus init
stopped with exact marker/profile/network/storage/resource/image arguments ->
readback stopped identity/local+all profile+expanded route equality -> verify no
disallowed listener -> durable routes-verified -> fresh inventory/listener proof
-> explicit start -> readback complete route/listener proof -> completed.
Manager start never precedes stopped exact proof. Selected worker behavior remains
legacy and cannot consume the dedicated manager profile.

CLI query semantics are pinned from Incus6.0.5 cmd/incus/query.go: --project is
forbidden with query, so all fixed local query URIs carry ?project=default and
--force-local with non-state-saving INCUS_CONF. --request/--data/--raw/--wait are
supported; API write result alone is never success proof. Profile create can use
one full typed POST to avoid uncheckpointed per-device creation. Node init/start
uses existing command runner and explicit --project default. No shell text.

Every write: applied/acknowledged, known not applied, applied/response lost,
unreadable or mismatching readback. Only exact freshly observed postcondition may
advance; otherwise persist recoverable and stop. No automatic rerun of an
uncertain write. Cleanup is explicit and only pre-start exact operation-owned
stopped instance plus unconsumed dedicated profile after fresh proof; post-start
never deletes on failure. External writers remain excluded by maintenance
precondition, with per-write re-reads detecting drift rather than atomic CAS.

Fresh scoped creation/resume and unchanged installed scoped identity are covered.
Legacy generic-marked instances/profile reassignment remain blocked pending the
separate reviewed migration proof. Route-changing an already running manager
must use a separately admitted S05 delta; no implicit stop/route widening is added
by S04. Existing updates preserve bound profile and routes with strict verification.

## Exact implementation locks

All package paths under src/tiny_swarm_world:
- new domain/lifecycle/profile_lifecycle.py;
- application/ports/lifecycle/installation_profile.py (extend explicit port types);
- new application/services/installation_profile.py;
- new infrastructure/adapters/lifecycle/profile_journal.py;
- new infrastructure/adapters/clients/lxc/profile/lifecycle.py;
- new infrastructure/adapters/repositories/incus_profile_capability_repository.py;
- infrastructure/adapters/clients/lxc_node_provider.py;
- infrastructure/adapters/clients/lxc/command/args.py;
- infrastructure/adapters/clients/lxc/node/safety.py;
- infrastructure/adapters/lifecycle/setup_state.py;
- infrastructure/adapters/lifecycle/installation_operation_lock.py;
- infrastructure/composition_platform.py, composition_lifecycle.py,
  composition_setup.py and composition.py;
- application/services/platform/incus/lxc_service_exposure.py and
  infrastructure/adapters/clients/lxc_proxy_device_runtime.py only to consume the
  admitted dedicated identity/full-verification boundary, no new repair fallback.
Asset infra/config/incus-profile-capabilities.json.
Tests: new tests/domain/lifecycle/test_profile_lifecycle.py,
new tests/application/services/test_installation_profile.py,
new tests/infrastructure/adapters/lifecycle/test_profile_journal.py,
new tests/infrastructure/adapters/clients/test_lxc_profile_lifecycle.py,
new tests/infrastructure/adapters/repositories/test_incus_profile_capability_repository.py;
existing test_lxc_node_provider.py, platform/test_lxc_service_exposure.py,
test_lxc_proxy_device_runtime.py, infrastructure/test_composition.py,
infrastructure/test_selective_setup.py and test_installation_operation_lock.py.
Docs: this record, slice44904 distribution/consolidation, existing manifest and
provider contracts. Root owns normative/workflow/version-support decisions.
Any additional coupling path is reported before editing.

## Verification boundary

Author source/fixtures serially; no local import, tests or live calls. AST/diff
only. Tests assert production argv/DTO/journal boundaries, no empty/stub live port,
all four outcomes per write and both sides of each durable stage, source intent
and consumer drift, unknown versions, same-object independent writer denial,
cleanup retention and sanitized errors. Root executes exact-pin PC WSL typecheck,
focused tests and all seven quality gates after independent frozen review.
No runtime/live capability claim is inferred from successful unit tests.

Primary source: https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/query.go
and https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/profile.go .

### Finite inventory/journal clarification before code

Production observation limits: 2048 commands, 300s aggregate monotonic deadline,
16MiB aggregate output and 8MiB one-response limit, at most64 projects,512 distinct
canonical profiles,1024 instances,256 devices per producer and64 routes. Exhaustion
is unknown/refused, never an accepted partial inventory. Keep stderr/results typed
and sanitize public exceptions. Fixed local raw GETs enumerate complete projects,
each project's recursive profiles/instances, current intended profile/instance and
exact server identity; no arbitrary caller URI. Query observations distinguish an
exact API not-found from transport/permission/schema failure. Mutations validate
all components and fixed method/body/URI arity before spawn.

Project profile feature: default owns default; exact true owns its own profiles;
false/absent inherits default. Retain all inherited views and require full raw
metadata/config/devices/used_by equality with canonical owner; duplicates/missing
canonical views/consumer omissions block. Consumer membership derives from all
projects' ordered unique instance profile lists; no raw/local-vs-expanded union.
Unknown project/profile/instance DTO metadata is rejected unless explicitly typed
as a discarded pinned6.0.5 field; authority/config/devices/used_by never null or
coerced. Before code, model exact DTO maps from pinned shared/api definitions;
no generic subset extraction from an unchecked document is admitted.

The checkpoint is a separate strict schema1 profile-lifecycle checkpoint under
anchor installation/profile-operation.json, not an in-place schema change to old
product/component journals. It embeds the validated S03 profile intent and exact
manager-create fields; target/source/schema/location/marker mismatches block.
Existing profile intent remains nullable only in old checkpoints, whose absence
cannot start this new path. S03 shared component journal claim/lock arbitrates
against component/Portainer; product lock is not nested. Recovery reacquires the
same outer lease and shared claim, then compares exact immutable intent before
any inventory-driven write. File/CAS/regular-owner-private/no-follow safety is
provided by a focused adapter using the existing owner-private persistence ports,
not an unguarded arbitrary filename or transient caller-owned store.

## Implemented candidate clarification — 2026-11-08

Root authorized the following bounded implementation couplings after the original
review. Baseline is the actual integrated S03 plus fixture/normative commit
9de8fa1e531da00cb634a0fa2d8611d2ff5ac345; historical S03 overlay changes were not
reintroduced. This record is source evidence, not a capability or live acceptance.

- Capability entry `fixture_source_revision` identifies reviewed fixture source,
  not its own containing Git HEAD (which would be self-referential). Admission
  matches exact client/server versions. Current clean controller HEAD remains a
  separate immutable setup/change/runtime intent field. The shipped matrix stays
  EMPTY; S02 and independent host evidence remain mandatory before populating it.
- The production creation intent retains the original transient manifest,
  installation/operation UUIDs, exact immutable local image fingerprint, fixed
  manager/worker specs and desired stack-owner modes. `initial_manifest` contains
  references, no credential values. Actual Portainer IDs live only in separately
  verified checkpoint ownership records; S05 persists its own guarded API journal
  before the async owner callback. No ContextVar or shared mutable lease binding.
- Local alias resolution adds one fixed `/1.0/images/aliases/{validated-name}` GET
  per selected node, with default project and exact four-field DTO. Remote mutable
  aliases/imports are not silently executed. Missing local image blocks setup.
- Live inventory uses `instances?recursion=1`, whose pinned Instance DTO already
  contains expanded config/devices; recursion2 is InstanceFull and would add state,
  backups and historical snapshots outside this slice. The fixed manager state
  GET supplies the actual manager PID for listener ancestry proof. No historical
  snapshot/device expansion or snapshot mutation is introduced.
- The private context shares 2048 commands and 16MiB output across phases/templates;
  300s means summed monotonic adapter-command execution, including failure/timeout
  cleanup. Unrelated host/Docker/deployment idle time is excluded. Each command's
  timeout is bounded by the remaining cumulative allowance; concurrent/reentrant
  command use and negative/nonfinite clock duration refuse. CAS reserves bounded
  child HTTP bodies/headers in the same output budget. This precise interpretation
  was explicitly approved by Root; there is no per-phase reset of private budgets.
- Root approved `ProfileRuntimeOperation.for_runtime`: existing installation-owned
  profile/manager/workers/routes are freshly observed without new create authority;
  original UUIDs and creator markers remain bound. Existing component/product/
  Portainer writers receive this context explicitly. Public wrappers keep no lease;
  private wrappers require exactly the admitted lease and fresh async admission.
  Legacy/shared internal paths and scoped reset/destroy/repair remain refused.
- Existing services add uses immutable `ProfileChangeIntent`, actual baseline
  manifest, before/target route templates and manager/worker UUIDs in a separate
  `profile-change.json`. It does not overwrite creation history. Pending changes
  block independent installation writers. Explicit recovery accepts exact before
  or exact target only; unknown/partial states remain retained. Manifest commit
  follows verified effective target and actual selected stack ownership. Recovery
  also handles manifest-write-before-final-journal-commit; pure repeated operations
  retain manifest bytes and perform no profile mutation.
- Incus6.0.5 `query` supplies no ETag argument (`RawQuery(..., "")`), so Add does
  not pretend a CLI PUT is CAS. A literal isolated stdlib helper performs fixed
  local Unix-socket GET/PUT with root-owned parents/socket, root SO_PEERCRED,
  bounded HTTP framing and strict seven-field envelopes. It directly compares
  observed before metadata, derives the profile name from the installation UUID,
  validates complete finite proxy bodies, and sends the exact ETag as If-Match.
  HTTP412/lost response remains unknown until fresh target readback; no blind retry,
  force deletion, foreign pruning, remote endpoint or writable-source child import.
- Profile change journals use the same installation lease/shared component journal
  claim and descriptor-based private no-follow reads. File generations use full
  expected-checkpoint CAS. Unselected profiles/projects/config/devices/consumers
  remain in the preservation projection; canonical inherited profile views and
  ordered memberships are validated, never repaired by union or name adoption.
- Necessary approved helper locks: application/services/profile_setup.py,
  application/services/profile_change.py, adapters/lifecycle/profile_setup.py,
  adapters/lifecycle/profile_change.py, clients/lxc/profile/observations.py and
  clients/lxc/profile/cas.py plus corresponding tests. Existing CLI parser adds
  `setup run --recover` and `services add --recover`; private setup composition
  and S03 `composition_operation.py` forward the explicit context. S05/S06 shared
  composition/selection deltas require Root's three-way integration.

Windows bridge/PortProxy reconciliation remains its existing separate platform
phase. Linux Incus route proof does not claim Windows route removal/addition or
live Windows acceptance. S06 desired exposure must reach canonical manifests and
its admission point remains after the real context is bound, before prepare returns.

Primary pinned references:
https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/query.go ,
https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/instances_get.go ,
https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/instance.go .

Authored verification includes actual manager transitions and four effect outcomes,
selected three-node UUID/no-proxy lifecycle, durable journal faults and repeated
cancellation, real private journal/independent-writer denial, complete read-only
command/DTO frames with final drift/inheritance denials and canary redaction,
strict image/capability boundaries, the literal CAS helper exercised by an in-memory
Unix HTTP transport (real HTTP headers, If-Match,412/lost/no-retry), aggregate budget
clock/concurrency cases, Add before/target recovery and post-manifest-write recovery.
Worker verification: AST parsing and diff whitespace only. ALL tests, typecheck,
quality gates, hosts and effects are NOT_RUN by this worker. Root executes exact
frozen hashes after independent review. No commit or publication by this worker.

Final endpoint correction before freeze: Root confirmed actual native and WSL
binding `incus_var_lib` from already retained unit/evidence, not a new host query.
CreateIntent now requires finite `endpoint_kind` (`incus_run` or `incus_var_lib`).
Each Incus CLI connection first rereads the exact active loaded `incus.socket`
Listen tuple and compares it to the retained binding; absent, ambiguous, masked,
foreign or changed endpoint refuses. Both allowlisted paths receive root-owned
no-follow parent/socket and root SO_PEERCRED checks. The CAS child accepts only
the retained finite kind, verifies that same fixed path/peer and never falls back.
Actual default `/var/lib/incus/unix.socket` is supported; no hardcoded run-path
assumption survives. Direct-service/no-socket-unit layouts remain explicitly
unsupported rather than guessed. Tests cover both finite kinds and changed/unknown
binding refusal before any Incus effect, plus the literal child's exact bound path.

## Frozen worker handoff

34 changed assets: 32 Python source/test files, the empty capability JSON, and this
record. Last static checks: all changed Python plus the embedded CAS literal parsed
with `ast.parse`; `git diff --check` passed. No test/project import/typecheck/quality
or host command was executed by this worker. The external SHA256 file is
`/tmp/epic440-scoped-profile-candidate-hashes.json`; it includes this record's exact
bytes and the unchanged 9de8fa1e baseline identity. Source freeze is for independent
review and Root PC verification, not S02/capability/live/EPIC acceptance.

### Pre-merge independent review correction: selected recovery transport

Root's independent review found that the accepted parser-level setup/add recovery
exception was still rejected by `cli/selection.py` for selected/minimal flows.
Narrow correction permits recover only for setup/run or services/add with --live,
without --preview/--preflight. Every stack/service/from-image/to-image option stays
rejected for selection, services/remove remains preview-only, and platform recovery
retains its separate required stack/service and image-option restrictions. Setup
recovery without explicit selection also receives the same live-only validation.

New actual parse_args regression covers selected/minimal/default setup and add
recovery, denied live/preview/preflight/update-option combinations, and unchanged
platform recovery. No tests or hosts executed. AST/diff-only verification repeated.
This supersedes the earlier 34-pin freeze with 36 assets; other product source bytes
remain frozen. Original pin manifest is retained as the `.before-recovery-cli.json`
sidecar before writing the revised exact list.

### Independent review corrections: ownership, preview, existing verify and compatibility

P1 ownership is now anchored to `before_manifest.effective_stack_ownership()`.
ChangeIntent must retain that actual baseline policy. Callback and typed recovered
checkpoint preserve owner mode, endpoint/stack/resource-control IDs and ownership
fingerprint; only a verified definition fingerprint may change. Existing baseline
IDs may be retained before target verification; new IDs/changed definitions require
the verified target stage. Newly added stacks retain their first durable identity
across subsequent callbacks AND direct journal CAS writes. Runtime-update callbacks
reuse the same identity invariant. Tests deny every ID/mode/fingerprint/type drift,
forged recovered maps, removed durable owners and baseline-policy forgery, and
allow verified definition-only updates and genuinely new selected stack IDs.
The change tests now use an explicit change-checkpoint fake journal: the previous
creation-checkpoint fake incorrectly accessed a nonexistent pending_action field.

P1 existing-provider transport now selects its template by validated intent type:
ManagerCreateIntent itself, ProfileRuntimeIntent.original or ProfileChangeIntent.target.
Unknown shapes refuse; no hasattr/name fallback admits a node. Actual dispatch tests
cover both existing intent variants and unknown/unselected targets. The bounded
scoped dispatcher lives in clients/lxc/node/scoped.py instead of growing the legacy
provider class. Existing host-capacity checks still precede scoped node effects.

P2 CLI preview now emits deterministic before/after/additions/removals from the
persisted binding and canonical selected/exposure-filtered SetupManifest. One pure
route helper is shared with create/change producers; no UUID, Incus, host observation
or mutation is needed. A persisted listen address wins; fresh policy reads the same
validated TSW_LXC_PROXY_LISTEN_ADDRESS source configuration used by live preparation.
The JSON explicitly says runtime_observed=false and whether a bound baseline exists.
Actual CLI tests cover internal Swagger {10001}, published {10001,16080,16081}, both
add/remove directions, unchanged manifest bytes and no runtime composition. These
canonical-exposure tests require the reviewed S06 integration, not a synthetic port list.

P2 public standalone verification now has a separate ProfileVerificationObserver
port and ScopedProfileObserver. It observes persisted committed history, exact
versions, current source, UUIDs, effective profile/listeners and before/after state
consistency. It creates neither a lease nor fake LiveConsent and exposes no write
admission method. Public composed node/exposure verify uses this observer; node
ensure, exposure ensure and ordinary bound-policy writers remain denied without
an actual private write context. A real composed-component regression drives the
actual Incus parser/runtime through fake read-only Incus/kernel transports and
asserts no mutation argv, no manifest change, and refusal after matrix revocation.

ADR compatibility is retained: an EMPTY capability matrix permits the established
fresh full-preset Classic path only without explicit services/minimal/config,
internal exposure, Portainer-owner request, recovery, manifest or retained scoped
intent. Published/Swarm legacy guards remain. Qualified versions prefer scoped
creation. New selected/internal/owner requests still require qualified scoped
admission. The legacy fallback reaches the existing dispatcher runner; direct
selective builders remain inspectable but refuse missing scoped authority in the
admitted factory before workflow effects. Existing CLI fake states explicitly set
profile_operation=None rather than accidentally synthesizing a Mock capability.

Preparation/preview/compat composition is factored in composition_profile.py;
command-budget execution and pure manifest postconditions are factored from the
large new classes. No thresholds/baselines/exceptions changed. A transient text
append error was caught by static export comparison before any test/host execution:
both composition.py and composition_lifecycle.py were restored from actual 9de8
source plus the precise S04 deltas. All 44 original facade and 7 lifecycle exports
are explicitly AST-checked present; context injection still precedes admit_exposure.

Latest freeze: 44 assets (42 Python plus empty matrix and this record). AST parsing,
embedded CAS parsing, original composition-export comparison and diff whitespace
checks passed. No worker tests, imports, typecheck, quality gates, hosts or commits.
The prior 36-pin file is retained as `.before-ownership-preview-verify-compat.json`.
Root must review exact new bytes, three-way S05/S06 composition/selection deltas and
run PC verification before any capability, live readiness or EPIC acceptance.
