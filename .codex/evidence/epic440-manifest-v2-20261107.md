# S449-03 — exact code-only manifest v2 and operation-lock plan

State: EXACT_DESIGN_REVIEW_REQUIRED, no code release yet. Worktree
`/home/micro/tsw440-manifest-v2`, branch
`fix/epic440-manifest-v2-20261107`, baseline
`9a81972cd722a759ccd4d7118fe5eec833bf075e`.
Root explicitly permits authoring this design now. The forthcoming reviewed
ordering amendment may release pure state/serialization code parallel to S02.
This plan does NOT enable scoped profiles, admit an Incus version, start a new
live path, or claim S02 acceptance. Root owns normative ordering, integration,
SSH/WSL tests and gates; worker performs no hosts/tests/commits.

Authority: accepted ADRs `adr-installation-scoped-incus-profile.adoc`,
`adr-classic-selection-exposure-stack-ownership.adoc`, and
`adr-product-effective-infrastructure-source.adoc`. Existing effective-infra
binding/capture/migration is implemented and will be preserved, not rebuilt.
No new CLI, lifecycle engine, catalog, generic merge or adoption-by-name.

## Requirements and exact state decisions

| ID | Required behavior | Implementation boundary | Evidence |
| --- | --- | --- | --- |
| M1 | Strict v1/v2 without read-time mutation | models/manifest and pure compatibility helpers | real file reads create/write nothing; roundtrip and malformed denials |
| M2 | Persist selection, exposure, owner and optional owned-profile binding | schema2 values; existing catalog membership validation | selected-key/owner/route/UUID coherence and preservation |
| M3 | Explicit migration only after existing operation verification | actual successful commit sites; original journal stays original | failed/no-op/preview/interrupted operations cannot migrate early |
| L1 | One outer installation lock before captures/writes | application lock port plus secure adapter/composition | multiprocess contention and real entrypoint call ordering |
| L2 | At most one nested journal; separate product journal lock | update/Portainer/product adapters and services | order/recovery/reverse/nested contention tests |
| C1 | Durable immutable operation/profile intent | optional typed intent on existing journals; pure serializer | interruption/drift/old-journal compatibility |
| P1 | Preserve external infrastructure and secrets | existing product paths/capture/validation/migration/activation | retain current regression suite plus v2/lock integration |

### Manifest schema

Keep `InstallationManifest` as the existing constructor and frozen strict model;
accept exact integer schema_version 1 or 2. Existing defaults remain schema1 for
backward-compatible callers. Add these three explicit schema2-only fields:

- `service_exposure: dict[Identifier, Literal['published','internal']]`;
  exactly `{'swagger': ...}` iff Swagger is resolved, otherwise empty. Other keys
  fail. V1 effective projection is published iff Swagger is selected.
- `stack_ownership: dict[Identifier, StackOwnership]`; exact selected OPTIONAL
  stack service IDs, excluding Incus/Portainer foundations; catalog checks every
  key against selected services with a native stack asset. `SwarmOwnership` has
  exactly `owner='swarm'`. `PortainerOwnership` has exactly owner='portainer',
  endpoint_id, stack_id, resource_control_id (strict positive integers),
  ownership_fingerprint and definition_fingerprint (existing Digest type).
  The latter binds complete authenticated ownership identity and saved definition;
  this model does not authenticate a supplied observation. No name-only ownership.
  V1 projects every selected optional stack to SwarmOwnership.
- `installation_profile: InstallationProfileBinding | None`;
  null explicitly means legacy/unbound, NOT an owned empty profile. Non-null has
  exactly project='default', profile_name and routes. profile_name must equal
  `tsw-manager-` plus first 24 lowercase hex characters of SHA256 of the canonical
  validated installation UUID text. Identity is data passed as argv, never shell.

`ProxyRoute` is a strict complete tuple: device_name (`tsw-proxy-<listen_port>`),
device_type='proxy', bind='host', listen_protocol='tcp', listen_address
('0.0.0.0' or '127.0.0.1'), listen_port, connect_protocol='tcp',
connect_address='127.0.0.1', connect_port, nat=False, proxy_protocol=False.
Ports are strict integers 1..65535. Duplicate device/listen tuples and unsorted
routes fail. Unknown options, IPv6/UDP/guest binding or other tuple shapes remain
unsupported by this first writer contract; actual observed unknown options must
block in S04, never be normalized away. Selection-to-route derivation remains
with the canonical manifest/port catalog and is wired in S04/S05, not duplicated.
A non-null profile binding is not automatically created for a legacy v1 record.

V1 input must reject supplied new fields even if null/empty. Its serialization
must omit the new fields and retain original schema; implement a field-presence
validator and schema-aware serializer so old journals and exact v1 CAS tokens
remain meaningful. V2 input must contain all three fields; missing/null maps,
extra fields and unknown versions/types fail. Pure effective-policy helpers
return defaults without changing the model, bytes, schema or filesystem.
Existing component/credential/configuration fields are preserved exactly.

Pure `migrate_manifest_v1` creates schema2 with effective published/swarm defaults
and installation_profile=None, preserving installation/product/selection and
all references. No raw read/preview, generic repository save or no-op implicitly
calls it. Successful verified setup/add/component/product/Portainer commit sites
may call this explicit helper under the outer lock immediately before their CAS;
pre-commit errors leave v1 untouched. Recovery comparisons admit only this exact
policy-preserving migration of the original manifest, not arbitrary schema/policy
changes. Original checkpoint payloads are not rewritten to hide original input.
Preview exposes planned migration/effective policy without saving it.

### Operation/profile checkpoint

Add strict `InstallationProfileIntent` values in models.py: operation_id (32
lowercase hex), operation_kind (setup/add/component-update/product-upgrade/
portainer-upgrade/recovery/cleanup), installation_id (canonical UUID),
controller_revision (Revision), product_source_revision (Revision),
product_target_revision (Revision|null), incus_version (bounded version string),
manifest_token (64 lowercase hex|null for fresh), requested_services and
resolved_services (ordered duplicate-free identifiers), service_exposure,
stack_ownership, profile (InstallationProfileBinding|null), and stage.
Stage enum: intent/profile-configured/instance-initialized/routes-verified/
instance-started/completed/recoverable. Invalid cross-field state fails.
S03 supplies durable values and validation only; it cannot execute or advance
profile/node stages. Actual writer transitions/observations belong to S04/S05.

Existing ProductPlan, UpdateBatch and PortainerCheckpoint gain optional
`profile_intent` default None; absent old payload means unbound. Unknown fields
still fail. Read/recovery never populates an absent intent from environment,
current selection or guessed runtime. New bound intent is copied unchanged
through unrelated journal transitions and must match installation/selection and
source/target identity. New scoped operations will require this intent before
first profile mutation once S02/S04/S05 permit that path. Existing full Classic
operations with null intent remain supported under their existing gates.

## Outer lock API, storage and writer coverage

Port `InstallationOperationLock.exclusive(operation: str, *, lease=None)` returns
a synchronous context manager yielding an opaque InstallationLease, usable across
awaits; application code knows no paths/flock. A lease is an in-memory capability,
never manifest/journal/JSON data. Explicitly pass it through nested service and
workflow construction; absence always means a new independent lock attempt.
Mutating entrypoints require an injected lock; missing lock refuses before
capture/mutation. Preview/read-only construction can omit it. Unit tests inject
an explicit recording/fake port, never a production no-op default.

Concrete path is the canonical ANCHOR repository's
`.tiny-swarm-world/installation/operation.lock`, shared by all operations before
an installation UUID exists. The managed launcher already pins
TSW_REPOSITORY_ROOT to that anchor; target code must use this same lock/state,
not a staging checkout's private lock. Reject unsafe/non-native state rather
than relocating or repairing it. Traverse descriptors without following symlinks;
verify trusted ancestors, owner-private state directories 0700, regular lock
file 0600, owner UID and single link; use O_NOFOLLOW/O_NONBLOCK and nonblocking
exclusive flock. Fsync newly created directory/file state; unsafe state,
contention or uncertain durability yields a fixed LifecycleStateError before
runtime/configuration mutation. Lock paths never enter public diagnostic output.

Nested operations may reuse ONLY an explicitly passed active lease for the same
anchor, retained descriptor, OS PID and operation identity; foreign/closed/replaced
leases fail. ContextVar inheritance alone never grants ownership. This matters
because existing setup phases may run in child Tasks and blocking workers:
composition passes the admitted lease explicitly to its known nested workflows
and metadata services, rather than relying on current Task identity or a global
reentrant flag. Concurrent independent top-level Task/thread/process operations
have no lease and must attempt flock, which refuses contention. A borrowed lease
never closes/releases the owner's descriptor. The outer scope retains ownership
until all admitted child operations and started blocking workers settle on
cancellation (reuse current product shielding and add coverage). OS exit releases
flock; durable checkpoint remains. No unrelated process-global mutex.

Order: outer installation lock -> exactly one component OR product journal.
Component and Portainer retain the existing shared component-update.lock.
Product journal uses its own product-upgrade.lock, not component-update.lock.
Under outer lock, journals check competing unsettled checkpoint states without
acquiring another journal. Never acquire installation lock from inside an
already-held journal or nest component/product journal ownership. Recovery and
cleanup follow the identical order.

Supported writer entrypoints covered by explicit composition/application wiring:

1. `InstallationLifecycleService.adopt` apply and `ServiceSelectionService.persist`;
   read/preview remains unmodified and creates no lock files.
2. Selective setup/add: lock before selection/manifest capture, hold through
   admission, existing setup run, observations and commit/failure/cancellation.
3. Full Classic setup: lock before construction/capture and hold through its
   whole existing workflow, including nested platform/deployment writers.
4. Component, Portainer and product run/recovery: outer lock before journal,
   manifest/runtime capture and verification; release journal first.
5. Legacy Classic single-service update/recovery and standalone platform
   init/reconcile/expose/reset/destroy/repair, cluster Docker/Swarm writes, and
   deployment bootstrap/apply: use a small composition-level locked workflow
   decorator around existing `.run` operations; no duplicated orchestration.
   Read-only preflight/verify/preview do not create lock state. Existing explicit
   consent stays ahead of mutation; wrapper does not grant it.
6. Every built service shares canonical anchor authority, including the actual
   LxcNodeProvider construction in composition_platform.py. No scoped profile
   implementation or capability enablement is added to this constructor in S03.

A recording adapter tests each public/composed mutation entry, including nested
setup and separate direct platform/deployment calls; no undocumented unlocked
fallback. Existing pure command builders/ports remain reusable implementation
helpers, not independently authorized live entrypoints.

## Exact proposed locks and ordered implementation

Only this record is edited before independent architecture/root code GO. The
following extends historical S03 locks to cover the actual full writer boundary;
root must bind these exact scope amendments before implementation.

1. State/ports: domain/lifecycle/{models,product_upgrade,update_execution,
   portainer_upgrade}.py; application/ports/lifecycle/installation_profile.py
   (new), product_upgrade.py; adapters/lifecycle/manifest.py.
2. Secure persistence: adapters/lifecycle/installation_operation_lock.py (new),
   update_journal.py, product_journal.py, portainer_journal.py; extend existing
   manifest/setup state without weakening private effective-infra persistence.
3. Writer services: application/services/{lifecycle,service_selection,
   component_execution,portainer_upgrade,product_upgrade}.py;
   application/services/platform/workflow/update.py.
4. Actual adapters/composition: adapters/lifecycle/{setup_state,product_admission,
   product_installation,product_runtime,product_verification,product_environment,
   product_paths,product_migration,product_configuration_source,
   product_configuration_capture,product_configuration_validation}.py;
   adapters/cli/{selective_setup,dispatcher}.py;
   infrastructure/{composition_lifecycle,composition_product,composition_setup,
   composition_platform,composition_deployment,composition_runtime,composition}.py.
   Existing bound infrastructure code changes only where required to propagate
   the admitted state/lock or verify migration; preserve current capture algorithms.
5. Evidence/docs: this record; slice-449-03 distribution/consolidation records;
   existing transition proposal and product-upgrades.md; installation-manifest.md
   for exact v2 contract. Root retains workflow/context/ADR amendment ownership.

All Python paths above are under src/tiny_swarm_world; adapters are under
infrastructure/adapters. Any additional path requires reporting before editing.
No S04 capability YAML/profile lifecycle/Incus init or new runtime query here.

## Verification contract (tests authored, root executes)

Exact test locks:
- tests/domain/lifecycle/{test_models,test_selection,test_update_planning}.py;
- tests/application/services/{test_lifecycle,test_service_selection,
  test_component_execution,test_portainer_upgrade,test_product_upgrade}.py;
- tests/infrastructure/adapters/lifecycle/{test_manifest,test_setup_state,
  test_product_upgrade,test_product_configuration_source,test_portainer_runtime,
  test_native_component_transitions,test_installation_operation_lock(new)}.py;
- tests/infrastructure/{test_composition,test_selective_setup,
  test_setup_status_cancellation}.py;
- tests/test_{product_upgrade_cli,service_selection_cli,selective_setup_cli,
  package_entrypoint}.py;
- tests/application/services/platform/test_classic_update_workflow.py;
- tests/tools/{test_r46_ports_policy,test_secure_runtime_paths}.py.

Use meaningful public-flow fixtures and real private state IO. Cover strict
v1/v2, schema-aware serialization/old nested journals, no-write previews,
malformed exposure/ownership/routes, exact migration after verified commit only,
unchanged other state, old interrupted checkpoints, migration-compatible CAS
recovery and tampered binding denial. Lock tests use separate processes, Tasks
and threads, real flock and hostile path fixtures; assert lock order and no
runtime calls on unsafe paths/contention. Inject cancellation and pending blocking
workers, durable save/fsync failure, interruption before/after commit and exact
retry/no-op. Product tests retain effective-infra byte/ownership/capacity/secret
and bound/unbound recovery cases, including managed-launcher anchor lock identity.
No test may infer capability/version admission or scoped live readiness.

Worker static review plus AST/diff checks only. After exact independent candidate
review, root runs designated SSH PC/WSL typecheck, focused lifecycle/lock/setup/
composition suites and all seven quality gates on exact hashes. Any failure is
retained and classified before correction. S03 acceptance remains code/state
scope only; S02/S04/S05 prerequisites continue gating capability/live use.

## Exact design release and bounded clarification

Root and independent architecture approved plan SHA256
`dba326012817f9ad5e9df4bbac5d2193f99c20e117a7c8aeaaba862a0e967abb`
for the complete pure-state scope. Root granted code GO after review. Architecture
requires the active lease to arbitrate ONE journal holder in memory as well as
OS flock: explicit journal-claim context rejects nested/competing component versus
product holders, including child Tasks sharing the same admitted lease, and
releases in finally after workers settle. Add that concurrent-child regression.
This is a bounded clarification of L2, not a new engine or live authority.
Trusted root/system/current-user ancestors may be safe 0755; only TSW state
components must be owner-private 0700, with owner-only regular 0600 lock file.
Tests inject explicit fake locks; no production no-op fallback. Implementation
is now authorized; no capability enablement, scoped profile writes, tests/hosts
or commits by worker.

### Reviewed implementation refinements

Root and architecture approved explicit target-reader support before effects.
ProductRelease.supported_manifest_schemas defaults to (1,) for old checkpoints;
the exact pinned 0.4.0/0.5.0 readers admit only (1,). Schema2 cannot upgrade to a
reader1 target, and legacy product completion retains schema1 when activating the
unchanged reader1 target. No read-only transport projection or schema downgrade
is used. Additional authorized locks: product_source.py and
infra/config/product-releases.json, with catalog/policy regression synchronization.

Root authorized application/ports/lifecycle/component_execution.py and
infrastructure/adapters/lifecycle/component_runtime.py for explicit runtime-port
lease propagation into the already-existing ClassicUpdateWorkflow through private
operation views. Public reusable runtime/workflow objects retain no capability. Root additionally confirmed the mandatory pure compatibility
predicate: current runtime writers refuse internal exposure, Portainer ownership
or an owned profile binding until the separate S04/S05 capability exists. Pure
read/preview/state serialization retains these policies without executing them.

### L1 shared-composition race correction

Root and architecture identified that mutating shared wrappers with an admitted
lease would let independent Tasks implicitly borrow the current operation.
Delegation now returns private dataclass/wrapper views. Setup composes its phase
closures against private children after acquisition, and Classic runtime delegation
copies the runtime/workflow rather than binding shared state. Dispatcher also uses
private views. Public wrappers remain unbound; no ContextVar or automatic Task
inheritance. Regression covers a paused setup with successful authorized nested
calls and a competing public writer on the same composed object, plus independent
setup refusal and repeated cancellation while a blocking worker settles.
No runtime capability or source authority is added by this correction.

### Candidate handoff (2026-11-07)

Implementation covers the approved pure-state paths and compatibility refinements.
The L1 fix additionally preserves private PlatformLifecycleOrchestrator aliases;
public platform/setup/runtime objects retain no borrowed lease. Existing mocked
suites explicitly inject recording lock ports; the new real filesystem/process/
async tests do not replace production authority checks. Documentation distinguishes
schema2 state from the still-gated runtime capabilities and reader1 releases.

Worker static checks: AST parsing of every changed/new Python file PASS;
`git diff --check` PASS. Runtime imports, unit tests, typecheck, quality gates,
remote hosts, commits and live effects: NOT RUN by worker. Candidate is submitted
for independent exact review, then root-owned SSH PC/WSL typecheck, nearest/focused
and all seven gates. No acceptance or live qualification is claimed.

### Strict legacy journal serialization correction

Root held PC staging after identifying new default-only keys in serialized old
checkpoint shapes. ProductRelease now omits supported_manifest_schemas only for
its semantic default (1,); ProductPlan, UpdateBatch and PortainerCheckpoint omit
profile_intent only when unbound/None. Explicit nondefault reader metadata and
bound intent remain serialized. A reader1 product target refuses bound intent
before effects rather than discarding it. Tests cover the actual new completed
product journal through a strict baseline-controller model/real durable loader,
repeat verification without rewriting it, retained nondefault metadata and bound
component/Portainer intent. No old checkpoint is rewritten on read.

Verified Git-object correction: target b3de7fa16e24c5702d61f855851c6c3255871489
has no domain/lifecycle/product_upgrade.py or product_journal.py and no product
upgrade command. Therefore no target ProductJournal compatibility is claimed.
It does contain InstallationManifest with schema Literal[1]/extra-forbid and the
component/Portainer readers. The strict product fixture reflects controller
baseline 9a81972cd722a759ccd4d7118fe5eec833bf075e, where those product models exist.
The target's real composition.py exports both verification builders;
composition_platform.build_platform_services and
composition_deployment.build_deployment_services_for_provider accept
resolved_services. Target Platform/Cluster/DeploymentWorkflows expose verify.
Thus TARGET_VERIFICATION uses real pinned APIs with schema1 input; source/API
inspection does not constitute live transition qualification.

### Pre-test M3 no-op correction

Independent architecture review found a fresh v1 already-target batch still
reached the component commit migration. Root held staging before any PC test.
After live transition revalidation and original-state validation, a service plan
with immutable status no_op now settles its journal without any manifest write,
including reverse recovery. This uses the admitted plan status, not VersionIdentity
text equality. The fresh no-existing-journal regression proves no deployment,
byte/mtime/schema preservation and durable completion/recovery. Non-no-op service
commits retain verified migration; a mixed batch can migrate only for an actual
admitted transition. AST/diff checks repeated; tests/hosts remain NOT RUN.

### Pre-test Classic delegation correction

Architecture found the private lease reached Classic _run but was not threaded
through _apply_and_verify; its factory call referenced an undefined local. Root
staging remains held. The call and signature now explicitly propagate the local
lease; no mutable public service authority is introduced. Existing actual
apply/recovery tests cover the transition, and apply additionally asserts the
factory received a non-null, subsequently expired lease while public workflow
operation_lease remains None. AST/diff PASS; no tests or hosts by worker.

### PC verification R1 — typing-only correction

Root reports all 68 integrated pins matched and lint PASS. Typecheck over 905
files failed only two errors in bind_operation_lease: reuse of local `private`
made mypy retain InstallationLockedWorkflow in the PlatformLifecycleOrchestrator
branch. Rename only that branch local to lifecycle_view; behavior and tests are
unchanged. Focused/full gates were NOT RUN after this failure. Private retained
lint log SHA256 a1ceaede228aa5a6c5232941afde234f59a6488766ef5effc52064bec72bb2e2;
typecheck log SHA256 94babc78382fe69c791e14af0e01887cc4a7857b5a299e60931d71a8fb144f51.
Worker repeated AST/diff checks only; no hosts, tests or commits. Root owns R2.

### PC verification R2 — real JSON boundary and delegation defects

Root reports all integrated pins matched, lint PASS and typecheck PASS over 905
files. Focused 601 tests in 24.069s failed with 10 failures/126 errors; full gates
NOT RUN. Private full-log SHA256 fca64905b7a26b0a7c51f0cbc1a369292f182f0766eda393e453975650a8c38b
was transferred byte-identically and read by this worker. Repeated errors occur
at real JsonManifestRepository.save -> decode_manifest, not a fake writer.
The log's direct checkpoint ValidationError shows JSON arrays materialized as
Python lists against strict tuple fields by the new whole-model before hook.

Fix: validate schema-specific field presence after native strict JSON decoding
using model_fields_set; preserve extra-forbid, strict types and required schema2
keys, without coercing arrays or relaxing the reader. Add actual nonempty v1/v2
file roundtrips. The analogous ProductRelease schema array now uses strict
bounded integer elements and tuple/order after-validation, with explicit JSON
roundtrip and malformed bool/float/string/empty/order/range denials.

Independent defects: generic copy(wrapper) recursed through __getattr__ before
state reconstruction; delegation now explicitly constructs the same private
wrapper with its workflow/lock/token/factory. Existing real private-view tests
remain unchanged. Swagger test uses supported inferred preset. Composition tests
assert both outer InstallationLockedWorkflow/unbound public authority and inner
real workflow type; the explicit fake setup builder requires an active lease,
and dispatcher expectation includes its expired delegated lease. No lock fallback,
weaker fixture ownership, discarded checkpoint intent or broad exception bypass.
The minimal CLI verification failure is downstream of its real manifest.save;
its verification/commit expectations remain intact.

Worker AST/diff checks only; no runtime imports, tests, hosts or commits. Root
owns the controlled validation probe and next exact PC verification.

## Root R3 verification correction

PC WSL exact 68-asset R3 lint/typecheck PASS; focused602 tests in92.438s had one failure, legacy selection no-op migrated schema1 to2. Full quality NOT_RUN. Focus log SHA256 a5054746a407642cf05e6cd0cb7d7daf50be7380d64b979198243bcd5fd6124b remains private on PC. Root moved the already-validated unchanged-selection return before verified migration; actual changes still migrate only at commit. Existing real-file selection no-op now also asserts verified_migration=True preserves bytes/schema/token/time. Existing setup-state source-observation regression retains its byte/time assertion. No reader weakening or mocked persistence replaces either path. AST/diff only locally; PC rerun pending.

## Root R4 quality and bounded orchestration decomposition

Root reports PC R4 lint/typecheck PASS and all602 focused tests PASS in33.265s
(focused log reported prefix d826bc93). Full quality then stopped at five real
complexity findings (log reported prefix3527a103): grown ClassicUpdateWorkflow,
grown dispatcher/setup module coupling, critical SetupSelectionState and critical
ServiceSelectionService._persist. This is FAILED quality, not slice acceptance.
No thresholds, baseline snapshots or exceptions are changed.

Root approved/exclusively locked five focused helper paths:
application/services/selection_commit.py (pure validated selection candidates),
application/services/platform/workflow/update_admission.py (shared explicit
Classic consent/lease admission), infrastructure/adapters/lifecycle/setup_inventory.py
(freshness/source manifest factory), infrastructure/adapters/cli/operation_dispatch.py
(private CLI operation delegation), and infrastructure/composition_operation.py
(setup/Classic operation composition including the actual Classic factory).

Public entry points, real validators, no-op return before migration, CAS save,
explicit private lease flow, journal order, source/host checks and error messages
are preserved. The selection candidate is decomposed into plan validation,
component preservation, reference preservation and schema2 policy extension.
The setup class delegates fresh-source inventory to the focused factory while
retaining its private method seams. Classic apply/recovery share one application
admission function. CLI passes its existing public callbacks explicitly to the
private dispatcher. Setup/Classic composition delegates operation wiring and
retains the facade builders/process runner compatibility path. Test fake lock
injection follows the exact new modules; no production fallback is introduced.
Existing602 tests remain; none are deleted or weakened.

Static AST inspection gives Classic class branch score81 (reviewed baseline80),
SetupSelectionState91 lines and ServiceSelectionService58 lines. These are static
inspection facts, not a locally run complexity gate. Worker AST parsing and
git diff --check PASS; imports/tests/typecheck/quality/hosts/commits NOT RUN by
worker. Root must review all62 exact pins and rerun PC gates.

## PC R5 lint-only correction

Root reports all82 integrated assets matched. Lint failed only unused
InstallationManifest in service_selection.py and unused/redefined global os in
composition_setup.py (private log reported prefix0c36a783). Typecheck/focused/full
were NOT RUN. Root removed those two global imports; independent worker review
confirmed selection now uses the pure helper and setup retains its local os
import before environment capture. No executable statement or lock changes.
Root structurally reviewed the five decomposition helpers. Worker AST/diff checks
only; R6 remains root-owned, no local tests or hosts.

## PC R6 architecture correction

Root reports exact82 integrated assets; complexity/lint/typecheck PASS and all602
focused tests PASS in30.264s (reported log prefix f7e8610a). Full quality stopped
at architecture: four concrete CLI-layer violations from operation_dispatch.py
(log prefix2e7802d). No full-quality success is claimed. Root's architecture
routing decision moves that complete private delegation into the existing focused
composition_operation.py and adds explicit async composition.py facade function
run_installation_cli_operation. CLI dispatcher imports that facade alongside its
existing composition APIs. The untracked CLI helper is removed entirely, with
explicit staged-file deletion required before PC scanning; fake lock injection
uses composition_operation only. No checker/baseline/exception change. Existing602
behavior tests remain; root adds architecture-focused tests before the full gates.
Worker AST/diff only; no tests or hosts. Current candidate has61 paths, replacing
the previous62-path artifact and deleting operation_dispatch.py.

## Root R7 complete-discovery correction

81 exact assets including network source plus v1.51 normative scheduling: architecture43, complexity, lint, typecheck909 and focused602 in20.496s PASS. Focus logbb5738557f8633e52d941dc34b9a07a06b1716ee6279e58d331da5fa581d81b1. Complete discovery3369 in197.647s had one error/36skips: older lazy ProductComposition lifecycle fixture omitted the required installation operation_lock. Full log95d2b70f299167090fb323d277e6dda1bba510dcb9c61539291a8176b85279a2. Root supplies the real lazy JsonInstallationOperationLock(root) in that fixture and explicitly asserts the composed service keeps this same lock; existing no-secret/no-runtime/no-filesystem-effect assertions stay. Production behavior/guards unchanged. PC nearest+full rerun pending; failed logs retained.

## Root final integration evidence

Independent root source review accepted the final persistence/lease model and the four focused helpers. Worker independently reviewed root typing/no-op/real-lock-fixture corrections. Final62 source/doc/test pins2bfb74ddf3fc87ef9639b5eded0a7931bb3ff6679d03402a84775bb66b875e22 were combined with committed network coexistence and current fixture/v1.51 normative files into82 exact assets. PC WSL R9 verified every pin before running; nearest actual ProductAdmission13 tests PASS0.292s log97b96cf9fa839a76144721f13472451831e785c41d41bcfc16f687a34e3737e5. All seven QUALITY gates PASS, architecture43 and full3369 in192.646s with36 skips, exit0, logcbbb896ff0b05df1645ff10bb163882993ea2f6c28f0cbb16ccc28bd3cdaea2b. Previous final-runtime602 PASS20.496s remains attributed to R7 before the extra lazy-fixture assertion. Failed prior logs remain; R8 stage failed on an obsolete one-time deletion inherited by its generated driver before any test ran. R9 rebuilt clean staging and required no source/guard relaxation. Private logs remain PC ext4/0600; no raw log copy to root is claimed.

S03 source/quality integration accepted. This does not enable scoped-profile versions, internal Swagger runtime, optional Portainer ownership, host adoption or live acceptance. S02/S04–09 remain open.

Root staged diff check caught a trailing blank line in the newly tracked setup_inventory helper (untracked PC overlays are outside git diff checks). Removed only the extra EOF newline after all-seven PASS; oldSHA5adda5e5f96042e7a742b426e5a7a918738c1760d68970d8bd76d0e0bff5a479 newSHA3e9fe3b6eacf1edd901c9a5db3fd5a9a53ea3716c40e48fb603d966a78a909d7. Root staged diff check then PASS. No behavior/test/guard change; no additional test run for whitespace-only correction.
