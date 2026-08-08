# Issue #154 Requirement Matrix

Issue: [#154 Installer: Extract and enforce the real Docker Swarm cluster phase](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/154)
Workflow: `issue-154-20260808`
Status at workflow creation: `READY_FOR_WORKFLOW`
Current implementation status: `PLANNED`; no product implementation is
claimed by this matrix.

This matrix is the implementation gate. Every issue requirement, named file,
acceptance criterion, test expectation and completion-evidence expectation is
represented by a stable ID. `PLANNED`, `OPEN` or `IN_PROGRESS` rows block
`DONE`; only named implementation and verification evidence may move a row to
`VERIFIED_LOCAL` or an explicitly classified live state.

| ID | Requirement from Issue #154 | Type | Files likely affected | Implementation evidence | Test/evidence verification | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Make `cluster` a real executable setup phase for the default `lxc_native` provider. | functional | setup composition, installation plan, platform workflows | Explicit cluster-owned phase names in assembled setup | Setup phase and plan-order tests | PLANNED |
| REQ-002 | `platform init` owns node creation/reconciliation/start/reachability only and no longer owns Docker installation or Swarm bootstrap. | architecture / functional | composition, platform workflow assembly | Docker/Swarm steps removed from platform-init ownership | Composition and platform tests | PLANNED |
| REQ-003 | `platform reconcile` remains limited to the LXC/Incus node layer. | architecture / functional | composition, platform tests | Reconcile step list contains node operations only | Reconcile ownership test | PLANNED |
| REQ-004 | Stable cluster-owned phases exist for Docker, Swarm bootstrap and cluster verification, or clearly equivalent names. | contract | setup composition, plan, YAML | Stable names shared by plan and setup | Plan/setup parity test | PLANNED |
| REQ-005 | Cluster Docker runs after platform reconciliation. | ordering | setup composition | Ordered phase list | Setup ordering test | PLANNED |
| REQ-006 | Docker is installed, inspected and verified inside every configured managed node. | functional | Docker service/step, LXC adapter | Typed per-node runtime service reused | Docker/setup tests | PLANNED |
| REQ-007 | Swarm manager initialization occurs only when required and after Docker readiness. | ordering | Swarm service, setup composition | Bootstrap follows Docker success | Manager/Docker gate tests | PLANNED |
| REQ-008 | Manager initialization completes before any worker join. | safety | Swarm service | Existing service ordering retained | Worker ordering test | PLANNED |
| REQ-009 | Worker join is blocked without a valid join token. | safety / functional | Swarm port/DTO/adapter/service | Placeholder/unavailable token is non-success | Missing-token test with zero join calls | PLANNED |
| REQ-010 | Installation plan explicitly maps `cluster` to executable cluster workflow phases. | contract | domain plan, YAML | Domain/YAML workflow mapping | Plan parity tests | PLANNED |
| REQ-011 | Ordering is `platform -> cluster -> network-routing`. | ordering | plan, setup composition | Dependency graph and arrangement | Domain/setup tests | PLANNED |
| REQ-012 | `network-routing`/`platform expose` runs only after successful cluster verification. | safety | setup composition, plan | Cluster verify precedes expose | Boundary test | PLANNED |
| REQ-013 | Cluster verification checks Docker readiness for every expected node. | acceptance | DTOs, services, adapters | All-node aggregation | Missing/not-ready tests | PLANNED |
| REQ-014 | Verification uses structured membership from the managed Swarm environment, not host Docker. | architecture / functional | Swarm port/adapter/service, DTOs | Managed manager-observed contract | Adapter fake/source tests | PLANNED |
| REQ-015 | Verification fails for missing expected nodes. | safety | cluster verification | Expected/observed completeness check | Missing-node test | PLANNED |
| REQ-016 | Verification rejects nodes that are not `Ready`. | acceptance | cluster DTO/contract/adapter | Ready-state validation | Non-Ready test | PLANNED |
| REQ-017 | Verification rejects nodes that are not `Active`. | acceptance | cluster DTO/contract/adapter | Active-state validation | Non-Active test | PLANNED |
| REQ-018 | Verification requires expected manager role and contract-defined manager/leader state. | acceptance | cluster DTO/contract/adapter | Manager/leader validation | Missing/wrong-state tests | PLANNED |
| REQ-019 | Swarm is initialized before membership is accepted. | safety | Swarm DTO/contract/adapter | Uninitialized state is non-success | Uninitialized test | PLANNED |
| REQ-020 | Prefer existing structured DTOs and avoid fragile substring parsing when structured state is available. | architecture / quality | DTOs, adapter | Typed contract reused or explicitly extended | Architecture/source review | PLANNED |
| REQ-021 | Failed/blocked cluster subphase makes every downstream executable phase `not_run`. | safety | setup/composition | Existing generic propagation reused | Downstream status test | PLANNED |
| REQ-022 | Downstream stop includes expose/routing, deployment bootstrap, artifact bootstrap/readiness/prepare/verify, deployment apply/verify and final platform verify. | acceptance | setup tests, composition | Full phase list retains `not_run` | Failure-boundary test | PLANNED |
| REQ-023 | Domain `InstallationPlan` and YAML express the same executable boundaries. | contract / quality | plan sources, parity tests | Plan parity including host preparation | Plan parity test | PLANNED |
| REQ-024 | `cicd`, `quality`, `messaging`, `control`, `docs` and `validation` do not present a misleading mixed executable/metadata model. | architecture | plan, YAML, setup tests | Explicit metadata/executable distinction | Logical-phase review/test | PLANNED |
| REQ-025 | Preserve service ordering; do not broaden into deployment redesign. | architecture / regression | plan, setup/deployment tests | Scoped ordering diff | Regression/review | PLANNED |
| REQ-026 | Native Linux and WSL2 host-preflight behavior from #218 remains unchanged. | regression | host-preflight source/tests | No host behavior change | Host tests | PLANNED |
| REQ-027 | Artifact preflight/readiness behavior from #232 remains unchanged. | regression | artifact/setup source/tests | No artifact redesign | Artifact tests | PLANNED |
| REQ-028 | Reuse generic setup fail-closed and `not_run` behavior. | architecture / safety | setup workflow/composition | Existing stop path remains sole generic guard | Setup tests | PLANNED |
| REQ-029 | Verification commands are read-only and live mutation remains consent-gated. | safety | adapters, composition, evidence | Read-only adapter path and consent boundary | Static/mocked review | PLANNED |
| REQ-030 | Test that platform init no longer owns Docker or Swarm. | quality | platform/composition tests | Ownership regression | Named test | PLANNED |
| REQ-031 | Test cluster Docker after platform reconciliation. | quality | setup tests | Ordered fake calls | Named test | PLANNED |
| REQ-032 | Test Swarm bootstrap only after Docker readiness. | quality | setup/platform tests | Docker failure blocks bootstrap | Named test | PLANNED |
| REQ-033 | Test manager initialization before worker joins. | quality | Swarm tests | Call-order fake | Named test | PLANNED |
| REQ-034 | Test worker join blocked without valid token. | quality | Swarm tests | Invalid-token fixture | Named test | PLANNED |
| REQ-035 | Test every expected node is required. | quality | Swarm tests | Expected/observed mismatch | Named test | PLANNED |
| REQ-036 | Test non-Ready node rejection. | quality | Swarm tests | Structured fixture | Named test | PLANNED |
| REQ-037 | Test non-Active node rejection. | quality | Swarm tests | Structured fixture | Named test | PLANNED |
| REQ-038 | Test missing manager/leader state rejection where required. | quality | Swarm tests | Wrong-state fixture | Named test | PLANNED |
| REQ-039 | Test network-routing only after cluster verification. | quality | setup/composition tests | Success/failure sequence | Named test | PLANNED |
| REQ-040 | Test failed/blocked cluster marks all downstream phases `not_run`. | quality | setup tests | Complete status assertions | Named test | PLANNED |
| REQ-041 | Test plan and executable setup ordering consistency. | quality | domain/setup/YAML tests | Ordered name comparison | Named test | PLANNED |
| REQ-042 | Preserve #218 host-preflight in the default suite. | regression | host tests | Existing tests remain green | Test result/diff review | PLANNED |
| REQ-043 | Preserve #232 artifact-preflight/readiness in the default suite. | regression | artifact tests | Existing tests remain green | Test result/diff review | PLANNED |
| REQ-044 | Use mocks/fakes/ports; default quality gate must not require live Docker, Incus/LXD, Swarm, networking or deployment. | safety / quality | affected tests, evidence | No live command fixtures | Test evidence/static review | PLANNED |
| REQ-045 | Preserve hexagonal architecture; domain/application code must not execute shell directly. | architecture | domain/application/infrastructure | Port-based orchestration | arch-lint, arch-tests, review | PLANNED |
| REQ-046 | Record changed files, before/after sequence, cluster plan mapping, ownership proof and focused results. | completion | issue evidence | Evidence package | Evidence review | PLANNED |
| REQ-047 | Run and record `python3 tools/quality_gate.py quality`. | quality-gate | quality evidence | Full local result | `test_results.md` | PLANNED |
| REQ-048 | Update docs only where executable sequence or terminology changed. | documentation | Arc42, installation guide | Verified behavior docs | `git diff --check`, review | PLANNED |
| REQ-049 | Separate live verification from local acceptance and use repository `LIVE_*` states. | verification | optional live evidence | Redacted state record | Live-state review | PLANNED |
| REQ-050 | Complete evidence and obtain Requirement Lead, System Architect, Test/Evidence Reviewer and independent Auditor decisions before `DONE`. | governance | issue evidence, audit handoff | Six-file package and audit | Completion audit | PLANNED |

## Review Gate

- Requirement Lead: Senior Requirement Engineer confirms every issue sentence,
  bullet, named file and acceptance condition is captured.
- System Architect Reviewer: Senior System Architect confirms managed-runtime
  ownership, hexagonal boundaries, plan parity and no deployment redesign.
- Test / Evidence Reviewer: Senior Tester confirms each row has a named test,
  check or evidence artifact and local gates were not bypassed.
- Issue Completion Auditor: independent `issue-completion-auditor` decides
  `PASS`, `INCOMPLETE`, `BLOCKED` or `REJECTED` after implementation evidence.

No row may move from `PLANNED` to `VERIFIED_LOCAL` without implementation
evidence and a named test, check or evidence artifact. Any unresolved or
unverifiable row forces `INCOMPLETE`, `BLOCKED` or `FAILED`.
