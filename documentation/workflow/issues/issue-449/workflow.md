# LCM-W09 — Selective installation and upgrades on native Linux and WSL2

Workflow ID: `issue-449-lcm-w09`
Workflow version: `1.4`
Status: `EXECUTION GATE — same-hash four-role release and S3D preflight required`
Issue: [#449 LCM-W09](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449)
Epic: [#440 LCM-04](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/440)
Branch: `feature/lcm-w09-issue449-implementation-20261027`
Workflow authoring branch: `feature/workflow-lcm-w09-20261027`
Baseline: `a0310224946b63e2152ff4086d22a450c3d0f214`
Execution profile: `FULL_PATH — lifecycle/provider implementation, regression, documentation, native and WSL2 qualification`

## Executive Summary

Complete every open #449 requirement and acceptance criterion. A separate dirty
source checkout contains substantial setup, update, persistence, CLI, test and
documentation changes. They are not part of this workflow-authoring baseline;
only the slice-approved public paths and exact hashes may be ported after S3D.
The unrelated Sub-Issue governance changes must be excluded.

The key unresolved behavior is that resolved service selection reaches later
exposure planning but not Incus manager-profile selection. The provider may
attach a shared profile with extra proxy routes and starts the manager with
`incus launch` before exact effective routes are checked. Installation state
does not yet bind an installation-owned profile identity and effective route
set. The R67j profile ownership/selection policy has same-hash Requirements,
Architecture, Security, DevOps and Test/Evidence approval for canonical ADR
acceptance only; the supported Incus-version set for this new capability is
empty.

The user has approved the selection-scoped Incus profile and #318 semantics:
persist Swagger exposure as `published` or `internal`; migrate v1 manifests to
`published` with `swarm` ownership; keep internal Swagger free of published host
ports and implicit routes; verify Portainer stack ownership without pruning;
commit selection only after Swarm convergence. WSL exposure is limited to the
already approved Portainer TCP/10001 route. The existing Windows firewall
(`RemoteAddress=Any`) and PortProxy rules remain unchanged; ports
80/443/16080/16081 must stay absent. This approval resolves the design/consent
dependency only. It is not live-run GO/JIT or scenario evidence. Native
replacement of the three owned TSW instances is authorized and optional backup
preparation is waived; native route exposure still requires exact scenario
evidence and current independent approval. Unrelated resources remain protected.

## Target Picture

- Native Linux and WSL2 use the same exact admitted candidate and a separately
  qualified Incus version.
- Setup, add, update, recovery, displayed access and verification agree on the
  same persisted selection. Add preserves the admitted baseline and adds only
  the planned dependency delta; update/recovery preserve installed selection;
  unsupported omission blocks.
- An installation-owned exposure profile contains exactly the routes derived
  from that selection. All attached-profile and instance-level devices are
  checked before manager start. The shared legacy profile is never silently
  pruned.
- Profile identity, project, route tuples, operation identity and checkpoint
  stage are durable before the first profile mutation.
- The installation operation lock is acquired first, then at most one journal
  lock; recovery uses the same order.
- Existing full-manifest Classic behavior and full-selection support remain
  required. The capability-specific empty version set does not withdraw them.
- Every live scenario has exact source, host, command, exit, before/after state,
  service/task/API/data/identity results and independently reviewed evidence.

## Requirement Clarification Gate

- Original Request: complete #449 with reviewed implementation, native Linux
  and WSL2 evidence, Three-Amigos review and an independent completion audit.
- Interpreted Intent: close every original issue requirement and AC1–AC5,
  including selective setup, add, single/batch updates, Portainer/product
  upgrades, no-op, drift/refusal, interruption/recovery, preservation, W07/R35
  disposition and W10 parent handoff.
- Change Type: lifecycle behavior, Incus provider safety, durable operation
  state, tests, documentation and live qualification.
- Affected Process Strand: issue completion and lifecycle workflow execution.
- Affected Architecture Area: application ports/orchestration, domain lifecycle
  state, Incus infrastructure adapters, CLI, persistence, Compose selection,
  arc42 and evidence.
- Explicit Requirements: matrix rows R449-01–35, narrative amendments
  R449-36–38, all currently open rows, AC1–AC5, inherited W07/R35 disposition,
  W10 handoff and #440 LCM-04 selection-matched routing in
  `.tiny-swarm/evidence/issue-449/requirement_matrix.md`.
- Implicit Requirements: preserve source/runtime provenance, prevent hidden
  route activation, isolate issue447, stop before start until exact effective
  routes pass, recover uncertain outcomes deterministically, protect unrelated
  resources and prove test-host files match the candidate.
- Assumptions: WSL route consent is TCP/10001 only; Windows firewall/PortProxy
  stay unchanged. Native route consent must be bound per live scenario. The
  three owned TSW instances may be replaced; host-baseline backup preparation
  for that replacement is waived. This does not remove product-upgrade backup,
  preservation or restoration acceptance requirements. Neither authorization
  covers unrelated resources or additional routes.
- Non-Goals: global Incus support withdrawal; non-default Incus projects;
  mutation of the shared legacy profile; Windows firewall/PortProxy changes;
  Java, Spring, Kubernetes-first or React work.
- Risks: foreign consumers/devices, premature proxy activation, unsupported
  controller behavior, uncertain writes, native memory headroom, incomplete
  issue447 inventory, historical W07 attribution and unapproved routes.
- Open Questions: no unresolved design question for authoring. Native route
  consent must be evidenced per case. Any live case that requires a route
  beyond TCP/10001 remains blocked until that exact route has separate operator
  approval.
- Blocking Questions: none for local design/implementation planning. Live
  execution still requires its route consent, exact host JIT and new Three-Amigos
  GO.
- Confidence Level: 86% for the initial clarification only.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` for workflow authoring, subject
  to all four mandatory roles approving the same
  workflow/context hashes and S3D to return `EXECUTION_PLAN`. The operator's
  2026-10-27 approval clears the product-policy question but does not waive
  S3D, implementation verification, live JIT/GO, or issue-completion gates.

## Verified Baseline and Scope

- Clean workflow baseline: `a0310224946b63e2152ff4086d22a450c3d0f214`.
- The workflow authoring branch was created from current `origin/main` and
  verified clean before workflow changes. The existing issue branch and its
  worktree remain untouched; product source changes will be copied by a
  hash-verified manifest after the workflow checkpoint is published.
- The root #355 workflow/context files remain in place. This #449 workflow is
  selected from `documentation/workflow/workflow.index.md`.
- R68 host records are read-only state snapshots, not install/upgrade passes.
  Native admission must be repeated after teardown and against the exact
  candidate before any native mutation.
- The R67j design proposal hash and its five same-hash design-policy approvals
  are retained in ignored local evidence. S449-01 publishes the accepted
  profile policy and reviewed bounded #318 owner/exposure decision into arc42;
  neither qualifies a runtime version or live scenario.

## Scope and Safety Boundaries

All open requirements in the matrix remain in scope. Historical, synthetic,
preview-only, skipped or ambiguous cases are not credited as live success.

- Do not enable host routes beyond TCP/10001 without route-specific approval
  and a new live Three-Amigos GO.
- Do not change Windows firewall or PortProxy rules.
- Do not mutate the shared `docker-swarm-manager` profile or issue447 resources.
- The selection-scoped profile reconciler must refuse before mutation when the
  controller lacks its contract. This does not withdraw full-manifest Classic
  behavior outside that new capability.
- No Incus version is supported for the new capability until the isolated
  6.0.5 fixture, independent evidence review and separate support-matrix change
  are complete.
- Do not claim preservation of explicitly replaced old instances or backups
  that the user waived.

## Architecture Constraints

- Preserve hexagonal dependencies and concrete wiring in infrastructure.
- Carry persisted post-operation selection and installation identity through
  application ports to the Incus profile lifecycle adapter.
- Persist exact project, profile identity, route tuples and checkpoint before
  the first profile mutation.
- Acquire installation lock first, then at most one journal lock; release the
  journal lock first. No reverse or nested component/product lock order.
- Use `incus init` stopped; verify every attached profile and instance device
  before explicit start. Do not use `incus launch` for this capability.
- Unknown consumers/devices, collisions, malformed output, drift, unreadable
  readback or uncertain command outcomes fail closed and retain state.
- Explicitly target Incus project `default`; project/profile isolation alone
  does not prove issue447 non-interference.
- Empty supported-version set is specific to the new profile-reconciliation
  capability and leaves existing full-manifest Classic behavior intact.

## Python Automation Assessment

Python 3.12, asyncio, unittest and existing command/provider ports are
authoritative. Expected impacts include Incus command args, node/profile
lifecycle, setup selection/state, manifest and checkpoint schemas, journal
locking, composition and tests. Prefer a dedicated profile lifecycle
port/adapter over growing the node provider. No shell interpolation,
import-time side effects, broad exception translation or weakened admission
guards.

## Frontend Assessment

No browser/React frontend exists in scope. CLI preview, selection, consent,
error and recovery output are in scope only where behavior changes; verify with
CLI regressions and documentation review.

## Test Strategy and Resilience

- Cover minimal TCP/10001, full selection, add delta, update/recovery selection
  preservation, unsupported omission, profile collision, foreign consumers,
  all-profile plus instance-device tuples, explicit project, stopped-init and
  pre-start ordering, lock contention and exact recovery binding.
- Inject applied/succeeded, explicit not-applied, applied/response-lost and
  unreadable/mismatched readback at every write boundary; inject interruption
  around every durable checkpoint. Continue only from a proven exact
  checkpoint-bound postcondition.
- The disposable listener fixture must use Incus server 6.0.5, an empty IPv4/
  IPv6 baseline for its selected unique loopback port in 61000–65535. JIT
  verifies that the selected port is unused after reservation and before any
  profile or instance write. There is no listener after profile creation or
  stopped `init`. After start, only the
  attributable listener on 127.0.0.1 at that exact loopback port may be added;
  its connect target is the disposable instance's private listener. The existing
  TCP/10001 service tuple and destination stay unchanged; firewall and PortProxy
  rules stay unchanged, with no new host route
  or listeners on 0.0.0.0/::, 80/443/16080/16081. Retain complete device tuples,
  process attribution, commands/exits and resource inventory.
- Run Python tests/quality only over SSH to the approved PC WSL test host after
  resolving the remote checkout and matching exact candidate hashes.
- Run focused tests first and `python3 tools/quality_gate.py quality` after all
  Python source/test/adapter changes. The seven stages are verification-policy,
  complexity, lint, arch-lint, arch-tests, typecheck and test.
- Local quality, live installation, browser/API and external checks have
  separate evidence states. One never substitutes for another.

## Resilience Requirements

- On timeout, disconnect, malformed response or lost write result, re-read
  checkpoint and exact project/profile/consumer/instance state while holding
  the installation lock. Do not blind retry, broaden routes or clean uncertain
  state.
- Recovery uses the checkpoint-bound profile identity and selection; changed
  devices, consumers or project state blocks.
- Cleanup requires fresh exact ownership, no-consumer and stopped-state proof.
  After start, retain state for recovery.
- External Incus writers are outside TSW flock. Require a controlled
  maintenance window and before/after state re-reads.
- A live failure is non-pass until disposition, recovery and required
  restoration are independently evidenced.

## Ordered Slices

### Slice 01 — Canonicalize the owner-approved profile policy

Purpose: canonicalize the already reviewed R67j installation-profile policy, the accepted effective-infrastructure source policy, and the newly approved bounded #318 exposure/stack-ownership contract. Preserve the capability-specific empty Incus-version set. Record the 2026-10-27 user approval without treating it as runtime support or live GO.

Prerequisites: branch/worktree verified; exact R67j hash and five owner
decisions rechecked; record the 2026-10-27 operator approval for #318 semantics
and WSL TCP/10001; compare lifecycle ADRs and active ADR index.

```yaml
slice_id: S449-01
profile: DOCS_AND_ARCHITECTURE
owner: Senior System Architect
secondary_reviewers: [Senior Requirement Engineer, Security, DevOps, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-449/adr-installation-scoped-incus-profile-draft.md, .tiny-swarm/evidence/issue-449/three-amigos-r67j-design-acceptance.md, documentation/evidence/lcm-w09-q12-design-proposal.md, documentation/arc42/09_architecture_decisions.adoc, documentation/arc42/09_decisions/adr-installation-scoped-incus-profile.adoc, documentation/arc42/09_decisions/adr-product-effective-infrastructure-source.adoc, documentation/arc42/09_decisions/adr-classic-selection-exposure-stack-ownership.adoc, .codex/evidence/slice-449-01-distribution.md, .codex/evidence/slice-449-01-consolidation.md]
affected_modules: [arc42 architecture decisions, lifecycle profile ownership, selection exposure and Portainer stack ownership]
affected_contracts: [LCM-04 selection, profile ownership, Incus capability support, published/internal exposure, manifest v2 migration, optional-stack ownership/no-prune/convergence, bounded WSL TCP/10001 route consent]
dependencies: []
parallel_group: sequential
file_locks: [.tiny-swarm/evidence/issue-449/adr-installation-scoped-incus-profile-draft.md, .tiny-swarm/evidence/issue-449/three-amigos-r67j-design-acceptance.md, documentation/evidence/lcm-w09-q12-design-proposal.md, documentation/arc42/09_architecture_decisions.adoc, documentation/arc42/09_decisions/adr-installation-scoped-incus-profile.adoc, documentation/arc42/09_decisions/adr-product-effective-infrastructure-source.adoc, documentation/arc42/09_decisions/adr-classic-selection-exposure-stack-ownership.adoc, .codex/evidence/slice-449-01-distribution.md, .codex/evidence/slice-449-01-consolidation.md]
module_locks: [arc42 decision index, lifecycle profile ownership, selection exposure and Portainer stack ownership]
contract_locks: [selection/profile contract, published/internal exposure, manifest v2 migration, optional-stack ownership/no-prune/convergence, bounded WSL TCP/10001 route consent]
architecture_locks: [Incus manager profile ownership, installation identity, optional-stack ownership boundary]
quality_gates:
  targeted: [git diff --check]
  required: [git diff --check]
documentation:
  arc42: update canonical entry
  adr: accept reviewed R67j profile policy plus the user-approved Q12/#318 exposure and ownership contract
stop_conditions: [same-hash review mismatch, owner withdraws approval, full-manifest conflict, scope exceeds current route approval]
```

Completion criteria: all three locked ADRs are created/indexed in arc42: the
installation-profile ADR, effective-infrastructure-source ADR, and the
selection/exposure/stack-ownership ADR. Together they define persisted
`published|internal` exposure; v1 `published`/`swarm` defaults without read-time
adoption; one explicit owner per stack; Portainer ownership bound to endpoint
ID, stack ID, ResourceControl identity and exact saved-definition fingerprint;
no-prune updates; selection persistence only after convergence; and the user's
TCP/10001 boundary while retaining fresh JIT/GO. Owner decisions bind exact
policy. No Incus version is supported for selection-scoped reconciliation;
`git diff --check` passes.

### Slice 02C — Harden the opt-in live fixture runner before use

Purpose: make the fixture runner fail closed on stale targets, unverifiable
approval, malformed approval data or unexpected live-state drift before any
Incus command can mutate a resource.

Prerequisites: S449-01; exact live-approval contract review; no live execution.
This is a code-and-test-only slice. It must not run Incus or contact either
test host.

```yaml
slice_id: S449-02C
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Security, Senior Tester, Senior DevOps Engineer]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/incus_profile_listener_fixture.py, tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py, .codex/evidence/slice-449-02C-distribution.md, .codex/evidence/slice-449-02C-consolidation.md]
affected_modules: [opt-in Incus fixture runner, approval validation, target-drift guard]
affected_contracts: [raw approval SHA-256, strict 16-key GO schema, workflow/runner/test hash bindings, clean expected HEAD and tree, inventory/profile/resource digest schemas, approved live route-state digest, strict proxy tuple and port-range/list parsing, strict IPv4/IPv6 listener checks, exact stopped-init effective devices and profiles, post-reservation read-only JIT, consumed BLOCKED_TARGET_DRIFT]
dependencies: [S449-01]
parallel_group: sequential
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/incus_profile_listener_fixture.py, tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py, .codex/evidence/slice-449-02C-distribution.md, .codex/evidence/slice-449-02C-consolidation.md]
module_locks: [opt-in listener fixture runner]
contract_locks: [approval digest and 16-key schema, exact workflow/runner/test bindings, clean HEAD/tree, JIT inventory/profile/resource/route-state digest, strict proxy tuple and port-range/list parser, strict effective-profile/device inventory, typed drift result]
architecture_locks: [fail-closed live qualification boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_profile_listener_fixture]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: no change
stop_conditions: [approval digest mismatch, duplicate or unknown approval keys, dirty or unexpected checkout HEAD, typed target drift, invalid authorization]
```

Completion criteria: require explicit `--expected-approval-sha256` matching
the exact raw GO bytes; parse with duplicate-key and unknown-key rejection and
require exactly these 16 top-level keys: `decision`, `source_commit`,
`workflow_sha256`, `runner_sha256`, `test_sha256`, `resource_admission_sha256`,
`issue447_inventory_sha256`, `target`, `proxy`, `cleanup`, `reviews`,
`windows_rules_unchanged`, `external_routes_enabled`,
`default_profile_sha256`, `default_profile_used_by`, and
`approved_route_state_sha256`. Require `decision` to
be `GO`; `source_commit` to be lowercase 40-hex and equal current `HEAD`; every
`*_sha256` to be lowercase 64-hex; source, workflow, runner and test hashes to
match the exact checkout bytes; and the tracked worktree to be clean.

Require `target` to contain exactly string fields `host`, `endpoint`, `project`,
`server_version`, `run_id`, `profile`, `instance`, and `image_fingerprint`, all
matching the approved target, compiled host/project/version, and derived unique
resource names; `image_fingerprint` is lowercase 64-hex. Require `proxy` to
contain exactly string fields `listen`, `connect`, and `bind`: `listen` must
be `tcp:127.0.0.1:<port>` for a unique, unused per-run port in 61000–65535;
`connect` must identify only the fixture instance's private listener; `bind`
must equal `host`. TCP/10001 is forbidden for the fixture listener and remains
bound to the existing service. The loopback-only listener is not externally
routable; verify it is absent before and after the run and that no Windows
firewall or PortProxy state changes. Require `cleanup` to be exactly the
ordered two-string list `[instance, profile]`, with the names from `target`.
Require `reviews` to contain exactly `requirements`, `architecture`, `security`,
`devops`, and `test_evidence`, each exactly `APPROVED`; a separate independent
review artifact binds all five decisions to the same raw GO SHA-256.
`windows_rules_unchanged` must be boolean `true`; `external_routes_enabled`
must be boolean `false` and means this scenario creates no additional external
route. The already authorized TCP/10001 route remains unchanged and is not
counted as a scenario-created route. Require `default_profile_used_by` to be a list of
unique string URIs in strict lexical order and compare it with the exact JIT
consumer list. Compute `default_profile_sha256` from UTF-8 canonical compact
JSON with sorted object keys and no ASCII escaping for exactly
`{"config": <complete profile config>, "devices": <complete profile devices>}`.

`resource_admission_sha256` and `issue447_inventory_sha256` bind separate,
independently reviewed evidence artifacts; the runner validates lowercase
digest syntax only and must not claim it reopened or verified those external
bytes. The independent review artifact identifies and hashes the exact resource
admission and full issue447 project/profile/consumer/device inventory artifacts.
`approved_route_state_sha256` binds an independently reviewed pre-run snapshot
of the TCP/10001 host listener rows, all Incus TCP/10001 profile and instance
routes, and the WSL Windows firewall plus PortProxy bytes (empty on native
Linux). The runner computes the same canonical UTF-8 JSON digest from its
post-reservation read-only JIT and requires a match before any Incus write. The
payload has exactly `listeners_10001_b64` (base64 list of exact `ss -H -ltnp`
rows), `incus_10001_routes` (the sorted structured route records), and
`windows_snapshot_b64` (base64 of the combined Windows snapshot; empty bytes on
native Linux), serialized with sorted keys, compact separators and
`ensure_ascii=False`. A mismatch is durably recorded as
`BLOCKED_TARGET_DRIFT`.
Read the GO once as a no-follow regular file, compare its raw bytes with caller
`--expected-approval-sha256`, then parse strict UTF-8 JSON; reject duplicate
keys and missing/extra keys at every object. Before reservation allow read-only
Git inspection and the single GO-file read only: no host/Incus command and no
lock/evidence mutation. Then acquire an exclusive O_EXCL reservation and
byte-exact NOT_RUN evidence recheck. Only after reservation perform read-only
Incus/listener JIT for target, version, project, image, unique names, complete
default-profile config/devices/consumers, selected loopback-port availability,
existing TCP/10001 tuple/destination, unchanged Windows rules, and resource
baseline before any profile or instance write. Reject malformed profile/device
records, including malformed proxy listen/connect/bind fields, invalid
IP-literal addresses, and unsupported Incus protocol pairings, even when a
proxy is not a TCP/10001 match. Accept only IPv4/IPv6 literals (including
bracketed IPv6 and the documented wildcard forms `0.0.0.0` and `[::]`) or
valid Unix socket paths. Follow the supported connection pairs in the
[Incus proxy device reference](https://linuxcontainers.org/incus/docs/main/reference/devices_proxy/).
Parse TCP/UDP port lists and ranges; reject any
range/list containing 10001 and any UDP 10001 mapping, because the approved
route is only one TCP/10001 tuple. Only an exact singleton TCP/10001 mapping
may enter the approved route-state inventory. Reject any proxy device in the attached `default` profile. After stopped
`init`, read the full expanded instance config and require the exact expected
merged device map from `default` plus the fixture profile, the exact two-profile
list, and no instance-level device overrides. Detect listeners on the selected
fixture port across IPv4 and IPv6 before start; after start allow exactly the
attributable IPv4 loopback fixture listener. Any mismatch or unreadable drift is durably recorded as
typed `BLOCKED_TARGET_DRIFT`, consumes the attempt, retains lock/evidence, and
returns nonzero before every Incus write. Regression tests prove each schema,
digest, ordering and no-mutation guard. Record exact source/test hashes for S02.

### Slice 02 — Incus 6.0.5 disposable listener fixture evidence

Purpose: verify proxy listener timing and attribution before implementing the
new capability.

Prerequisites: S449-01 and S449-02C; disposable Incus server exactly 6.0.5; fresh exact-source
and target JIT for the specific host; resource admission; full issue447
project/profile/consumer/device inventory; empty baseline for the exact selected
loopback fixture tuple and preserved baseline for the existing TCP/10001 route;
and a one-shot scenario-specific live Three-Amigos GO whose raw SHA-256 and
workflow/runner/test hashes match S449-02C, naming the exact host, expected HEAD,
default project, unique disposable instance/profile identity, inventory/profile
and resource digests, loopback-only fixture tuple and cleanup bound. The
fixture uses an unused 61000–65535 loopback listener port, never TCP/10001; the
already approved TCP/10001 route and its destination remain unchanged.
The fixture must never touch user-owned or issue447 resources. The authorized
WSL route is TCP/10001 only, with its existing Windows `RemoteAddress=Any`
firewall and PortProxy rules unchanged. Any other host/route requires exact
user approval; WSL approval does not transfer. The opt-in fixture runner is
never called by automated quality gates; tests mock its command port.

```yaml
slice_id: S449-02
profile: RUNTIME_QUALIFICATION
owner: Senior DevOps Engineer
secondary_reviewers: [Senior System Architect, Security, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-449/three-amigos-s02-live-go.json, .tiny-swarm/evidence/issue-449/r67-incus-6.0.5-listener-fixture.json, .codex/evidence/slice-449-02-distribution.md, .codex/evidence/slice-449-02-consolidation.md]
affected_modules: [Incus disposable fixture, listener evidence]
affected_contracts: [proxy bind timing, effective tuple and listener attribution, exact 16-key five-review GO, workflow/source/runner/test/target hashes, canonical default-profile config/devices digest, sorted consumer list, approved live route-state digest, external resource and issue447 evidence attestations, unchanged Windows rules, no external routes]
dependencies: [S449-02C]
parallel_group: serialized-live
file_locks: [.tiny-swarm/evidence/issue-449/three-amigos-s02-live-go.json, .tiny-swarm/evidence/issue-449/r67-incus-6.0.5-listener-fixture.json, .codex/evidence/slice-449-02-distribution.md, .codex/evidence/slice-449-02-consolidation.md]
module_locks: [Incus profile capability qualification, disposable listener fixture]
contract_locks: [16-key five-review GO schema, raw approval digest, proxy tuple, canonical default-profile digest and consumer list, approved live route-state digest, external evidence attestations, fixture evidence schema]
architecture_locks: [capability version boundary]
quality_gates:
  targeted: [git diff --check, verify exact S449-02C source/test evidence hashes]
  required: [reuse S449-02C full quality evidence only when exact source hash matches]
documentation:
  arc42: no change
  adr: record version support only after independent fixture review
stop_conditions: [version mismatch, nonempty baseline, forbidden listener, attribution failure, non-loopback or TCP/10001 fixture listener, unapproved fixture connect target, any added external route, Windows firewall or PortProxy change]
```

Completion criteria: empty baseline and no listener after profile creation/stopped init; after
start only the attributable loopback fixture listener exists and the approved
TCP/10001 service tuple/destination remains unchanged; forbidden
80/443/16080/16081 absent; exact
commands/exits, tuples/processes/resources captured and independently accepted.
The live fixture consumes the exact runner and test hashes qualified by
S449-02C; it cannot edit those code files. S449-04 owns the runtime capability registry and its consumer. The registry is
read by an infrastructure adapter at profile admission and fails closed when
missing, malformed, or unsupported. S449-02 fixture evidence alone never
admits a version. The full quality gate never invokes the live fixture.

### Slice 03 — Durable lifecycle identity and product-upgrade source authority

Purpose: persist project/profile/route identity, Swagger exposure mode and
optional-stack ownership alongside product-upgrade source, configuration and
checkpoint authority; migrate v1 to v2 as `published`/`swarm` without
read-time mutation or implicit adoption; preserve configuration/secrets and
implement the owner-private installation lock and fixed lock order.

Prerequisites: S449-01 and S449-02 fixture evidence independently accepted;
runtime capability admission contract, product source authority, migration and
recovery contracts approved.

```yaml
slice_id: S449-03
profile: DOMAIN_AND_PERSISTENCE
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Security, Senior Tester]
affected_files: [documentation/evidence/lcm-w09-transition-proposal.md, documentation/user_guide/product-upgrades.md, src/tiny_swarm_world/application/ports/lifecycle/installation_profile.py, src/tiny_swarm_world/application/ports/lifecycle/product_upgrade.py, src/tiny_swarm_world/application/services/product_upgrade.py, src/tiny_swarm_world/domain/lifecycle/models.py, src/tiny_swarm_world/domain/lifecycle/product_upgrade.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/installation_operation_lock.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/manifest.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_admission.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_capture.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_source.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_validation.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_environment.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_installation.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_journal.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_migration.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_paths.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_runtime.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_verification.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_state.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/update_journal.py, src/tiny_swarm_world/infrastructure/composition_product.py, tests/application/services/test_product_upgrade.py, tests/domain/lifecycle/test_models.py, tests/domain/lifecycle/test_selection.py, tests/domain/lifecycle/test_update_planning.py, tests/infrastructure/adapters/lifecycle/test_installation_operation_lock.py, tests/infrastructure/adapters/lifecycle/test_manifest.py, tests/infrastructure/adapters/lifecycle/test_product_configuration_source.py, tests/infrastructure/adapters/lifecycle/test_product_upgrade.py, tests/infrastructure/adapters/lifecycle/test_setup_state.py, tests/tools/test_r46_ports_policy.py, tests/tools/test_secure_runtime_paths.py, .codex/evidence/slice-449-03-distribution.md, .codex/evidence/slice-449-03-consolidation.md]
affected_modules: [manifest, setup state, checkpoints, lifecycle ports, persisted selection/exposure/stack ownership, product-upgrade admission, configuration capture/source/validation, product composition]
affected_contracts: [manifest v2 migration, published/internal exposure persistence, v1 published/swarm defaults without read-time adoption, stack ownership/no-prune/convergence, route binding, checkpoint identity, lock order, selected image/source authority, configuration and secret preservation]
dependencies: [S449-01, S449-02]
parallel_group: sequential
file_locks: [documentation/evidence/lcm-w09-transition-proposal.md, documentation/user_guide/product-upgrades.md, src/tiny_swarm_world/application/ports/lifecycle/installation_profile.py, src/tiny_swarm_world/application/ports/lifecycle/product_upgrade.py, src/tiny_swarm_world/application/services/product_upgrade.py, src/tiny_swarm_world/domain/lifecycle/models.py, src/tiny_swarm_world/domain/lifecycle/product_upgrade.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/installation_operation_lock.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/manifest.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_admission.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_capture.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_source.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_validation.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_environment.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_installation.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_journal.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_migration.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_paths.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_runtime.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_verification.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_state.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/update_journal.py, src/tiny_swarm_world/infrastructure/composition_product.py, tests/application/services/test_product_upgrade.py, tests/domain/lifecycle/test_models.py, tests/domain/lifecycle/test_selection.py, tests/domain/lifecycle/test_update_planning.py, tests/infrastructure/adapters/lifecycle/test_installation_operation_lock.py, tests/infrastructure/adapters/lifecycle/test_manifest.py, tests/infrastructure/adapters/lifecycle/test_product_configuration_source.py, tests/infrastructure/adapters/lifecycle/test_product_upgrade.py, tests/infrastructure/adapters/lifecycle/test_setup_state.py, tests/tools/test_r46_ports_policy.py, tests/tools/test_secure_runtime_paths.py, .codex/evidence/slice-449-03-distribution.md, .codex/evidence/slice-449-03-consolidation.md]
module_locks: [installation manifest and operation checkpoint, installation-operation lock, persisted selection/exposure/stack ownership, product-upgrade configuration preservation, selected product source authority]
contract_locks: [manifest/checkpoint schema, lock order, upgrade source selection, preserved configuration semantics]
architecture_locks: [hexagonal state ownership, product-upgrade port and adapter boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_models tests.domain.lifecycle.test_selection tests.domain.lifecycle.test_update_planning tests.application.services.test_product_upgrade tests.infrastructure.adapters.lifecycle.test_manifest tests.infrastructure.adapters.lifecycle.test_setup_state tests.infrastructure.adapters.lifecycle.test_product_upgrade tests.infrastructure.adapters.lifecycle.test_installation_operation_lock tests.infrastructure.adapters.lifecycle.test_product_configuration_source tests.tools.test_r46_ports_policy tests.tools.test_secure_runtime_paths]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: verify S449-01 includes the accepted ADR; do not edit the active index
  adr: implement accepted decision only
stop_conditions: [unsafe lock path, reverse/nested lock order, ambiguous legacy migration, data loss]
```

Completion criteria: manifest v2 persists selection/profile identity, exposure
mode `published|internal`, and optional-stack ownership across setup/add/update/
recovery. V1 migrates to `published`/`swarm` without read-time mutation or
implicit adoption. Product-upgrade input is source-authoritative, validated
before mutation, and preserves typed infrastructure/configuration and secrets;
lock is owner-private, no-follow, nonblocking and durable; tests cover
old/malformed state, contention, migration and checkpoint interruption.

### Slice 04 — Incus capability registry, profile reconciliation and stopped start boundary

Purpose: implement a dedicated profile lifecycle adapter and exact union checks
over every attached profile and instance device; use stopped `init`, verify,
then start.

Prerequisites: S449-03; independently accepted S449-02 fixture evidence; no
foreign consumers. This slice creates the runtime capability-registry entry
only after that fixture evidence and support decision are accepted.

```yaml
slice_id: S449-04
profile: INFRASTRUCTURE_ADAPTER
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [infra/config/node-providers/incus-profile-capability.yaml, infra/config/node-providers/provider_config.yaml, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_container_docker_runtime.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/args.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/diagnostics.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/profile/capability.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/profile/lifecycle.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/profile/policy.py, src/tiny_swarm_world/infrastructure/composition_runtime.py, tests/infrastructure/adapters/clients/lxc/profile/test_capability.py, tests/infrastructure/adapters/clients/lxc/profile/test_policy.py, tests/infrastructure/adapters/clients/lxc/swarm/test_swarm_stack_runtime.py, tests/infrastructure/adapters/clients/test_lxc_container_docker_runtime.py, tests/infrastructure/adapters/clients/test_lxc_node_provider.py, tests/infrastructure/adapters/clients/test_lxc_proxy_device_runtime.py, .codex/evidence/slice-449-04-distribution.md, .codex/evidence/slice-449-04-consolidation.md]
affected_modules: [Incus command adapter, node provider, profile lifecycle adapter, composition]
affected_contracts: [profile inventory, complete proxy tuples, explicit default project, init/verify/start]
dependencies: [S449-03]
parallel_group: sequential
file_locks: [infra/config/node-providers/incus-profile-capability.yaml, infra/config/node-providers/provider_config.yaml, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_container_docker_runtime.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/args.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/diagnostics.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/profile/capability.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/profile/lifecycle.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/profile/policy.py, src/tiny_swarm_world/infrastructure/composition_runtime.py, tests/infrastructure/adapters/clients/lxc/profile/test_capability.py, tests/infrastructure/adapters/clients/lxc/profile/test_policy.py, tests/infrastructure/adapters/clients/lxc/swarm/test_swarm_stack_runtime.py, tests/infrastructure/adapters/clients/test_lxc_container_docker_runtime.py, tests/infrastructure/adapters/clients/test_lxc_node_provider.py, tests/infrastructure/adapters/clients/test_lxc_proxy_device_runtime.py, .codex/evidence/slice-449-04-distribution.md, .codex/evidence/slice-449-04-consolidation.md]
module_locks: [Incus command adapter, profile lifecycle adapter, node provider]
contract_locks: [Incus argv, profile lifecycle port]
architecture_locks: [provider/profile adapter boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider tests.infrastructure.adapters.clients.test_lxc_proxy_device_runtime tests.infrastructure.adapters.clients.test_lxc_container_docker_runtime tests.infrastructure.adapters.clients.lxc.swarm.test_swarm_stack_runtime tests.infrastructure.adapters.clients.lxc.profile.test_policy tests.infrastructure.adapters.clients.lxc.profile.test_capability]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: no change
stop_conditions: [foreign/unknown consumer/device, collision, malformed output, uncertain outcome, unapproved listener, shared profile mutation]
```

Completion criteria: installation-owned profile matches exact selection; all inherited and
instance devices are checked; no shared profile mutation; manager starts only
after stopped-state exact route and listener checks pass.

### Slice 05 — Wire selection through setup, add, update, upgrade and recovery

Purpose: pass persisted post-operation selection and profile binding through
all lifecycle operations, refusing unsupported omission or stale state; bind
Portainer optional-stack updates to verified endpoint/stack/definition ownership,
disable pruning, and commit selection only after Swarm convergence.

Prerequisites: S449-04; durable state contract stable.

```yaml
slice_id: S449-05
profile: APPLICATION_INTEGRATION
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [documentation/contracts/lifecycle.md, documentation/user_guide/selective-setup.md, src/tiny_swarm_world/application/services/component_execution.py, src/tiny_swarm_world/application/services/component_updates.py, src/tiny_swarm_world/application/services/deployment/empty_apply.py, src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py, src/tiny_swarm_world/application/services/deployment/ensure_portainer_stack.py, src/tiny_swarm_world/application/services/deployment/workflows.py, src/tiny_swarm_world/application/ports/clients/port_portainer_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py, src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py, src/tiny_swarm_world/infrastructure/adapters/cli/selective_setup.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_observations.py, src/tiny_swarm_world/infrastructure/composition_cli.py, src/tiny_swarm_world/infrastructure/composition_deployment_selection.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, src/tiny_swarm_world/infrastructure/composition_lifecycle.py, src/tiny_swarm_world/infrastructure/composition_setup.py, src/tiny_swarm_world/infrastructure/composition.py, tests/application/services/deployment/test_deployment_workflows.py, tests/application/services/deployment/test_ensure_portainer_endpoint.py, tests/application/services/deployment/test_ensure_portainer_stack.py, tests/application/services/deployment/test_ensure_swarm_stack.py, tests/infrastructure/adapters/clients/test_portainer_http_client.py, tests/infrastructure/adapters/clients/lxc/services/test_lxc_service_clients.py, tests/e2e/classic/test_browser_evidence_paths.py, tests/infrastructure/test_composition.py, tests/infrastructure/test_selective_setup.py, tests/infrastructure/test_setup_status_cancellation.py, tests/test_package_entrypoint.py, tests/test_selective_setup_cli.py, tests/test_service_selection_cli.py, tests/test_simple_installer.py, .codex/evidence/slice-449-05-distribution.md, .codex/evidence/slice-449-05-consolidation.md]
affected_modules: [setup, services add, component execution, product upgrade, recovery, Portainer optional-stack ownership]
affected_contracts: [selection propagation, planner delta, update/recovery invariance, no implicit removal, endpoint/stack/definition ownership, no-prune update, selection commit after Swarm convergence]
dependencies: [S449-04]
parallel_group: sequential
file_locks: [documentation/contracts/lifecycle.md, documentation/user_guide/selective-setup.md, src/tiny_swarm_world/application/services/component_execution.py, src/tiny_swarm_world/application/services/component_updates.py, src/tiny_swarm_world/application/services/deployment/empty_apply.py, src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py, src/tiny_swarm_world/application/services/deployment/ensure_portainer_stack.py, src/tiny_swarm_world/application/services/deployment/workflows.py, src/tiny_swarm_world/application/ports/clients/port_portainer_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py, src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py, src/tiny_swarm_world/infrastructure/adapters/cli/selective_setup.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_observations.py, src/tiny_swarm_world/infrastructure/composition_cli.py, src/tiny_swarm_world/infrastructure/composition_deployment_selection.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, src/tiny_swarm_world/infrastructure/composition_lifecycle.py, src/tiny_swarm_world/infrastructure/composition_setup.py, src/tiny_swarm_world/infrastructure/composition.py, tests/application/services/deployment/test_deployment_workflows.py, tests/application/services/deployment/test_ensure_portainer_endpoint.py, tests/application/services/deployment/test_ensure_portainer_stack.py, tests/application/services/deployment/test_ensure_swarm_stack.py, tests/infrastructure/adapters/clients/test_portainer_http_client.py, tests/infrastructure/adapters/clients/lxc/services/test_lxc_service_clients.py, tests/e2e/classic/test_browser_evidence_paths.py, tests/infrastructure/test_composition.py, tests/infrastructure/test_selective_setup.py, tests/infrastructure/test_setup_status_cancellation.py, tests/test_package_entrypoint.py, tests/test_selective_setup_cli.py, tests/test_service_selection_cli.py, tests/test_simple_installer.py, .codex/evidence/slice-449-05-distribution.md, .codex/evidence/slice-449-05-consolidation.md]
module_locks: [selective setup orchestration, deployment selection, lifecycle composition, Portainer optional-stack ownership]
contract_locks: [resolved selection propagation, profile/checkpoint identity, endpoint/stack/definition ownership, no-prune update, selection commit after Swarm convergence]
architecture_locks: [application orchestration and ports]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.test_selective_setup tests.infrastructure.test_setup_status_cancellation tests.infrastructure.test_composition tests.application.services.test_component_updates tests.application.services.test_product_upgrade tests.application.services.deployment.test_deployment_workflows tests.application.services.deployment.test_ensure_portainer_endpoint tests.application.services.deployment.test_ensure_portainer_stack tests.application.services.deployment.test_ensure_swarm_stack tests.infrastructure.adapters.clients.test_portainer_http_client tests.infrastructure.adapters.clients.lxc.services.test_lxc_service_clients tests.e2e.classic.test_browser_evidence_paths tests.test_package_entrypoint tests.test_selective_setup_cli tests.test_service_selection_cli tests.test_simple_installer]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: no change
stop_conditions: [manifest/runtime mismatch, unsupported omission, ambient recomputation, checkpoint/profile mismatch]
```

Completion criteria: fresh minimal derives TCP/10001; full selection derives its complete
required set; add extends only the admitted baseline plus planner delta;
update/recovery preserve selection; unsupported removal blocks before mutation.
Before an optional Portainer stack update, endpoint, stack, ownership and saved
definition identity are verified; pruning is disabled; credentials/JWTs are not
persisted or logged; selection commits only after Swarm convergence.

### Slice 06 — Component transition policy, Compose, regressions, operator docs and exact-source quality

Purpose: cover every write boundary and CLI refusal; implement and verify
Swagger published/internal Compose behavior; synchronize docs and run targeted/
full quality gates on exact source. Portainer optional-stack ownership is S449-05.

Prerequisites: S449-05; SSH WSL checkout resolved and candidate hashes verified.

```yaml
slice_id: S449-06
profile: TESTS_DOCS_QUALITY
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Security, Senior System Architect, Senior Documentation Engineer]
affected_files: [documentation/user_guide/component-updates.md, infra/config/compose/swagger/docker-compose.yml, README.md, src/tiny_swarm_world/domain/update/classic_update.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/catalog.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/component_transitions.py, src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py, tests/application/services/test_component_updates.py, tests/architecture/test_legacy_surface_documentation.py, tests/domain/update/test_classic_update.py, tests/infrastructure/adapters/lifecycle/test_catalog.py, tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py, tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py, tests/test_classic_update_cli.py, .codex/evidence/slice-449-06-distribution.md, .codex/evidence/slice-449-06-consolidation.md]
affected_modules: [provider tests, recovery tests, CLI, Swagger exposure, Compose selection, user docs, evidence]
affected_contracts: [uncertain write outcomes, no route expansion, CLI consent, selection behavior, published/internal Swagger exposure, internal mode has no published host ports or implicit routes]
dependencies: [S449-05]
parallel_group: sequential
file_locks: [documentation/user_guide/component-updates.md, infra/config/compose/swagger/docker-compose.yml, README.md, src/tiny_swarm_world/domain/update/classic_update.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/catalog.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/component_transitions.py, src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py, tests/application/services/test_component_updates.py, tests/architecture/test_legacy_surface_documentation.py, tests/domain/update/test_classic_update.py, tests/infrastructure/adapters/lifecycle/test_catalog.py, tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py, tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py, tests/test_classic_update_cli.py, .codex/evidence/slice-449-06-distribution.md, .codex/evidence/slice-449-06-consolidation.md]
module_locks: [Incus safety regressions, lifecycle recovery tests, Swagger exposure policy, Compose selection, operator documentation]
contract_locks: [CLI and route semantics, "published/internal Swagger exposure", internal mode has no published host ports or implicit routes]
architecture_locks: [hexagonal boundaries]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.test_component_updates tests.architecture.test_legacy_surface_documentation tests.domain.update.test_classic_update tests.infrastructure.adapters.lifecycle.test_catalog tests.infrastructure.adapters.lifecycle.test_native_component_transitions tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml tests.test_classic_update_cli]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: verify links and includes
  adr: verify canonical decision
stop_conditions: [weakened guard, missing applied/not-applied/lost/unreadable cases, docs imply unsupported version or unapproved route, quality failure]
```

Completion criteria: each write boundary covers applied, explicit failure, applied/lost result,
unreadable/mismatched readback and checkpoint interruption; default `published`
behavior remains compatible; tests assert `internal` Swagger has no published
host ports or implicit routes. Exact recovery and lock behavior pass; docs match
implementation; full seven-stage gate passes on exact SSH WSL candidate;
independent implementation review accepts.

### Slice 07 — Fresh host JIT and scenario-specific live Three-Amigos GO

Purpose: establish native and WSL eligibility for each live case after exact
source verification, support entry and local quality pass.

Prerequisites: S449-06; user approval for the exact scenario; Incus maintenance
window with external writers stopped.

```yaml
slice_id: S449-07
profile: HOST_PREFLIGHT
owner: Senior DevOps Engineer
secondary_reviewers: [Requirements, Architecture, Security, Test/Evidence]
affected_files: [.tiny-swarm/evidence/issue-449/r69-native-jit.json, .tiny-swarm/evidence/issue-449/r69-wsl-jit.json, .tiny-swarm/evidence/issue-449/three-amigos-r69-live-gate.md, tests/infrastructure/adapters/host/test_preflight_evidence_writer.py, tests/infrastructure/adapters/repositories/test_native_resource_budget.py, tests/test_incus_preparation.py, tests/test_prepare_linux.py, .codex/evidence/slice-449-07-distribution.md, .codex/evidence/slice-449-07-consolidation.md]
affected_modules: [source/resource/route admission, host JIT]
affected_contracts: [exact candidate, issue447 isolation, consent, capacity]
dependencies: [S449-06]
parallel_group: serialized-live
file_locks: [.tiny-swarm/evidence/issue-449/r69-native-jit.json, .tiny-swarm/evidence/issue-449/r69-wsl-jit.json, .tiny-swarm/evidence/issue-449/three-amigos-r69-live-gate.md, tests/infrastructure/adapters/host/test_preflight_evidence_writer.py, tests/infrastructure/adapters/repositories/test_native_resource_budget.py, tests/test_incus_preparation.py, tests/test_prepare_linux.py, .codex/evidence/slice-449-07-distribution.md, .codex/evidence/slice-449-07-consolidation.md]
module_locks: [native host inventory, WSL host inventory, resource admission, issue447 isolation]
contract_locks: [host ownership, route consent, resource admission]
architecture_locks: [project/profile isolation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.host.test_preflight_evidence_writer tests.infrastructure.adapters.repositories.test_native_resource_budget tests.test_incus_preparation tests.test_prepare_linux, read-only exact-source and host inventory]
  required: [fresh independent Three-Amigos GO per host and scenario, python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: verify accepted policy/support entry
stop_conditions: [native capacity guard fails, issue447 consumers/devices unproven, forbidden listener, profile drift, Windows rules differ or need change, route beyond TCP/10001 required]
```

Completion criteria: both issue447 projects' profile isolation/references/consumers/effective
devices are enumerated; native post-teardown capacity is admitted against exact
candidate and 10/6/1-GiB tree; WSL firewall/PortProxy remain unchanged; per-case
source, profile, listener and selection evidence is reviewed. Any other route
needed remains `LIVE_CONSENT_MISSING` and blocks that case.

### Slice 08 — Execute open native and WSL setup/update/recovery scenarios

Purpose: complete all still-open issue scenario rows, including Q02–Q20
applicable cases, Q12/LIVE-4, Q16–Q18, Q19 remaining variants and R35/W07
disposition. Existing bounded evidence is reused only if exact source and
provenance remain valid.

Prerequisites: S449-07 GO for the exact host/case; WSL route remains TCP/10001
only and native route has its own exact consent; failure cases have reviewed
recovery and cleanup. For WSL Q12/LIVE-4, only TCP/10001 may be reachable;
internal Swagger publishes no host port or implicit route; Windows firewall and
PortProxy remain unchanged. The approved design does not itself qualify Q12 or
authorize execution without current JIT/GO.

```yaml
slice_id: S449-08
profile: SERIALIZED_LIVE_QUALIFICATION
owner: Senior DevOps Engineer
secondary_reviewers: [Requirements, Architecture, Security, Test/Evidence]
affected_files: [.tiny-swarm/evidence/issue-449/live-scenarios.md, documentation/evidence/lcm-w09-blocker-refinement.md, documentation/evidence/lcm-w09-q16-wsl-r52.md, documentation/evidence/lcm-w09-q16-wsl-r54.md, .codex/evidence/slice-449-08-distribution.md, .codex/evidence/slice-449-08-consolidation.md]
affected_modules: [native/WSL setup, component update, Portainer managed stack, product upgrade, recovery]
affected_contracts: [selection, no-op, task/API/auth/data/identity preservation, failure disposition]
dependencies: [S449-07]
parallel_group: serialized-live
file_locks: [.tiny-swarm/evidence/issue-449/live-scenarios.md, documentation/evidence/lcm-w09-blocker-refinement.md, documentation/evidence/lcm-w09-q16-wsl-r52.md, documentation/evidence/lcm-w09-q16-wsl-r54.md, .codex/evidence/slice-449-08-distribution.md, .codex/evidence/slice-449-08-consolidation.md]
module_locks: [native Incus default project, WSL Incus default project, Windows route state, private scenario evidence ledger]
contract_locks: [scenario provenance, serial host mutation, recovery identity]
architecture_locks: [route/profile ownership]
quality_gates:
  targeted: [scenario command and direct before/after state]
  required: [per-scenario Three-Amigos/JIT and independent evidence review]
documentation:
  arc42: no change
  adr: no change
stop_conditions: [unapproved route, source mismatch, issue447 interference, mutation failure without reviewed recovery, missing attribution]
```

Completion criteria: every applicable requirement row has native and WSL scenario evidence,
exact commands/exits, source/target, direct before/after state, identities,
task/API/auth/data status, recovery/repeat/no-op, cleanup and redacted artifacts.
Historical, synthetic, mock, preview-only, skipped or unattributed results stay
non-pass. W07 cause may remain a documented non-pass only if the issue's parent
owner accepts the disposition; otherwise the issue remains open.

### Slice 09 — AC1–AC5/W10 traceability and independent completion audit

Purpose: reconcile requirement matrix, acceptance checklist, changed files,
test results, risks, parent #440 handoff and the final issue audit.

Prerequisites: S449-08 evidence and hashes verified; no open requirement.

```yaml
slice_id: S449-09
profile: ISSUE_CLOSURE_AUDIT
owner: Senior Requirement Engineer
secondary_reviewers: [Issue Completion Auditor, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-449/acceptance_checklist.md, .tiny-swarm/evidence/issue-449/acceptance_crosswalk.md, .tiny-swarm/evidence/issue-449/changed_files.md, .tiny-swarm/evidence/issue-449/completion_audit.md, .tiny-swarm/evidence/issue-449/final_completion_report.md, .tiny-swarm/evidence/issue-449/implementation_summary.md, .tiny-swarm/evidence/issue-449/remaining_risks.md, .tiny-swarm/evidence/issue-449/requirement_matrix.md, .tiny-swarm/evidence/issue-449/test_results.md, .tiny-swarm/evidence/issue-449/w10-handoff-issue-449-draft.md, documentation/evidence/lcm-w09-ac5-traceability.md, documentation/evidence/lcm-w09-qualification.md, .codex/evidence/slice-449-09-distribution.md, .codex/evidence/slice-449-09-consolidation.md]
affected_modules: [issue evidence, parent handoff, closure report]
affected_contracts: [AC1–AC5, W10, issue completion status]
dependencies: [S449-08]
parallel_group: sequential
file_locks: [.tiny-swarm/evidence/issue-449/acceptance_checklist.md, .tiny-swarm/evidence/issue-449/acceptance_crosswalk.md, .tiny-swarm/evidence/issue-449/changed_files.md, .tiny-swarm/evidence/issue-449/completion_audit.md, .tiny-swarm/evidence/issue-449/final_completion_report.md, .tiny-swarm/evidence/issue-449/implementation_summary.md, .tiny-swarm/evidence/issue-449/remaining_risks.md, .tiny-swarm/evidence/issue-449/requirement_matrix.md, .tiny-swarm/evidence/issue-449/test_results.md, .tiny-swarm/evidence/issue-449/w10-handoff-issue-449-draft.md, documentation/evidence/lcm-w09-ac5-traceability.md, documentation/evidence/lcm-w09-qualification.md, .codex/evidence/slice-449-09-distribution.md, .codex/evidence/slice-449-09-consolidation.md]
module_locks: [issue evidence package, "parent #440 handoff", final completion status]
contract_locks: ["parent #440 traceability", final status]
architecture_locks: []
quality_gates:
  targeted: [git diff --check, independent issue-completion-auditor review]
  required: [all R449 rows VERIFIED, AC1–AC5 and W10 accepted]
documentation:
  arc42: verify canonical ADR and links
  adr: accepted canonical decision linked
stop_conditions: [any open/partial requirement, unverified hash, route/version gap, missing W10 or parent acceptance]
```

Completion criteria: every requirement has implementation and verification evidence, AC1–AC5
and W10 are accepted, the independent auditor returns PASS, and only then may
GitHub #449 be closed. Otherwise status remains INCOMPLETE/BLOCKED/FAILED.

## Slice Dependency Graph

```text
S449-01 → S449-02C → S449-02 → S449-03 → S449-04 → S449-05 → S449-06 → S449-07 → S449-08 → S449-09
```

The version fixture precedes implementation because the new capability has no
supported version. Exact-source quality precedes live JIT. Live validation is
serialized per host/project.

## Requirement-to-Slice and Verification Map

The matrix is the detailed source of current evidence and status. This map
assigns every row to workflow work; existing bounded evidence is accepted only
where its exact source and provenance remain valid.

| Requirement | Slice owner | Verification/evidence target |
|---|---|---|
| R449-01 | S07–S09 | W01 host/profile/version/selection matrix and cross-host scenario ledger |
| R449-02 | S07–S08 | Current-candidate fresh minimal and two optional selections per eligible host |
| R449-03 | S05, S08 | Add selection preserves foundation, node/data/auth identity |
| R449-04 | S06, S08 | Single/batch transitions, task/image/metadata and failure/recovery rows |
| R449-05 | S08 | Native bounded result retained; WSL Q12/LIVE-4 uses approved #318 ownership/exposure semantics and TCP/10001-only consent; current implementation, JIT, same-hash GO and live evidence remain required |
| R449-06–07 | S08 | Exact-source product transition, direct after-state and literal repeat `no_op` |
| R449-08–10 | S06, S08 | Drift/source refusal, mandatory-foundation behavior, interruption/partial recovery |
| R449-11–14 | S08–S09 | AC1–AC4 per-case hashes, before/after, auth/data/identity, applicability, cleanup/restoration |
| R449-15 | S09 | AC5 traceability and accepted W10/parent #440 handoff |
| R449-16 | S06–S07 | Exact-candidate targeted and full SSH/WSL quality gates |
| R449-17–18 | S06, S08 | Mutation help/preview/consent and exact source/host/command/exit provenance |
| R449-19 | S01, S03–S06 | Architecture review, accepted ADR, provider/lifecycle boundary and no second engine |
| R449-20 | S07–S08 | Authorization per instance/route, exact ownership, scoped recovery/disposal |
| R449-21 | S08–S09 | W07 cause/restoration disposition and R35 evidence status |
| R449-22 | S09 | Deliverables and independent issue-completion audit |
| R449-23–26 | S06, S09 | Fixed transition/catalog policy, Compose mapping, regression/quality and truthful docs |
| R449-27–28 | S07–S08 | Historical failed-attempt separation and actual resource/socket admission |
| R449-29–31 | S05–S08 | New-only runtime observations, metadata preservation and honest observation failure |
| R449-32–34 | S07–S08 | Authorized native disposal, resource admission, fresh native selections |
| R449-35 | S03, S08 | Effective-infrastructure source authority, native pass and WSL recovery attribution |
| R449-36–37 | S05–S06 | Foundation-only empty Apply and selected image-authority propagation |
| R449-38 | S05–S06, S08 | Cancellation status, bounded async regression and live interruption disposition |
| AC1–AC4 | S08–S09 | Scenario evidence ledger, preservation, applicable live results and cleanup |
| AC5 / W10 | S09 | Parent bullet-to-artifact crosswalk, W10 acceptance and independent audit |

  The Q12/WSL LIVE-4 product-policy and route-consent dependency is resolved by
the operator's 2026-10-27 decision, including #318 semantics. Execution remains
blocked until canonical ADR acceptance, implementation, exact-source quality,
fresh host JIT and scenario-specific same-hash GO pass. This decision does not
infer a pass from native Q12 or historical WSL candidates.

## Parallel Execution

- Can this workflow run in parallel? No for implementation or live mutation;
  independent read-only reviews may run concurrently.
- Conflicting workflows: any Incus/provider/network/lifecycle operation using
  the same modules, manifests/journals, default Incus projects or hosts.
- Shared files: lifecycle models, setup state, provider/composition, CLI,
  qualification docs and issue evidence.
- Shared infrastructure: approved native Linux test host and approved PC WSL
  test host, each with a default Incus project; WSL Windows firewall/PortProxy.
- Requires isolated worktree: yes; this workflow branch is isolated. Keep the
  original source worktree untouched until explicit consolidation.
- Requires serialized live validation: yes.
- Merge-order constraints: ADR → fixture/support → implementation/tests → exact
  quality → JIT/Three-Amigos → live cases → evidence/audit.

## Automatic Work Distribution Policy

For every executable slice, analyze safe specialist decomposition. Use real
Codex subagents where supported; otherwise document role-based fallback.
Require `.codex/evidence/slice-449-<suffix>-distribution.md` before implementation
and `.codex/evidence/slice-449-<suffix>-consolidation.md` after implemented slices.
Codex is final integration/test/evidence owner.

Stream map: backend/domain/application/provider; frontend/status only if CLI
output changes; tests; runtime; docs; quality; architecture; security. Use
isolated stream worktrees only for disjoint locks and stable contracts. Do not
parallelize overlapping files, unclear/contradictory design, ordered migrations,
shared schema changes, generated conflicts, unsafe live changes, unclear
secrets, weakened guards, or a Three-Amigos no-parallel decision.

No live validation runs in parallel.

## Git Worktree Execution Rule

Every workflow uses its own worktree. Workers verify this workflow branch before
editing, stay within declared paths/locks and do not merge directly. Do not
switch, clean or reset the original mixed source worktree. Codex consolidates
reviewed changes only after required checks and evidence pass.

## Ownership Map

- Workflow sequence: Senior Workflow Architect.
- Requirements/EPIC drift: Senior Requirement Engineer.
- Architecture/arc42/provider boundary: Senior System Architect.
- Incus/runtime qualification: Senior DevOps Engineer.
- Python implementation: Senior Python Automation Developer.
- Test/evidence/quality: Senior Tester and Test/Evidence reviewer.
- Route consent and ownership: Security reviewer.
- Final acceptance: independent `issue-completion-auditor`.
- Codex: final integration and decision owner.

## Four-Role Three-Amigos Workflow Release Gate

Workflow authoring is not workflow readiness. Record the four mandatory reviews
against the final workflow/context-pack hashes here; a prior design-only
approval of R67j is not a workflow review.

| Role | Required review | Current status |
|---|---|---|
| Senior Requirement Engineer | R449-01–38, AC1–AC5, W10, EPIC #440 and traceability | See hash-bound release evidence for this snapshot |
| Senior System Architect | hexagonal boundaries, Incus profile ownership, persistence, arc42 and locks | See hash-bound release evidence for this snapshot |
| Senior Python Automation Developer | ports/adapters/composition, slice paths, testability and lock ownership | See hash-bound release evidence for this snapshot |
| Senior Tester | acceptance evidence, exact test gates, live/local state and lock ownership | See hash-bound release evidence for this snapshot |

Release decision: execution is eligible only when the four-role record contains
`APPROVED` decisions for one workflow/context hash set and S3/S3D returns
`EXECUTION_PLAN` for that same revision. Record each review artifact and hash
in `.tiny-swarm/evidence/issue-449/three-amigos-workflow-release.md`.

## S3 / S3D Preflight and Clean Execution Handoff

Before any implementation write:

1. Create one workflow-authoring baseline commit containing only the reviewed
   workflow, sibling context pack, workflow index and directly required
   executor discovery support. This is a workflow-authoring checkpoint, not an
   implementation slice. Keep ignored `.tiny-swarm/` approvals, host inventory,
   requirement matrix and source-copy evidence local; never force-add them.
2. Push the reviewed workflow-authoring baseline to
   `origin/feature/workflow-lcm-w09-20261027` as required by workflow-authoring.
   Do not open a PR from that branch. Create a clean
   `feature/lcm-w09-issue449-implementation-20261027` worktree from the
   reviewed checkpoint. Run S3/S3D on that clean implementation branch before
   S449-01, then copy only slice-approved files using the exact-byte
   source-copy manifest. Never execute slices in the dirty source checkout.

3. Copy the ignored local `.tiny-swarm/evidence/issue-449/` files needed by
   `context-pack.json` (requirement matrix, acceptance crosswalk/checklist,
   release review and worktree-copy manifest) from the source snapshot into the
   clean worktree without changing bytes. Verify every recorded SHA-256 before
   use; keep them ignored/untracked and never force-add them. Record the copy
   inventory and hashes in the local S3D preflight evidence.
4. Verify `git branch --show-current`, the local feature branch ref, and
   `git status --short --branch`; require the expected branch and a clean tree
   before applying only the selected slice's hash-verified overlay paths from
   the preserved source snapshot. The workflow branch must be free and checked
   out only in the clean execution worktree.
5. Record S3_STATUS, S3_BRANCH, S3_SCOPE and S3_CLASSIFY, including source and
   overlay hashes, in `.tiny-swarm/evidence/issue-449/s3d-preflight.md`.
6. Run S3D over all ten YAML blocks. Validate concrete dependencies and
   acyclicity; exact file/contract/module/architecture locks; affected streams;
   owner/reviewer routing; serial/parallel decision; quality gates; and
   distribution/consolidation evidence paths. Any overlapping lock or missing
   owner/path returns `LOCK_CONFLICT` or `ORCHESTRATION_BLOCKER`; do not edit.
7. Store the structured `EXECUTION_PLAN` and selected stream map in the same
   preflight record. Re-run S3/S3D after workflow, scope, branch, overlay or
   lock changes. Only then apply the selected slice overlay and begin work.

The workflow-authoring worktree is not an implementation worktree. After this
baseline is published, create the implementation worktree from its checkpoint,
require a clean status there, and run S3/S3D before any slice write. Preserve the
separate source checkout for hash-verified, scope-limited file transfer only.

## Issue Completion Discipline

- Requirement matrix: `.tiny-swarm/evidence/issue-449/requirement_matrix.md`.
- Evidence path: `.tiny-swarm/evidence/issue-449/` and
  `documentation/evidence/lcm-w09-qualification.md`.
- Required evidence: `requirement_matrix.md`, `implementation_summary.md`,
  `changed_files.md`, `test_results.md`, `remaining_risks.md`,
  `acceptance_checklist.md`, `acceptance_crosswalk.md`, `final_completion_report.md`,
  completion audit and W10 handoff.
- Requirement Lead: Senior Requirement Engineer maps all issue/EPIC sentences
  and AC1–AC5.
- System Architect Reviewer: validates provider, profile, persistence,
  selection and arc42 fit.
- Test/Evidence Reviewer: verifies exact scenario and quality evidence.
- Issue Completion Auditor: independent review after implementation and handoff.
- DONE rule: any open, partial, unverified or unattributed requirement forces
  `INCOMPLETE`, `BLOCKED` or `FAILED`; never DONE.

## Quality Gates

Run Python only through SSH to the approved PC WSL test host after resolving the
remote checkout and verifying exact candidate hashes. Commands from repository
root:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_node_provider tests.infrastructure.test_selective_setup
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

The full gate is mandatory for product code. `arch-lint` requires
`.importlinter`; `arch-tests` uses the architecture test modules. Workflow/docs
only require `git diff --check`. Local quality is never live success.

## Documentation Governance and arc42 Check Status

Status: the ADR convention and active index were inspected. The new
installation-owned profile decision is a draft awaiting canonical placement
and accepted review; no Incus version is supported yet for this capability.
S449-01 places the exact owner-approved R67j policy, effective-infrastructure-
source decision, and selection/exposure/stack-ownership decision in
`documentation/arc42/09_decisions/`, and adds all three includes to
`documentation/arc42/09_architecture_decisions.adoc`.
S449-03 owns product-upgrade implementation under that accepted decision, not
the ADR or active index. Product and user documentation changes land only with
their owning verified code slice and may not describe planned or unsupported
behavior as implemented.

Arc42 check before release: verify decision scope against LCM-04/#440, index
include resolution, no conflict with Classic full-manifest behavior, and
consistent profile ownership, selection, consent and capability-version
statements. Record checked files and hashes in the workflow release review.
The workflow-executor arc42 start condition is satisfied in order: S449-01 is
the first docs-only slice, and no product-code slice may execute until its
canonical ADR and index include are reviewed and committed.

## Stop Conditions

Stop the affected slice on route consent beyond TCP/10001, Windows rule changes,
unknown Incus consumer/device, unsupported capability version, issue447 risk,
native resource guard failure, exact-source mismatch, stale checkpoint, unknown
writer, process/result ambiguity, failed gate, missing reviewer or lost
provenance. Record canonical LIVE/QUALITY state. Continue independent local
work only when it does not rely on the blocked condition.

## Commit, Push and PR Plan

- The workflow-only checkpoint is an ancestor of the final implementation branch. Each implementation slice commit stays on `feature/lcm-w09-issue449-implementation-20261027`; the final PR is opened only from that implementation branch.
- Each implementation slice is one commit; never combine slices. All scoped
  workflow and product commits are published together in the user's single PR.
- Run exact `push auto` only after implementation, issue evidence, independent
  completion audit, green required checks, configured SonarQube status and known
  mergeability. The guarded lifecycle then merges the PR, closes #449, deletes
  the merged remote branch and cleans the local branch.

## Definition of Done

Issue #449 is complete only when every requirement and AC1–AC5 is implemented
and verified on exact source; all applicable native and WSL2 live scenarios
pass; current route consent and recovery bounds are honored; W10/parent handoff
is accepted; required quality gates pass; all evidence agrees; the independent
completion auditor returns PASS; and the issue is closed through the approved
publication lifecycle. Any missing condition keeps it open.

## Handoff to workflow execute

S449-01 may begin only after all four workflow Three-Amigos roles approve the
same workflow/context-pack hashes, the recorded S3/S3D preflight returns
`EXECUTION_PLAN`, and implementation is moved to a clean worktree. Implementation
requires canonical ADR and qualified Incus version. Live slices require
exact-scenario Three-Amigos GO and fresh host JIT; TCP/10001-only WSL consent and
unchanged Windows rules are mandatory. No other host or route inherits that
approval.
