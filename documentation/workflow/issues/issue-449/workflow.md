# LCM-W09 — Selective installation and upgrades on native Linux and WSL2

Workflow ID: `issue-449-lcm-w09`
Status: `S02C_CANDIDATE_SYNCED — current runner 7929f9dc5d6fea32c55125c3b9f8fb4f02b72a07d3ea0ef80cb0a2aea6279c12; tests 6f888dc59182c7b02ed86fd3e80ddbadb5d7e5a6286e27b4c67d5d3eeb7fcba3; 95 focused tests PASS on approved PC WSL; full QUALITY PASS on Python 3.14.4 private venv with CI-pinned tools (43 architecture tests, 2,969 tests, 18 skipped; log SHA-256 daa2d3952b97aef496035ea773ede718fa5e79e61df1f832c9761ab15126e8df, mode 0600, parent directory mode 0700); exact candidate not run on CI Python 3.12; The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; the directory must be mode 0700 and the record mode 0600. Workflow execution requires four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Host/scenario GO and normalized host admission are separate prerequisites. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. Available native and WSL project inventories and route captures are tied to pre-candidate checkout be2e031e8f0fb137ea6c15f74d81a88181aa4183; they are not current-candidate evidence for branch HEAD a286b22db8988e2cc8fab39d97d6abb34f4129ab. Native route-state PASS digest fe31f78643962ce3757e8bcfc8cc8ed1e9c9eb46a2c1728f52f773fbc2f84758 is historical to that checkout. WSL route-state capture returned JIT_COMMAND_FAILED and is not a pass. Current native read-only preflight is blocked by active snap.lxd.daemon.service; no normalized current-candidate admission exists. `
Issue: [#449 LCM-W09](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/449)
Epic: [#440 LCM-04](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/440)
Branch: `feature/lcm-w09-issue449-implementation-20261027`
Workflow authoring branch: `docs/workflow-lcm-w09-route-baseline-20261027`
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
of the TCP/10001 host listener rows, all Incus TCP/10001 profile and instance
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
decode/re-encode or normalize line endings. Combine the canonical firewall JSON
and exact PortProxy bytes as base64 values under the fixed
`firewall_active_store_b64` and `portproxy_raw_b64` keys, then serialize that
object with sorted keys, compact separators and `ensure_ascii=False` as the
combined snapshot bytes.
The exact PowerShell command string is fixed in the hash-pinned runner; callers
cannot supply or replace it.
The listener and route lists may be empty only when commands succeeded,
their exact empty state is independently reviewed, and the digest binds that
state. The runner computes the same canonical UTF-8 JSON digest from its
post-reservation read-only JIT and requires a match before any Incus write.
Enumerate projects with read-only `incus project list --format json`; reject
malformed results, missing/empty or duplicate names, and require `default`.
Strictly read each project's metadata and enumerate its profiles and instances
using that explicit project. Read each profile's complete config/devices and
each instance's complete config/devices/profiles. TCP/10001 proxy route records
carry exactly the project and owner identity plus the complete route device
configuration and effective profile list. Sort project names lexically and
sort routes by `(project, owner_type, owner, device)`. This inventory is
read-only across all projects; S449 profile reconciliation and fixture
mutations remain limited to Incus project `default`.

The digest payload has exactly four fields: `listeners_10001_b64` (sorted
base64 values for the exact `ss -H -ltnp` rows), `incus_projects` (sorted
project-name strings), `incus_10001_routes` (the sorted project-bound route
records), and `windows_snapshot_b64` (base64 of the combined Windows snapshot;
empty bytes on native Linux). Serialize the payload as UTF-8 JSON with sorted
object keys, compact separators and `ensure_ascii=False`, then compute
SHA-256. The pre-GO capture artifact records the same project names, route
records and digest. A mismatch is durably recorded as
`BLOCKED_TARGET_DRIFT`.
In normal one-shot run mode, read the GO once as a no-follow regular file, compare its raw bytes with caller
`--expected-approval-sha256`, then parse strict UTF-8 JSON; reject duplicate
keys and missing/extra keys at every object. Before reservation, normal run
mode allows read-only Git inspection and the single GO-file read only: no
host/Incus command and no lock/evidence mutation. The separate pre-GO
`--capture-route-state` mode is read-only except for creating its exclusive
mode-0600 evidence artifact. Its artifact contains the complete read-only
Incus project-name inventory and project-bound TCP/10001 profile and instance
routes, in addition to listener rows and the WSL snapshot where applicable.
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
Historical v1.32 evidence: runner/test `f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628` / `8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668`, 85 focused tests, and full QUALITY log SHA-256 `247da0bd35bbf91138811ba7355f39681fd7dc5b3e47c78474cdc4b806a90e26` remain historical and are not current candidate evidence. Current candidate runner SHA-256 `7929f9dc5d6fea32c55125c3b9f8fb4f02b72a07d3ea0ef80cb0a2aea6279c12`; test SHA-256 `6f888dc59182c7b02ed86fd3e80ddbadb5d7e5a6286e27b4c67d5d3eeb7fcba3`; focused suite 95 PASS on approved PC WSL. Full QUALITY PASS: GATE_EXIT=0 on Python 3.14.4 in a private venv with CI-pinned tools; 43 architecture tests, 2,969 total tests, 18 skipped; private log SHA-256 `daa2d3952b97aef496035ea773ede718fa5e79e61df1f832c9761ab15126e8df`, file mode 0600, parent directory mode 0700. This exact candidate was not run on CI Python 3.12. Available native and WSL project inventories and route captures are from pre-candidate checkout be2e031e8f0fb137ea6c15f74d81a88181aa4183; they are not exact-current-candidate evidence for branch HEAD a286b22. The native route-state PASS digest fe31f78643962ce3757e8bcfc8cc8ed1e9c9eb46a2c1728f52f773fbc2f84758 is historical to that checkout. WSL route-state capture returned JIT_COMMAND_FAILED and is not a pass. Current native read-only preflight is blocked by active snap.lxd.daemon.service; no normalized current-candidate admission exists. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. Native read-only preflight is blocked by active `snap.lxd.daemon.service`. The pre-candidate native inventory showed only the default LXD project and three stopped TSW containers; no host-stop GO exists. Pre-candidate native resource observations were 8 CPUs, 20,111,052,800 bytes MemTotal, 15,452,803,072 bytes MemAvailable, 724,140,146,688 bytes free disk, ext4 `/`, and `incus version` reports Client/Server 6.0.5. For native R449-33, the accepted resource floor is 18,253,611,008 bytes (17 GiB), CPU >= 8 and free disk >= 150 GiB; observed MemTotal, CPU and disk meet those numerical floors. The 19 GiB default-node guard applies only where that baseline applies; the accepted ADR supports a 17 GiB TSW_INFRA_ROOT override for this host. MemAvailable is recorded as an observation, not an admission threshold. This numerical comparison is not a normalized resource-admission artifact or PASS: active snap.lxd.daemon.service blocks read-only service-access preflight, and the exact admission artifact and per-scenario GO are absent. Incus 6.0.5 does not establish capability support. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites.  The current candidate has no host/scenario GO or normalized admission. The v1.32 approval record and its S3D result remain historical. No host admission, scenario GO, or target mutation is claimed.
sanitization, schema rejection, output metadata, sanitized-artifact-only hash,
private exclusive ext4 write, and no GO/reservation/NOT_RUN/Incus-write behavior.
S449-02 may not collect or claim this inventory before that implementation and
until required same-hash reviews, full QUALITY and S3/S3D pass.


#### S449-02 per-scenario read-only admission and inventory phase (separate from S449-02C)

Begin only after exact S449-02C source, runner/tests and required reviews are
approved. Inspect only native Linux `192.168.178.33` and PC WSL2
`192.168.178.58`, with the exact approved Ubuntu WSL distro identity. Store all
artifacts beneath `.tiny-swarm/evidence/issue-449/s449-private-20261027/` on
verified ext4 checkout, directory mode 0700 and files mode 0600. Fail closed on
unknown distro, failed commands, incomplete output, unknown schema,
insufficient capacity, or unverifiable source/filesystem state.

**Exact source and native host admission.** Run from the approved ext4 repository
root and record argv, exit code and stdout/stderr byte counts for every command.
Keep only parsed/sanitized values. Hash raw stdout only for the explicit safe
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
Ubuntu. Run the existing read-only Windows preflight; preserve only allowlisted
parsed resource fields and exit code, plus argv and stdout/stderr byte counts.
Do not persist or hash raw PowerShell output:

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
`{argv, exit_status, stdout_bytes, stderr_bytes}` and may include
`stdout_sha256` only for raw stdout of `git status --short --branch`,
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
failure. Direct regressions cover identity stdout/stderr, inventory aggregate output, serialized artifact, total entity and command-count caps; every limit failure must fail closed without creating an artifact.


The payload top-level is exactly `{schema_version, target_host, source_commit,
projects, command_records}` with `schema_version` `tsw.incus.project-inventory.v1`.
Each command record is exactly `{argv, exit_status, stdout_bytes, stderr_bytes}`; metadata only, no output bytes or raw hashes. Each Incus inventory command is capped at 2 MiB independently for stdout and stderr; aggregate captured stdout+stderr across the run is capped at 16 MiB. Sanitized output is capped at 8 MiB before exclusive file creation. The total project/profile/instance/device entity count is capped at 10,000 and total Incus command count at 10,000. Any per-stream, aggregate byte, serialized-artifact, entity or command cap overflow, 30-second timeout, nonzero exit, malformed/unknown field or incomplete visibility fails closed; no sanitized inventory is accepted. Selector-driven collection enforces each 2 MiB stream cap while reading, kills the process on a cap or 30-second timeout, and parses only bounded complete output. It retains only safe byte counts and exit status, never raw Incus output or its hash. No output artifact is created if a limit or validation fails. The pre-existing private ext4 evidence directory must be verified before capture; this read creates the artifact only after bounded capture, sanitization, schema checks and size validation succeed. The remote-list/default reads use the same caps and command-count budget.
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
endpoint binding, exact argv (including `--format json --expanded` order), all-project
visibility/order, null/absent feature behavior, sanitized devices, no raw
output or hashes, deterministic artifact binding, no GO/reservation/Incus write,
and exclusive private ext4 output. Any unknown project, permission-limited
visibility, absent/unreadable required state, or schema mismatch blocks S02.
This mode is not normal fixture run mode. Five-role per-host GO remains
mandatory before normal fixture invocation, profile/instance mutations,
install/upgrade or service/system changes.
### Slice 02 — Incus 6.0.5 disposable listener fixture evidence

Purpose: verify proxy listener timing and attribution before implementing the
new capability.

Prerequisites: S449-01 and S449-02C; disposable Incus server exactly 6.0.5; fresh exact-source
and target JIT for the specific host; pre-GO route-state evidence from the
read-only S449-02C capture mode; resource admission; full issue447
project/profile/consumer/device inventory; empty baseline for the exact selected
loopback fixture tuple and the exact current TCP/10001 listener/route baseline,
which may be empty; any existing entries and Windows firewall/PortProxy bytes
must remain unchanged;
and a one-shot scenario-specific live Three-Amigos GO whose raw SHA-256 and
workflow/runner/test hashes match the released S449-02C candidate, naming the exact host, expected HEAD,
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
affected_contracts: [proxy bind timing, effective tuple and listener attribution, exact 16-key five-review GO, workflow/source/runner/test/target hashes, canonical default-profile config/devices digest, sorted consumer list, approved live route-state digest, ext4 private evidence root and POSIX 0700/0600 modes, external resource and issue447 evidence attestations, unchanged Windows rules, no external routes]
dependencies: [S449-02C]
parallel_group: serialized-live
file_locks: [.tiny-swarm/evidence/issue-449/s449-private-20261027/s02-private-posix-verification.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-pre-go-route-state.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-pre-go-route-state.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-resource-admission.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-resource-admission.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/native-issue447-inventory.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-issue447-inventory.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-s02-live-go.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/three-amigos-s02-live-review.md, .tiny-swarm/evidence/issue-449/s449-private-20261027/r67-incus-6.0.5-listener-fixture.json, .tiny-swarm/evidence/issue-449/s449-private-20261027/r67-incus-6.0.5-listener-fixture.json.reservation, .codex/evidence/slice-449-02-distribution.md, .codex/evidence/slice-449-02-consolidation.md]
module_locks: [per-host live qualification host state, disposable target identity and cleanup evidence]
contract_locks: [per-host GO target identity and cleanup binding, immutable listener-fixture result schema, ext4 private evidence root and POSIX 0700/0600 modes, host-specific run command/exit/provenance record, route-preservation outcome]
architecture_locks: [capability version boundary]
quality_gates:
  targeted: [git diff --check, verify exact S449-02C source/test evidence hashes, verify ext4 target checkout and private evidence permissions]
  required: [reuse S449-02C full quality evidence only when exact source hash matches]
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
approval of R67j is not a workflow review. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. The current candidate has no host/scenario GO or normalized admission. The record path is
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

Status: `S02C_CANDIDATE_SYNCED — final runner/test hashes, 95 focused tests and full QUALITY evidence recorded above; exact candidate not run on CI Python 3.12; current live blockers remain; no host admission or scenario GO`
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
