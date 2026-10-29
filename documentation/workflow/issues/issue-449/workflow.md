# LCM-W09 — Selective installation and upgrades on native Linux and WSL2

Workflow ID: `issue-449-lcm-w09`
Status: ACTIVE_FOR_ISSUE_449 v1.71 — user-authorized issue execution; every slice requires fresh same-hash reviews and its own S3D EXECUTION_PLAN; live host mutations require scenario-specific GO
Issue: [#449 LCM-W09](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449)
Epic: [#440 LCM-04](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/440)
Branch: `feature/lcm-w09-issue449-implementation-20261027`
Workflow authoring branch: `docs/workflow-lcm-w09-route-baseline-20261027`
Baseline: `a0310224946b63e2152ff4086d22a450c3d0f214`
ACTIVE_FOR_ISSUE_449 v1.71. The user explicitly authorized completion of issue #449 on the named test hosts and a bounded diagnosis of the latest native blocker. This permits issue execution to proceed, while each slice still requires fresh same-hash reviews and a phase-specific S3D EXECUTION_PLAN; every live host mutation still requires its applicable host/scenario admission and GO. The existing S449-02 pre-GO plan authorizes only its original exact read-only phase.
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
commit selection only after Swarm convergence. The TSW application route under
qualification is limited to Portainer TCP/10001. For this run, the user has
accepted the existing Windows firewall (`RemoteAddress=Any`) and complete
PortProxy state as-is; both must remain unchanged. The fixture neither adds nor
validates reachability through other pre-existing Windows forwards. Ports
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
- Acceptance trace details: AC1 requires current command, runtime/version,
  timestamp and outcome for every host/transition; AC2 requires before/after
  data, service identity, endpoints and credential-state evidence; AC3 forbids
  skipped, mocked or login-only checks from satisfying live acceptance; AC4
  requires cleanup/restoration evidence and explicit unsupported combinations;
  AC5 traces each parent #440 LCM-01–LCM-05 requirement and W10 handoff to
  implementation and verification artifacts. These requirements remain open
  until evidence is reviewed; the workflow amendment does not claim completion.
- Implicit Requirements: preserve source/runtime provenance, prevent hidden
  route activation, isolate issue447, stop before start until exact effective
  routes pass, recover uncertain outcomes deterministically, protect unrelated
  resources and prove test-host files match the candidate.
- Assumptions: TSW application exposure is limited to TCP/10001. The current
  WSL Windows firewall/PortProxy state is accepted as-is for this run and must
  stay byte-identical. No new externally reachable TSW listener or route may
  be introduced; the sole temporary exception is the GO-bound loopback fixture
  listener, which must be removed and verified absent after cleanup. Native
  route consent must be bound per live scenario. The
  three owned TSW instances may be replaced; host-baseline backup preparation
  for that replacement is waived. This does not remove product-upgrade backup,
  preservation or restoration acceptance requirements. Neither authorization
  covers unrelated resources or additional routes.
- Non-Goals: global Incus support withdrawal; management or reconciliation in
  non-default Incus projects (read-only TCP/10001 route inventory still covers
  every Incus project);
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
- The expected final R67j acceptance bytes are missing; the older acceptance is
  superseded and must not be substituted. S449-01 records provenance and creates
  a separate acceptance from current canonical inputs and fresh same-hash
  reviews under `.tiny-swarm/evidence/issue-449/s449-private-20261027/`.
  S449-01 publishes the accepted profile policy and reviewed bounded #318
  owner/exposure decision into arc42; neither qualifies a runtime version or
  live scenario.

## Private Evidence Storage

The parent `.tiny-swarm/evidence/issue-449/` directory has a broad inherited
NTFS ACL and is not an approved location for private evidence. Keep private
records below
`.tiny-swarm/evidence/issue-449/s449-private-20261027/`.

Only these human-only S449-01 design and provenance artifacts may use a
verified restrictive NTFS ACL instead of POSIX modes:

- `adr-installation-scoped-incus-profile-draft.md`
- `three-amigos-r67j-design-acceptance.md`
- `source-copy-manifest-v1.8-20261027.md`
- `private-acl-verification.md`

The ACL exception requires inheritance removed and access limited to the
current user, SYSTEM and Administrators; reject broad `Users` or
`Authenticated Users` principals. These human-only files are never read or
written by the fixture runner. All workflow-release approval records and all
other private evidence require the POSIX ext4 rule below.

Every runner-used S02 capture, GO, reservation/NOT_RUN, review and result
artifact must reside in the private evidence directory of an approved live
checkout on a local Linux/WSL ext4 filesystem. The checkout must not be under
`/mnt/c`, `/mnt/d` or another DrvFS/NTFS mount; ACL-only protection is not
sufficient. Verify the filesystem type (for example with `findmnt -T`) before
writing, require directory mode 0700 and file mode 0600, and fail closed if
either the filesystem or permissions are not verifiable. Store the target
filesystem check in
`.tiny-swarm/evidence/issue-449/s449-private-20261027/s02-private-posix-verification.md`.
The workflow-execution approval record and all other private runtime evidence
also use the private POSIX ext4 directory. Keep public requirement/acceptance
artifacts at their declared paths and do not store credentials or secrets in
any evidence file.

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
and WSL TCP/10001; verify and record private evidence directory permissions;
compare lifecycle ADRs and active ADR index. If
`.tiny-swarm/evidence/issue-449/source-copy-manifest-v1.3.md` expects
R67j acceptance SHA-256
`6768cd40a6dfda4d639acda8afcb721472959bd6f6ffd2c6e12eedbe022b576f` but those
bytes are absent, record that absence in
`.tiny-swarm/evidence/issue-449/s449-private-20261027/source-copy-manifest-v1.8-20261027.md`.
Do not substitute or copy the superseded `493c613f731aa549fdc4fa4f6002b82f069553446c6509b7ea8cf3a8b92e5345`
record as the missing final artifact. Reconstruct a new acceptance from the
exact current SHA-256 of
`documentation/arc42/09_decisions/adr-installation-scoped-incus-profile.adoc`
and `documentation/evidence/lcm-w09-q12-design-proposal.md`, plus fresh
same-hash Requirement, Architecture, Security, DevOps and Test/Evidence
reviews. Copy neither superseded acceptance bytes nor unverified source bytes
to the destination. Store the reconstructed record at
`.tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-r67j-design-acceptance.md`,
record its new SHA-256 in the provenance manifest, and never claim it recovers
either historical hash.
Fail closed if the current source hashes, required reviews or owner-only ACL
cannot be verified. Keep all private S449-01 records under the owner-only child
directory.

```yaml
slice_id: S449-01
profile: DOCS_AND_ARCHITECTURE
owner: Senior System Architect
secondary_reviewers: [Senior Requirement Engineer, Security, DevOps, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-449/s449-private-20261027/adr-installation-scoped-incus-profile-draft.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-r67j-design-acceptance.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/private-acl-verification.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/source-copy-manifest-v1.8-20261027.md, documentation/evidence/lcm-w09-q12-design-proposal.md, documentation/arc42/09_architecture_decisions.adoc, documentation/arc42/09_decisions/adr-installation-scoped-incus-profile.adoc, documentation/arc42/09_decisions/adr-product-effective-infrastructure-source.adoc, documentation/arc42/09_decisions/adr-classic-selection-exposure-stack-ownership.adoc, .codex/evidence/slice-449-01-distribution.md, .codex/evidence/slice-449-01-consolidation.md]
affected_modules: [arc42 architecture decisions, lifecycle profile ownership, selection exposure and Portainer stack ownership]
affected_contracts: [LCM-04 selection, profile ownership, Incus capability support, published/internal exposure, manifest v2 migration, optional-stack ownership/no-prune/convergence, bounded WSL TCP/10001 route consent]
dependencies: []
parallel_group: sequential
file_locks: [.tiny-swarm/evidence/issue-449/s449-private-20261027/adr-installation-scoped-incus-profile-draft.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-r67j-design-acceptance.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/private-acl-verification.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/source-copy-manifest-v1.8-20261027.md, documentation/evidence/lcm-w09-q12-design-proposal.md, documentation/arc42/09_architecture_decisions.adoc, documentation/arc42/09_decisions/adr-installation-scoped-incus-profile.adoc, documentation/arc42/09_decisions/adr-product-effective-infrastructure-source.adoc, documentation/arc42/09_decisions/adr-classic-selection-exposure-stack-ownership.adoc, .codex/evidence/slice-449-01-distribution.md, .codex/evidence/slice-449-01-consolidation.md]
module_locks: [arc42 decision index, lifecycle profile ownership, selection exposure and Portainer stack ownership]
contract_locks: [selection/profile contract, published/internal exposure, manifest v2 migration, optional-stack ownership/no-prune/convergence, bounded WSL TCP/10001 route consent]
architecture_locks: [Incus manager profile ownership, installation identity, optional-stack ownership boundary]
quality_gates:
  targeted: [git diff --check]
  required: [git diff --check]
documentation:
  arc42: update canonical entry
  adr: accept reviewed R67j profile policy plus the user-approved Q12/#318 exposure and ownership contract
stop_conditions: [same-hash review mismatch, owner withdraws approval, full-manifest conflict, scope exceeds current route approval, private evidence ACL is broad or unverifiable]
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
Incus command can mutate a resource. Accept an empty TCP/10001 host-listener
and Incus-route baseline only when successful strict reads and the exact empty
state are independently approved, digest-bound and verified unchanged.

Prerequisites: S449-01; exact live-approval contract review; no live execution.
This S449-02C implementation slice is code/test-only and permits SSH/SCP only to the approved PC WSL test host for exact remote checkout/hash verification and the targeted tests/QUALITY gates listed here. It must not contact the native host, run Incus, invoke any fixture mode, or make host/system/service changes. After S449-02C source and reviews are exact and approved, the separate S449-02 pre-GO evidence phase may perform only the bounded read-only checks below on each of the two approved targets; this exception does not authorize normal fixture run mode or mutations.

```yaml
slice_id: S449-02C
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/incus_profile_listener_fixture.py, tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py, .codex/evidence/slice-449-02C-distribution.md, .codex/evidence/slice-449-02C-consolidation.md]
affected_modules: [opt-in Incus fixture runner, approval validation, target-drift guard]
affected_contracts: [raw approval SHA-256, strict 16-key GO schema, workflow/runner/test hash bindings, clean expected HEAD and tree, inventory/profile/resource digest schemas, pending sanitized all-project capture schema and fixed read-only argv, empty-or-populated TCP/10001 route inventory, approved live route-state digest, strict proxy tuple and port-range/list parsing, strict IPv4/IPv6 listener checks, exact stopped-init effective devices and profiles, post-reservation read-only JIT, consumed BLOCKED_TARGET_DRIFT]
dependencies: [S449-01]
parallel_group: sequential
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/incus_profile_listener_fixture.py, tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py, .codex/evidence/slice-449-02C-distribution.md, .codex/evidence/slice-449-02C-consolidation.md]
module_locks: [opt-in listener fixture runner]
contract_locks: [approval digest and 16-key schema, exact workflow/runner/test bindings, clean HEAD/tree, JIT inventory/profile/resource/route-state digest, strict proxy tuple and port-range/list parser, strict effective-profile/device inventory, typed drift result, strict empty-or-populated TCP/10001 route inventory, pending sanitized all-project inventory mode and exact read-only argv contract]
architecture_locks: [fail-closed live qualification boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_profile_listener_fixture]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: no change
stop_conditions: [approval digest mismatch, duplicate or unknown approval keys, dirty or unexpected checkout HEAD, unreadable or malformed route inventories, route/listener drift, Windows firewall or PortProxy change, any added external route, typed target drift, invalid authorization]
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
resource names; `project` must be exactly `default`, and `image_fingerprint`
is lowercase 64-hex. Require `proxy` to
contain exactly string fields `listen`, `connect`, and `bind`: `listen` must
be `tcp:127.0.0.1:<port>` for a unique, unused per-run port in 61000–65535;
`connect` must identify only the fixture instance's private listener; `bind`
must equal `host`. TCP/10001 is forbidden for the fixture listener. Read the
full host listener and Incus route inventories successfully; their TCP/10001
entries may be empty when that exact empty state is independently approved and
bound into the route-state digest. Malformed or unreadable inventories must
fail and must never be treated as empty. Any existing TCP/10001 entries must
pass route validation and remain unchanged after cleanup. The fixture must not
create or remove TCP/10001 routes. On WSL, preserve the complete effective
Windows Defender Firewall `ActiveStore` snapshot (profiles, global settings,
rules, and all associated address/application/interface/interface-type/port/
security/service filters) and exact PortProxy bytes; on native Linux the
Windows snapshot is empty.
The loopback-only fixture listener is not externally routable; verify it is
absent before and after the run and that no Windows firewall or PortProxy state
changes. Require `cleanup` to be exactly the
ordered two-string list `[instance, profile]`, with the names from `target`.
Require `reviews` to contain exactly `requirements`, `architecture`, `security`,
`devops`, and `test_evidence`, each exactly `APPROVED`; a separate independent
review artifact binds all five decisions to the same raw GO SHA-256.
`windows_rules_unchanged` must be boolean `true`; `external_routes_enabled`
must be boolean `false` and means this scenario creates no additional external
route. Any pre-existing TCP/10001 route remains unchanged; an empty baseline
remains empty. Require `default_profile_used_by` to be a list of
unique string URIs in strict lexical order and compare it with the exact JIT
consumer list. Compute `default_profile_sha256` from UTF-8 canonical compact
JSON with sorted object keys and no ASCII escaping for exactly
`{"config": <complete profile config>, "devices": <complete profile devices>}`.

`resource_admission_sha256` and `issue447_inventory_sha256` bind separate,
independently reviewed evidence artifacts; the runner validates lowercase
digest syntax only and must not claim it reopened or verified those external
bytes. The independent review artifact identifies and hashes the exact resource
admission and full issue447 project/profile/consumer/device inventory artifacts.
Before GO creation, capture route-state evidence on each exact clean target
checkout with the read-only `--capture-route-state --target-host <approved-ip>
--output <private-evidence-path>` mode. This mode requires no GO, takes no
reservation, and performs no Incus writes; it creates a mode-0600 private JSON
artifact with source commit, timestamp, exact target host/IP, listener/route
observations, Windows snapshot where applicable, and the canonical digest.
Before capture, verify the selected IP with `ip -j -4 addr` on native Linux;
on WSL verify `uname -r` identifies Microsoft WSL2 and PowerShell
`Get-NetIPAddress -AddressFamily IPv4` contains the selected Windows host IP.
Before each host capture, verify that the approved checkout and evidence
directory are on ext4 and have POSIX owner-only permissions. Record the
filesystem type, mount target, directory mode and artifact mode in
`.tiny-swarm/evidence/issue-449/s449-private-20261027/s02-private-posix-verification.md`.
The independent review artifact
`.tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-s02-live-review.md`
records the exact capture path and target host/IP, hashes the capture, and
confirms its digest and target match the GO. Keep each capture, GO,
reservation/NOT_RUN state, review and result artifact below the POSIX-private
directory on the approved ext4 checkout. The fixture runner must reject a
checkout under `/mnt/c`, `/mnt/d` or DrvFS even when NTFS ACLs appear
restrictive.
The normal fixture invocation independently
repeats JIT after reservation and rejects any mismatch before writes.
Approved invocations are `python3 tools/qualification/incus_profile_listener_fixture.py
--capture-route-state --target-host 192.168.178.33 --output
.tiny-swarm/evidence/issue-449/s449-private-20261027/native-pre-go-route-state.json`
on native Linux
and the same command with `--target-host 192.168.178.58` and output
`.tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-pre-go-route-state.json`
inside WSL.
`approved_route_state_sha256` binds an independently reviewed pre-run snapshot
of the TCP/10001 host listener tuples exactly `{protocol, local_address,
local_port}` (never process IDs, paths or raw `ss` rows), all Incus TCP/10001
profile and instance
routes, and the WSL effective ActiveStore firewall profiles/global settings/
rules/all associated filters plus exact PortProxy bytes (empty on native
Linux). On WSL, query with Windows PowerShell
`/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile
-NonInteractive -Command <fixed query embedded in the hash-pinned runner>`
using `Get-NetFirewallProfile
-PolicyStore ActiveStore`, `Get-NetFirewallSetting -PolicyStore ActiveStore`,
`Get-NetFirewallRule -PolicyStore ActiveStore`, and for every rule query
`Get-NetFirewallProfile -AssociatedNetFirewallRule`, `Get-NetFirewallAddressFilter`,
`Get-NetFirewallApplicationFilter`, `Get-NetFirewallInterfaceFilter`,
`Get-NetFirewallInterfaceTypeFilter`, `Get-NetFirewallPortFilter`,
`Get-NetFirewallSecurityFilter`, and `Get-NetFirewallServiceFilter`, each with
`-AssociatedNetFirewallRule <rule> -PolicyStore ActiveStore`. Capture all CIM
properties with `Select-Object *`; order profiles by `Name`, rules by `Name`,
and filter records by their canonical JSON bytes. Set PowerShell output
to UTF-8 without BOM, parse the JSON strictly, then serialize with sorted keys,
compact separators and `ensure_ascii=False` before UTF-8 encoding. Capture
PortProxy independently as the exact stdout bytes from
`/mnt/c/Windows/System32/netsh.exe interface portproxy show all`; do not trim,
decode/re-encode or normalize line endings. This is a separate command with a
30-second timeout and 2 MiB stdout/stderr caps. Keep complete canonical
firewall JSON and exact PortProxy bytes in memory only. Compute the combined snapshot
SHA-256 over canonical wrapper bytes, but persist only the digest and approved
metadata (schema version, collection counts and byte lengths, timestamp, target
and source identity). Never persist `windows_snapshot_b64`,
`firewall_active_store_b64`, `portproxy_raw_b64`, raw PowerShell output,
security filters/ACLs/SIDs or PortProxy bytes in evidence or logs. At run/JIT
checkpoints retain the complete before/after snapshots only in memory and
compare exact canonical bytes; digest equality alone does not replace that
in-process byte equality check.
The exact PowerShell command string is fixed in the hash-pinned runner; callers
cannot supply or replace it.
The listener and route lists may be empty only when commands succeeded,
their exact empty state is independently reviewed, and the digest binds that
state. Parse `ss -H -ltnp` in memory, discard process details, and persist only
the sorted safe listener tuples, count and SHA-256 of their canonical JSON;
never retain raw rows, PIDs, process names or executable paths in logs or
artifacts. The runner computes the same canonical UTF-8 JSON digest from its
post-reservation read-only JIT and requires a match before any Incus write.
Enumerate projects with read-only `incus project list --format json`; reject
malformed results, missing/empty or duplicate names, and require `default`.
Strictly read each project's metadata and enumerate its profiles and instances
using that explicit project. Read each profile's complete config/devices and
each instance's complete config/devices/profiles in memory. Persisted
`incus_10001_routes` rows have exactly `{project, owner_type, owner, device,
device_type, effective_profiles, listen, connect, bind}`. `project`, `owner`,
`device` and profile names are validated Incus identifiers; `owner_type` is
exactly `profile|instance`; `device_type` is exactly `proxy`;
`effective_profiles` is sorted unique validated names. A source route device is
projectable only when its complete key set is exactly `{type,listen,connect,bind}`
and `type=proxy`; any optional or unknown key fails closed.
`listen` and `connect` are objects exactly `{protocol,address,port}` with
`protocol=tcp`, normalized IP literal or approved inventory target address,
integer port 1..65535, and `listen.port=10001`. `bind` is exactly `host` or
`instance`. Reject unknown fields, protocols, values, device keys, paths,
host-path sources or malformed addresses before artifact creation. Keep full
route/device configs only in memory; never persist raw config, arbitrary host
paths or raw route JSON. Sort project names lexically and sort safe route rows
by `(project, owner_type, owner, device)`. This inventory is
read-only across all projects; S449 profile reconciliation and fixture
mutations remain limited to Incus project `default`.

The route digest payload has exactly five fields: `listeners_10001_count`,
`listeners_10001_sha256` (digest of sorted safe listener tuples, never raw
`ss` rows), `incus_projects` (sorted project-name strings),
`incus_10001_routes` (sorted project-bound route records), and
`windows_snapshot_sha256` (combined Windows snapshot digest; empty string on
native Linux). Serialize the payload as UTF-8 JSON with sorted object keys,
compact separators and `ensure_ascii=False`, then compute SHA-256.
The pre-GO capture artifact records project names, route records, approved
snapshot metadata and digests only; no snapshot contents or raw PortProxy bytes
are retained. A mismatch is durably recorded as
`BLOCKED_TARGET_DRIFT`.
In normal one-shot run mode, read the GO once as a no-follow regular file, compare its raw bytes with caller
`--expected-approval-sha256`, then parse strict UTF-8 JSON; reject duplicate
keys and missing/extra keys at every object. Before reservation, normal run
mode allows read-only Git inspection and the single GO-file read only: no
host/Incus command and no lock/evidence mutation. The separate pre-GO
`--capture-route-state` mode is read-only except for creating its exclusive
mode-0600 evidence artifact. Its artifact contains the complete read-only
Incus project-name inventory and project-bound TCP/10001 profile and instance
routes, in addition to sanitized listener tuples/count/digest and snapshot
metadata/digest where applicable.
Then acquire an exclusive O_EXCL reservation and
byte-exact `NOT_RUN` evidence recheck in normal mode; capture mode does not read,
create or mutate GO, result, reservation or `NOT_RUN` files. Only after
reservation perform read-only
Incus/listener JIT for target, version, project, image, unique names, complete
default-profile config/devices/consumers, selected loopback-port availability,
exact observed TCP/10001 listener/route inventories (including an approved
empty baseline), unchanged Windows rules, and resource
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
digest, ordering and no-mutation guard. Add the read-only
`--capture-route-state` mode for pre-GO evidence preparation; it writes only an
exclusive mode-0600 private artifact and issues only read-only Git,
native/Windows host-identity, listener, Incus inventory, Windows Firewall query
and PortProxy commands. It uses the
same canonical digest function as post-reservation JIT and never reserves a
live run or issues Incus writes. Store the artifact only beneath an owned
mode-0700 private evidence directory using exclusive `O_CREAT|O_EXCL|O_NOFOLLOW`
creation and mode 0600; reject a symlink, existing path, or unsafe directory.
The WSL snapshot includes effective
ActiveStore profiles/global settings/rules and all associated filter types
before PortProxy. Regression tests also prove native and
WSL empty TCP/10001 listener/route baselines pass only when read successfully
and bound to the exact approved digest; malformed/unreadable inventories and
pre-write drift fail closed; post-cleanup absence is verified; WSL firewall
and PortProxy snapshots remain unchanged; and populated-baseline behavior
remains protected. Capture-mode tests explicitly prove native/WSL host-identity
checks and exact target-IP binding, the read-only command allowlist, no GO
read/reservation/NOT_RUN artifact, owned mode-0700 directory,
exclusive no-follow mode-0600 output with no overwrite or symlink acceptance,
and byte-identical
snapshot/digest parity with JIT. Record exact source/test hashes for S02.
Historical v1.32 evidence: runner/test `f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628` / `8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668`, 85 focused tests, and full QUALITY log SHA-256 `247da0bd35bbf91138811ba7355f39681fd7dc5b3e47c78474cdc4b806a90e26` remain historical and are not current candidate evidence. Earlier candidate runner SHA-256 `7929f9dc5d6fea32c55125c3b9f8fb4f02b72a07d3ea0ef80cb0a2aea6279c12`; test SHA-256 `6f888dc59182c7b02ed86fd3e80ddbadb5d7e5a6286e27b4c67d5d3eeb7fcba3`; earlier focused suite 95 PASS on approved PC WSL. Earlier full QUALITY PASS: GATE_EXIT=0 on Python 3.14.4 in a private venv with CI-pinned tools; 43 architecture tests, 2,969 total tests, 18 skipped; private log SHA-256 `daa2d3952b97aef496035ea773ede718fa5e79e61df1f832c9761ab15126e8df`, file mode 0600, parent directory mode 0700. This exact candidate was not run on CI Python 3.12. Older inventories and captures from pre-candidate checkout be2e031e8f0fb137ea6c15f74d81a88181aa4183 are historical and not exact-source evidence for 509908; previously recorded 509908 native inventory/route evidence and WSL capture failure are recorded in context-pack.md. The native route-state PASS digest fe31f78643962ce3757e8bcfc8cc8ed1e9c9eb46a2c1728f52f773fbc2f84758 is historical to that checkout. WSL route-state capture returned JIT_COMMAND_FAILED and is not a pass. The earlier native read-only preflight was blocked by active snap.lxd.daemon.service; no normalized admission for that earlier candidate exists. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. Native read-only preflight is blocked by active `snap.lxd.daemon.service`. The pre-candidate native inventory showed only the default LXD project and three stopped TSW containers; no host-stop GO exists. Pre-candidate native resource observations were 8 CPUs, 20,111,052,800 bytes MemTotal, 15,452,803,072 bytes MemAvailable, 724,140,146,688 bytes free disk, ext4 `/`, and `incus version` reports Client/Server 6.0.5. For native R449-33, the accepted resource floor is 18,253,611,008 bytes (17 GiB), CPU >= 8 and free disk >= 150 GiB; observed MemTotal, CPU and disk meet those numerical floors. The 19 GiB default-node guard applies only where that baseline applies; the accepted ADR supports a 17 GiB TSW_INFRA_ROOT override for this host. MemAvailable is recorded as an observation, not an admission threshold. This numerical comparison is not a normalized resource-admission artifact or PASS: active snap.lxd.daemon.service blocks read-only service-access preflight, and the exact admission artifact and per-scenario GO are absent. Incus 6.0.5 does not establish capability support. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites.  That earlier candidate had no host/scenario GO or normalized admission. The v1.32 approval record and its S3D result remain historical. No host admission, scenario GO, or target mutation is claimed.
sanitization, schema rejection, output metadata, sanitized-artifact-only hash,
private exclusive ext4 write, and no GO/reservation/NOT_RUN/Incus-write behavior.
S449-02 may not collect or claim this inventory before that implementation and
until required same-hash reviews, full QUALITY and S3/S3D pass.


#### Workflow amendment v1.33 — new phases are not covered by historical S3D

S449-02D and S449-02E are complete and committed; S449-02F remains planned and
unreleased. The existing S449-02 pre-GO `EXECUTION_PLAN` is bound to its
original hashes and exact read-only phase; it does not authorize these new
code slices, new host reads, live fixture actions, Incus mutations,
service/system changes, installations or upgrades. Before any amended slice or its host read phase,
obtain fresh same-hash Requirement, Architecture, Python Automation, Tester,
Security and DevOps reviews and a fresh S3D `EXECUTION_PLAN` for that exact
phase. Work remains limited to native `192.168.178.33` and WSL2
`192.168.178.58`. The current WSL route capture is still `JIT_COMMAND_FAILED`;
the native service-access preflight is still blocked by active
`snap.lxd.daemon.service`. Neither state is a pass or host/scenario GO.

Amendment clarification (execution-phase update, not workflow creation): the
original request is to complete #449 on the two approved test hosts. The
interpreted intent of this amendment is to provide reviewed, bounded paths for
the WSL full-snapshot failure and native LXD/Incus ownership blocker. Change
type is workflow sequencing and qualification evidence; affected areas are the
Incus fixture, the PowerShell snapshot boundary, and native runtime evidence.
Explicit requirements are to preserve all firewall/PortProxy state and avoid
activating shared routes, prove native ownership before any maintenance, and
bind new execution to fresh hashes/reviews/S3D. Implicit requirements include
strict output bounds, private sanitized evidence and a separate GO for every
mutation. Assumptions are limited to the user's existing authorization to
qualify only the two listed test hosts and replace the three named TSW
instances. Non-goals are changing Windows networking, touching unrelated
resources, treating historical captures as current, or claiming #449 complete.
Risks are incomplete host inventory, stale hash bindings, route activation and
service disruption. Open decisions: whether S449-02F proves exclusive TSW
ownership; whether the full WSL snapshot completes under the bounded timeout;
and whether each host reaches current admission/GO. No question blocks this
planning amendment, but all listed evidence gates block execution. Confidence
is 80% until exact captures; decision is `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`
for this amendment only, not release of any live phase.

The three slices are sequential because the workflow/context, runner, tests
and live evidence contracts overlap. Preserve full firewall and PortProxy
capture, the TCP/10001 exposure boundary, private ext4 evidence requirements,
and fail-closed behavior.

##### Slice 02D — Isolate the disposable fixture from shared default routes

Purpose: prevent a disposable Incus fixture from activating any proxy inherited
from the shared `default` profile. The derived profile retains only explicitly
allowlisted safe config keys and device shapes; it does not copy every
non-proxy setting or device.

Prerequisites: S449-02C; fresh approvals and S3D `EXECUTION_PLAN` for this
code/test slice; no host fixture execution. The current S449-02 pre-GO plan does
not authorize this implementation.

Before any write, capture the complete default profile in memory only, compute
its canonical SHA-256 over the UTF-8 bytes of compact JSON with lexically sorted
object keys, separators exactly `,` and `:`, and `ensure_ascii=false`,
serializing exactly `{"config": <complete source config>, "devices": <complete
source devices>}`. Accept only finite JSON values (`null`, booleans, strings,
finite numbers, arrays and objects with string keys); reject NaN/infinities,
non-JSON types and invalid Unicode before hashing or writing. Parse source
Incus profile JSON with duplicate-key rejection at every object before
canonicalization; duplicate top-level or nested config/device keys fail closed
before hashing or any write.
S449-02D source-profile reads use the same bounded inventory command contract
as amended S449-02 capture: at most 256 commands total, 300 seconds aggregate
wall-clock, 30 seconds per command, 2 MiB each for stdout and stderr per
command, 16 MiB aggregate output, 8 MiB serialized sanitized artifact, and
10,000 total entities. Counts/bytes exactly at each maximum are accepted;
limit+1 is rejected. Exactly 30/300 seconds is accepted only when the command
or run completes within the deadline; any overrun is rejected. Cap exhaustion,
timeout, malformed or incomplete data fails closed before writes and creates
no artifact. Strict duplicate-key rejection applies at every depth to every
LXD/Incus/project/profile/instance JSON response before schema validation or
artifact creation.
Bind that digest plus exact sorted `used_by` list and allowlisted profile
identity metadata into GO. Never persist source profile
config/device values, arbitrary paths or raw source profile JSON in GO, results,
logs or artifacts. Re-read and compare the full source profile in memory before
each write, at every lifecycle checkpoint and after cleanup; persist only the
digest and sanitized result. Derive a temporary base profile retaining only
config keys from this explicit safe allowlist using the Incus API's string
types (see [Incus instance options](https://linuxcontainers.org/incus/docs/main/reference/instance_options/)):
`limits.cpu` must be a string accepted by Python 3.12
`re.fullmatch(r"[1-9][0-9]*", value)`; `limits.memory` must be a string
accepted by `re.fullmatch(r"[1-9][0-9]*(KiB|MiB|GiB)?", value)`; see the
[Python 3.12 regular-expression documentation](https://docs.python.org/3.12/library/re.html).
Full-match semantics reject a trailing newline as well as all other unmatched
characters. Source `boot.autostart`, when present, must be exactly the lowercase
string `true` or `false`. Always set derived `boot.autostart` to the string
`false`, whether the source key is true, false, or absent, so an Incus daemon
restart cannot restore or autostart the fixture. Missing source keys are
allowed; do not coerce or normalize values. Reject JSON numbers/booleans,
leading zeros, signs, whitespace, case variants, suffix variants and every other key/value,
including `security.privileged`, `security.nesting`, `raw.lxc`,
`linux.kernel_modules`, every `linux.*`, `idmap.*`, malformed values and
unknown config fields before any write. Device schemas are exact: root disk is
exactly `{type: disk, path: /, pool: <approved pool>}` with map key `root`;
bridge NIC is exactly `{type: nic, name: eth0, network: <approved bridge>}`
with the approved map key. No optional metadata keys are accepted. Reject
proxy devices, host-path bind mounts, unknown device types/keys, missing or
extra required fields, unapproved pool/network names and unknown shapes before
any write. Never copy arbitrary non-proxy devices. Never attach, edit, rename or
delete the shared `default` profile. Attach only this temporary base profile
and the unique fixture profile with its approved loopback-only listener. Extend
the exact GO schema with `fixture_base_profile_sha256`, computed as SHA-256 of
UTF-8 compact JSON with sorted keys and `ensure_ascii=false` for exactly
`{"config": <allowlisted sanitized config>, "devices": <allowlisted sanitized devices>}`;
its digest and safe device identity enums may be persisted, but not raw source
profile data or arbitrary device paths. Logs and artifacts must redact all
config/device values outside the fixed safe allowlist. The approved sorted
consumer list must be checked again in memory immediately before every write;
any drift blocks before mutation. Also add exact `target.base_profile`; change
ordered cleanup to
`[instance, fixture_profile, fixture_base_profile]`. Cleanup deletes the
instance first, then the two temporary profiles, including all partial-create
failure prefixes. At every lifecycle checkpoint and after cleanup, re-read the
shared default profile, its consumers, all-project route inventories and the
approved listener/route digest; they must equal the baseline. The expanded
fixture profiles/devices must exactly match the sanitized base plus fixture
profile. Deterministic tests must cover each allowed device shape and reject
host-path bind mounts, proxy devices, unknown/extra keys, unknown device types,
unapproved pool/network references and malformed fields before the first write;
tests must also cover every allowed string config value, reject numeric/bool
JSON values and lexical variants including trailing newlines under Python 3.12, prove source `boot.autostart` true, false, and absent each yields derived string `"false"` and never starts automatically, and reject privileged,
raw LXC, kernel-module, idmap, unknown-key and malformed-value config before
the first write. Tests must assert GO/result/log/artifact schemas contain no
raw source config, device values or arbitrary paths. They must prove the exact
sorted default `used_by` list is GO-bound; a consumer-list change at any
checkpoint blocks; and consumer drift immediately before any write causes zero
writes. Add canonicalizer known-answer tests: empty profile bytes
`{"config":{},"devices":{}}` must hash to
`079aa36c8373b157f411a389cd569d038a5da42dfcb380ba625a366cc95205c3`; Unicode
bytes `{"config":{"user.note":"München"},"devices":{}}` must hash to
`cc7a06da6878973e8431910042d01f3ff1a8a7bafb972917a3ee329436fddd2c`.
Equivalent mappings with different key insertion order must produce identical
canonical bytes and hashes. Reject non-finite numbers and non-JSON types.
Tests must reject duplicate keys at every level of the source profile JSON,
including duplicate `config` or `devices` keys, and duplicate keys in every
LXD/Incus inventory response, before schema/artifact creation and with zero
writes. Paired boundary tests must prove exact-limit acceptance and limit+1 or
over-deadline rejection for per-stream bytes, aggregate output, serialized
artifact size, entity count, command count, per-command elapsed time and
aggregate elapsed time. Use deterministic fake clock/subprocess fixtures;
every over-limit case must produce zero host writes and no artifact.
Repeated hashing of an unchanged full source profile must yield the same digest.
A source config/device change after baseline capture must be
detected in memory and block before the first write with zero writes. A
populated wildcard TCP/10001 baseline is preserved and never copied to or
activated by the fixture.

```yaml
slice_id: S449-02D
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/incus_profile_listener_fixture.py, tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py, .codex/evidence/slice-449-02D-distribution.md, .codex/evidence/slice-449-02D-consolidation.md]
affected_modules: [Incus disposable listener fixture, GO validation, profile derivation and cleanup]
affected_contracts: [exact GO schema and target.base_profile binding, sanitized default-derived temporary base profile, loopback fixture profile, effective profile/device validation, shared default/consumer/route immutability, partial-prefix cleanup order]
dependencies: [S449-02C]
parallel_group: sequential
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/incus_profile_listener_fixture.py, tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py, .codex/evidence/slice-449-02D-distribution.md, .codex/evidence/slice-449-02D-consolidation.md]
module_locks: [Incus fixture profile lifecycle, exact GO contract]
contract_locks: [shared default profile read-only, no inherited proxy devices, fixture profile tuple, cleanup order and failure-prefix behavior, route-state digest]
architecture_locks: [fail-closed live qualification boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_profile_listener_fixture]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: no change; preserve shared-profile ownership and route boundary
stop_conditions: [unknown default profile field/device, proxy copied to fixture base, host-path bind mount, unknown device key/type/shape, unapproved root pool or bridge network, exact default used_by baseline mismatch at any checkpoint, shared default profile/consumer/route drift, invalid GO/schema/hash binding, cleanup failure or wrong order, any host fixture or Incus write before fresh scenario GO]
```

##### Slice 02E — Bound and preserve complete WSL route snapshots

Purpose: make the WSL read-only route-state/JIT snapshot complete and reliably
bounded while retaining the full ActiveStore firewall, all associated filter
families and exact PortProxy bytes.

Prerequisites: S449-02D; fresh same-hash approvals and S3D `EXECUTION_PLAN` for
this code/test slice; no host capture until implementation and quality gates
pass. This slice shares runner/tests with S449-02D and cannot run in parallel.

First apply the bounded fix to the distinct subprocesses. Only the complete
PowerShell ActiveStore firewall snapshot gets the timeout exception: at most
120 seconds, stdout <=14 MiB and stderr <=2 MiB. The separate `netsh ...
portproxy show all` command remains at most 30 seconds with stdout/stderr <=2
MiB each. Every byte from both commands contributes to the shared 16 MiB
aggregate output cap; each command counts toward the shared 256-command limit,
and both durations count toward the 300-second aggregate wall-clock cap. The
sanitized artifact remains capped at 8 MiB. Any cap+1, timeout, or aggregate overrun
fails closed before artifact creation or host writes. Preserve kill/reap
behavior, strict parsing and byte accounting. Keep per-rule filter
query semantics. If the full snapshot still fails, stop and request a separately
reviewed design before attempting bulk CIM joins; never remove rules, filter
families, profiles, settings or PortProxy entries to make capture pass. Tests
must distinguish timeout from nonzero exit; reject missing, duplicate, orphaned,
malformed or unexpected associated-filter results; prove all eight filter
families and complete canonical snapshot semantics, stable digest over the full
snapshot, exact in-memory before/after byte equality, exact PortProxy preservation,
absence of `windows_snapshot_b64` and other raw/base64 snapshot fields, and
redaction of raw output, ACL/SID and PortProxy bytes from artifacts/logs. The
PowerShell tests must prove exact 120 seconds and 14 MiB/2 MiB stream caps are
accepted, while timeout+1 and cap+1 fail closed. Separate `netsh` tests prove
exact 30 seconds and 2 MiB/2 MiB accepted and timeout/cap+1 rejected. Combined
tests prove both commands' bytes/counts/durations share the 16 MiB/256/300s
budgets, including exact aggregate acceptance and +1/overrun failure. All
snapshot bytes count toward aggregate limits. Route artifact tests must prove only safe
listener tuples/count/digest are persisted and raw `ss` rows, PIDs, process
names and paths are absent. Tests must verify exact nine-field
`incus_10001_routes` rows and value types/enums, reject unknown source proxy
keys, malformed endpoints and host paths before artifact creation, and prove
raw route config/JSON never appears in evidence or logs. The
eight associated collections are
the profile collection plus seven rule-filter families: address, application,
interface, interface type, port, security and service. Any later bulk-query optimization must
prove complete ActiveStore equivalence first.

```yaml
slice_id: S449-02E
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/incus_profile_listener_fixture.py, tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py, .codex/evidence/slice-449-02E-distribution.md, .codex/evidence/slice-449-02E-consolidation.md]
affected_modules: [WSL PowerShell ActiveStore snapshot, route-state capture, fixture JIT]
affected_contracts: [bounded snapshot timeout and output caps, full firewall profiles/settings/rules and eight associated filter families, exact PortProxy bytes, strict associations, canonical digest parity, raw output redaction]
dependencies: [S449-02D]
parallel_group: sequential
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/incus_profile_listener_fixture.py, tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py, .codex/evidence/slice-449-02E-distribution.md, .codex/evidence/slice-449-02E-consolidation.md]
module_locks: [WSL full route-state capture]
contract_locks: [complete ActiveStore snapshot, all associated filter families, exact PortProxy bytes, bounded command failure behavior]
architecture_locks: [fail-closed live qualification boundary]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_lxc_profile_listener_fixture]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: no change; retain TCP/10001-only exposure and unchanged Windows networking
stop_conditions: [timeout or nonzero snapshot failure, incomplete/ambiguous filter association, output cap breach, raw SID-rich output persistence/logging, firewall or PortProxy mutation, reduced snapshot scope]
```

##### Slice 02F — Capture native LXD/Incus ownership without mutation

Purpose: investigate the native preflight blocker with bounded, sanitized,
read-only evidence distinguishing the active LXD daemon from the Incus endpoint
and enumerating visible LXD projects, instances, profiles, networks, storage
pools and consumers.

Prerequisites: S449-02D and S449-02E; fresh same-hash reviews and S3D
`EXECUTION_PLAN` explicitly naming this native diagnostic phase. The existing
pre-GO plan does not authorize these new commands. Run only on native Linux
`192.168.178.33`, from the exact approved ext4 candidate, writing a sanitized
mode-0600 artifact below the existing owner-only mode-0700 evidence directory.
The checkout and evidence directory must be ext4; verify the directory is mode
0700 before capture and each evidence file mode 0600 after exclusive creation.
Do not contact WSL or another host in this slice.

Use a fixed command allowlist for LXD/Incus versions/endpoints and `systemctl
show` on only the fixed LXD and Incus units listed below. For service units,
`systemctl show` may request only
`LoadState`, `ActiveState`, `SubState`, `UnitFileState` and `MainPID`; for
socket units, those same properties plus `Listen` only. Never request or retain
`Environment`,
`ExecStart`, command lines or environment values. Socket units may omit
`MainPID` in `systemctl show`; only for the two fixed socket units, accept an
omitted or explicit decimal `0` value and normalize it to integer `0`. Reject
an empty, malformed, or nonzero value. Do not resolve a socket executable
identity. For each active service
unit, resolve the executable identity and compare it in memory with the fixed
map: `snap.lxd.daemon.service` -> `/snap/lxd/<revision>/bin/lxd`, where revision
matches `[1-9][0-9]*` (`lxd_snap`, `snap:lxd`),
`lxd.service` -> `/usr/lib/lxd/lxd` or `/usr/libexec/lxd/lxd`
(`lxd_system`, `system:lxd`), and `incus.service` ->
`/usr/libexec/incus/incusd` or `/usr/lib/incus/incusd`
(`incus_system`, `system:incus`). A known `not-found` unit, or a loaded
`inactive`/`failed` unit with MainPID 0, is recorded without an executable row;
only active units require a validated positive MainPID and allowlisted
executable identity. Any other or contradictory state is `BLOCKED`. Inspect
only fixed, documented LXD and Incus Unix socket endpoints; compare canonical
endpoint identity in memory to the fixed allowlist and record only its
symbolic endpoint ID and state. Bind unit, MainPID, executable identity and
socket endpoint state to the read-only resource inventory. Missing or
ambiguous binding for an active CLI query remains `BLOCKED`.

Every LXD inventory command must include global `--force-local` before its
subcommand, bypassing user-configured remotes and contacting only the local
daemon. Bind this fixed local endpoint identity to the active LXD service unit,
verified executable identity and matching allowlisted socket unit/path/type.
Any mismatch or unavailable binding blocks capture; never inspect remote
aliases or send queries over TCP. For Incus, use the same exact subcommands
and arguments specified below, replacing the executable token `lxc` with
`incus` (for example, `incus --force-local version` and
`incus --force-local project list --format json`); never concatenate two
executable prefixes or treat an Incus endpoint as LXD.
Persist only symbolic endpoint IDs, never URLs or socket paths.

Only these units may be inspected: LXD `lxd.service`,
`snap.lxd.daemon.service` and `snap.lxd.daemon.unix.socket`; Incus
`incus.service` and `incus.socket`. Only these socket
paths may be tested or canonicalized, without returning path text:
`/var/lib/lxd/unix.socket`, `/var/snap/lxd/common/lxd/unix.socket`,
`/var/lib/incus/unix.socket` and `/run/incus/unix.socket`.
Resolve `/proc/<MainPID>/exe` only for a service unit with validated positive
MainPID; compare to the fixed executable identity allowlist and persist an
identity enum, never the resolved path. For socket units require normalized
MainPID=0 and parse `Listen` in memory, normalize it against the fixed socket-path
allowlist, and persist only symbolic endpoint ID/type/state. Test socket
existence/type with fixed `test -e`/`test -S` argv and bind the result to that
normalized `Listen` endpoint.

Exact command templates are `systemctl show <service-unit>
--property=LoadState --property=ActiveState
--property=SubState --property=UnitFileState --property=MainPID --no-pager`;
for the socket unit only, this exact argv with `--property=Listen` added;
`readlink -f /proc/<validated-MainPID>/exe`; fixed `test -e <allowlisted-socket>`
and `test -S <allowlisted-socket>`; `readlink -f <allowlisted-socket>`;
`lxc --force-local version`; and, for
projects/resources, `lxc --force-local project list --format json`; per project,
`lxc --force-local project show <project> --format json`,
`lxc --force-local profile list --project <project> --format json`,
`lxc --force-local profile show <profile> --project <project> --format json`,
`lxc --force-local list --project <project> --format json`,
`lxc --force-local config show <instance> --project <project> --format json`,
`lxc --force-local config show <instance> --project <project> --format json --expanded`,
`lxc --force-local network list --project <project> --format json`,
`lxc --force-local network show <network> --project <project> --format json`,
`lxc --force-local storage list --project <project> --format json` and
`lxc --force-local storage show <pool> --project <project> --format json`,
`lxc --force-local storage volume list <pool> --project <project> --format json`,
and for each listed volume
`lxc --force-local storage volume show <pool> <volume-type>/<volume-name> --project <project> --format json`.
For Incus use the same subcommands and arguments with `incus` replacing `lxc`,
including `incus --force-local version` and `incus --force-local project list
--format json`. If its CLI does not support `--force-local`, remain BLOCKED.
Execute every command with `shell=False`, a fixed executable token, and
validated values as separate argv items. Client argv[0] is fixed by the verified
daemon identity: `/snap/bin/lxc` for `lxd_snap`, `/usr/bin/lxc` for
`lxd_system`, and `/usr/bin/incus` for `incus_system`. Do not resolve a client
through PATH. Do not inherit the caller environment: set only `LC_ALL=C`,
fixed `PATH=/usr/bin:/bin`, and exactly one explicitly selected local endpoint
variable:
`LXD_SOCKET=<validated-canonical-LXD-socket>` for LXD commands or
`INCUS_SOCKET=<validated-canonical-Incus-socket>` for Incus commands. These
values must come from the fixed allowlist and match the already-active service
and socket binding; no caller-supplied endpoint override is read. The explicit
socket value overrides CLI default discovery. Its documented client behavior
is verified against the upstream endpoint variables and connection logic:
https://github.com/canonical/lxd/blob/main/client/connection.go and
https://github.com/lxc/incus/blob/main/client/connection.go. Immediately
before every LXD or Incus CLI query, re-read its matching
service state and require that service to be
`active/running` with the same positive MainPID and allowlisted executable;
if a socket unit can activate that service while it is not already active, do
not query it. The LXD socket is selected from the verified service:
`lxd_snap` maps only to `/var/snap/lxd/common/lxd/unix.socket`;
`lxd_system` maps only to `/var/lib/lxd/unix.socket`. It must match the active
LXD socket unit's `Listen` value, or the fixed service mapping when its socket
unit is not installed. For Incus, use the loaded `incus.socket` `Listen` value
when available; otherwise exactly one of `/run/incus/unix.socket` and
`/var/lib/incus/unix.socket` must exist and be a socket. Set the matching
`INCUS_SOCKET` explicitly for every Incus command, bypassing client default
path selection and its `/run` `lstat` branch. The selected endpoint must match
an already-active `incus.service` and the `incus.socket` Listen value
when that socket unit is loaded. If `incus` service is missing/inactive or the
socket mapping is ambiguous, do not query.
If
`incus.service` is `not-found`, record Incus unavailable only when `incus.socket`
is also `not-found` and both Incus endpoint paths are absent; otherwise remain
`BLOCKED` without running the Incus CLI. More than
one active local daemon that could satisfy a query, or any ambiguous canonical
socket-to-unit mapping, is `BLOCKED`.
Every command has timeout <=30 seconds, stdout <=2 MiB and stderr <=2 MiB;
aggregate output <=16 MiB; sanitized artifact <=8 MiB; entities <=10,000;
total commands <=256 and aggregate wall-clock time <=300 seconds. Any cap,
timeout, unexpected nonzero exit or incomplete inventory yields `BLOCKED`
with no artifact. For `test -e` and `test -S`, status 0 means true and status
1 means false; any other status is a command failure. A false `test -e` is an
expected absent endpoint and skips type/canonicalization checks. An existing
endpoint must also have `test -S` status 0, or capture is `BLOCKED`. Service
unit rows are accepted only for `loaded` plus
`active/running` with positive MainPID, or `loaded` plus `inactive/dead` or
`failed/failed` with MainPID 0; `not-found/inactive/dead` with MainPID 0 and
UnitFileState empty or `not-found` is also recorded without an executable row.
Socket rows are accepted only for `loaded/active/listening`,
`loaded/inactive/dead`, or `loaded/failed/failed`, always with normalized
MainPID 0; additionally, exact unit `incus.socket` may be
`loaded/active/running` with normalized MainPID 0. This Incus state is accepted
only when `incus.service` is `loaded/active/running` with the same stable
positive PID and allowlisted executable, its exact allowlisted Listen endpoint
exists as a Unix socket, and the complete existing pre-query and final
rechecks pass. No other unit may use `active/running`. A
`not-found/inactive/dead` socket has empty Listen. UnitFileState must be one of
`enabled`, `enabled-runtime`, `disabled`,
`disabled-runtime`, `static`, `indirect`, `alias`, `linked`, `linked-runtime`,
`masked`, `generated`, `transient`, or empty/`not-found` only for a
`not-found` unit. Serialize empty UnitFileState and Listen as empty strings.
Any other
state tuple is `BLOCKED`. Before each CLI query and again before artifact
creation, repeat the complete selected service/socket tuples, including
MainPID and Listen, executable identity, endpoint existence/type and canonical
endpoint mapping; any difference from initial values yields `BLOCKED` and no
artifact. Do not persist raw stdout/stderr. `identity_id` and `package` come
only from the fixed executable-identity allowlist after in-memory exact
executable comparison. `version` comes only from the strict `Server version`
field of each bounded local `lxc --force-local version` or
`incus --force-local version` response after its socket-to-service binding
succeeds; missing or ambiguous version is `BLOCKED`. Persist both active LXD
and Incus process identities in separate `lxd_executables` and
`incus_executables` collections; inactive services have no executable row.

The artifact schema is exactly `{schema_version,target_host,source_commit,
captured_at_utc,lxd_units,incus_units,lxd_executables,incus_executables,sockets,
lxd_projects,incus_projects,command_records,decision}`. Service-unit rows contain exactly
`{unit,load_state,active_state,sub_state,unit_file_state,main_pid}`; the socket
unit row contains exactly those fields plus `listen`. `lxd_units` contains only
the three LXD unit rows; `incus_units` contains only `incus.service` and
`incus.socket` rows. Executable
rows exactly `{unit,main_pid,identity_id,package,version}`; socket rows exactly
`{endpoint_id,state,unit}`. Project/resource rows retain only names, status,
type, profile/consumer links, network identity, storage pool/volume identity,
volume content type and device type; do not persist device or volume config
values, secrets or host paths. Command rows contain only
`{command_id,safe_args,exit_status,stdout_bytes,stderr_bytes}`. `command_id`
must be a fixed template enum; `safe_args` may contain only validated unit,
endpoint, project, profile, instance, network, pool, volume type or volume
identity tokens. Raw argv,
socket paths, `/proc` paths, executable paths, URLs and endpoint addresses stay
memory-only and are never serialized. No raw JSON or raw command output is
retained or hashed. Unknown fields fail closed before artifact
creation.

Parse bounded LXD/Incus JSON in memory and persist only the exact schema fields
needed for project/resource identity, state, type, ownership/consumer links,
profile identities, endpoint IDs and command metadata. Exclude secrets,
credential/config values not allowlisted, arbitrary host paths, raw JSON, raw
argv, command lines and unrelated host configuration; unknown
resource fields fail closed instead of being copied. Do not log `systemctl
show` output or resolved executable paths. Persist the executable's allowlisted
package/basename/version identity and fixed symbolic socket endpoint ID/state,
not a command line or arbitrary host path. Unknown units, resources, consumers,
endpoints, schemas or incomplete visibility yield `BLOCKED`; inventory is not
resource admission, capability support or scenario GO. Regression tests must
inspect serialized artifacts and logs and assert they contain no raw `argv`,
socket path, `/proc` path, executable path, URL or endpoint address; only fixed
command template IDs and validated symbolic safe arguments may be retained.

Do not stop, start, enable, disable, install, remove, reconfigure or otherwise
mutate LXD/Incus, services, networking, storage, Windows state or host
resources. If active LXD still blocks native preflight, retain `BLOCKED` and
route a separate architecture/requirement decision before proposing runtime
coexistence or maintenance changes.

The local socket identity must be root or a member of the matching full-access
`lxd` or `incus-admin` group; a restricted per-user Incus identity cannot claim
complete project visibility. Validate project `used_by` against the complete
set of inventoried instances, profiles, networks and volumes. The project API
does not report storage pools in this relation; pools are checked through their
own list/detail consumer view. Unknown project-consumer kinds or mismatched
membership block with no artifact. Validate pool-to-volume links and reciprocal profile/instance
disk-device consumers, resolve all profile, network, pool and volume consumers
across projects, and require list/detail and reciprocal device/profile
references to agree. A volume list or detail row whose owner project differs
from the project-scoped query is inherited/shared and is explicitly unsupported
by this slice; return `BLOCKED` with no artifact. Any other unresolved,
asymmetric or unknown storage-volume relationship also remains `BLOCKED` with
no artifact.

```yaml
slice_id: S449-02F
profile: RUNTIME_QUALIFICATION
owner: Senior DevOps Engineer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Python Automation Developer, Senior Tester]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/native_runtime_inventory.py, tests/tools/test_native_runtime_inventory.py, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-runtime-inventory.json, .codex/evidence/slice-449-02F-distribution.md, .codex/evidence/slice-449-02F-consolidation.md]
affected_modules: [native qualification evidence, bounded LXD/Incus inventory]
affected_contracts: [LXD systemd unit identity/state, LXD-vs-Incus endpoint identity, full-admin all-project visibility, reciprocal profile/network/pool/volume ownership inventory, strict sanitized private artifact, bounded read-only command allowlist including storage volume list/show]
dependencies: [S449-02E]
parallel_group: sequential
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/native_runtime_inventory.py, tests/tools/test_native_runtime_inventory.py, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-runtime-inventory.json, .codex/evidence/slice-449-02F-distribution.md, .codex/evidence/slice-449-02F-consolidation.md]
module_locks: [native LXD/Incus runtime ownership evidence]
contract_locks: [read-only command allowlist, bounded sanitized inventory, unknown state blocks admission]
architecture_locks: [no host-wide service mutation without separate accepted decision]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change pending a separate accepted coexistence decision
  adr: no change; inventory alone does not establish LXD/Incus compatibility
stop_conditions: [unknown/incomplete LXD or Incus visibility, shared or unowned resources, command/output bound exceeded, raw sensitive output retained, any service/system/Incus mutation; exclusive TSW-only LXD ownership routes to conditional S449-02G; unproven ownership remains BLOCKED]
```

##### Slice 02F2 — Diagnose fixed service identity without exposing paths

Purpose: identify which fixed native service unit failed the v1.37 executable
identity check after the exact native capture returned
`BLOCKED:EXECUTABLE_IDENTITY_BLOCKED`. This diagnostic is not an inventory,
ownership admission, scenario GO, or permission to broaden the executable
allowlist.

Prerequisites: committed S449-02F v1.37 implementation; its approved native
read-only attempt is recorded as blocked with no artifact; fresh same-hash
Requirement, Architecture, Python Automation, Tester, Security and DevOps
reviews; and a dedicated S3D plan for the committed symbolic diagnostic.

The opt-in `--diagnose-units` mode reuses the existing Runner, fixed unit list,
strict parser and executable identity map. It may query only `lxd.service`,
`snap.lxd.daemon.service`, `snap.lxd.daemon.unix.socket`, `incus.service` and
`incus.socket`, using the existing exact systemd property sets and existing
unit order. Process one unit at a time: query and validate it, resolve and
recheck an active service before moving to the next unit. Resolve
`/proc/<validated-positive-MainPID>/exe` only for active service units, with
the existing absolute `/usr/bin/readlink -f` argv and `shell=False`. Compare
the result in memory against the existing exact allowlist. After each
readlink, re-read that service's fixed systemd properties and require the
normalized service tuple to match before emitting its identity. The mode must
stop on the first unknown identity, malformed unit or state/PID drift and
return nonzero, before issuing any command for a later fixed unit.

Stdout is exactly one compact deterministic JSON object. A complete result is
`{"mode":"diagnose-units","status":"DIAGNOSTIC_COMPLETE","services":[{"unit":"lxd.service","identity":"lxd_system"}]}` with one row per fixed service in the defined service order; inactive services use identity `NOT_ACTIVE`. On the first unknown identity, emit only
`{"mode":"diagnose-units","status":"BLOCKED_UNKNOWN","unit":"lxd.service","identity":"UNKNOWN"}` and stop without partial service rows. Other failures emit only a fixed `BLOCKED:<CODE>` on stderr. Never emit or persist PIDs, raw paths, raw systemd/readlink output, exception text, command records or endpoint addresses. Do not inspect socket endpoints, run LXD/Incus client commands, query resources, or write an artifact in this diagnostic mode. Preserve Runner per-command/output/aggregate/wall-clock caps; the mode may execute at most five initial systemd queries, three readlink queries and three active-service rechecks (eleven commands total).

The diagnostic CLI accepts only `--diagnose-units`; it does not require
`--source-commit` or `--output`, and it must never call the artifact writer.
If `--diagnose-units` is combined with any other argument, reject it before
argparse can print usage or echo caller-supplied values; emit only the fixed
`BLOCKED:DIAGNOSTIC_ARGUMENTS_INVALID` code.
Normal inventory mode retains its existing required `--source-commit` and
`--output` arguments and behavior. Regression tests must prove this CLI split,
the exact unit/readlink argv and environment, post-readlink tuple equality,
first-UNKNOWN short-circuit before later unit queries, no path/PID/raw-output
leakage in either stream, no endpoint/client/resource/artifact calls, and the
eleven-command maximum including a timeout/output failure. Invalid diagnostic
arguments must not echo the unexpected token or usage text.

An `UNKNOWN` result remains BLOCKED. Any executable allowlist change requires
separate authoritative package provenance, exact unit-to-identity approval,
new source/tests/workflow/context reviews and a new S3D plan. S449-02F capture
must be planned and executed separately after that change, if needed.

```yaml
slice_id: S449-02F2
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, tools/qualification/native_runtime_inventory.py, tests/tools/test_native_runtime_inventory.py, .codex/evidence/slice-449-02F2-design.md, .codex/evidence/slice-449-02F2-distribution.md, .codex/evidence/slice-449-02F2-consolidation.md, .codex/evidence/slice-449-02F-consolidation.md]
affected_modules: [native qualification unit and executable identity diagnosis]
affected_contracts: [fixed five-unit query set, validated active-service PID handling and post-readlink unit recheck, exact existing executable allowlist, deterministic symbolic-only output, no artifact or runtime mutation]
dependencies: [S449-02F]
parallel_group: sequential
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, tools/qualification/native_runtime_inventory.py, tests/tools/test_native_runtime_inventory.py, .codex/evidence/slice-449-02F2-design.md, .codex/evidence/slice-449-02F2-distribution.md, .codex/evidence/slice-449-02F2-consolidation.md, .codex/evidence/slice-449-02F-consolidation.md]
module_locks: [native LXD/Incus unit identity inspection]
contract_locks: [symbolic diagnostic only; unknown identity blocks; inventory capture remains separate]
architecture_locks: [no host service, endpoint, resource or installation mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: no change; the diagnostic does not establish coexistence or ownership
stop_conditions: [unknown/malformed unit or state/PID drift, raw path/PID/output leakage, unexpected argv/environment, any endpoint/client/resource query, artifact write, command/output/time bound exceeded, any host/runtime mutation]
```

S449-02F2 implementation and its bounded native symbolic diagnostic are
complete. The PC WSL focused suite passed 58 tests; full quality exited 0 with
3,053 tests and 18 skips. On the native test host, the exact committed runner
returned `BLOCKED_UNKNOWN` for `snap.lxd.daemon.service`; no artifact or host
mutation occurred, and its hash-matched temporary copy was removed. This is a
fail-closed diagnostic result, not an identity admission or inventory pass.

##### Slice 02F3 — Classify a blocked Snap executable shape symbolically

Purpose: make the S449-02F2 `BLOCKED_UNKNOWN` result actionable without exposing
the process path or running additional host commands. The classifier uses only
the already-read resolved executable path held in memory and never admits an
identity or changes the executable allowlist.

For an unknown `snap.lxd.daemon.service` identity, emit exactly one fixed
`reason` enum in the existing blocked JSON result:

- `SNAP_ROOT_PATH_MISMATCH` when the absolute path is beneath `/snap/lxd/` but
  does not match the existing approved numeric-revision executable pattern.
- `SNAP_EXECUTABLE_OUTSIDE_ROOT` when the absolute path is outside `/snap/lxd/`.
- `SNAP_EXECUTABLE_UNCLASSIFIABLE` when the value is empty or not an absolute
  path.

For any other unknown service identity, use the fixed reason
`EXECUTABLE_IDENTITY_BLOCKED`. Keep status `BLOCKED_UNKNOWN` and identity
`UNKNOWN` in every case. Do not emit or persist any path, revision, basename,
PID, package/version, command output or exception. Do not run `snap`, `stat`,
`findmnt`, additional `readlink`, client, endpoint or resource commands. Do not
write an artifact. Preserve the first-unknown stop, full service recheck,
existing runner bounds and normal inventory behavior.

Tests must cover each reason, exact deterministic JSON, no raw-value leakage,
the unchanged allowed identity path, first-unknown short-circuit, no extra
commands, no artifact, and unchanged normal capture behavior. This diagnostic
classification does not satisfy an #449 acceptance criterion. Any allowlist
change needs separate authoritative provenance, fresh reviews and S3D.

```yaml
slice_id: S449-02F3
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, tools/qualification/native_runtime_inventory.py, tests/tools/test_native_runtime_inventory.py, .codex/evidence/slice-449-02F2-consolidation.md, .codex/evidence/slice-449-02F2-distribution.md, .codex/evidence/slice-449-02F3-design.md, .codex/evidence/slice-449-02F3-distribution.md, .codex/evidence/slice-449-02F3-consolidation.md]
affected_modules: [native LXD/Incus executable diagnosis]
affected_contracts: [fixed symbolic reason enum for rejected executable path, fail-closed UNKNOWN, no additional host commands or artifact]
dependencies: [S449-02F2]
parallel_group: sequential
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, tools/qualification/native_runtime_inventory.py, tests/tools/test_native_runtime_inventory.py, .codex/evidence/slice-449-02F2-consolidation.md, .codex/evidence/slice-449-02F2-distribution.md, .codex/evidence/slice-449-02F3-design.md, .codex/evidence/slice-449-02F3-distribution.md, .codex/evidence/slice-449-02F3-consolidation.md]
module_locks: [bounded native service executable classification]
contract_locks: [symbolic category only; identity remains UNKNOWN; no allowlist change]
architecture_locks: [reuse existing readlink result and runner; no new host command, artifact, or mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: no change; the diagnostic does not establish runtime ownership
stop_conditions: [raw path/PID/output leakage, category outside the fixed enum, extra command, endpoint/client/resource query, artifact write, unit drift, normal capture regression]
```

S449-02F3 implementation is PC WSL verified: 61 focused tests passed; the
full quality gate exited 0 with 3,053 tests and 18 skips. The symbolic reason
does not change the `BLOCKED_UNKNOWN` result or establish identity. Obtain
fresh same-hash implementation reviews, commit this slice, and request a
separate post-commit S3D plan before any native rerun.

##### Slice 02F4 — Verify the Snap wrapper and direct LXD child before normalization

The native F3 result under committed b30828089a2fb2ec1bafa10f15796ec07fa1bbe3 was BLOCKED_UNKNOWN with reason SNAP_EXECUTABLE_OUTSIDE_ROOT. This observation is not ownership, inventory admission or host/scenario GO. Canonical packaging can retain a shell MainPID supervising a direct LXD child. F4 proves that exact relation against the trusted root-owned installed package instead of allowing a generic shell.

The complete normative proof, closed parsers, context allowlists, candidate aliases, cooperative filesystem deadlines, tests, trust limits and release sequence are in `.codex/evidence/slice-449-02F4-design.md`; this file is an explicit read/contract lock of this slice. Exactly two additional fixed systemctl calls belong to the proof; existing outer inventory calls and aggregate budget remain unchanged. The helper keeps the child path internal. `_resolve_executable` returns only the existing `(lxd_snap, snap:lxd)` identity/package pair; no child path is returned, logged or persisted and the inventory artifact schema remains unchanged.

F2/F3 UNKNOWN diagnostics remain unchanged for their CLI modes and historical runs. Only successful full F4 proof inside normal inventory resolution supersedes the MainPID-only assumption for the fixed Snap LXD service. A failed proof remains blocked before client/socket/resource/artifact work. Do not infer exclusive TSW ownership: existing coexistence inventory must still inspect and preserve unrelated resources.

Current execution, review, verification and checkpoint state is recorded only in `.codex/evidence/slice-449-02F4-consolidation.md`; historical observations below do not grant a new release or native invocation. The same-slice v1.41 correction normalizes only omitted empty ExecCondition, ExecStartPre, ExecStartPost and EnvironmentFiles arrays while still requesting all properties. ExecStart and every other property remain mandatory; nonempty hooks, duplicates, unknown/malformed records stay blocked. See the normative design for primary systemd source, exact tests and unchanged proof constraints. A new post-commit exact-source plan and host GO remain mandatory before any native inventory invocation.
```yaml
slice_id: S449-02F4
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F4-design.md, .codex/evidence/slice-449-02F4-distribution.md, .codex/evidence/slice-449-02F4-consolidation.md]
affected_modules: [native Snap wrapper and direct-child identity normalization]
affected_contracts: [exact installed wrapper and unique direct-child proof, existing lxd_snap identity pair only, unchanged inventory artifact and F3 diagnostic]
dependencies: [S449-02F3]
parallel_group: sequential
file_locks: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F4-design.md, .codex/evidence/slice-449-02F4-distribution.md, .codex/evidence/slice-449-02F4-consolidation.md]
module_locks: [bounded native Snap wrapper and child normalization]
contract_locks: [proof before existing identity normalization, no child path emitted or persisted, unchanged outer inventory budget]
architecture_locks: [qualification tooling only, no host mutation or product runtime wiring]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: unchanged; existing qualification adapter boundary and trusted-host-root model remain
  adr: unchanged; no new provider or runtime architecture
stop_conditions: [missing exact-hash role GO or S3D, unsupported unit or process schema, unverified wrapper or child relation, raw-value leakage, expanded allowlist, changed F3 or artifact schema, host mutation, failed quality gate]
```

##### Slice 02F5 — Classify the blocked Snap unit context without disclosure

Historical authoring status: **PLANNED**. F5 has since been implemented and a bounded native F5 result is recorded in S449-02F6. A separately reviewed native S449-02F attempt from clean
source `1ec15b3e9f7f943cdde85e43d00ec01ff9c7e9fd` exited 2 with
`BLOCKED:SNAP_WRAPPER_CONTEXT_BLOCKED`; no inventory artifact or host mutation
occurred. The reason is not known. The bounded F5 contract and D01–D08
requirements are defined in `.codex/evidence/slice-449-02F5-design.md`.
They explicitly extend the historical F4 no-diagnostic-CLI statement only
for this separate diagnostic; normal F4 proof acceptance and errors remain
unchanged. No existing result approves F5 implementation or native execution.

The diagnostic uses exactly the existing fixed F4 systemctl queries and
trusted allowed drop-in/environment reads; no additional command, socket,
client, endpoint or resource query, arbitrary path, artifact or host mutation.
The sole invocation is `python3 tools/qualification/native_runtime_inventory.py
--diagnose-snap-context`. The flag must be the only argument; any combination,
duplicate or value returns fixed `UNKNOWN` JSON and exit 2 without argparse
usage, argument text or host access. The design specifies the initial fixed
five-property unit snapshot followed by at most two identical F4 detailed
systemctl queries, exact argv, collection/recheck/abort order and budgets.
It performs in-memory bounded checks and emits exactly `status` and `reason`;
status is always `BLOCKED_UNKNOWN`, exit 2. The closed reason priority is
`EXECSTART_FORMAT_OR_TIME`, `CONTROL_GROUP`, `FRAGMENT_OR_HOOK`,
`DROPIN_OR_ENV_SETTING`, `ENVIRONMENT_FILE_SPEC`, `DROPIN_CONTENT`,
`ENVIRONMENT_FILE_CONTENT`, then `UNKNOWN`. Invalid/malformed, I/O, limit,
drift, ambiguous prerequisite or no reproducible rejection yields `UNKNOWN`.
Never emit raw values, paths, PIDs, arguments, environment, file content,
exceptions or secret hashes. Recheck service/context/file identity and fail
closed. Deadlines on local file operations remain cooperative.

Same-hash Requirement, Architecture, Python Automation, Tester, Security and
DevOps reviews and S3D are required before implementation. Run focused tests
and the full required gate on exact bytes through the designated SSH PC WSL
host. A native diagnostic requires a separate post-commit same-source plan,
reviews and host GO; it is not an inventory, ownership proof or live support.
An evidence-based correction and subsequent S449-02F retry each require their
own separately authorized scope, review and GO. S449-02F remains BLOCKED until
a fresh complete inventory succeeds; S449-02G requires that successful
inventory and proof of exclusive ownership. S449-02H retains its YAML dependency
on S449-02F and must not start before that prerequisite is satisfied. No later
host mutation is authorized.

```yaml
slice_id: S449-02F5
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F5-design.md, .codex/evidence/slice-449-02F5-distribution.md, .codex/evidence/slice-449-02F5-consolidation.md]
affected_modules: [native Snap context qualification diagnosis]
affected_contracts: [closed symbolic diagnostic result, unchanged F4 fail-closed proof, no disclosure or host mutation]
dependencies: [S449-02F4]
parallel_group: sequential
file_locks: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F5-design.md, .codex/evidence/slice-449-02F5-distribution.md, .codex/evidence/slice-449-02F5-consolidation.md]
module_locks: [native Snap proof and diagnostic]
contract_locks: [closed reason enum, F4 acceptance and errors unchanged, no sensitive values or artifact]
architecture_locks: [qualification only, no product or host mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: no change; qualification-only diagnostic
  adr: no change; no ownership, version admission or runtime policy change
stop_conditions: [unknown or drifting identities, unsafe path or disclosure, altered F4 acceptance, extra host command or resource call, output or deadline limit, missing independent review, mismatched source, any host mutation]
```


##### Slice 02F6 — Classify the rejected Snap drop-in form without disclosure

Historical authoring status: PLANNED. F6 was implemented at 4f52873330b665ab013b607c26d7172194ff375b and a bounded native result is recorded in F7; that private result still needs independent review. A separately reviewed native F5 diagnosis on source
04a0c3cf3b641775cad59da12a7951e0eb5035cc returned BLOCKED_UNKNOWN /
DROPIN_CONTENT and exit 2. It did not disclose file values or admit inventory,
identity, support or ownership. Private evidence must be independently reviewed
for the later host phase. The user requested a separate bounded diagnosis.

The sole F6 invocation is python3 tools/qualification/native_runtime_inventory.py
--diagnose-snap-dropin. Any other argument, duplicate, combination or value
returns fixed UNKNOWN JSON and exit 2 without argparse or host access. Every
result is a closed JSON object containing status BLOCKED_UNKNOWN and reason
SECTION_SHAPE, UNKNOWN_DIRECTIVE, DEPENDENCY_VARIANT or UNKNOWN; exit is 2.
No raw content, values, paths, PIDs, arguments, exceptions or secret hashes.

Only the F5 fixed initial five-property query and up to two existing detailed
F4 unit queries are allowed, with the same order, state/PID checks, arguments
and bounds. After unit-level F4 checks pass, use existing descriptor-bound
no-follow trust checks to read only fixed F4 UNIT_FILE and, if its exact
reference is admitted, DROP_IN. Never derive a path from unit data or read
/etc/environment, even on a valid drop-in. Candidate categories require a
reproducible F5 DROPIN_CONTENT rejection on the same trusted snapshot; before
emission repeat the detailed query and re-observe each file actually read,
requiring identical trusted descriptor identities and bytes. Unknown state,
I/O or drift yields UNKNOWN; no extra commands, resource calls or mutation.

After exact F4 blank/comment filtering, CR, NUL, any backslash escape or
continuation, invalid UTF-8, ambiguous syntax, I/O, trust, limits or a
non-reproducible rejection produce UNKNOWN. Otherwise use strict priority:
SECTION_SHAPE if section structure is not exactly one first [Unit];
UNKNOWN_DIRECTIVE if there is not exactly one subsequent After= line or an
additional significant line or duplicate; DEPENDENCY_VARIANT only if section
and directive shape pass but the complete After= line differs from F4's exact
accepted line. Category is only a form observation, never a safety judgment or
permission to broaden accepted grammar. Detailed D01–D10 and collection rules
are in .codex/evidence/slice-449-02F6-design.md. F4/F5 behavior is unchanged.

F6 explicitly extends the historical F5 sole-CLI contract, without changing
the latter's behavior. Six same-hash Requirement, Architecture, Python, Tester,
Security and DevOps reviews and S3D precede implementation. Run targeted tests,
direct Ruff on the two qualification tools and full QUALITY on the designated
SSH PC WSL host on exact bytes. A native diagnosis requires a separate
post-commit exact-source six-role plan, S3D and host GO. It does not admit an
automatic correction or inventory retry. S449-02F remains BLOCKED; 02G and 02H
retain their explicit S449-02F dependencies and other gates.

```yaml
slice_id: S449-02F6
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F6-design.md, .codex/evidence/slice-449-02F6-distribution.md, .codex/evidence/slice-449-02F6-consolidation.md]
affected_modules: [native Snap drop-in qualification diagnosis]
affected_contracts: [closed structural reason enum, unchanged F4 and F5 acceptance, no disclosure or host mutation]
dependencies: [S449-02F5]
parallel_group: sequential
file_locks: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F6-design.md, .codex/evidence/slice-449-02F6-distribution.md, .codex/evidence/slice-449-02F6-consolidation.md]
module_locks: [native Snap proof and diagnostic]
contract_locks: [closed F6 reason enum, F4 and F5 acceptance unchanged, fixed trusted files, no sensitive values or artifact]
architecture_locks: [qualification only, no product or host mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance, python3 -m ruff check tools/qualification/native_runtime_inventory.py tools/qualification/native_lxd_snap_provenance.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: no change; qualification-only diagnosis
  adr: no change; no ownership, version admission or runtime policy change
stop_conditions: [unverified F5 result, unknown or drifting identity, unsafe path or disclosure, altered F4 or F5 behavior, environment read, extra host command or resource call, deadline or output limit, missing review, mismatched source, any host mutation]
```

##### Slice 02F7 — Compare a source-bound Snap generator form

Historical authoring status: PLANNED. F7 was implemented at fd8dd1478329ee00a907822b4e43b19efc14a631 and its bounded native diagnosis returned BLOCKED_UNKNOWN / UNKNOWN, exit 2; private evidence requires independent review. Native F6 source 4f52873330b665ab013b607c26d7172194ff375b
returned BLOCKED_UNKNOWN / DEPENDENCY_VARIANT, exit 2; private F6 evidence
requires independent review before F7 host phase. The exact public source,
digest, sixteen static tokens and bounded subset grammar are normative in
`.codex/evidence/slice-449-02F7-design.md`; this is a read/contract lock.

Only `--diagnose-snap-generator-form` alone is valid. Every result is a
closed JSON status BLOCKED_UNKNOWN with reason MATCH or UNKNOWN and exit 2.
Invalid CLI combinations produce UNKNOWN without host I/O. MATCH is only
stable form correlation, never actual authorship, identity, safety or
inventory admission. No raw data, path, PID, argv or secret hash is emitted.

Use the existing fixed F5 initial unit query plus at most two F4 detailed
queries. Reproduce F6 rejection on fixed trusted UNIT_FILE/DROP_IN. Bind the
active fixed service/PID/cgroup and Snap revision 40958 through existing
bounded `_Proof.process`, `_Proof.main_environment` and `_Proof.shell`.
Use `_Proof.pair` to read only the fixed validated-revision script in host
and PID-root views with no-follow, root/mode, read-only package device,
identity/bytes equality, 1 MiB cap and exact pinned public SHA-256; never
execute it. Process environment/argv stay in memory and are not emitted,
retained or hashed. Do not read `/etc/environment`. Recheck unit, process,
script and fixed drop-in descriptors/identity/bytes before output. Fixed
closed grammar, deadlines and aggregate budgets are in the F7 design. Unknown,
trust, I/O, malformed syntax, changed revision or drift => UNKNOWN. No
additional systemctl, client, socket, resource, network or host mutation.

This F7-only extension to F6's no-extra-file contract does not change normal
F4/F5/F6 behavior or admit identity. Six same-hash role reviews, S3D,
exact-source SSH PC WSL targeted tests, direct Ruff and full QUALITY are
required. A separate post-commit native plan/S3D/JIT/GO is required before
one host diagnostic; correction and S449-02F inventory each need separately
reviewed phases. S449-02F remains BLOCKED; 02G and 02H retain prerequisites.

```yaml
slice_id: S449-02F7
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F7-design.md, .codex/evidence/slice-449-02F7-distribution.md, .codex/evidence/slice-449-02F7-consolidation.md]
affected_modules: [native Snap source-bound generator-form diagnosis]
affected_contracts: [pinned source and revision, closed symbolic result, unchanged F4 F5 F6 behavior, no disclosure or host mutation]
dependencies: [S449-02F6]
parallel_group: sequential
file_locks: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F7-design.md, .codex/evidence/slice-449-02F7-distribution.md, .codex/evidence/slice-449-02F7-consolidation.md]
module_locks: [native Snap proof and diagnostics]
contract_locks: [closed F7 result, fixed source grammar, F4 F5 F6 behavior unchanged, no sensitive output or artifact]
architecture_locks: [qualification only, no product or host mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance, python3 -m ruff check tools/qualification/native_runtime_inventory.py tools/qualification/native_lxd_snap_provenance.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: no change; qualification-only diagnosis
  adr: no change; no ownership, support or runtime policy change
stop_conditions: [unverified F6 result, unknown or drifting unit PID revision script or drop-in, unsafe path or disclosure, altered F4 F5 F6 behavior, environment-file read, extra host command or resource call, deadline or output limit, missing review, mismatched source, any host mutation]
```


##### Slice 02F8 — Diagnose the first reproducible F7 failure stage

Historical authoring status: PLANNED. F8 was subsequently implemented at
7615a29962b0fd3ae2d44e4246893335ad9fadd3 and its bounded native diagnosis
returned BLOCKED_UNKNOWN / PROCESS_BINDING, exit 2; private evidence requires
independent review. The separately reviewed native F7 diagnosis on source
fd8dd1478329ee00a907822b4e43b19efc14a631 returned BLOCKED_UNKNOWN / UNKNOWN,
exit 2; no failure cause or inventory admission follows. Private native records
must be independently reviewed before the F8 host phase. The user requested
continued investigation. The normative stage, stability, recheck, budget,
disclosure and D01–D10 contract is .codex/evidence/slice-449-02F8-design.md.

Only python3 tools/qualification/native_runtime_inventory.py
--diagnose-snap-generator-stage with the flag alone is valid. Invalid, duplicate,
combined, equals-value and help inputs return fixed UNKNOWN JSON/exit 2 without
argparse leakage or host I/O. All outputs are two-field BLOCKED_UNKNOWN JSON and
exit 2. Closed priority: UNIT_CONTEXT, DROPIN_TRUST_OR_FORM, PROCESS_BINDING,
REVISION_BINDING, SHELL_BINDING, SCRIPT_PAIR_OR_DIGEST, RECHECK_DRIFT, UNKNOWN.

Classify only explicit typed deterministic negative predicates, with previously
acquired trusted observations independently and stably rechecked within the
existing F7 limits. Never map arbitrary exception strings. I/O/permission,
parse/schema, timeout/limits, ambiguity or incomplete/failed recheck returns
UNKNOWN. A successful F7 path returns UNKNOWN. RECHECK_DRIFT requires two fully
trusted semantically comparable successful observations which differ. Preserve
the first F7-stage priority; do not access later unsafe stages to force a reason.
No value, PID, argv, environment, secret hash, error text, path or traceback
appears on either stream. No identity, ownership, safety or inventory admission.

Only F7 fixed initial and up to two detailed systemctl queries and existing
bounded trusted fixed unit/drop-in, validated PID/process/shell/revision, script
pair and necessary in-memory proc reads are allowed. No extra subprocess,
derived path, client/socket/network, /etc/environment, host mutation or
inventory artifact. F4–F7 behavior remains unchanged. Six same-hash roles and
S3D precede implementation. Exact-source SSH PC WSL targeted tests, direct
Ruff and full QUALITY precede an independently reviewed post-commit host
plan/S3D/JIT/GO. S449-02F remains BLOCKED; 02G/02H retain prerequisites.

```yaml
slice_id: S449-02F8
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F8-design.md, .codex/evidence/slice-449-02F8-distribution.md, .codex/evidence/slice-449-02F8-consolidation.md]
affected_modules: [native Snap shared proof and stage diagnosis]
affected_contracts: [closed typed failure-stage enum, trusted stable observations, unchanged F4 F5 F6 F7, no disclosure or host mutation]
dependencies: [S449-02F7]
parallel_group: sequential
file_locks: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F8-design.md, .codex/evidence/slice-449-02F8-distribution.md, .codex/evidence/slice-449-02F8-consolidation.md]
module_locks: [native Snap proof and diagnostics]
contract_locks: [closed typed stage enum, F4 F5 F6 F7 invariants, existing read and command budget, no sensitive output or artifact]
architecture_locks: [qualification only, no product or host mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance, python3 -m ruff check tools/qualification/native_runtime_inventory.py tools/qualification/native_lxd_snap_provenance.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: no change; qualification-only diagnostic
  adr: no change; no ownership, support or runtime policy change
stop_conditions: [unverified F7 result, missing exact-hash review or S3D, unstable or unsafe observations, disclosure, changed F4 F5 F6 F7 behavior, environment-file read, extra host command or resource call, deadline or output limit, any host mutation]
```

##### Slice 02F9 — Classify the rejected process cgroup relation

Status: **HISTORICAL — implemented and executed**. Native F9 source `4adcdfe456afddd881820c9a060a53113a2febfd` returned `BLOCKED_UNKNOWN / PROC_ROOT`, exit 2; its private result requires independent review. This does not establish a cause, namespace identity, inventory success or host admission.

Earlier F9 planning basis: Native F8 source
`7615a29962b0fd3ae2d44e4246893335ad9fadd3` returned
`BLOCKED_UNKNOWN / PROCESS_BINDING`, exit 2. Code links this bounded stage to
a reproducible cgroup-v2 path mismatch, not its cause, namespace, process
identity or ownership. The private result must be independently reviewed
before an F9 host phase; no inventory or host mutation is claimed.

The only F9 invocation is `python3 tools/qualification/native_runtime_inventory.py
--diagnose-snap-cgroup-relation`. If this flag is mixed with any other argument
or supplied as a duplicate or value, emit fixed UNKNOWN JSON and exit 2 without
argparse or host I/O. Calls without the flag preserve F4–F8 behavior. The output
is exactly two JSON keys, status `BLOCKED_UNKNOWN`, reason
`PROC_ROOT|PROC_STRICT_ANCESTOR|PROC_STRICT_DESCENDANT|DISJOINT|UNKNOWN`,
and exit 2. Never disclose raw values, paths, PID, arguments or sensitive
hashes. The comparison is component-based; `/a` is not an ancestor of `/ab`.
Its direction, root precedence, syntax, exact F8 input/recheck requirements,
budget, D01–D10 and failure handling are normative in
`.codex/evidence/slice-449-02F9-design.md` and are locked for this slice.

No common cgroup namespace is assumed or proven. Unit ControlGroup root is
rejected by the unchanged F8 context guard: a pure helper may test its
mathematical relation, but the F9 diagnostic returns UNKNOWN and never admits
that context. Only F8's already admitted
fixed queries and trusted unit/drop-in/process snapshots may be consumed or
rechecked under the same command, byte and cooperative deadline budgets. No
additional file, systemd command, client, socket, network, /etc/environment,
artifact or host mutation is authorized. F4–F8 acceptance and outputs remain
unchanged. I/O, invalid input, drift, incomplete recheck or non-reproduced
F8 mismatch returns UNKNOWN. Every relation is a bounded observation only.

Six same-hash Requirement, Architecture, Python, Tester, Security and DevOps
reviews plus S3D precede implementation. Exact-source targeted tests, direct
Ruff and full QUALITY run on the designated SSH PC WSL host. A separate
post-commit exact-source plan, independent reviews, S3D/JIT and host GO are
required before at most one native diagnosis. A correction or new S449-02F
inventory requires its own scope, evidence and review; S449-02F remains
BLOCKED and 02G/02H retain successful-inventory prerequisites.

```yaml
slice_id: S449-02F9
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F9-design.md, .codex/evidence/slice-449-02F9-distribution.md, .codex/evidence/slice-449-02F9-consolidation.md]
affected_modules: [native Snap process and cgroup relation diagnosis]
affected_contracts: [closed componentwise reason enum, trusted stable F8 snapshots, unchanged F4 F5 F6 F7 F8, no disclosure or host mutation]
dependencies: [S449-02F8]
parallel_group: sequential
file_locks: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F9-design.md, .codex/evidence/slice-449-02F9-distribution.md, .codex/evidence/slice-449-02F9-consolidation.md]
module_locks: [native Snap proof and diagnostics]
contract_locks: [closed componentwise enum, F4 F5 F6 F7 F8 invariants, existing read and command budget, no sensitive output or artifact]
architecture_locks: [qualification only, no product or host mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance, python3 -m ruff check tools/qualification/native_runtime_inventory.py tools/qualification/native_lxd_snap_provenance.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: no change; qualification-only diagnostic
  adr: no change; no ownership, namespace, support or runtime policy change
stop_conditions: [unverified F8 result, missing exact-hash review or S3D, unstable or unsafe observations, namespace inference, disclosure, changed F4 F5 F6 F7 F8 behavior, additional file or host command, resource access, deadline or output limit, any host mutation]
```

##### Slice 02F10 — Compare the current reader and visible PID 1 cgroup namespaces

Status: **PLANNED**. F9 native source `4adcdfe456afddd881820c9a060a53113a2febfd` returned `BLOCKED_UNKNOWN / PROC_ROOT`, exit 2; private result requires independent review. F9 made no namespace reads. The kernel documents that the reader's cgroup namespace controls the view of `/proc/<target>/cgroup`; this observation does not establish the F9 reader, target process or PID 1 namespace identity, nor a cause. See [kernel cgroup v2 namespace documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html#namespace).

The separate sole invocation `python3 tools/qualification/native_runtime_inventory.py --diagnose-snap-reader-namespace` emits exactly `status=BLOCKED_UNKNOWN` and `reason=SAME|DIFFERENT|UNKNOWN` as two JSON fields and exits 2. Invalid combinations, duplicate flags and flag values emit UNKNOWN without host I/O. Existing F4–F9 behavior stays unchanged. SAME or DIFFERENT describes only this F10 reader versus its visible PID 1, never host/initial namespace, target namespace, membership, safety, admission or the cause of F9. F10 is the sole narrow exception to F9's no-namespace-read boundary. The design and safety requirements in `.codex/evidence/slice-449-02F10-design.md` are mandatory; unsupported ABI, unverified filesystem provenance or unproven reader binding must fail UNKNOWN. Within the existing F4 trusted local-root boundary, fixed proc self readlink must equal getpid; pinned procfs traversal uses openat2 no-cross-mount/no-symlink resolution and statx mount IDs. Final fixed link descriptors are checked before namespace FDs are followed and rechecked; unavailable or uncertain checks have no fallback. No host or initial PID namespace is inferred. S449-02F remains BLOCKED, and 02G/02H retain successful-inventory prerequisites.

```yaml
slice_id: S449-02F10
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F10-design.md, .codex/evidence/slice-449-02F10-distribution.md, .codex/evidence/slice-449-02F10-consolidation.md]
affected_modules: [native Snap diagnostic]
affected_contracts: [fixed namespace comparison, F9 baseline, no disclosure, unchanged F4-F9]
dependencies: [S449-02F9]
parallel_group: sequential
file_locks: [tools/qualification/native_runtime_inventory.py, tools/qualification/native_lxd_snap_provenance.py, tests/tools/test_native_runtime_inventory.py, tests/tools/test_native_lxd_snap_provenance.py, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-02F10-design.md, .codex/evidence/slice-449-02F10-distribution.md, .codex/evidence/slice-449-02F10-consolidation.md]
module_locks: [native Snap proof and diagnostics]
contract_locks: [standalone flag and closed output, trusted procfs and namespace type, pinned identities and F9 recheck, no disclosure]
architecture_locks: [F10-only read exception, no runtime behavior change, bounded read-only, no new network or commands]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_runtime_inventory tests.tools.test_native_lxd_snap_provenance, python3 -m ruff check tools/qualification/native_runtime_inventory.py tools/qualification/native_lxd_snap_provenance.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: no change; qualification-only diagnostic
  adr: no change; existing F4 trust boundary and no runtime policy change
stop_conditions: [unverified F9 evidence, unsupported ABI, unsafe procfs or namespace descriptor, identity drift, resource limit, missing six reviews or S3D, disclosure, F4-F9 regression, host mutation]
```

Six independent same-hash Requirement, Architecture, Python, Tester, Security and DevOps reviews plus S3D EXECUTION_PLAN precede implementation. A separate exact-source host plan, JIT checks, independent review and host GO follow implementation and successful SSH PC WSL quality; only one F10 diagnostic execution is authorized within that separate phase. Neither this plan nor quality results constitute host GO or successful inventory.

##### Conditional Slice 02G — Native LXD maintenance for TSW replacement

This slice may be authored only if S449-02F exact evidence proves the active
LXD service owns exclusively the three named TSW instances
`swarm-manager`, `swarm-worker-1` and `swarm-worker-2`, with no unrelated
instances, profiles, networks, storage pools, projects, consumers or host
services. Any unknown, shared or unrelated resource keeps native qualification
`BLOCKED` and forbids this slice. User authorization to replace these three TSW
instances does not itself approve a service stop.

If eligible, create a separate maintenance/recovery plan and obtain fresh
Requirement, Architecture, Security, DevOps and Test/Evidence approval bound to
one native host/scenario GO before any write. The GO must bind exact source and
inventory hashes, the exact LXD unit and three instance identities, private
pre-state and intended new post-state, maintenance window, bounded stop/restart
commands, expected exit/state at each checkpoint, and qualification-run
recovery behavior. Store the GO and result only on verified ext4 below the
existing owner-only evidence directory, mode 0700, with each file mode 0600.
No backup or restoration of the old three TSW instance
contents is required; their replacement is explicitly authorized. Stop only
the exact verified TSW-owned service, replace only the three named TSW
instances, then restart only that service and verify the intended new runnable
TSW state, endpoints, network and storage identity. Verify service recovery
after restart. A host reboot is an optional, separate
host-wide operation and requires separate explicit authorization, its own exact
GO and recovery evidence; no reboot is automatic. Never stop,
restart or modify Incus, another LXD service, unrelated host services, shared
profiles, firewall/PortProxy state, or any unlisted resource.

```yaml
slice_id: S449-02G
profile: RUNTIME_QUALIFICATION
owner: Senior DevOps Engineer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Test/Evidence Reviewer]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/native_lxd_maintenance.py, tests/tools/test_native_lxd_maintenance.py, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-maintenance-go.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-maintenance-result.json, .codex/evidence/slice-449-02G-distribution.md, .codex/evidence/slice-449-02G-consolidation.md]
affected_modules: [native LXD service maintenance, three TSW instance replacement and recovery]
affected_contracts: [exact native five-role GO, exact unit and instance allowlist, private pre-state and intended new post-state, bounded stop/restart and service recovery, qualification-run recovery evidence]
dependencies: [S449-02F]
parallel_group: serialized-live
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/qualification/native_lxd_maintenance.py, tests/tools/test_native_lxd_maintenance.py, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-maintenance-go.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-maintenance-result.json, .codex/evidence/slice-449-02G-distribution.md, .codex/evidence/slice-449-02G-consolidation.md]
module_locks: [native host LXD service and the three allowlisted TSW instances]
contract_locks: [five-role host/scenario GO, explicit instance allowlist, exact intended new state, qualification recovery and service recovery]
architecture_locks: [no shared or unowned host resource mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.tools.test_native_lxd_maintenance]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: update only if an accepted coexistence decision changes architecture
  adr: required before changing LXD/Incus coexistence or runtime ownership policy
stop_conditions: [inventory not exclusive to the three named TSW instances, any unlisted/unknown resource, GO/hash mismatch, ext4/0700/0600 evidence check failure, pre-state drift, stop/restart timeout or unexpected exit, intended new TSW state or qualification recovery failure, optional separately approved reboot recovery failure, any unrelated service/resource/network/storage/profile drift]
```

##### Conditional Slice 02H — Resolve WSL feature readiness before admission

The current sanitized Windows preflight reports
`Microsoft-Windows-Subsystem-Linux` disabled and proposes `enable_features`
with Windows restart scope. This is a current `BLOCKED` prerequisite; no
feature or configuration change and no restart has occurred. First verify from
the supported Windows Store WSL operating requirements whether this feature is
required for the exact WSL installation and distro. Persist only allowlisted
parsed fields and command metadata on verified ext4 under the owner-only
evidence directory (directory mode 0700, files mode 0600). Keep raw PowerShell
output, ACL details and SIDs in memory only; do not place them in logs or
evidence. If the feature is required, obtain fresh exact-hash Requirement,
Architecture, Security, DevOps and Test/Evidence approval plus explicit
Windows-host GO before enabling only the exact feature and restarting Windows.
Bind the GO to before/after feature state, exact distro and WSL identity,
command/exit/timestamp, restart and recovery procedure, and unchanged
firewall/PortProxy snapshots. Verify WSL/distro and service recovery afterward.
No current read-only S3D plan authorizes enabling the feature or restarting
Windows.

If authoritative Store WSL requirements establish the optional feature is not
needed, the existing product preflight still reports it disabled and cannot
pass unchanged. Remain `BLOCKED` and route a separately reviewed S449-02I
product-preflight compatibility slice, or obtain explicit exact Windows-host
GO to enable the feature. Do not infer that documentation makes the current
preflight succeed.

```yaml
slice_id: S449-02H
profile: RUNTIME_QUALIFICATION
owner: Senior DevOps Engineer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Test/Evidence Reviewer]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-feature-readiness.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-feature-maintenance-go.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-feature-maintenance-result.json, .codex/evidence/slice-449-02H-distribution.md, .codex/evidence/slice-449-02H-consolidation.md]
affected_modules: [Windows WSL feature readiness, host maintenance and recovery evidence]
affected_contracts: [exact feature applicability evidence, explicit Windows-host GO, before/after feature state, exact distro identity, restart/recovery, unchanged firewall/PortProxy]
dependencies: [S449-02E, S449-02F]
parallel_group: serialized-live
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-feature-readiness.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-feature-maintenance-go.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-feature-maintenance-result.json, .codex/evidence/slice-449-02H-distribution.md, .codex/evidence/slice-449-02H-consolidation.md]
module_locks: [Windows WSL feature and WSL/distro recovery]
contract_locks: [no feature enable/restart without explicit exact-hash host GO, complete firewall/PortProxy preservation]
architecture_locks: [WSL2 host boundary]
quality_gates:
  targeted: [git diff --check, verify exact pre/post Windows feature and WSL recovery evidence]
  required: [independent five-role maintenance review and host-specific GO]
documentation:
  arc42: no change
  adr: no change unless supported WSL platform requirements alter architecture
stop_conditions: [feature necessity unverified, GO/hash mismatch, unsupported distro, unexpected Windows state, raw PowerShell/ACL/SID output logged or persisted, ext4/0700/0600 evidence check failure, restart/recovery failure, any firewall/PortProxy change; optional-feature outcome routes to S449-02I or explicit Windows-host GO and remains BLOCKED meanwhile]
```

##### Conditional Slice 02I — Reconcile preflight with supported Store WSL

Author this separate compatibility slice only if S449-02H records authoritative
Microsoft requirements and exact host evidence showing Store-managed WSL makes
`Microsoft-Windows-Subsystem-Linux` optional for this target. The existing
blocker is produced by `prepare_windows.ps1` policy in
`tools/windows/preparation/Policy.ps1`, before WSL version and distro checks;
do not change the unrelated Python host-preparation adapter. In `Policy.ps1`
and its host-fact adapter, permit bypassing only this missing-feature action
when Store package identity and supported package version are verified, the
selected distro is observed in the authoritative inventory with generation
exactly 2, and `VirtualMachinePlatform` is enabled. Require exact typed facts;
missing/unknown facts, inbox WSL, WSL1, absent/unknown generation, or missing
VirtualMachinePlatform continue to block. Preserve all other feature checks,
WSL version/install gates, resource checks, and safety checks. Add deterministic
mocked policy cases in `tests/windows/prepare-windows.Tests.ps1`, executed by
`tests/test_prepare_windows.py`; no Windows feature/configuration/restart action
is permitted. Require fresh same-hash Requirement, Architecture, Python
Automation, Security and Tester reviews plus phase-specific S3D
`EXECUTION_PLAN`, targeted test and full QUALITY before a new exact-source
read-only preflight. If official evidence or any typed fact is unavailable,
remain `BLOCKED`.

```yaml
slice_id: S449-02I
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior DevOps Engineer, Senior Tester]
affected_files: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/windows/preparation/Policy.ps1, tools/windows/preparation/Adapters.ps1, tests/windows/prepare-windows.Tests.ps1, tests/test_prepare_windows.py, .codex/evidence/slice-449-02I-distribution.md, .codex/evidence/slice-449-02I-consolidation.md]
affected_modules: [Windows preparation policy and host-fact adapters]
affected_contracts: [authoritative Store WSL feature applicability, explicit distro/platform compatibility rule, unchanged independent resource/safety checks, no Windows host mutation]
dependencies: [S449-02H]
parallel_group: sequential
file_locks: [documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, tools/windows/preparation/Policy.ps1, tools/windows/preparation/Adapters.ps1, tests/windows/prepare-windows.Tests.ps1, tests/test_prepare_windows.py, .codex/evidence/slice-449-02I-distribution.md, .codex/evidence/slice-449-02I-consolidation.md]
module_locks: [WSL Windows preparation feature preflight]
contract_locks: [optional Windows feature applicability, fail-closed WSL identity and capacity validation]
architecture_locks: [Linux/WSL-only host preparation boundary]
quality_gates:
  targeted: ["SSH approved PC WSL; from verified repo root run: PYTHONPATH=src python3 -m unittest tests.test_prepare_windows.TestWindowsPreparation.test_mocked_pre_linux_lifecycle_and_preservation_contract"]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no change
  adr: no change unless the supported WSL platform contract changes
stop_conditions: [official applicability evidence missing/ambiguous, Store package identity/version not verified, selected distro generation not exactly 2, VirtualMachinePlatform missing/unknown, inbox/unknown WSL channel, weakened resource checks, any Windows feature/config/restart action, tests or quality gate fail]
```

Only after S449-02D/E/F pass their fresh reviews and S3D phases may a new
S449-02 pre-GO capture run. It must use the amended exact-source candidate and
produce current per-host route state, resource admission and project/runtime
inventory. Native S449-02 remains blocked unless conditional S449-02G is
eligible and separately passes. WSL S449-02 remains blocked until the feature
requirement is verified; if enabling the Windows feature is required,
conditional S449-02H must pass its exact host GO. Each host then remains
independently gated by its own admission and scenario GO. A host-specific
five-role GO remains mandatory before the
disposable fixture, any Incus/profile/instance write, installation, upgrade,
service/system change or recovery test. Current route capture and native
preflight remain failures/blockers, not passes.

#### S449-02 per-scenario read-only admission and inventory phase (separate from S449-02C)

Begin only after exact S449-02C/02D/02E/02F source, runner/tests and required
reviews are approved and a fresh S3D plan authorizes this read-only phase.
Inspect only native Linux `192.168.178.33` and PC WSL2
`192.168.178.58`, with the exact approved Ubuntu WSL distro identity. Store all
artifacts beneath `.tiny-swarm/evidence/issue-449/s449-private-20261027/` on
verified ext4 checkout, directory mode 0700 and files mode 0600. Fail closed on
unknown distro, failed commands, incomplete output, unknown schema,
insufficient capacity, or unverifiable source/filesystem state.

**Exact source and native host admission.** Run from the approved ext4 repository
root and persist only fixed `command_id`, validated symbolic `safe_args`, exit
code and stdout/stderr byte counts for every command. Never persist argv,
filesystem paths, URLs, raw output or dynamic raw argument values. Keep only
parsed/sanitized values. Hash raw stdout only for the explicit safe
allowlist below; never persist raw stdout or stderr. Run:

```bash
set -o pipefail
git rev-parse HEAD
git status --short --branch
git show HEAD:documentation/workflow/issues/issue-449/workflow.md | sha256sum
git show HEAD:documentation/workflow/issues/issue-449/context-pack.md | sha256sum
git show HEAD:documentation/workflow/issues/issue-449/context-pack.json | sha256sum
git show HEAD:tools/qualification/incus_profile_listener_fixture.py | sha256sum
git show HEAD:tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py | sha256sum
git show HEAD:infra/config/node-providers/provider_config.yaml | sha256sum
findmnt -T "$ROOT" -n -o FSTYPE,TARGET
nproc --all
free -b
df -B1 --output=avail "$ROOT"
incus version
ip -j -4 addr
./prepare_linux.sh --preflight --service-profile service-access
```
Require `HEAD` to equal the reviewed candidate commit, clean tracked tree and
exact SHA-256 values computed from the committed Git blob bytes for the
workflow, runner, tests and `provider_config.yaml` before admission. Use
`git show HEAD:<path> | sha256sum` on both Linux targets so line-ending
conversion in a Windows working copy cannot alter the candidate binding. The
workflow/context review tuple uses the same committed-blob SHA-256 rule for
`workflow.md`, `context-pack.md` and `context-pack.json`; compute each from the
reviewed commit with `git show <commit>:<path> | sha256sum`. Never substitute a
working-tree file hash for any tuple member. Validate the context JSON artifact
map against those canonical blob digests; tracked-tree cleanliness remains a
separate check.
native script invokes existing `NativePreparationService` and
`qualification_failures` in read-only preflight mode; inspect its structured
result and exit and stop on failure/unknown output. Do not install packages or
mutate the host. Raw stdout hash is permitted only for `git status --short
--branch`, `nproc --all`, `free -b`, `df -B1 --output=avail "$ROOT"` and
`incus version` (hash only the exact text output; parse client/server version fields without inferring capability support). For `git rev-parse`, `sha256sum`, `findmnt`,
`ip` and `./prepare_linux.sh`, keep only parsed commit, file hashes,
filesystem/identity facts and resource fields; no raw output or raw-output
hash. The route-state capture follows its separate route-state contract.

Native `service-access` floor is CPU >= 8, RAM >= 15 GiB and free disk >=
150 GiB. R449-33/R449-34 native selection is manager/worker1/worker2 RAM
10/6/1 GiB, CPU 2/2/4 and disk 20/50/10 GiB, totaling 17 GiB RAM, 8 CPU and
80 GiB disk. Native host admission is `max(service-access 15 GiB, selection
17 GiB) = 17 GiB` RAM, CPU >= 8 and free disk >= 150 GiB. Existing default
19 GiB default-node guard applies only where that baseline applies; the accepted ADR supports a 17 GiB TSW_INFRA_ROOT override for this native host. These are accepted
Three-Amigos requirement thresholds, not a host admission result or per-host
GO. They are tied to `src/tiny_swarm_world/infrastructure/adapters/host/native_preparation.py`,
`documentation/arc42/09_decisions/adr-native-linux-preparation-and-install-lifecycle.adoc`,
`documentation/arc42/09_decisions/adr-product-effective-infrastructure-source.adoc`
and R449-33/R449-34.

**Exact WSL host admission.** Verify the exact selected distro identity is
Ubuntu. The current disabled `Microsoft-Windows-Subsystem-Linux` feature is a
BLOCKED prerequisite. Verify whether the exact supported Store WSL installation
requires it. If required, complete conditional S449-02H with its separate
Windows-host GO and restart/recovery evidence first. If authoritative evidence
shows it is optional, complete S449-02I's reviewed product-preflight
compatibility change before rerunning the preflight; an unchanged preflight
that still blocks cannot count as admission. Unknown applicability remains
BLOCKED. This pre-GO phase never enables a feature or restarts Windows. Only
after the applicable H or I path is complete, run the read-only Windows
preflight; preserve only allowlisted parsed resource fields and exit code plus
safe command metadata, never argv or raw PowerShell output/hash:

```powershell
prepare_windows.ps1 -Distro <exact distro> -Preflight -Json -LinuxCheckout <ext4 ROOT>
```
Inside that exact distro and ext4 checkout, run the same Git/hash/filesystem,
CPU/RAM/disk and Incus-version commands listed above, plus `uname -r`. Require
the exact candidate commit, clean tracked tree, workflow/runner/test/
`provider_config.yaml` hashes, structured Windows physical memory/logical CPU,
configured WSL memory/CPU/swap/storage facts and distro/profile identity. Use
`free -b`, `nproc --all` and `df -B1 --output=avail "$ROOT"` for observed guest
usable RAM, CPU and free disk. Unknown/failing facts block; do not use a native
override, substitute a distro, or infer from config alone. Raw stdout hashes
are allowed only for the same five-command safe list above. WSL preflight,
`uname`, `findmnt`, identity queries and other output remain parsed/sanitized
only with no raw-output hash.

WSL selection is manager/worker1/worker2 RAM 10/8/1 GiB, CPU 2/2/4 and disk
20/50/10 GiB (19 GiB RAM, 8 CPU, 80 GiB disk). Apply accepted WSL policy with
no native override: configured WSL RAM >= 21 GiB (19 GiB node budget plus
2 GiB overhead); observed usable guest RAM >= 19 GiB; CPU >= 8; usable distro
disk >= 150 GiB. Windows must satisfy both `configured WSL RAM + max(4 GiB,
ceil(physical RAM / 4)) <= physical RAM` and `8 guest CPUs + max(1,
ceil(logical CPUs / 4)) <= logical CPUs`; implied minimums are 28 GiB physical
RAM and 11 logical CPUs. Retain >= 20 GiB Windows storage after swap growth.
Swap is not physical service RAM. Tie these per-scenario thresholds to
`documentation/arc42/09_decisions/adr-wsl-capacity-adaptation.adoc`,
`src/tiny_swarm_world/infrastructure/adapters/host/native_preparation.py`'s
node source and R449-33/R449-34. Unknown values block; no native threshold
supersedes WSL policy.

**Resource admission artifacts.** Write per-scenario normalized JSON
`native-resource-admission.json` (`scenario_id: R449-33`) and
`wsl-resource-admission.json` (`scenario_id: R449-34`). Recapture and create a
new artifact for every other live scenario; never overwrite prior evidence.
The exact top-level key set is `schema_version`, `target_host`, `platform`,
`scenario_id`, `captured_at_utc`, `source_commit`, `candidate`, `selection`,
`observed`, `thresholds`, `checks`, `decision`, `commands`.
`schema_version` is `tsw.resource-admission.v1`; `platform` is `native_linux`
or `wsl2`; `scenario_id` is the exact requirement/scenario identifier;
`captured_at_utc` is an ISO-8601 UTC timestamp; `source_commit` is lowercase
40-hex and equals current `HEAD`.

`candidate` is exactly `{workflow_sha256, runner_sha256, test_sha256,
provider_config_sha256, clean_tracked_tree}`. Each hash is lowercase SHA-256
of the exact candidate file; `provider_config_sha256` binds
`infra/config/node-providers/provider_config.yaml`, and clean tree is boolean
true only after verifying tracked cleanliness. `selection` is exactly
`{manager, worker1, worker2}`; each node is exactly `{cpu_threads,
memory_bytes, disk_bytes}` and records that scenario's selected budget from
`provider_config.yaml`. Native R449-33 values are respectively (CPU, RAM,
disk) `(2, 10737418240, 21474836480)`, `(2, 6442450944, 53687091200)`,
`(4, 1073741824, 10737418240)`. WSL R449-34 values are `(2, 10737418240,
21474836480)`, `(2, 8589934592, 53687091200)`, `(4, 1073741824,
10737418240)`.

`observed` contains only parsed, platform-specific facts. Native records
Ubuntu distro/version/kernel identity, ext4 filesystem/mount, host RAM, CPU
threads, free disk, Incus version and structured `service-access` preflight.
WSL records exact distro/version/kernel, Windows physical memory/logical CPUs,
configured WSL memory/CPU/swap, Windows free storage after swap growth and
reserved memory/CPU, observed guest usable RAM/CPU/free disk, ext4 filesystem/
mount and Incus version. `thresholds` records the exact relevant floors and
formulas from the preceding section. `checks` records explicit per-check
booleans for exact source cleanliness/hashes, ext4/private storage, service
floor, selection budget, guest capacity and (WSL only) Windows memory/CPU
reserve and post-swap storage checks. `decision` is exactly `PASS` or
`BLOCKED`; any false, unknown or unavailable required fact makes it `BLOCKED`.

`commands` is ordered command metadata only. Each record is exactly
`{command_id, safe_args, exit_status, stdout_bytes, stderr_bytes}` and may
include `stdout_sha256` only for raw stdout of `git status --short --branch`,
`nproc --all`, `free -b`, `df -B1 --output=avail "$ROOT"`, or
`incus version`. No raw command output is persisted; a SHA-256 may be recorded only for this exact command's text stdout. Parse the Client and Server version lines; this observation does not establish capability support.
Preflight, identity, source/hash and Incus project/config outputs remain
parsed/sanitized only. The independent reviewer computes and binds SHA-256 of
the complete normalized resource artifact in GO. Unknowns must be explicit in
`checks` and yield `BLOCKED`, never a default PASS. This evidence is fresh per
host and scenario and is not itself a live-pass claim.
**Route-state capture.** After target identity verification, use only the
existing `--capture-route-state --target-host <approved-ip> --output
<private-path>` mode. It is read-only apart from exclusive private artifact
creation, uses the exact target local endpoint, and does not read GO, reserve,
change `NOT_RUN`, or write Incus state. Its detailed route snapshot contract
remains separate from resource-output redaction.

**Project inventory capture.** The current S449-02C candidate has an opt-in
`--capture-project-inventory` mode, but it is not accepted for S449-02 until
full-access visibility, absent-feature handling, exact schema/argv and tests
are approved. CLI:

```text
python3 tools/qualification/incus_profile_listener_fixture.py --capture-project-inventory --target-host <approved-ip> --output <private-evidence-path>
```
Before enumeration, verify target identity and local Incus Unix endpoint using
`incus remote list --format json` and `incus remote get-default`; require the selected default alias to be `local` and its `Addr` to equal `unix://`. Other configured aliases may exist; they are not selected or recorded because the collector uses a sanitized environment and exact allowlisted commands without remote prefixes.
The remote list schema allows exactly `Addr`, `AuthType`, `KeepAlive`, `Project`, `Protocol`, `CredHelper`, `Public`, `Global` and `Static`. `Addr` must equal `unix://`; optional `KeepAlive` must be a nonnegative JSON integer (not bool); other optional fields must have their Incus 6.0.5 types. Persist or hash no raw remote JSON.
Require full project visibility: local effective uid 0 or membership in local
`incus-admin`; otherwise fail closed with `INCUS_PROJECT_VISIBILITY_UNVERIFIED`.
This is required because project listing can be visibility-limited for
confined users. Use only these Incus argv templates; expand validated names as
separate argv items, never through a shell:

```text
incus remote list --format json
incus remote get-default
incus project list --format json
incus project show <project> --format json
incus profile list --project <project> --format json
incus profile show <profile> --project <project> --format json
incus list --project <project> --format json
incus config show <instance> --project <project> --format json
incus config show <instance> --project <project> --format json --expanded
```
The exact expanded-config argv order is `--format json --expanded`, matching the
runner. A profile-show response may omit `project`; if present, it must equal
the requested project or fail closed.
Identity queries (`ip -j -4 addr`, `uname -r` and the approved PowerShell IPv4
query) use selector-driven bounded reads. Stdout and stderr each have a 2 MiB
cap and the command timeout is 20 seconds. On overflow or timeout, terminate,
wait 0.5 seconds, then kill and wait if needed; fail closed. Do not persist
or hash raw output; retain only validated identity values and safe command
metadata. Direct cap/timeout regressions must prove no artifact is created on
failure. Direct regressions cover identity stdout/stderr, inventory aggregate output, serialized artifact, total entity and command-count caps, and the 300-second aggregate wall-clock deadline; every limit failure must fail closed without creating an artifact.


The payload top-level is exactly `{schema_version, target_host, source_commit,
projects, command_records}` with `schema_version` `tsw.incus.project-inventory.v1`.
Every capture artifact uses the shared command record schema exactly
`{command_id, safe_args, exit_status, stdout_bytes, stderr_bytes}`; metadata
only, no raw argv, paths, URLs, output bytes or output hashes. `command_id` is
a fixed enum; `safe_args` contains only validated symbolic identifiers such as
project/profile/instance names and endpoint IDs, never path or URL values.
Apply this schema to resource admission, route-state and project-inventory
captures, including the legacy S449-02C mode. Each Incus inventory command is
capped at 2 MiB independently for stdout and stderr; aggregate captured
stdout+stderr across the run is capped at 16 MiB. Sanitized output is capped at
8 MiB before exclusive file creation. The total project/profile/instance/device
entity count is capped at 10,000, total Incus command count at 256, and
aggregate capture wall-clock time at 300 seconds. Any per-stream, aggregate
byte, serialized-artifact, entity or command cap overflow, 30-second
per-command timeout, aggregate wall-clock overrun, nonzero exit,
malformed/unknown field or incomplete visibility fails closed; no sanitized
inventory is accepted. Selector-driven collection enforces each 2 MiB stream
cap while reading, kills the process on a cap, per-command timeout or aggregate
deadline, and parses only bounded complete output. It retains only safe byte
counts and exit status, never raw Incus output or its hash. No output artifact
is created if a limit or validation fails. The pre-existing private ext4
evidence directory must be verified before capture; this read creates the
artifact only after bounded capture, sanitization, schema checks and size
validation succeed. The remote-list/default reads use the same caps and command-count budget.
`issue447_inventory_sha256` binds the exact sanitized inventory artifact.

Projects are sorted and each is exactly `{name, isolation, profiles,
instances}`. Profiles are sorted and each is `{name, used_by, devices}` with
sorted unique `used_by`. Instances are sorted and each is
`{name, status, type, profiles, local_devices, expanded_devices}` with sorted
unique profiles. Device maps are sorted and contain only string fields from
`type`, `name`, `nictype`, `parent`, `network`, `listen`, `connect`, `bind`,
`ports`, `path`, `source`, `pool`, `size`, `readonly`, `required`, `shift`,
`limits.cpu`, `limits.memory`, and `boot.priority`; device types are disk/nic/
proxy. Unknown/sensitive fields/types fail closed. `isolation` is exactly the
four keys `features.images`, `features.profiles`,
`features.storage.volumes`, `features.networks`. Each value is a boolean when
explicitly configured and `null` when absent/unset; null means unknown
configuration, never inferred effective default. Malformed values fail closed.
The current candidate emits the four feature keys as booleans when explicitly
configured and `null` when absent, without inferring effective defaults.

The current payload schema and command argv above are read-only, sanitized
capture requirements, not a claim that the current candidate passes. Tests
must prove root/incus-admin acceptance and confined-user rejection, local
endpoint binding, exact execution argv (including `--format json --expanded` order)
without persisting argv, all-project visibility/order, null/absent feature
behavior, sanitized devices, no raw argv/path/URL/output or hashes in artifacts
and logs, deterministic artifact binding, no GO/reservation/Incus write,
and exclusive private ext4 output. Any unknown project, permission-limited
visibility, absent/unreadable required state, or schema mismatch blocks S02.
This mode is not normal fixture run mode. Five-role per-host GO remains
mandatory before normal fixture invocation, profile/instance mutations,
install/upgrade or service/system changes.
### Slice 02 — Incus 6.0.5 disposable listener fixture evidence

Purpose: verify proxy listener timing and attribution before implementing the
new capability.

Prerequisites: S449-01 and S449-02C/02D/02E/02F; for native, eligible and
accepted S449-02G if active LXD remains the preflight blocker; for WSL, exact
feature applicability is resolved and S449-02H is accepted if enable/restart
is required; disposable
Incus server exactly 6.0.5; fresh exact-source
and target JIT for the specific host; pre-GO route-state evidence from the
amended S449-02D/02E capture mode; resource admission; full issue447
project/profile/consumer/device inventory; empty baseline for the exact selected
loopback fixture tuple and the exact current TCP/10001 listener/route baseline,
which may be empty; any existing entries and Windows firewall/PortProxy bytes
must remain unchanged;
and a one-shot scenario-specific live Three-Amigos GO whose raw SHA-256 and
workflow/runner/test hashes match the released amended candidate, naming the exact host, expected HEAD,
default project, unique disposable instance/profile identity, inventory/profile
and resource digests, loopback-only fixture tuple and cleanup bound. The
fixture uses an unused 61000–65535 loopback listener port, never TCP/10001;
any existing TCP/10001 route and its destination remain unchanged, and an empty
baseline remains empty.
The fixture must never touch user-owned or issue447 resources. TSW application
exposure is limited to TCP/10001; the complete existing WSL Windows firewall
(`RemoteAddress=Any`) and PortProxy state is accepted as-is for this run and
must remain byte-identical. No other TSW listener or route may be introduced;
this fixture does not attest reachability through other pre-existing Windows
forwards. Any other host/route requires exact user approval; WSL approval does
not transfer. The opt-in fixture runner is
never called by automated quality gates; tests mock its command port.

```yaml
slice_id: S449-02
profile: RUNTIME_QUALIFICATION
owner: Senior DevOps Engineer
secondary_reviewers: [Senior System Architect, Security, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-449/s449-private-20261027/s02-private-posix-verification.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-pre-go-route-state.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-pre-go-route-state.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-resource-admission.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-resource-admission.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-issue447-inventory.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-issue447-inventory.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-s02-live-go.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-s02-live-review.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/r67-incus-6.0.5-listener-fixture.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/r67-incus-6.0.5-listener-fixture.json.reservation, .codex/evidence/slice-449-02-distribution.md, .codex/evidence/slice-449-02-consolidation.md]
affected_modules: [Incus disposable fixture, listener evidence]
affected_contracts: [proxy bind timing, effective tuple and listener attribution, exact 17-key five-review GO, workflow/source/runner/test/target hashes, canonical default-profile and sanitized fixture-base-profile digests, sorted consumer list, approved live route-state digest, ext4 private evidence root and POSIX 0700/0600 modes, external resource and issue447 evidence attestations, unchanged Windows rules, no external routes]
dependencies: [S449-02C, S449-02D, S449-02E, S449-02F]
parallel_group: serialized-live
file_locks: [.tiny-swarm/evidence/issue-449/s449-private-20261027/s02-private-posix-verification.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-pre-go-route-state.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-pre-go-route-state.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-resource-admission.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-resource-admission.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-issue447-inventory.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-issue447-inventory.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-s02-live-go.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-s02-live-review.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/r67-incus-6.0.5-listener-fixture.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/r67-incus-6.0.5-listener-fixture.json.reservation, .codex/evidence/slice-449-02-distribution.md, .codex/evidence/slice-449-02-consolidation.md]
module_locks: [per-host live qualification host state, disposable target identity and cleanup evidence]
contract_locks: [per-host GO target identity and cleanup binding, immutable listener-fixture result schema, ext4 private evidence root and POSIX 0700/0600 modes, host-specific run command/exit/provenance record, route-preservation outcome]
architecture_locks: [capability version boundary]
quality_gates:
  targeted: [git diff --check, verify exact amended source/test evidence hashes, verify ext4 target checkout and private evidence permissions]
  required: [reuse full quality evidence only when exact amended source hash matches]
documentation:
  arc42: no change
  adr: record version support only after independent fixture review
stop_conditions: [version mismatch, non-ext4 checkout, /mnt/c or DrvFS evidence path, invalid private directory/file modes, selected loopback port already in use, unreadable route inventory, forbidden listener, attribution failure, non-loopback or TCP/10001 fixture listener, unapproved fixture connect target, any route/listener drift, any added external route, Windows firewall or PortProxy change]
```

Completion criteria: the selected fixture tuple is empty and there is no
listener after profile creation/stopped init; after start only the attributable
loopback fixture listener exists. The pre-run TCP/10001 host/Incus route state
may be empty; any populated state must remain identical, and an empty baseline
must remain empty. Forbidden
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
S449-01 → S449-02C → S449-02D → S449-02E → S449-02F; S449-02F → S449-02G (conditional native maintenance) → S449-02 (native); S449-02F → S449-02H (verify Windows feature applicability); if feature is required, 02H → explicit Windows-host GO and restart/recovery → S449-02 (WSL); if authoritative evidence proves Store WSL exception applies, 02H → S449-02I (policy/tests) → fresh same-hash review/S3D → new read-only preflight → S449-02 (WSL); S449-02 (both hosts accepted) → S449-03 → S449-04 → S449-05 → S449-06 → S449-07 → S449-08 → S449-09
```

The 2026-10-29 blocked native attempt adds the separate serial diagnostic
`S449-02F4 → S449-02F5 → separately reviewed post-commit F5 diagnosis → S449-02F6 → separately reviewed post-commit F6 diagnosis → S449-02F7 → separately reviewed post-commit F7 diagnosis → S449-02F8 → separately reviewed post-commit F8 diagnosis → S449-02F9 → separately reviewed post-commit F9 diagnosis → S449-02F10 → separately reviewed post-commit F10 diagnosis`. Later correction and successful S449-02F inventory remain separate prerequisites.
The diagnostic observation alone does not release the next inventory retry;
any supported correction needs a separately governed decision, then a fresh
post-commit S449-02F plan and GO. This phase-specific retry is not a new edge
from S449-02F5 back to the already executed S449-02F slice.

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
approval of R67j is not a workflow review. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. That earlier candidate had no host/scenario GO or normalized admission. The record path is
`.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md`;
S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. The private record binds decisions to the
exact workflow/context hashes; every reviewed tuple is tracked there.

| Role | Required review | Current candidate status |
|---|---|---|
| Senior Requirement Engineer | R449-01–38, AC1–AC5, W10, EPIC #440 and traceability | See private record for decisions bound to the final hashes |
| Senior System Architect | hexagonal boundaries, Incus profile ownership, persistence, arc42 and locks | See private record for decisions bound to the final hashes |
| Senior Python Automation Developer | ports/adapters/composition, slice paths, testability and lock ownership | See private record for decisions bound to the final hashes |
| Senior Tester | acceptance evidence, exact test gates, live/local state and lock ownership | See private record for decisions bound to the final hashes |

Release decision: every workflow/context hash tuple must receive four-role review, and the private record binds the exact reviewed hashes. Execution is eligible only when the record contains
`APPROVED` decisions for one workflow/context hash set and S3/S3D returns
`EXECUTION_PLAN` for that same revision. The v1.32 approval record and its
`EXECUTION_PLAN` are historical and do not approve this candidate. A private ext4 record becomes authoritative only after its exact hash-bound decisions and storage controls are verified. Each
workflow/context tuple must be reviewed and recorded with its exact hashes.
The v1.5–v1.11 approvals and preflight
do not authorize the current candidate amendment. The v1.6 workflow approval record and
any later pre-v1.12 approval records are superseded. The private
`workflow-execution-approval-v1.32-20261028.md` is historical and must not be
treated as the approval record for this candidate. The current approval state
must be recorded at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` after the record is verified on ext4.

## S3 / S3D Preflight and Clean Execution Handoff

Before any implementation write:

1. Create one workflow-authoring baseline commit containing only the reviewed
   workflow, sibling context pack, workflow index and directly required
   executor discovery support. This is a workflow-authoring checkpoint, not an
   implementation slice. Keep ignored `.tiny-swarm/` approvals, host inventory,
   requirement matrix and source-copy evidence local; never force-add them.
2. Push the reviewed workflow-authoring baseline to
   `origin/docs/workflow-lcm-w09-route-baseline-20261027` as required by workflow-authoring.
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

Status: `ACTIVE_FOR_ISSUE_449 v1.43 — issue execution authorized; slice-specific S3D and scenario GO gates remain mandatory`
The installation-owned profile decision is accepted design policy; no Incus
version is supported yet for this capability. The uncommitted ADR amendment in
the separate primary worktree is proposed and is not adopted by this workflow.
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

- The workflow-only checkpoint is an ancestor of the implementation branch.
  Keep one commit per approved slice and group commits into separate topic
  branches and PRs only where the issue dependency graph gives a complete,
  reviewable topic boundary. Each later topic branch must be based on the
  merged predecessor so `main` receives each topic once and in dependency
  order.
- Do not split a slice across PRs or combine unrelated slices in a commit.
  Close the issue and clean branches/worktrees only after every required topic
  is merged and the independent completion audit passes.
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

## Execution-phase amendment v1.37

S449-02F accepts omitted or explicit zero `MainPID` only for its two fixed
socket units, normalizing the value to zero in the sanitized artifact. It also
accepts `loaded/active/running` only for `incus.socket`, coupled to the active
Incus service identity, exact listener endpoint, endpoint checks and existing
complete rechecks. All other unit tuples remain fail-closed. The first native
read-only attempt under v1.36 returned `UNIT_SCHEMA_INVALID` because systemd
omitted `MainPID` for socket units; it produced no artifact and made no runtime
change. This amendment authorizes only a new exact-hash read-only capture after
fresh reviews and S3D; it grants no host mutation or scenario GO.

S02F v1.37 candidate verification: runner SHA-256
`2084dc090f3b0d55007a9ad017fee4621b4d077642fe402f6fd0538c883f5f0c`; test
SHA-256 `23c8395a3c8a5b6167f36b5e76f052f9df4a307cdc7499a88c898d0cf942aa37`.
On approved PC WSL, the focused suite passed 53 tests. The full quality gate
exited 0 with all seven gates passed. It reported 3,048 tests and 18 skips.
Those skipped tests were not executed and receive no pass credit. Log SHA-256
`cc3f5f1b94219e5b4774c57e5f5063b1d8315c497d9938457d9d66c5ed1ec295`. The
isolated HOME was `/home/pc/projects/issue449-s02f-home-v137-20261028`. An
earlier default-HOME run failed two stale-checkpoint tests; the isolated rerun
passed. The first focused attempt exposed an obsolete assertion, removed before
the final pass. S02F remains `IN_PROGRESS`: no v1.37 native capture or artifact
exists. Commit this candidate, then obtain a separate S3D plan bound to the
committed source/test/workflow/context hashes before the one bounded native
read-only capture. This does not authorize host mutation or scenario GO.


## Code-only consolidation publication path — v1.42

The explicit user instruction excludes live evidence for publication of the existing 86-file candidate. Requirement review authorizes the four exact code-only slices below under local-quality authority. This is an independent consolidation path for ordinary existing-path fixes, not completion of S03–S09. Future scoped Incus profiles, internal Swagger and optional ownership remain unimplemented and gated by S02 and the original dependency chain. No new live work, ownership admission or issue closure belongs to this amendment. See `.codex/evidence/issue-449-code-consolidation-design.md` and `.codex/evidence/issue-449-code-consolidation-distribution.md`; execution/review outcomes belong only in root consolidation. All logical commits are serialized in one PR #499; aggregate final exact quality must be reported honestly.

### S449-C01 — Bind prepared-product effective configuration source and recovery

```yaml
slice_id: S449-C01
profile: CODE_ONLY_CONSOLIDATION
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester]
affected_files: ["documentation/contracts/lifecycle.md","documentation/user_guide/product-upgrades.md","src/tiny_swarm_world/application/ports/lifecycle/product_upgrade.py","src/tiny_swarm_world/application/services/product_upgrade.py","src/tiny_swarm_world/domain/lifecycle/product_upgrade.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_admission.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_capture.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_source.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_validation.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_environment.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_installation.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_journal.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_migration.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_paths.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_runtime.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_verification.py","src/tiny_swarm_world/infrastructure/composition_product.py","tests/application/services/test_product_upgrade.py","tests/infrastructure/adapters/lifecycle/test_product_configuration_source.py","tests/infrastructure/adapters/lifecycle/test_product_upgrade.py","tests/tools/test_secure_runtime_paths.py","documentation/workflow/issues/issue-449/workflow.md","documentation/workflow/issues/issue-449/context-pack.md","documentation/workflow/issues/issue-449/context-pack.json","documentation/workflow/workflow.index.md",".codex/evidence/issue-449-code-consolidation-design.md",".codex/evidence/issue-449-code-consolidation-distribution.md"]
affected_modules: [existing lifecycle and selective setup paths]
affected_contracts: ["R449-06","R449-07","R449-08","R449-10","R449-35"]
dependencies: []
parallel_group: serialized-code-consolidation
file_locks: ["documentation/contracts/lifecycle.md","documentation/user_guide/product-upgrades.md","src/tiny_swarm_world/application/ports/lifecycle/product_upgrade.py","src/tiny_swarm_world/application/services/product_upgrade.py","src/tiny_swarm_world/domain/lifecycle/product_upgrade.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_admission.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_capture.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_source.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_configuration_validation.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_environment.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_installation.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_journal.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_migration.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_paths.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_runtime.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/product_verification.py","src/tiny_swarm_world/infrastructure/composition_product.py","tests/application/services/test_product_upgrade.py","tests/infrastructure/adapters/lifecycle/test_product_configuration_source.py","tests/infrastructure/adapters/lifecycle/test_product_upgrade.py","tests/tools/test_secure_runtime_paths.py","documentation/workflow/issues/issue-449/workflow.md","documentation/workflow/issues/issue-449/context-pack.md","documentation/workflow/issues/issue-449/context-pack.json","documentation/workflow/workflow.index.md",".codex/evidence/issue-449-code-consolidation-design.md",".codex/evidence/issue-449-code-consolidation-distribution.md"]
module_locks: [existing lifecycle and composition integration]
contract_locks: [code-only publication, issue remains INCOMPLETE, no live qualification claimed]
architecture_locks: [hexagonal architecture, existing consented flows, no new scoped capability]
quality_gates:
  targeted: ["PYTHONPATH=src python3 -m unittest tests.application.services.test_product_upgrade tests.infrastructure.adapters.lifecycle.test_product_configuration_source tests.infrastructure.adapters.lifecycle.test_product_upgrade tests.tools.test_secure_runtime_paths"]
  required: [final exact PC WSL integration quality, git diff --check, required CI and Sonar when configured]
documentation:
  arc42: verify existing ADR boundaries
  adr: no new architecture decision
stop_conditions: [unrelated change, sensitive artifact, changed architecture, failed required check, live success or issue completion falsely claimed]
```

### S449-C02 — Retain immutable component candidates with fail-closed update admission

```yaml
slice_id: S449-C02
profile: CODE_ONLY_CONSOLIDATION
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester]
affected_files: ["README.md","documentation/process/skills/audit/skill-registry.json","documentation/user_guide/component-updates.md","infra/config/compose/swagger/docker-compose.yml","src/tiny_swarm_world/application/services/component_execution.py","src/tiny_swarm_world/application/services/component_updates.py","src/tiny_swarm_world/domain/lifecycle/models.py","src/tiny_swarm_world/domain/lifecycle/update_planning.py","src/tiny_swarm_world/domain/update/classic_update.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/catalog.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/component_transitions.py","src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py","tests/application/services/test_component_updates.py","tests/architecture/test_legacy_surface_documentation.py","tests/domain/lifecycle/test_update_planning.py","tests/domain/update/test_classic_update.py","tests/infrastructure/adapters/lifecycle/test_catalog.py","tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py","tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py","tests/test_classic_update_cli.py"]
affected_modules: [existing lifecycle and selective setup paths]
affected_contracts: ["R449-04","R449-08","R449-10","R449-23","R449-24","R449-25","R449-26"]
dependencies: ["S449-C01"]
parallel_group: serialized-code-consolidation
file_locks: ["README.md","documentation/process/skills/audit/skill-registry.json","documentation/user_guide/component-updates.md","infra/config/compose/swagger/docker-compose.yml","src/tiny_swarm_world/application/services/component_execution.py","src/tiny_swarm_world/application/services/component_updates.py","src/tiny_swarm_world/domain/lifecycle/models.py","src/tiny_swarm_world/domain/lifecycle/update_planning.py","src/tiny_swarm_world/domain/update/classic_update.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/catalog.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/component_transitions.py","src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py","tests/application/services/test_component_updates.py","tests/architecture/test_legacy_surface_documentation.py","tests/domain/lifecycle/test_update_planning.py","tests/domain/update/test_classic_update.py","tests/infrastructure/adapters/lifecycle/test_catalog.py","tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py","tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py","tests/test_classic_update_cli.py"]
module_locks: [existing lifecycle and composition integration]
contract_locks: [code-only publication, issue remains INCOMPLETE, no live qualification claimed]
architecture_locks: [hexagonal architecture, existing consented flows, no new scoped capability]
quality_gates:
  targeted: ["PYTHONPATH=src python3 -m unittest tests.application.services.test_component_updates tests.domain.lifecycle.test_update_planning tests.infrastructure.adapters.lifecycle.test_catalog tests.infrastructure.adapters.lifecycle.test_native_component_transitions tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml tests.test_classic_update_cli"]
  required: [final exact PC WSL integration quality, git diff --check, required CI and Sonar when configured]
documentation:
  arc42: verify existing ADR boundaries
  adr: no new architecture decision
stop_conditions: [unrelated change, sensitive artifact, changed architecture, failed required check, live success or issue completion falsely claimed]
```

### S449-C03 — Repair existing selective setup runtime observations and cancellation

```yaml
slice_id: S449-C03
profile: CODE_ONLY_CONSOLIDATION
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester]
affected_files: ["documentation/user_guide/selective-setup.md","src/tiny_swarm_world/application/services/deployment/empty_apply.py","src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py","src/tiny_swarm_world/application/services/deployment/workflows.py","src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py","src/tiny_swarm_world/infrastructure/adapters/cli/selective_setup.py","src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/args.py","src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/diagnostics.py","src/tiny_swarm_world/infrastructure/adapters/clients/lxc_container_docker_runtime.py","src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_observations.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_state.py","src/tiny_swarm_world/infrastructure/composition.py","src/tiny_swarm_world/infrastructure/composition_cli.py","src/tiny_swarm_world/infrastructure/composition_deployment.py","src/tiny_swarm_world/infrastructure/composition_deployment_selection.py","src/tiny_swarm_world/infrastructure/composition_lifecycle.py","src/tiny_swarm_world/infrastructure/composition_runtime.py","src/tiny_swarm_world/infrastructure/composition_setup.py","tests/application/services/deployment/test_deployment_workflows.py","tests/application/services/deployment/test_ensure_portainer_endpoint.py","tests/application/services/deployment/test_ensure_swarm_stack.py","tests/e2e/classic/test_browser_evidence_paths.py","tests/infrastructure/adapters/clients/lxc/swarm/test_swarm_stack_runtime.py","tests/infrastructure/adapters/clients/test_lxc_container_docker_runtime.py","tests/infrastructure/adapters/clients/test_lxc_node_provider.py","tests/infrastructure/adapters/host/test_preflight_evidence_writer.py","tests/infrastructure/adapters/lifecycle/test_setup_state.py","tests/infrastructure/adapters/repositories/test_native_resource_budget.py","tests/infrastructure/test_composition.py","tests/infrastructure/test_selective_setup.py","tests/infrastructure/test_setup_status_cancellation.py","tests/test_incus_preparation.py","tests/test_package_entrypoint.py","tests/test_prepare_linux.py","tests/test_selective_setup_cli.py","tests/test_service_selection_cli.py","tests/test_simple_installer.py","tests/tools/test_r46_ports_policy.py"]
affected_modules: [existing lifecycle and selective setup paths]
affected_contracts: ["R449-02","R449-03","R449-09","R449-17","R449-19","R449-29","R449-30","R449-31","R449-36","R449-37","R449-38"]
dependencies: ["S449-C02"]
parallel_group: serialized-code-consolidation
file_locks: ["documentation/user_guide/selective-setup.md","src/tiny_swarm_world/application/services/deployment/empty_apply.py","src/tiny_swarm_world/application/services/deployment/ensure_portainer_endpoint.py","src/tiny_swarm_world/application/services/deployment/workflows.py","src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py","src/tiny_swarm_world/infrastructure/adapters/cli/selective_setup.py","src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/args.py","src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/diagnostics.py","src/tiny_swarm_world/infrastructure/adapters/clients/lxc_container_docker_runtime.py","src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_observations.py","src/tiny_swarm_world/infrastructure/adapters/lifecycle/setup_state.py","src/tiny_swarm_world/infrastructure/composition.py","src/tiny_swarm_world/infrastructure/composition_cli.py","src/tiny_swarm_world/infrastructure/composition_deployment.py","src/tiny_swarm_world/infrastructure/composition_deployment_selection.py","src/tiny_swarm_world/infrastructure/composition_lifecycle.py","src/tiny_swarm_world/infrastructure/composition_runtime.py","src/tiny_swarm_world/infrastructure/composition_setup.py","tests/application/services/deployment/test_deployment_workflows.py","tests/application/services/deployment/test_ensure_portainer_endpoint.py","tests/application/services/deployment/test_ensure_swarm_stack.py","tests/e2e/classic/test_browser_evidence_paths.py","tests/infrastructure/adapters/clients/lxc/swarm/test_swarm_stack_runtime.py","tests/infrastructure/adapters/clients/test_lxc_container_docker_runtime.py","tests/infrastructure/adapters/clients/test_lxc_node_provider.py","tests/infrastructure/adapters/host/test_preflight_evidence_writer.py","tests/infrastructure/adapters/lifecycle/test_setup_state.py","tests/infrastructure/adapters/repositories/test_native_resource_budget.py","tests/infrastructure/test_composition.py","tests/infrastructure/test_selective_setup.py","tests/infrastructure/test_setup_status_cancellation.py","tests/test_incus_preparation.py","tests/test_package_entrypoint.py","tests/test_prepare_linux.py","tests/test_selective_setup_cli.py","tests/test_service_selection_cli.py","tests/test_simple_installer.py","tests/tools/test_r46_ports_policy.py"]
module_locks: [existing lifecycle and composition integration]
contract_locks: [code-only publication, issue remains INCOMPLETE, no live qualification claimed]
architecture_locks: [hexagonal architecture, existing consented flows, no new scoped capability]
quality_gates:
  targeted: ["PYTHONPATH=src python3 -m unittest tests.infrastructure.test_selective_setup tests.infrastructure.test_setup_status_cancellation tests.infrastructure.adapters.lifecycle.test_setup_state tests.infrastructure.adapters.clients.test_lxc_node_provider tests.infrastructure.adapters.clients.test_lxc_container_docker_runtime tests.application.services.deployment.test_deployment_workflows"]
  required: [final exact PC WSL integration quality, git diff --check, required CI and Sonar when configured]
documentation:
  arc42: verify existing ADR boundaries
  adr: no new architecture decision
stop_conditions: [unrelated change, sensitive artifact, changed architecture, failed required check, live success or issue completion falsely claimed]
```

### S449-C04 — Publish historical qualification ledger and incomplete AC5 traceability

```yaml
slice_id: S449-C04
profile: CODE_ONLY_CONSOLIDATION
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester]
affected_files: ["documentation/evidence/lcm-w09-ac5-traceability.md","documentation/evidence/lcm-w09-blocker-refinement.md","documentation/evidence/lcm-w09-q16-wsl-r52.md","documentation/evidence/lcm-w09-q16-wsl-r54.md","documentation/evidence/lcm-w09-qualification.md","documentation/evidence/lcm-w09-transition-proposal.md",".codex/evidence/issue-449-code-consolidation.md"]
affected_modules: [existing lifecycle and selective setup paths]
affected_contracts: ["R449-01","R449-15","R449-18","R449-21","R449-22","R449-27"]
dependencies: ["S449-C03"]
parallel_group: serialized-code-consolidation
file_locks: ["documentation/evidence/lcm-w09-ac5-traceability.md","documentation/evidence/lcm-w09-blocker-refinement.md","documentation/evidence/lcm-w09-q16-wsl-r52.md","documentation/evidence/lcm-w09-q16-wsl-r54.md","documentation/evidence/lcm-w09-qualification.md","documentation/evidence/lcm-w09-transition-proposal.md",".codex/evidence/issue-449-code-consolidation.md"]
module_locks: [existing lifecycle and composition integration]
contract_locks: [code-only publication, issue remains INCOMPLETE, no live qualification claimed]
architecture_locks: [hexagonal architecture, existing consented flows, no new scoped capability]
quality_gates:
  targeted: ["git diff --check"]
  required: [final exact PC WSL integration quality, git diff --check, required CI and Sonar when configured]
documentation:
  arc42: verify existing ADR boundaries
  adr: no new architecture decision
stop_conditions: [unrelated change, sensitive artifact, changed architecture, failed required check, live success or issue completion falsely claimed]
```

## Historical execution-phase amendment v1.46 — F7 failure-stage diagnosis

The native F7 diagnostic on fd8dd1478329ee00a907822b4e43b19efc14a631 returned
BLOCKED_UNKNOWN / UNKNOWN, exit 2. No cause, inventory or host admission follows.
At authoring S449-02F8 was planned after F7; its subsequent implementation
and bounded native result are recorded in the v1.47 amendment. Private
evidence must be independently reviewed.
Sequence: F7 checkpoint and native result -> F8 same-hash review/S3D ->
implementation -> exact-source quality -> separately reviewed F8 host plan and
one diagnostic -> independent correction decision. S449-02F remains BLOCKED;
02G/02H retain successful-inventory prerequisites. Previous approvals do not
authorize F8.

## Execution-phase amendment v1.47 — F8 cgroup relation diagnosis

Native F8 source `7615a29962b0fd3ae2d44e4246893335ad9fadd3` returned
BLOCKED_UNKNOWN / PROCESS_BINDING, exit 2; this bounded observation is not
inventory or ownership admission. F9 is planned after F8; private F8 evidence
must be independently reviewed before F9 host execution. No namespace or
cause is inferred. See the F9 design and metadata for the closed relation
contract, separate reviews, gates and host phase. S449-02F remains BLOCKED.

## Execution-phase amendment v1.49 — End-to-end host admission proposal

`.codex/evidence/slice-449-02F11-host-admission-plan.md` records the Security decision NOT_FEASIBLE for strict endpoint binding in the current collector. A probe connection cannot bind later independent lxc connections; no host proof may execute under F11. It describes a proposed separately governed unit/process/endpoint proof and full inventory/host qualification route, scoped requirement traceability and independently reviewed alternative/parallel preparation. The proof extends prior read/socket boundaries and cannot be implemented or run until its concrete API/limits, safety model, file locks, six same-hash roles and S3D EXECUTION_PLAN are approved. No previous diagnostic, proposal or quality pass admits a host. Existing S449-02F/02G/02H and main graph dependencies remain unchanged; 02F stays BLOCKED. The uncommitted ADR proposal is not accepted by this amendment. User live-test consent remains valid; scenario JIT/GO and applicable host-operation scope remain mandatory.

## Historical execution-phase amendment v1.50 — accepted sequencing and G1 authoring

Historical authoring state follows; G1 was subsequently completed in commit `55c42029a7c1f0e7c219d1708060c4ed6b708dea`. Pending conditions and proposed wording in this v1.50 section describe the earlier state, not current status.

Status: D0 decision ACCEPTED on the independent six-role pre-acceptance review tuple recorded in `.codex/evidence/slice-449-adr-sequencing-review.md`; R67k supersedes R67h only for implementation sequencing. Existing live fixture, host and support dependencies remain binding. At authoring, G1 required its own contract refinement, independent same-hash reviews and S3D EXECUTION_PLAN. Existing F11 and 02F host blockers remain. The user-owned Windows ADR draft is outside this checkout and must not be overwritten. Architecture review identifies no existing new scoped-capability caller: the foundation below cannot claim to protect nonexistent call sites. Existing `lxc_node_provider.ensure_node` and fixed Classic configuration remain unchanged.

After decision acceptance, this proposed G1 may run while the separate listener fixture remains blocked. It only defines typed scoped intent and immutable empty version support; it does not wire a caller or claim runtime guard coverage. Every future G2/G3/G4 mutating caller must be separately planned and independently reviewed, use the typed scoped identity and enforce the capability decision before any external effect, and prove direct, recovery, cleanup and bypass cases. Until that integration is verified no new-capability host mutation, retry or cleanup is permitted. Legacy Classic remains separately supported. No external CI change or host admission follows.

### Proposed decision slice D0 — R67k and workflow review

D0 decision is complete: six independent role approvals on the pre-acceptance candidate tuple and accepted R67k are recorded in `.codex/evidence/slice-449-adr-sequencing-review.md`. Preserve the user-owned Windows ADR draft. At authoring, G1 required separate exact-source contract review and S3D EXECUTION_PLAN.

```yaml
slice_id: S449-ADR-SEQUENCE-D0
profile: GOVERNANCE_AND_DOCUMENTATION
owner: Senior Workflow Architect
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [documentation/arc42/09_decisions/adr-installation-scoped-incus-profile.adoc, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-adr-sequencing-workflow-proposal.md, .codex/evidence/slice-449-adr-sequencing-review.md, .codex/evidence/slice-449-capability-g1-contract.md]
affected_modules: [ADR history, issue-449 workflow]
affected_contracts: [R67h sequencing only, G1 design contract only, empty support, legacy Classic, unchanged host admission]
dependencies: [S449-01]
parallel_group: sequential
file_locks: [documentation/arc42/09_decisions/adr-installation-scoped-incus-profile.adoc, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-adr-sequencing-workflow-proposal.md, .codex/evidence/slice-449-adr-sequencing-review.md, .codex/evidence/slice-449-capability-g1-contract.md]
module_locks: [ADR history, issue-449 workflow graph]
contract_locks: [sequencing-only supersession, immutable empty capability support, unchanged legacy and host gates]
architecture_locks: [historical decisions preserved, no runtime effect]
quality_gates:
  targeted: [git diff --check, verify exact reviewed hashes and context artifact hashes]
  required: [independent same-hash Requirement Architecture Security Tester DevOps review, S3D EXECUTION_PLAN]
documentation:
  arc42: accepted R67k appended preserving history
  adr: R67k accepted on independent pre-acceptance review tuple
stop_conditions: [conflicting decision authority, user-owned ADR draft overwritten, missing reviews or S3D, unsafe graph change, changed live support]
```

### Proposed typed capability foundation G1

Traceability: R449-19 and R449-22, and parent #440 LCM-04/LCM-05; this narrow foundation alone does not satisfy those requirements. Normative proposed typed contract and test matrix: `.codex/evidence/slice-449-capability-g1-contract.md`, requiring independent same-hash review and S3D before implementation. Test typed scoped intent and version validation using an immutable, closed registry API with no external mutation: missing, malformed, unknown and `6.0.5` all deny; no operation can add support through this API. Exercise positive legacy Classic classification separately without granting new scoped support. Verify no imports or host calls and no change to legacy `ensure_node`; no caller or host protection is asserted.

```yaml
slice_id: S449-CAPABILITY-G1
profile: DOMAIN_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/domain/lifecycle/incus_capability.py, tests/domain/lifecycle/test_incus_capability.py, .codex/evidence/slice-449-capability-g1-contract.md, .codex/evidence/slice-449-capability-g1-distribution.md, .codex/evidence/slice-449-capability-g1-consolidation.md]
affected_modules: [domain lifecycle scoped capability]
affected_contracts: [strict typed IntentKind and G1-only ASCII version syntax, immutable closed empty registry, deny missing malformed unknown and 6.0.5, positive explicit legacy Classic classification, R449-19 and R449-22, LCM-04 and LCM-05]
dependencies: [S449-01, S449-ADR-SEQUENCE-D0]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/domain/lifecycle/incus_capability.py, tests/domain/lifecycle/test_incus_capability.py, .codex/evidence/slice-449-capability-g1-contract.md, .codex/evidence/slice-449-capability-g1-distribution.md, .codex/evidence/slice-449-capability-g1-consolidation.md]
module_locks: [domain lifecycle scoped capability]
contract_locks: [typed intent and capability identity, immutable empty support, legacy separation, no claimed caller protection]
architecture_locks: [domain independent of application and infrastructure, no runtime wiring or host effects]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_incus_capability, python3 -m ruff check src/tiny_swarm_world/domain/lifecycle/incus_capability.py tests/domain/lifecycle/test_incus_capability.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: accepted R67k required before implementation
  adr: no change in G1
stop_conditions: [R67k acceptance or approved workflow unverifiable, G1 contract not refined and independently reviewed, missing same-hash reviews or S3D, support set not empty, mutable or extensible support, malformed or ambiguous typed intent, domain dependency violation, legacy modification, external host effect, claimed caller protection]
```

All Python tests, Ruff and full quality run on the designated SSH PC WSL host against exact source. At authoring, G1 was pending its own contract refinement, reviews and S3D; this decision does not itself authorize editing product code or automatically change existing S449-03/04 dependencies. Before G2/G3/G4, author their exact file/module/contract/architecture locks, host-effect guard integrations and targeted negative regression matrices, then obtain six same-hash reviews and S3D separately. Fixture, separate support decision, host admission and both-host scenarios remain prerequisites for live new-capability use.

## Historical execution-phase amendment v1.51 — domain-only migration preview G2a

G2a was subsequently completed in `81acdd5c512820b3f69ca193c11d232cb6761ef6`; planned status and pre-execution conditions below describe the earlier authoring state.

Status: PLANNED; R67k sequencing accepted, D0 and G1 completed at baseline `55c42029a7c1f0e7c219d1708060c4ed6b708dea`. G2a is a strictly domain-only immutable `MigrationPreview` from validated v1 manifest and catalog; it is not a schema-v2 installation, runtime decoder change, adoption, host protection or live qualification. Normative behavior and tests: `.codex/evidence/slice-449-manifest-g2a-contract.md`. ADR defaults are policy only; actual project/profile/routes/owner identity remains UNKNOWN. Existing S449-03/04 and host/fixture dependencies remain in force for their original scopes. G2b/G2c require independently authored boundaries and gates.

```yaml
slice_id: S449-MANIFEST-G2A
profile: DOMAIN_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/domain/lifecycle/manifest_v2.py, tests/domain/lifecycle/test_manifest_v2.py, .codex/evidence/slice-449-manifest-g2a-contract.md, .codex/evidence/slice-449-manifest-g2a-distribution.md, .codex/evidence/slice-449-manifest-g2a-consolidation.md]
affected_modules: [domain lifecycle migration preview]
affected_contracts: [strict revalidated v1 and catalog with unique service/component IDs and canonical foundation kinds, immutable detached preview, selected stack swarm policy, selected Swagger stack published or not applicable, unknown host identity, unchanged v1 runtime]
dependencies: [S449-ADR-SEQUENCE-D0, S449-CAPABILITY-G1]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/domain/lifecycle/manifest_v2.py, tests/domain/lifecycle/test_manifest_v2.py, .codex/evidence/slice-449-manifest-g2a-contract.md, .codex/evidence/slice-449-manifest-g2a-distribution.md, .codex/evidence/slice-449-manifest-g2a-consolidation.md]
module_locks: [domain lifecycle manifest preview]
contract_locks: [v1 preservation, catalog uniqueness and selection, immutable unknown identities, no runtime schema acceptance]
architecture_locks: [domain-only, no I/O, no migration or adoption, no product runtime integration]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_manifest_v2 tests.domain.lifecycle.test_models, python3 -m ruff check src/tiny_swarm_world/domain/lifecycle/manifest_v2.py tests/domain/lifecycle/test_manifest_v2.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: follow accepted selection exposure and ownership ADR
  adr: no change
stop_conditions: [missing same-hash reviews or S3D, invalid or ambiguous v1 or catalog, unknown identities inferred, mutable shared state, changed v1 decoder, runtime integration, any host I/O, live support claim]
```

Six independent Requirement, Architecture, Security, Python, Tester and DevOps reviews of identical workflow/contract/source hashes and S3D EXECUTION_PLAN precede G2a edits. Exact source targeted/direct Ruff/full quality run on SSH PC WSL. G2a does not complete S449-03 or release existing fixture/host gates.

## Historical execution-phase amendment v1.52 — sanitized migration preview CLI G2b

G2b completed at `d2fbc06e6f1cfce51bce557499427c9d8c548c9d`; the following planned status describes earlier authoring.

Status PLANNED after G2a completion in `81acdd5c512820b3f69ca193c11d232cb6761ef6`. The early `services migration-preview` action loads only existing manifest/catalog ports and projects a closed safe DTO; no full v1 snapshot, credentials, host identity, paths, token or exception is exposed. It does not write, adopt, construct runtime services or prove schema-v2 support. Exact CLI/error/output semantics, tests and no-I/O boundary are specified by `.codex/evidence/slice-449-manifest-g2b-contract.md`. The existing generic lifecycle `inspect()` cannot supply this output. G2a is historical/completed; G2c and all host/fixture/version gates remain unchanged.

```yaml
slice_id: S449-MANIFEST-G2B
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/application/services/migration_preview.py, src/tiny_swarm_world/infrastructure/adapters/cli/migration_preview.py, src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py, src/tiny_swarm_world/infrastructure/adapters/cli/parser.py, src/tiny_swarm_world/infrastructure/adapters/cli/registry.py, src/tiny_swarm_world/infrastructure/composition_lifecycle.py, src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/catalog.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/preview_file_reader.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/preview_manifest.py, tests/infrastructure/adapters/lifecycle/test_catalog.py, tests/infrastructure/adapters/lifecycle/test_preview_file_reader.py, tests/infrastructure/adapters/lifecycle/test_preview_manifest.py, tests/application/services/test_migration_preview.py, tests/test_migration_preview_cli.py, tests/test_package_entrypoint.py, documentation/user_guide/selective-setup.md, .codex/evidence/slice-449-manifest-g2b-contract.md, .codex/evidence/slice-449-manifest-g2b-distribution.md, .codex/evidence/slice-449-manifest-g2b-consolidation.md]
affected_modules: [application migration preview, early CLI, local read-only composition, bounded preview FD readers]
affected_contracts: [manifest and catalog load only, strict safe DTO, fixed sanitized errors, no runtime construction, unchanged legacy CLI]
dependencies: [S449-MANIFEST-G2A]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/application/services/migration_preview.py, src/tiny_swarm_world/infrastructure/adapters/cli/migration_preview.py, src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py, src/tiny_swarm_world/infrastructure/adapters/cli/parser.py, src/tiny_swarm_world/infrastructure/adapters/cli/registry.py, src/tiny_swarm_world/infrastructure/composition_lifecycle.py, src/tiny_swarm_world/infrastructure/composition.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/catalog.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/preview_file_reader.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/preview_manifest.py, tests/infrastructure/adapters/lifecycle/test_catalog.py, tests/infrastructure/adapters/lifecycle/test_preview_file_reader.py, tests/infrastructure/adapters/lifecycle/test_preview_manifest.py, tests/application/services/test_migration_preview.py, tests/test_migration_preview_cli.py, tests/test_package_entrypoint.py, documentation/user_guide/selective-setup.md, .codex/evidence/slice-449-manifest-g2b-contract.md, .codex/evidence/slice-449-manifest-g2b-distribution.md, .codex/evidence/slice-449-manifest-g2b-consolidation.md]
module_locks: [lifecycle preview ports and CLI routing, shared NativeComponentCatalog, bounded preview FD reader, preview manifest repository]
contract_locks: [closed output whitelist and fixed stack-ID enum, operator-local unverified asset source, bounded no-follow FD asset handling without provenance or authority claim, no secret disclosure or argv reflection, reject flags before I/O, load only, legacy CLI parity]
architecture_locks: [application depends on ports, infrastructure composes local adapters, no host runtime or writes]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.test_migration_preview tests.infrastructure.adapters.lifecycle.test_catalog tests.infrastructure.adapters.lifecycle.test_preview_file_reader tests.infrastructure.adapters.lifecycle.test_preview_manifest tests.test_migration_preview_cli tests.test_service_selection_cli tests.test_package_entrypoint, python3 -m ruff check src/tiny_swarm_world/application/services/migration_preview.py src/tiny_swarm_world/infrastructure/adapters/cli/migration_preview.py src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py src/tiny_swarm_world/infrastructure/adapters/cli/parser.py src/tiny_swarm_world/infrastructure/adapters/cli/registry.py src/tiny_swarm_world/infrastructure/composition_lifecycle.py src/tiny_swarm_world/infrastructure/composition.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/catalog.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/preview_file_reader.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/preview_manifest.py tests/infrastructure/adapters/lifecycle/test_catalog.py tests/infrastructure/adapters/lifecycle/test_preview_file_reader.py tests/infrastructure/adapters/lifecycle/test_preview_manifest.py tests/application/services/test_migration_preview.py tests/test_migration_preview_cli.py tests/test_package_entrypoint.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  user_guide: document real command and non-adoption after implementation
  arc42: follow accepted selection exposure and ownership ADR
  adr: no change
stop_conditions: [missing same-hash reviews or S3D, unverified read-only loaders, disclosure, runtime construction, write or adoption, unsafe flags, changed legacy CLI, host operation]
```

Six independent Requirement, Architecture, Security, Python, Tester and DevOps reviews on identical workflow/contract/source hashes plus S3D EXECUTION_PLAN precede edits. SSH PC WSL targeted/direct Ruff/full quality uses exact source. No future G2c or live gate is discharged.

## Execution-phase amendment v1.53 — G2b operator-local unverified source

G2b is a bounded read-only operator preview. Every success and blocked output includes `source=operator_local_unverified`; `applied` and `qualified` remain false and host identities UNKNOWN. Local asset validity and no-write behavior must be checked, but their provenance, catalog authority, release identity, host safety and live admission are not established. No unverified asset or output can discharge a live or EPIC gate. Asset drift, missing/malformed/inconsistent files, symlink and permission failures follow the fixed fail-closed contract and reveal no sensitive content. The exact revised contract requires independent same-hash reviews and new S3D before code. Legacy CLI/parser regression remains mandatory.

## Execution-phase amendment v1.54 — bounded preview-only local asset reader

G2b uses an unverified operator-selected root pinned once and fixed relative no-follow FD traversal. Manifest `.tiny-swarm-world/installation/manifest.json` and each fixed Compose file are capped at 1 MiB; aggregate 16 MiB and 16 files. The current service-access catalog has nine Compose files, plus one manifest. Compose assets are read only under the selected local project root; `TSW_INFRA_ROOT` is not evaluated or represented, missing project-root assets block, and explicit alternate-infrastructure requests are rejected before loading. `NativeComponentCatalog` accepts a preview-only injected text reader while preserving the default legacy behavior; `PreviewManifestRepository` uses existing `decode_manifest` and rejects save. The contract explicitly excludes provenance, hostile privileged/hardlink/ABA guarantees and hard CPU deadline claims. New reader/catalog/test file locks are included in G2b; one serial implementation owner, six same-hash reviews and fresh S3D precede changes. No host admission or release follows.

## Execution-phase amendment v1.55 — G2b workflow-list regression scope

G2b may update only the fixed expected workflow list in `tests/test_package_entrypoint.py::test_every_declared_workflow_keeps_its_command_name` to include `services migration-preview`. Existing expectations and all other legacy CLI tests remain intact. Targeted execution reported one failure in this existing list assertion after adding the command; this amendment adds its file lock and does not claim that a revised test or full gate has passed. All other G2b and host safety gates remain unchanged.

## Execution-phase amendment v1.56 — strict domain schema and conversion plan G2c

Historical v1.56 G2c authoring had AUTHORITY_GAP and is superseded by v1.61 below; P0 has since completed. No former caller-supplied project/profile/routes contract is executable.

```yaml
slice_id: S449-MANIFEST-G2C
profile: DOMAIN_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/domain/lifecycle/desired_manifest_v2.py, tests/domain/lifecycle/test_desired_manifest_v2.py, .codex/evidence/slice-449-manifest-g2c-contract.md, .codex/evidence/slice-449-manifest-g2c-distribution.md, .codex/evidence/slice-449-manifest-g2c-consolidation.md]
affected_modules: [unadopted desired manifest and pure conversion]
affected_contracts: [strict unadopted desired v2 value, canonical v1 preservation, internal P0 recomputation, UNKNOWN host/source, no adoption]
dependencies: [S449-CAPABILITY-G1, S449-MANIFEST-G2A, S449-MANIFEST-G2B, S449-ROUTE-POLICY-P0]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/domain/lifecycle/desired_manifest_v2.py, tests/domain/lifecycle/test_desired_manifest_v2.py, .codex/evidence/slice-449-manifest-g2c-contract.md, .codex/evidence/slice-449-manifest-g2c-distribution.md, .codex/evidence/slice-449-manifest-g2c-consolidation.md]
module_locks: [desired manifest and P0 contract]
contract_locks: [schema1 invariants and values, internally recomputed P0, immutable desired output and unknown actual identities]
architecture_locks: [domain only, no I/O, no runtime decoder or persistence, no host mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_desired_manifest_v2 tests.domain.lifecycle.test_manifest_v2 tests.domain.lifecycle.test_scoped_route_policy tests.domain.lifecycle.test_models tests.infrastructure.adapters.lifecycle.test_manifest tests.test_migration_preview_cli, python3 -m ruff check src/tiny_swarm_world/domain/lifecycle/desired_manifest_v2.py tests/domain/lifecycle/test_desired_manifest_v2.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: follow accepted Classic selection exposure ownership and profile ADRs
  adr: no change
stop_conditions: [missing same-hash reviews or S3D, P0 authority gap bypassed, schema1 regression, shared mutable state, actual UNKNOWN identity claimed, host ownership inferred, runtime decoder or host operation]
```

The prior NO-GO and P0 authority gap were historical. P0 subsequently completed at `5e9f87c6b1dc1173b8d0a4609037d477eb0f5cca`; runtime-source, 8086 and internal-ingress gaps remain. Current G2c requires the new desired-only contract, fresh six-role reviews and S3D before edits; targeted/full quality runs on SSH PC WSL.

## Historical execution-phase amendment v1.57 — route authority before G2c

The following is the earlier blocked authoring state; P0 subsequently completed in `5e9f87c6b1dc1173b8d0a4609037d477eb0f5cca`, while actual source/host gaps remain.

G2c remains BLOCKED / AUTHORITY_GAP and not done. A separately governed `S449-ROUTE-POLICY-P0` must establish a versioned typed selection/port snapshot with explicit provenance and deterministic complete route policy, including mandatory Portainer TCP/10001, nat and proxy_protocol. Inventory existing service-stack port IDs, PortRegistry, SetupManifest, ports configuration and accepted ADRs; missing authoritative values remain UNKNOWN/BLOCKED. Profile naming requires its own reviewed proposed ADR decision, not a guessed suffix. No product implementation or live outcome is implied.

### P0 candidate decision inputs (not accepted)

The G2c contract records a source-backed `RoutePolicyInputV1` candidate, exact unresolved binding inputs and a proposed versioned SHA-256/UUID profile-name decision. Current PortRegistry maps Portainer 9000 internal / 10001 external, while the legacy proxy target is `127.0.0.1:10001`; SetupManifest/preflight does not establish complete routes. Nexus 13501 maps to `nexus-docker-https` (internal 5001) and published Swagger IDs map to 16080/16081, suppressed for internal exposure. A caller-set REVIEWED_POLICY enum is not authority; a versioned immutable built-in policy or separately reviewed trust binding is required. Listen addresses and nat/proxy_protocol false remain proposals requiring explicit decisions. Missing reviewed bindings remain AUTHORITY_GAP; no two caller lists or operator-local unverified assets prove completeness. P0 and G2c remain BLOCKED pending independent decisions, concrete slice metadata/reviews and S3D.

## Historical execution-phase amendment v1.58 — legacy published route candidate P0a

P0a subsequently completed at `f5f0ea1520a1abdb6ee281bb700c8635c9ad4e93`; the planned status and requirements below describe the authoring state.

P0a is PLANNED as an independently reviewable pure legacy-code candidate, not the still-blocked authoritative scoped P0 and not a G2c unblock. It uses all `default_setup_manifest` required ports, including compatibility ports, and returns `legacy_setup_code_unverified_runtime`, UNKNOWN nat/proxy_protocol, false applied/qualified and unknown identities. It does not infer internal Swagger, alternative infrastructure overrides, profile ownership or host state. Source conflict, exact contract and tests: `.codex/evidence/slice-449-route-p0a-contract.md`. The separate scoped profile-name decision and actual route authority remain pending.

```yaml
slice_id: S449-ROUTE-POLICY-P0A
profile: DOMAIN_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/domain/lifecycle/legacy_route_candidate.py, tests/domain/lifecycle/test_legacy_route_candidate.py, .codex/evidence/slice-449-route-p0a-contract.md, .codex/evidence/slice-449-route-p0a-distribution.md, .codex/evidence/slice-449-route-p0a-consolidation.md]
affected_modules: [domain-only legacy route candidate]
affected_contracts: [validated explicit selection and preset, all legacy setup required ports, unverified-runtime marker, unknown flags and identities, no host authority]
dependencies: [S449-CAPABILITY-G1, S449-MANIFEST-G2A, S449-MANIFEST-G2B]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/domain/lifecycle/legacy_route_candidate.py, tests/domain/lifecycle/test_legacy_route_candidate.py, .codex/evidence/slice-449-route-p0a-contract.md, .codex/evidence/slice-449-route-p0a-distribution.md, .codex/evidence/slice-449-route-p0a-consolidation.md]
module_locks: [domain legacy route candidate]
contract_locks: [all required ports including compatibility, explicit stock applicability, published only, unknown flags and host identity]
architecture_locks: [domain only, no I/O, no runtime wiring, no authoritative scoped policy]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_legacy_route_candidate tests.domain.lifecycle.test_manifest_v2 tests.application.services.platform.test_lxc_service_exposure, python3 -m ruff check src/tiny_swarm_world/domain/lifecycle/legacy_route_candidate.py tests/domain/lifecycle/test_legacy_route_candidate.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: existing ADR unchanged; candidate is unverified runtime
  adr: no change; scoped profile-name decision remains separate
stop_conditions: [missing same-hash reviews or S3D, unknown stock applicability, inferred internal exposure or flags, missing 10001 or 7750, domain I/O, host ownership claim, G2c authority claim]
```

Six independent Requirement, Architecture, Security, Python, Tester and DevOps reviews of identical workflow/contract/source hashes plus S3D EXECUTION_PLAN precede code. Exact-source tests and quality run on SSH PC WSL. P0a completion cannot unblock G2c without a separate accepted scoped authority decision.

## Historical execution-phase amendment v1.59 — accepted scoped route/profile design ADR D0

P0 subsequently completed in `5e9f87c6b1dc1173b8d0a4609037d477eb0f5cca`; earlier implementation-pending text below is historical.

`documentation/arc42/09_decisions/adr-scoped-route-policy-profile-identity.adoc` records ACCEPTED design policy on code-bound scoped-route-policy-v1 and UUID-byte/SHA-256 profile-name-v1; no existing ADR history or Windows user draft is modified. The candidate requires total-or-reject selection/preset semantics, explicit fixed proxy flags/listen address, published/internal Swagger behavior and empty supported-version set. The 8086 source conflict between SetupManifest Infisical and ports.yaml service-access is AUTHORITY_GAP for affected selections pending a separate decision. No actual host ownership, route, runtime version, live fixture or admission is claimed. Six independent Requirement, Architecture, Security, Python, Tester and DevOps roles approved the same pre-acceptance candidate tuple recorded in the decision evidence. Final checkpoint re-review and S3D remain required; the 8086 authority gap remains unresolved. P0a completed at `f5f0ea1520a1abdb6ee281bb700c8635c9ad4e93` but is unverified; P0/G2c remain BLOCKED until a separate accepted decision and reviewed implementation.

```yaml
slice_id: S449-SCOPED-ROUTE-ADR-D0
profile: GOVERNANCE_AND_DOCUMENTATION
owner: Senior Workflow Architect
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Python Automation Developer, Senior Tester, Senior DevOps Engineer]
affected_files: [documentation/arc42/09_decisions/adr-scoped-route-policy-profile-identity.adoc, documentation/arc42/09_architecture_decisions.adoc, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-scoped-route-decision.md]
affected_modules: [scoped route policy decision, profile identity decision, issue-449 workflow]
affected_contracts: [code-bound versioned selection route policy, strict explicit route flags, versioned UUID profile identity, no host claims]
dependencies: [S449-ROUTE-POLICY-P0A]
parallel_group: sequential
file_locks: [documentation/arc42/09_decisions/adr-scoped-route-policy-profile-identity.adoc, documentation/arc42/09_architecture_decisions.adoc, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-scoped-route-decision.md]
module_locks: [scoped route policy ADR, profile identity ADR, issue-449 workflow]
contract_locks: [immutable policy authority, selection and exposure, profile naming, existing host and support gates]
architecture_locks: [domain policy only, no host operations, preserve ADR history]
quality_gates:
  targeted: [git diff --check, verify ADR workflow and context hashes, verify reviewed source mapping]
  required: [independent six-role same-hash decision review, S3D EXECUTION_PLAN]
documentation:
  arc42: separate accepted design decision with historical candidate retained
  adr: accepted design policy; final checkpoint review and S3D pending
stop_conditions: [unresolved authority or policy choice, missing review or S3D, unsupported route inferred, changed existing ADR or user draft, host mutation or support claim]
```

A later separately authored pure-domain policy slice needs exact product/test file locks, its own tests and SSH PC WSL full quality. G2c depends on an accepted decision and completed policy, not this draft.

## Historical execution-phase amendment v1.60 — scoped route policy P0

P0 completed in `5e9f87c6b1dc1173b8d0a4609037d477eb0f5cca`; planned status below is historical.

Status PLANNED; accepted scoped route/profile ADR checkpoint `4886c84c92d7cb9ac628fe75e7a973829f36d713`. P0 introduces only code-bound immutable pure domain policy and deterministic profile identity, with explicit AUTHORITY_GAP for 8086-affected selections, default preset with Traefik and selected internal Swagger absent trustworthy shared-ingress proof. Detailed contract `.codex/evidence/slice-449-scoped-route-p0-contract.md`. It produces only an ideal code-policy reference with runtime_source=UNKNOWN; it cannot inspect environment or claim effective source/override applicability. A future separately reviewed pre-effect adapter must verify effective sources and block unknown. No public source self-attestation, host I/O, v1 runtime behavior change, ownership, capability support or live claim. G2c remains BLOCKED pending actual P0 completion and review.

```yaml
slice_id: S449-ROUTE-POLICY-P0
profile: DOMAIN_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/domain/lifecycle/scoped_route_policy.py, tests/domain/lifecycle/test_scoped_route_policy.py, .codex/evidence/slice-449-scoped-route-p0-contract.md, .codex/evidence/slice-449-scoped-route-p0-distribution.md, .codex/evidence/slice-449-scoped-route-p0-consolidation.md]
affected_modules: [code-bound scoped route policy and profile identity]
affected_contracts: [immutable code-policy reference and pure tuple drift check, runtime_source UNKNOWN, explicit profile-name-v1, no caller authority, 8086 gap, no observed host claims]
dependencies: [S449-SCOPED-ROUTE-ADR-D0, S449-ROUTE-POLICY-P0A]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/domain/lifecycle/scoped_route_policy.py, tests/domain/lifecycle/test_scoped_route_policy.py, .codex/evidence/slice-449-scoped-route-p0-contract.md, .codex/evidence/slice-449-scoped-route-p0-distribution.md, .codex/evidence/slice-449-scoped-route-p0-consolidation.md]
module_locks: [scoped route policy and profile identity]
contract_locks: [immutable ideal code policy, runtime_source UNKNOWN, explicit selection and listen, 8086 and internal ingress gap, UUID version, unchanged legacy]
architecture_locks: [domain only, no I/O or runtime integration, no source self-attestation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_scoped_route_policy tests.domain.lifecycle.test_legacy_route_candidate tests.domain.lifecycle.test_manifest_v2 tests.domain.lifecycle.test_models, python3 -m ruff check src/tiny_swarm_world/domain/lifecycle/scoped_route_policy.py tests/domain/lifecycle/test_scoped_route_policy.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: follow accepted scoped route profile ADR
  adr: no change
stop_conditions: [missing six reviews or S3D, source drift, fabricated source trust, 8086 or ingress ambiguity, unsupported selection, mutable policy, runtime or host effect, UUID or legacy regression]
```

Six independent Requirement, Architecture, Security, Python, Tester and DevOps reviews on identical workflow/contract/source hashes and S3D EXECUTION_PLAN precede changes. Targeted/direct Ruff/full quality run on designated SSH PC WSL with exact source. Existing host/fixture/version gates remain in force.

## Historical execution-phase amendment v1.61 — unadopted desired manifest G2c

G2c subsequently completed in `f45ca0b8ee3d3593eb02cd7f7a78e8a528440924`; planned status below describes the earlier state.

Status PLANNED after completed P0 `5e9f87c6b1dc1173b8d0a4609037d477eb0f5cca`; exact current contract `.codex/evidence/slice-449-manifest-g2c-contract.md` supersedes earlier caller-supplied binding text. G2c creates only immutable desired-state conversion and internally recomputes P0; actual host, source and owner stay UNKNOWN and applied/qualified false. No schema-v2 persistence, runtime decoder, CLI, adoption, host or capability support is changed. Six independent role reviews and S3D are pending; current P0 8086/internal gaps remain.

## Historical execution-phase amendment v1.62 — fail-closed migration admission G2d

G2d subsequently completed in `ef1e863b755faa3f8127a364b7926244abc35329`; planned status below is historical.

G2c completed at `f45ca0b8ee3d3593eb02cd7f7a78e8a528440924`. G2d is PLANNED as an internal application preparation step that loads V1/catalog, computes desired plan and returns only `BLOCKED_UNKNOWN` or `BLOCKED_UNSUPPORTED`, with scoped G1 classification concrete and non-injectable. The currently unconnected service does not affect existing operator paths; immediately following G2e must provide a separately reviewed CLI/composition/operator guide entrypoint. Snapshot token None, empty or non-string blocks; only a valid nonempty string reaches further checks. All valid scoped versions remain unsupported; there is no admission-positive branch, host/source/lock/checkpoint/writer call, CLI/runtime wiring, persistence or host access. Contract `.codex/evidence/slice-449-migration-g2d-contract.md` defines order and boundaries. Existing G2c/G2b/legacy and host/fixture/version gates stay unchanged.

```yaml
slice_id: S449-MIGRATION-G2D
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/application/ports/lifecycle/migration_admission.py, src/tiny_swarm_world/application/services/migration_admission.py, tests/application/services/test_migration_admission.py, .codex/evidence/slice-449-migration-g2d-contract.md, .codex/evidence/slice-449-migration-g2d-distribution.md, .codex/evidence/slice-449-migration-g2d-consolidation.md]
affected_modules: [application migration admission and typed future port boundary]
affected_contracts: [read-only v1 and catalog load, G2c desired plan, concrete fail-closed scoped capability, no positive admission or effects]
dependencies: [S449-CAPABILITY-G1, S449-MANIFEST-G2A, S449-MANIFEST-G2B, S449-ROUTE-POLICY-P0, S449-MANIFEST-G2C]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/application/ports/lifecycle/migration_admission.py, src/tiny_swarm_world/application/services/migration_admission.py, tests/application/services/test_migration_admission.py, .codex/evidence/slice-449-migration-g2d-contract.md, .codex/evidence/slice-449-migration-g2d-distribution.md, .codex/evidence/slice-449-migration-g2d-consolidation.md]
module_locks: [application migration admission, future typed migration boundaries]
contract_locks: [concrete scoped capability check, fixed blocked results, load only, no host or write, v1 and legacy parity]
architecture_locks: [application uses domain and ports, no infrastructure, no runtime wiring, no positive admission]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.test_migration_admission tests.domain.lifecycle.test_desired_manifest_v2 tests.domain.lifecycle.test_scoped_route_policy tests.test_migration_preview_cli tests.infrastructure.adapters.lifecycle.test_manifest, python3 -m ruff check src/tiny_swarm_world/application/ports/lifecycle/migration_admission.py src/tiny_swarm_world/application/services/migration_admission.py tests/application/services/test_migration_admission.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: follow accepted Classic selection and profile decisions
  adr: no change
stop_conditions: [missing role review or S3D, positive admission path, spoofable scoped capability, host or write call, runtime wiring, v1 or legacy regression, sensitive disclosure]
```

Six independent Requirement, Architecture, Security, Python, Tester and DevOps reviews on identical workflow/contract/source hashes and S3D EXECUTION_PLAN precede edits. Tests and full quality run on designated SSH PC WSL with exact bytes. Host admission and version-support decision remain separate and unresolved.

### Required next slice S449-MIGRATION-G2E — operator entrypoint

Immediately after G2d, author concrete G2e metadata with dependency `S449-MIGRATION-G2D` and execute it under independent review/S3D. Scope is early safe CLI plus read-only composition, no live runtime or host construction, fixed sanitized blocked status/exit behavior, `documentation/` operator guide and CLI/parser/composition regression tests. Until G2e exists, G2d is internal and does not alter existing commands. G2e does not itself authorize mutation, persistence or positive admission.

## Historical execution-phase amendment v1.63 — operator migration-check G2e

G2e completed at `b9f2543f3fea21fd7565a6f6bf02c72e6dc8f448`; planned status below is historical.

G2e is PLANNED after G2d commit `ef1e863b755faa3f8127a364b7926244abc35329`. It adds only a dedicated early `services migration-check` entry to expose G2d fixed blocked results using bounded local readers. Candidate version is operator supplied, never a host measurement; output is sanitized and unverified, no runtime/host mutation or admission. Exact grammar, result and no-write contract: `.codex/evidence/slice-449-migration-g2e-contract.md`.

```yaml
slice_id: S449-MIGRATION-G2E
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/cli/migration_admission.py, src/tiny_swarm_world/infrastructure/adapters/cli/parser.py, src/tiny_swarm_world/infrastructure/adapters/cli/registry.py, src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py, src/tiny_swarm_world/infrastructure/composition_lifecycle.py, src/tiny_swarm_world/infrastructure/composition.py, tests/test_migration_admission_cli.py, tests/test_package_entrypoint.py, documentation/user_guide/selective-setup.md, .codex/evidence/slice-449-migration-g2e-contract.md, .codex/evidence/slice-449-migration-g2e-distribution.md, .codex/evidence/slice-449-migration-g2e-consolidation.md]
affected_modules: [migration admission CLI, local read-only composition]
affected_contracts: [strict action grammar, fixed non-admitting JSON, bounded load only, no version detection, legacy CLI parity]
dependencies: [S449-MIGRATION-G2D]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/infrastructure/adapters/cli/migration_admission.py, src/tiny_swarm_world/infrastructure/adapters/cli/parser.py, src/tiny_swarm_world/infrastructure/adapters/cli/registry.py, src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py, src/tiny_swarm_world/infrastructure/composition_lifecycle.py, src/tiny_swarm_world/infrastructure/composition.py, tests/test_migration_admission_cli.py, tests/test_package_entrypoint.py, documentation/user_guide/selective-setup.md, .codex/evidence/slice-449-migration-g2e-contract.md, .codex/evidence/slice-449-migration-g2e-distribution.md, .codex/evidence/slice-449-migration-g2e-consolidation.md]
module_locks: [migration CLI parser routing, bounded preview composition]
contract_locks: [fixed safe output, early argument rejection, no host observation, legacy CLI behavior]
architecture_locks: [infrastructure composes application ports, no runtime initialization or mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.test_migration_admission_cli tests.test_migration_preview_cli tests.test_package_entrypoint tests.application.services.test_migration_admission tests.infrastructure.adapters.lifecycle.test_preview_file_reader tests.infrastructure.adapters.lifecycle.test_preview_manifest tests.infrastructure.adapters.lifecycle.test_catalog, python3 -m ruff check src/tiny_swarm_world/infrastructure/adapters/cli/migration_admission.py src/tiny_swarm_world/infrastructure/adapters/cli/parser.py src/tiny_swarm_world/infrastructure/adapters/cli/registry.py src/tiny_swarm_world/infrastructure/adapters/cli/dispatcher.py src/tiny_swarm_world/infrastructure/composition_lifecycle.py src/tiny_swarm_world/infrastructure/composition.py tests/test_migration_admission_cli.py tests/test_package_entrypoint.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  user_guide: document real command and unverified non-admitting meaning
  arc42: no change
  adr: no change
stop_conditions: [missing role reviews or S3D, argument leak or legacy regression, unbounded reader or writes, host runtime, positive admission, unsupported capability, sensitive disclosure]
```

Six Requirement, Architecture, Security, Python, Tester and DevOps same-hash reviews and S3D EXECUTION_PLAN precede edits. Tests and full quality run on designated SSH PC WSL using exact source.

### G2e narrow registry-loop test amendment

Within the already locked `tests/test_package_entrypoint.py`, the existing registry loop may append valid `--version`, `--exposure` and `--listen-address` arguments only for `services migration-check`, in addition to its workflow-list entry. Preserve all existing registry/workflow assertions and all other entries; no skip. A separate negative CLI test must prove missing options return fixed blocked JSON/exit 2 before repository load. This changes test scope only and does not relax the required CLI grammar. Fresh review and S3D apply to this amendment.

## Execution-phase amendment v1.64 — proposed 8086 scoped authority decision

The scoped route/profile ADR contains an ACCEPTED desired-policy-only 8086 amendment, with source evidence in `.codex/evidence/slice-449-route-8086-decision.md`. It distinguishes service-access route owner and Infisical backend, requires full dependency closure for 8086 and preserves Infisical-only 17080. Exact legacy tuples must be validated before a narrowly versioned transformation; other drift blocks. Existing code retains 8086 AUTHORITY_GAP until separately reviewed pure-domain implementation and quality pass. No current runtime, source, host, version or live route claim follows.

```yaml
slice_id: S449-ROUTE-8086-ADR-D0
profile: GOVERNANCE_AND_DOCUMENTATION
owner: Senior Workflow Architect
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Python Automation Developer, Senior Tester, Senior DevOps Engineer]
affected_files: [documentation/arc42/09_decisions/adr-scoped-route-policy-profile-identity.adoc, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-route-8086-decision.md]
affected_modules: [scoped route authority decision, issue-449 workflow]
affected_contracts: [8086 selection ownership and backend, exact legacy source drift before versioned transformation, unchanged legacy and host gates]
dependencies: [S449-SCOPED-ROUTE-ADR-D0, S449-ROUTE-POLICY-P0, S449-MIGRATION-G2E]
parallel_group: sequential
file_locks: [documentation/arc42/09_decisions/adr-scoped-route-policy-profile-identity.adoc, documentation/workflow/issues/issue-449/workflow.md, documentation/workflow/issues/issue-449/context-pack.md, documentation/workflow/issues/issue-449/context-pack.json, documentation/workflow/workflow.index.md, .codex/evidence/slice-449-route-8086-decision.md]
module_locks: [scoped route ADR, issue-449 workflow]
contract_locks: [8086 owner and backend, versioned source transformation, no host admission]
architecture_locks: [preserve legacy behavior and accepted ADR history, no runtime effects]
quality_gates:
  targeted: [git diff --check, verify source evidence and review hashes]
  required: [independent six-role same-hash decision review, S3D EXECUTION_PLAN]
documentation:
  arc42: append accepted desired-policy amendment retaining historical decisions
  adr: accepted desired policy only; runtime implementation remains separate
stop_conditions: [ambiguous source or selection closure, lost historical authority, missing reviews or S3D, claimed live or support outcome, host operation]
```

After independent decision acceptance, author a separate serial scoped-domain slice limited initially to `src/tiny_swarm_world/domain/lifecycle/scoped_route_policy.py` and its tests. Tests must prove Infisical-only 17080/no8086, full service-access closure 10000/8086/17080 exactly once, invalid dependency closure, exact legacy source validation before transformation, unrelated drift blocking, no changed legacy candidate/setup, and no host I/O. Its exact locks, versioned identity, six-role reviews, S3D and SSH PC WSL targeted/full quality are separate. G2c/G2e and host gates are not discharged by this proposal.

### D0 decision accepted — implementation still pending

S3/S3D EXECUTION_PLAN was reported for the clean base `ff9995913518fe7d268a64e367ef85b551794731` and six independent proposal reviews. The 8086 ADR decision is accepted as future desired policy; current scoped code continues to block until the separately reviewed implementation, exact-source quality and downstream G2c/G2d/G2e regressions pass. No legacy or host behavior changed.

## Historical execution-phase amendment v1.65 — coupled scoped 8086 implementation P1

P1 subsequently completed at `eacbdc418b6b7179e69441b718f7226609f96470`; planned status below is historical.

Status PLANNED after accepted D0 `90b5665e7fe01f198e78c5d4a130c3b5babcb6ac`. P1 implements only versioned pure scoped desired-policy transformation, validating the exact ordered historic SetupManifest tuple sequence before narrowly reclassifying/removing 8086; G2c and G2d exact policy/version consumers are updated together and G2e fixed blocked output regressed. Normative contract `.codex/evidence/slice-449-route-8086-p1-contract.md`. Legacy runtime/P0a, actual host identities, source UNKNOWN, empty capability support, fixture and live gates remain unchanged.

```yaml
slice_id: S449-ROUTE-8086-P1
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/domain/lifecycle/scoped_route_policy.py, src/tiny_swarm_world/domain/lifecycle/desired_manifest_v2.py, src/tiny_swarm_world/application/services/migration_admission.py, tests/domain/lifecycle/test_scoped_route_policy.py, tests/domain/lifecycle/test_desired_manifest_v2.py, tests/application/services/test_migration_admission.py, tests/test_migration_admission_cli.py, .codex/evidence/slice-449-route-8086-p1-contract.md, .codex/evidence/slice-449-route-8086-p1-distribution.md, .codex/evidence/slice-449-route-8086-p1-consolidation.md]
affected_modules: [scoped policy, desired v2 conversion, migration admission]
affected_contracts: [exact ordered legacy tuple sequence before 8086 transform, scoped policy v2 identity, exact coupled consumers, fail-closed capability, unchanged legacy runtime]
dependencies: [S449-ROUTE-8086-ADR-D0, S449-ROUTE-POLICY-P0, S449-MANIFEST-G2C, S449-MIGRATION-G2D, S449-MIGRATION-G2E]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/domain/lifecycle/scoped_route_policy.py, src/tiny_swarm_world/domain/lifecycle/desired_manifest_v2.py, src/tiny_swarm_world/application/services/migration_admission.py, tests/domain/lifecycle/test_scoped_route_policy.py, tests/domain/lifecycle/test_desired_manifest_v2.py, tests/application/services/test_migration_admission.py, tests/test_migration_admission_cli.py, .codex/evidence/slice-449-route-8086-p1-contract.md, .codex/evidence/slice-449-route-8086-p1-distribution.md, .codex/evidence/slice-449-route-8086-p1-consolidation.md]
module_locks: [scoped route policy, desired conversion, migration admission]
contract_locks: [exact legacy source sequence validation including reorder drift, 8086 versioned transformation, strict consumer version and exact tuples, blocked scoped capability]
architecture_locks: [domain and application boundaries, no runtime integration or host effects, no invented source authority]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_scoped_route_policy tests.domain.lifecycle.test_desired_manifest_v2 tests.domain.lifecycle.test_legacy_route_candidate tests.application.services.test_migration_admission tests.test_migration_admission_cli tests.test_migration_preview_cli, python3 -m ruff check src/tiny_swarm_world/domain/lifecycle/scoped_route_policy.py src/tiny_swarm_world/domain/lifecycle/desired_manifest_v2.py src/tiny_swarm_world/application/services/migration_admission.py tests/domain/lifecycle/test_scoped_route_policy.py tests/domain/lifecycle/test_desired_manifest_v2.py tests/application/services/test_migration_admission.py tests/test_migration_admission_cli.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: follow accepted scoped 8086 amendment
  adr: no change
stop_conditions: [missing same-hash reviews or S3D, accepted decision mismatch, legacy source drift, version/consumer mismatch, unguarded capability, legacy/runtime regression, host or file I/O]
```

One serial worker and six independent Requirement, Architecture, Security, Python, Tester and DevOps same-hash reviews plus S3D EXECUTION_PLAN precede edits. Targeted/direct Ruff/full QUALITY run on designated SSH PC WSL with exact source; this slice proves no live success.

## Execution-phase amendment v1.66 — versioned manifest record and isolated CAS

S449-MANIFEST-V2-REPOSITORY is PLANNED after P1 `eacbdc418b6b7179e69441b718f7226609f96470`. It proposes a strict typed UNADOPTED v2 draft at fixed noncanonical `.tiny-swarm-world/staging/manifest-v2-draft.json` and dedicated dual-read/isolated CAS port and adapter, not a runtime or canonical-manifest migration. ADR does not define exact wire/provenance shape; reported ADR-owner GO covers the prior isolated UNADOPTED-draft candidate only. The revised contract `.codex/evidence/slice-449-manifest-v2-repository-contract.md` still needs fresh independent same-hash role review/S3D; versioned migration is required before later production use. V1 decoder/consumers remain unchanged and fail closed for v2; no host/support/adoption is claimed.

```yaml
slice_id: S449-MANIFEST-V2-REPOSITORY
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/domain/lifecycle/manifest_v2_record.py, src/tiny_swarm_world/application/ports/lifecycle/versioned_manifest.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_repository.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_json.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_fs.py, tests/domain/lifecycle/test_manifest_v2_record.py, tests/infrastructure/adapters/lifecycle/test_versioned_manifest_repository.py, .codex/evidence/slice-449-manifest-v2-repository-contract.md, .codex/evidence/slice-449-manifest-v2-repository-distribution.md, .codex/evidence/slice-449-manifest-v2-repository-consolidation.md]
affected_modules: [domain unadopted v2 record, versioned repository port, isolated filesystem CAS adapter]
affected_contracts: [closed strict wire, canonical v1 preservation, UNKNOWN provenance, dual read no migration, isolated CAS durability]
dependencies: [S449-ROUTE-8086-P1, S449-MANIFEST-G2C, S449-MIGRATION-G2E]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/domain/lifecycle/manifest_v2_record.py, src/tiny_swarm_world/application/ports/lifecycle/versioned_manifest.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_repository.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_json.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_fs.py, tests/domain/lifecycle/test_manifest_v2_record.py, tests/infrastructure/adapters/lifecycle/test_versioned_manifest_repository.py, .codex/evidence/slice-449-manifest-v2-repository-contract.md, .codex/evidence/slice-449-manifest-v2-repository-distribution.md, .codex/evidence/slice-449-manifest-v2-repository-consolidation.md]
module_locks: [versioned manifest record, bounded JSON parser, isolated filesystem CAS and repository facade]
contract_locks: [closed unadopted draft wire and persisted listen input, UNKNOWN provenance, fixed staging path, bounded JSON, redacted repr, cooperating lock inode, bytehash CAS ABA limitation, no admission, crash semantics]
architecture_locks: [domain port adapter boundaries, no existing runtime wiring, no host mutation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_manifest_v2_record tests.infrastructure.adapters.lifecycle.test_versioned_manifest_repository tests.infrastructure.adapters.lifecycle.test_manifest tests.test_migration_preview_cli, python3 -m ruff check src/tiny_swarm_world/domain/lifecycle/manifest_v2_record.py src/tiny_swarm_world/application/ports/lifecycle/versioned_manifest.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_repository.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_json.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_fs.py tests/domain/lifecycle/test_manifest_v2_record.py tests/infrastructure/adapters/lifecycle/test_versioned_manifest_repository.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  arc42: reconcile unadopted wire shape with accepted selection and profile ADRs before implementation
  adr: separate decision if existing ADR forbids unadopted persisted records
stop_conditions: [unresolved draft persistence ADR or provenance semantics, missing six reviews or S3D, V1 regression, host effect, admitted state inferred, uncertain CAS or durability, secret disclosure]
```

One serial implementation owner; role review/S3D before edits. All agent Python checks run in SSH PC WSL on exact source. Follow-on operator migration, canonical persistence and every V2 consumer require separate accepted scopes; live fixture, host admission and support gates remain unchanged.

## Execution-phase amendment v1.67 — V2 repository complexity remediation

Initial full QUALITY failed four complexity guardrails for the new module/class/CAS/JSON parser; no quality pass is claimed. The same serial slice may split bounded JSON parsing and pinned FD/CAS primitives into the two additionally locked modules while retaining the existing repository facade and all security/failure semantics. No quality threshold, baseline or exception is weakened. Contract `.codex/evidence/slice-449-manifest-v2-repository-contract.md` specifies the decomposition. Fresh same-hash six-role reviews and S3D are required before continuing implementation; repeat targeted and full gates on SSH PC WSL.

## Historical execution-phase amendment v1.68 — Portainer shared update no-prune

NoPrune subsequently completed in `c3443ea56c420184124cdf0c8de892b18d301ecf`; planned status below is historical.

S449-PORTAINER-NO-PRUNE is PLANNED on baseline `29be9194c86a35f448f12f3b7905956dc7a430d2`: shared Portainer HTTP stack update sends `prune=False` for direct and LXC-delegated paths. Omitted services may remain; explicit removal and authenticated endpoint/stack/ResourceControl/definition ownership guard remain separately unresolved. No host/live outcome is claimed. Contract `.codex/evidence/slice-449-portainer-no-prune-contract.md`.

```yaml
slice_id: S449-PORTAINER-NO-PRUNE
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py, tests/infrastructure/adapters/clients/test_portainer_http_client.py, tests/infrastructure/adapters/clients/lxc/services/test_lxc_service_clients.py, documentation/user_guide/component-updates.md, .codex/evidence/slice-449-portainer-no-prune-contract.md, .codex/evidence/slice-449-portainer-no-prune-distribution.md, .codex/evidence/slice-449-portainer-no-prune-consolidation.md]
affected_modules: [Portainer shared HTTP stack update, LXC wrapper regression]
affected_contracts: [no automatic prune, omitted services may remain, unchanged create env auth timeout, ownership guard separately open]
dependencies: [S449-01]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py, tests/infrastructure/adapters/clients/test_portainer_http_client.py, tests/infrastructure/adapters/clients/lxc/services/test_lxc_service_clients.py, documentation/user_guide/component-updates.md, .codex/evidence/slice-449-portainer-no-prune-contract.md, .codex/evidence/slice-449-portainer-no-prune-distribution.md, .codex/evidence/slice-449-portainer-no-prune-consolidation.md]
module_locks: [Portainer HTTP update and wrapper contract]
contract_locks: [no prune, omitted service retention, unchanged request parameters, no ownership admission]
architecture_locks: [infrastructure adapter boundary, no live operation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client tests.infrastructure.adapters.clients.lxc.services.test_lxc_service_clients tests.infrastructure.adapters.lifecycle.test_portainer_runtime, python3 -m ruff check src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py tests/infrastructure/adapters/clients/test_portainer_http_client.py tests/infrastructure/adapters/clients/lxc/services/test_lxc_service_clients.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  user_guide: explain omitted-service retention and separate ownership/removal
  arc42: accepted selection exposure ownership ADR unchanged
  adr: no change
stop_conditions: [missing reviews or S3D, unverified removal semantics, changed create auth env timeout, ownership or convergence claimed, live host action]
```

Six Requirement, Architecture, Security, Python, Tester and DevOps same-hash reviews and S3D EXECUTION_PLAN precede edits. Targeted/full quality runs on designated SSH PC WSL exact source.

## Execution-phase amendment v1.69 — visible endpoint/stack conflicts

Status PLANNED for the narrower visible-conflict rejection in both legacy apply paths, after NoPrune `c3443ea56c420184124cdf0c8de892b18d301ecf`; the former global-guard proposal is historical and blocked. Reject visible duplicates, foreign endpoint, malformed records and drift before stack or network mutations after two snapshots. Auth POST and inventory GET are allowed. Legacy create and 404/405 fallback remain unchanged with an operator warning; no new retries, global absence/uniqueness, ownership, atomicity, S449-05 admission or direct update coverage claim. Contract `.codex/evidence/slice-449-portainer-endpoint-stack-contract.md`; fresh six-role reviews and S3D required.

```yaml
slice_id: S449-PORTAINER-ENDPOINT-STACK
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
affected_files: [src/tiny_swarm_world/application/ports/clients/port_portainer_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/portainer_apply_resolution.py, tests/infrastructure/adapters/clients/test_portainer_apply_resolution.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py, tests/infrastructure/adapters/clients/test_portainer_http_client.py, tests/infrastructure/adapters/clients/lxc/services/test_lxc_service_clients.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py, tests/application/services/deployment/test_ensure_portainer_endpoint.py, tests/infrastructure/adapters/exceptions/test_operation_failure_mapping.py, documentation/user_guide/component-updates.md, .codex/evidence/slice-449-portainer-endpoint-stack-contract.md, .codex/evidence/slice-449-portainer-endpoint-stack-distribution.md, .codex/evidence/slice-449-portainer-endpoint-stack-consolidation.md]
affected_modules: [Portainer endpoint and stack resolution, direct and LXC apply]
affected_contracts: [strict visible-conflict rejection, two snapshots before mutation, legacy create unchanged, no global uniqueness or ownership claim]
dependencies: [S449-PORTAINER-NO-PRUNE]
parallel_group: sequential
file_locks: [src/tiny_swarm_world/application/ports/clients/port_portainer_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py, src/tiny_swarm_world/infrastructure/adapters/clients/portainer_apply_resolution.py, tests/infrastructure/adapters/clients/test_portainer_apply_resolution.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py, tests/infrastructure/adapters/clients/test_portainer_http_client.py, tests/infrastructure/adapters/clients/lxc/services/test_lxc_service_clients.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py, tests/application/services/deployment/test_ensure_portainer_endpoint.py, tests/infrastructure/adapters/exceptions/test_operation_failure_mapping.py, documentation/user_guide/component-updates.md, .codex/evidence/slice-449-portainer-endpoint-stack-contract.md, .codex/evidence/slice-449-portainer-endpoint-stack-distribution.md, .codex/evidence/slice-449-portainer-endpoint-stack-consolidation.md]
module_locks: [Portainer port, HTTP and LXC apply, shared fakes]
contract_locks: [visible endpoint stack conflicts and recheck, unchanged legacy create, no prune, direct update bypass documented]
architecture_locks: [application port infrastructure adapters, no host operations]
quality_gates:
  targeted:
    - PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_http_client tests.infrastructure.adapters.clients.lxc.services.test_lxc_service_clients tests.infrastructure.adapters.clients.test_lxc_swarm_runtime tests.application.services.deployment.test_ensure_portainer_endpoint tests.infrastructure.adapters.exceptions.test_operation_failure_mapping
    - python3 -m ruff check src/tiny_swarm_world/application/ports/clients/port_portainer_client.py src/tiny_swarm_world/infrastructure/adapters/clients/portainer_http_client.py src/tiny_swarm_world/infrastructure/adapters/clients/portainer_apply_resolution.py src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py tests/infrastructure/adapters/clients/test_portainer_http_client.py tests/infrastructure/adapters/clients/lxc/services/test_lxc_service_clients.py tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py tests/application/services/deployment/test_ensure_portainer_endpoint.py tests/infrastructure/adapters/exceptions/test_operation_failure_mapping.py
    - 'if [ -f tests/infrastructure/adapters/clients/test_portainer_apply_resolution.py ]; then PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.clients.test_portainer_apply_resolution && python3 -m ruff check tests/infrastructure/adapters/clients/test_portainer_apply_resolution.py; fi'
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  user_guide: document ambiguous identity refusal and ownership limitation
  arc42: accepted ownership ADR unchanged
  adr: no change
stop_conditions: [missing role review or S3D, ambiguous visible endpoint or stack, malformed or failed snapshot, mutating stack POST/PUT or network/manager command before recheck, no-prune regression, ownership or atomicity claim, host action]
```

Six independent Requirement, Architecture, Security, Python, Tester and DevOps same-hash reviews and S3D EXECUTION_PLAN precede edits. Targeted and full quality run on designated SSH PC WSL with exact source.

## Execution-phase amendment v1.70 — visible conflict complexity remediation

The initial full QUALITY reported `grown-critical-class` for `PortainerHttpClient` and `grown-module-complexity` for its module. Do not weaken quality guardrails. Extend the existing S449-PORTAINER-ENDPOINT-STACK serial slice locks with `src/tiny_swarm_world/infrastructure/adapters/clients/portainer_apply_resolution.py` and optional `tests/infrastructure/adapters/clients/test_portainer_apply_resolution.py`. The contract specifies injection of the existing authenticated `_send`, two strict snapshots with exact 200 and no redirects, fingerprint/drift validation, sanitized errors, and unchanged effect ordering and legacy behavior. Preserve all existing regressions; run focused tests and full QUALITY on exact-source SSH PC WSL. Six fresh same-hash role reviews and S3D are required before implementing the amendment. No host action, ownership, completeness or admission follows.

## Execution-phase amendment v1.71 — Portainer upgrade ownership and recovery

PROPOSED, not executable pending ADR owner and six role decisions on `.codex/evidence/slice-449-portainer-upgrade-ownership-contract.md` and S3D. Missing ownership blocks new upgrade before checkpoint/backup; direct proof PUT also blocks. Recovery retains cancel/restore but must remain unsettled without proof; crash uncertainty and durable pending semantics need acceptance first: failed post-replace/fsync save may leave old or new complete checkpoint; read-only reopen, never report success or blindly retry. No V1 swarm setup block, host action or ownership admission.

```yaml
slice_id: S449-PORTAINER-UPGRADE-OWNERSHIP
profile: BACKEND_AND_TESTS
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Security, Senior Tester, Senior DevOps Engineer]
dependencies: [S449-PORTAINER-ENDPOINT-STACK]
parallel_group: sequential
affected_files: [src/tiny_swarm_world/application/services/portainer_upgrade.py, src/tiny_swarm_world/application/ports/lifecycle/portainer_upgrade.py, src/tiny_swarm_world/domain/lifecycle/portainer_upgrade.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/portainer_runtime.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/portainer_api.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/portainer_journal.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/update_journal.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/desired_images.py, tests/application/services/test_portainer_upgrade.py, tests/application/services/test_component_execution.py, tests/application/services/test_product_upgrade.py, tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py, tests/infrastructure/adapters/lifecycle/test_portainer_runtime.py, documentation/user_guide/component-updates.md, .codex/evidence/slice-449-portainer-upgrade-ownership-contract.md, .codex/evidence/slice-449-portainer-upgrade-ownership-distribution.md, .codex/evidence/slice-449-portainer-upgrade-ownership-consolidation.md]
file_locks: [src/tiny_swarm_world/application/services/portainer_upgrade.py, src/tiny_swarm_world/application/ports/lifecycle/portainer_upgrade.py, src/tiny_swarm_world/domain/lifecycle/portainer_upgrade.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/portainer_runtime.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/portainer_api.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/portainer_journal.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/update_journal.py, src/tiny_swarm_world/infrastructure/adapters/lifecycle/desired_images.py, tests/application/services/test_portainer_upgrade.py, tests/application/services/test_component_execution.py, tests/application/services/test_product_upgrade.py, tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py, tests/infrastructure/adapters/lifecycle/test_portainer_runtime.py, documentation/user_guide/component-updates.md, .codex/evidence/slice-449-portainer-upgrade-ownership-contract.md, .codex/evidence/slice-449-portainer-upgrade-ownership-distribution.md, .codex/evidence/slice-449-portainer-upgrade-ownership-consolidation.md]
affected_modules: [Portainer upgrade service and recovery, lifecycle checkpoints, Portainer API]
module_locks: [Portainer upgrade lifecycle, read-only recovery runtime port, checkpoint consumers]
affected_contracts: [pre-backup block, no unowned proof PUT, recovery pending and uncertain crash semantics]
contract_locks: [upgrade ownership, recovery durability, checkpoint compatibility]
architecture_locks: [domain application infrastructure separation, V1 swarm behavior, no host admission]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.test_portainer_upgrade tests.infrastructure.adapters.lifecycle.test_portainer_runtime tests.application.services.test_component_execution tests.application.services.test_product_upgrade tests.infrastructure.adapters.lifecycle.test_native_component_transitions, python3 -m ruff check src/tiny_swarm_world/application/services/portainer_upgrade.py src/tiny_swarm_world/application/ports/lifecycle/portainer_upgrade.py src/tiny_swarm_world/domain/lifecycle/portainer_upgrade.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/portainer_runtime.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/portainer_api.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/portainer_journal.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/update_journal.py src/tiny_swarm_world/infrastructure/adapters/lifecycle/desired_images.py tests/application/services/test_portainer_upgrade.py tests/application/services/test_component_execution.py tests/application/services/test_product_upgrade.py tests/infrastructure/adapters/lifecycle/test_portainer_runtime.py tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py]
  required: [python3 tools/quality_gate.py quality, git diff --check]
documentation:
  user_guide: explain blocked upgrade and pending recovery
  arc42: preserve existing ownership decision and document any accepted amendment
  adr: owner decision on pending recovery and checkpoint semantics required
stop_conditions: [missing ADR owner or six reviews or S3D, checkpoint uncertainty unaddressed, unowned PUT, false recovered or committed status, V1 regression, host operation]
```
