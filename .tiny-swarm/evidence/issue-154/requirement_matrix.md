# Issue #154 Requirement Matrix

Issue: [#154 Installer: Extract and enforce the real Docker Swarm cluster phase](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/154)
Workflow: `issue-154-20260808`
Status at workflow creation: `READY_FOR_WORKFLOW`
Current implementation status: `VERIFIED_LOCAL`; implementation, regression
tests, documentation review, and the local quality gate are complete. No live
verification is claimed because no live consented run was requested or
executed.

This matrix is the implementation gate. Every issue requirement, named file,
acceptance criterion, test expectation and completion-evidence expectation is
represented by a stable ID. `PLANNED`, `OPEN` or `IN_PROGRESS` rows block
`DONE`; only named implementation and verification evidence may move a row to
`VERIFIED_LOCAL` or an explicitly classified live state.

| ID | Requirement from Issue #154 | Type | Files likely affected | Implementation evidence | Test/evidence verification | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Make `cluster` a real executable setup phase for the default `lxc_native` provider. | functional | setup composition, installation plan, platform workflows | Explicit cluster-owned phase names in assembled setup | Setup phase and plan-order tests | VERIFIED_LOCAL |
| REQ-002 | `platform init` owns node creation/reconciliation/start/reachability only and no longer owns Docker installation or Swarm bootstrap. | architecture / functional | composition, platform workflow assembly | Docker/Swarm steps removed from platform-init ownership | Composition and platform tests | VERIFIED_LOCAL |
| REQ-003 | `platform reconcile` remains limited to the LXC/Incus node layer. | architecture / functional | composition, platform tests | Reconcile step list contains node operations only | Reconcile ownership test | VERIFIED_LOCAL |
| REQ-004 | Stable cluster-owned phases exist for Docker, Swarm bootstrap and cluster verification, or clearly equivalent names. | contract | setup composition, plan, YAML | Stable names shared by plan and setup | Plan/setup parity test | VERIFIED_LOCAL |
| REQ-005 | Cluster Docker runs after platform reconciliation. | ordering | setup composition | Ordered phase list | Setup ordering test | VERIFIED_LOCAL |
| REQ-006 | Docker is installed, inspected and verified inside every configured managed node. | functional | Docker service/step, LXC adapter | Typed per-node runtime service reused | Docker/setup tests | VERIFIED_LOCAL |
| REQ-007 | Swarm manager initialization occurs only when required and after Docker readiness. | ordering | Swarm service, setup composition | Bootstrap follows Docker success | Manager/Docker gate tests | VERIFIED_LOCAL |
| REQ-008 | Manager initialization completes before any worker join. | safety | Swarm service | Existing service ordering retained | Worker ordering test | VERIFIED_LOCAL |
| REQ-009 | Worker join is blocked without a valid join token. | safety / functional | Swarm port/DTO/adapter/service | Placeholder/unavailable token is non-success | Missing-token test with zero join calls | VERIFIED_LOCAL |
| REQ-010 | Installation plan explicitly maps `cluster` to executable cluster workflow phases. | contract | domain plan, YAML | Domain/YAML workflow mapping | Plan parity tests | VERIFIED_LOCAL |
| REQ-011 | Ordering is `platform -> cluster -> network-routing`. | ordering | plan, setup composition | Dependency graph and arrangement | Domain/setup tests | VERIFIED_LOCAL |
| REQ-012 | `network-routing`/`platform expose` runs only after successful cluster verification. | safety | setup composition, plan | Cluster verify precedes expose | Boundary test | VERIFIED_LOCAL |
| REQ-013 | Cluster verification checks Docker readiness for every expected node. | acceptance | DTOs, services, adapters | All-node aggregation | Missing/not-ready tests | VERIFIED_LOCAL |
| REQ-014 | Verification uses structured membership from the managed Swarm environment, not host Docker. | architecture / functional | Swarm port/adapter/service, DTOs | Managed manager-observed contract | Adapter fake/source tests | VERIFIED_LOCAL |
| REQ-015 | Verification fails for missing expected nodes. | safety | cluster verification | Expected/observed completeness check | Missing-node test | VERIFIED_LOCAL |
| REQ-016 | Verification rejects nodes that are not `Ready`. | acceptance | cluster DTO/contract/adapter | Ready-state validation | Non-Ready test | VERIFIED_LOCAL |
| REQ-017 | Verification rejects nodes that are not `Active`. | acceptance | cluster DTO/contract/adapter | Active-state validation | Non-Active test | VERIFIED_LOCAL |
| REQ-018 | Verification requires expected manager role and contract-defined manager/leader state. | acceptance | cluster DTO/contract/adapter | Manager/leader validation | Missing/wrong-state tests | VERIFIED_LOCAL |
| REQ-019 | Swarm is initialized before membership is accepted. | safety | Swarm DTO/contract/adapter | Uninitialized state is non-success | Uninitialized test | VERIFIED_LOCAL |
| REQ-020 | Prefer existing structured DTOs and avoid fragile substring parsing when structured state is available. | architecture / quality | DTOs, adapter | Typed contract reused or explicitly extended | Architecture/source review | VERIFIED_LOCAL |
| REQ-021 | Failed/blocked cluster subphase makes every downstream executable phase `not_run`. | safety | setup/composition | Existing generic propagation reused | Downstream status test | VERIFIED_LOCAL |
| REQ-022 | Downstream stop includes expose/routing, deployment bootstrap, artifact bootstrap/readiness/prepare/verify, deployment apply/verify and final platform verify. | acceptance | setup tests, composition | Full phase list retains `not_run` | Failure-boundary test | VERIFIED_LOCAL |
| REQ-023 | Domain `InstallationPlan` and YAML express the same executable boundaries. | contract / quality | plan sources, parity tests | Plan parity including host preparation | Plan parity test | VERIFIED_LOCAL |
| REQ-024 | `cicd`, `quality`, `messaging`, `control`, `docs` and `validation` do not present a misleading mixed executable/metadata model. | architecture | plan, YAML, setup tests | Explicit metadata/executable distinction | Logical-phase review/test | VERIFIED_LOCAL |
| REQ-025 | Preserve service ordering; do not broaden into deployment redesign. | architecture / regression | plan, setup/deployment tests | Scoped ordering diff | Regression/review | VERIFIED_LOCAL |
| REQ-026 | Native Linux and WSL2 host-preflight behavior from #218 remains unchanged. | regression | host-preflight source/tests | No host behavior change | Host tests | VERIFIED_LOCAL |
| REQ-027 | Artifact preflight/readiness behavior from #232 remains unchanged. | regression | artifact/setup source/tests | No artifact redesign | Artifact tests | VERIFIED_LOCAL |
| REQ-028 | Reuse generic setup fail-closed and `not_run` behavior. | architecture / safety | setup workflow/composition | Existing stop path remains sole generic guard | Setup tests | VERIFIED_LOCAL |
| REQ-029 | Verification commands are read-only and live mutation remains consent-gated. | safety | adapters, composition, evidence | Read-only adapter path and consent boundary | Static/mocked review | VERIFIED_LOCAL |
| REQ-030 | Test that platform init no longer owns Docker or Swarm. | quality | platform/composition tests | Ownership regression | Named test | VERIFIED_LOCAL |
| REQ-031 | Test cluster Docker after platform reconciliation. | quality | setup tests | Ordered fake calls | Named test | VERIFIED_LOCAL |
| REQ-032 | Test Swarm bootstrap only after Docker readiness. | quality | setup/platform tests | Docker failure blocks bootstrap | Named test | VERIFIED_LOCAL |
| REQ-033 | Test manager initialization before worker joins. | quality | Swarm tests | Call-order fake | Named test | VERIFIED_LOCAL |
| REQ-034 | Test worker join blocked without valid token. | quality | Swarm tests | Invalid-token fixture | Named test | VERIFIED_LOCAL |
| REQ-035 | Test every expected node is required. | quality | Swarm tests | Expected/observed mismatch | Named test | VERIFIED_LOCAL |
| REQ-036 | Test non-Ready node rejection. | quality | Swarm tests | Structured fixture | Named test | VERIFIED_LOCAL |
| REQ-037 | Test non-Active node rejection. | quality | Swarm tests | Structured fixture | Named test | VERIFIED_LOCAL |
| REQ-038 | Test missing manager/leader state rejection where required. | quality | Swarm tests | Wrong-state fixture | Named test | VERIFIED_LOCAL |
| REQ-039 | Test network-routing only after cluster verification. | quality | setup/composition tests | Success/failure sequence | Named test | VERIFIED_LOCAL |
| REQ-040 | Test failed/blocked cluster marks all downstream phases `not_run`. | quality | setup tests | Complete status assertions | Named test | VERIFIED_LOCAL |
| REQ-041 | Test plan and executable setup ordering consistency. | quality | domain/setup/YAML tests | Ordered name comparison | Named test | VERIFIED_LOCAL |
| REQ-042 | Preserve #218 host-preflight in the default suite. | regression | host tests | Existing tests remain green | Test result/diff review | VERIFIED_LOCAL |
| REQ-043 | Preserve #232 artifact-preflight/readiness in the default suite. | regression | artifact tests | Existing tests remain green | Test result/diff review | VERIFIED_LOCAL |
| REQ-044 | Use mocks/fakes/ports; default quality gate must not require live Docker, Incus/LXD, Swarm, networking or deployment. | safety / quality | affected tests, evidence | No live command fixtures | Test evidence/static review | VERIFIED_LOCAL |
| REQ-045 | Preserve hexagonal architecture; domain/application code must not execute shell directly. | architecture | domain/application/infrastructure | Port-based orchestration | arch-lint, arch-tests, review | VERIFIED_LOCAL |
| REQ-046 | Record changed files, before/after sequence, cluster plan mapping, ownership proof and focused results. | completion | issue evidence | Evidence package | Evidence review | VERIFIED_LOCAL |
| REQ-047 | Run and record `python3 tools/quality_gate.py quality`. | quality-gate | quality evidence | Full local result | `test_results.md` | VERIFIED_LOCAL |
| REQ-048 | Update docs only where executable sequence or terminology changed. | documentation | Arc42, installation guide | Verified behavior docs | `git diff --check`, review | VERIFIED_LOCAL |
| REQ-049 | Separate live verification from local acceptance and use repository `LIVE_*` states. | verification | optional live evidence | Redacted state record | Live-state review | VERIFIED_LOCAL |
| REQ-050 | Complete evidence and obtain Requirement Lead, System Architect, Test/Evidence Reviewer and independent Auditor decisions before `DONE`. | governance | issue evidence, audit handoff | Six-file package and audit | Completion audit | VERIFIED_LOCAL |

## Review Gate

- Requirement Lead: Senior Requirement Engineer confirms every issue sentence,
  bullet, named file and acceptance condition is captured.
- System Architect Reviewer: Senior System Architect confirms managed-runtime
  ownership, hexagonal boundaries, plan parity and no deployment redesign.
- Test / Evidence Reviewer: Senior Tester confirms each row has a named test,
  check or evidence artifact and local gates were not bypassed.
- Issue Completion Auditor: independent `issue-completion-auditor` decides
  `PASS`, `INCOMPLETE`, `BLOCKED` or `REJECTED` after implementation evidence.

Every row is now `VERIFIED_LOCAL` with named implementation and verification
evidence. `LIVE_VERIFIED` is intentionally not claimed; live-provider
acceptance remains an explicitly consent-gated follow-up and is recorded as a
remaining risk rather than silently inferred from local tests.
