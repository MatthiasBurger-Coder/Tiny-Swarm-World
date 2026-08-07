# Issue #232 Requirement Matrix

Issue: [#232 Implement complete artifact and container-image installation preflight](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/232)
Workflow: `issue-232-20260808`
Status at workflow creation: `READY_FOR_WORKFLOW`

This matrix is the implementation gate. It records issue requirements and
acceptance statements before product implementation. Empty implementation or
verification evidence remains `OPEN`; an open row blocks `DONE`.

| ID | Requirement from Issue #232 | Type | Files likely affected | Implementation evidence | Test/evidence verification | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Define a canonical, profile-aware artifact image inventory for all images required by the selected Compose/service profile. | functional / architecture | `domain/artifacts/**`, Compose repository, service-profile contracts | planned Slice 01/03 | profile inventory tests; matrix evidence | PLANNED |
| REQ-002 | Every deployed image has exactly one matching image contract and every required contract is consumed by deployment. | functional / quality | domain contracts, Compose repository, composition | planned Slice 01/03 | one-to-one alignment tests | PLANNED |
| REQ-003 | Image references do not allow implicit `latest` and follow the approved tag or digest strategy. | security / functional | `container_image_contract.py` | planned Slice 01 | invalid-reference tests | PLANNED |
| REQ-004 | `build` contracts resolve to an existing approved repository-local context; `pull` contracts have an immutable reference and declared upstream expectations. | functional / safety | domain contract, `PortLocalFileStorage`, adapters | planned Slice 01/02/03/05 | context and source-semantics tests | PLANNED |
| REQ-005 | Reject duplicate artifact target IDs, duplicate logical build contexts and conflicting image references. | functional / quality | domain inventory and contract validation | planned Slice 01 | duplicate/conflict tests | PLANNED |
| REQ-006 | Apply every supported `TSW_*_IMAGE` override consistently to Compose rendering and artifact preparation. | functional | composition, Compose repository, artifact services | planned Slice 03 | override matrix tests | PLANNED |
| REQ-007 | Add a non-mutating static artifact-contract check to installation preflight. | functional / safety | preflight service, CLI/composition | planned Slice 04 | mocked/static no-mutation tests | PLANNED |
| REQ-008 | After required Nexus/registry bootstrap and before image build/pull/push, check manager Docker readiness, endpoint reachability, repository readiness, storage/build inputs and public pull prerequisites. | functional / resilience | readiness ports/adapters, artifact workflow | planned Slice 05/06 | adapter mocks and sequencing tests; optional live evidence | PLANNED |
| REQ-009 | Return typed machine-readable results with safe evidence and remediation; never expose credentials, tokens, command output or secret values. | security / observability | result models, adapters, evidence | planned Slice 02/05/07 | redaction and schema tests | PLANNED |
| REQ-010 | Stop setup before `artifacts prepare`, `artifacts verify` or dependent deployment when a mandatory prerequisite fails. | functional / safety | artifact/setup/deployment orchestration | planned Slice 04/06 | fail-closed phase tests | PLANNED |
| REQ-011 | Keep domain code free of filesystem, Docker, HTTP, YAML and command-runner concerns; use ports and infrastructure adapters for live checks. | architecture | domain, application ports, adapters, composition | planned Slice 01/02/05 | import-linter and architecture tests | PLANNED |
| REQ-012 | Update artifact, installation, configuration and troubleshooting documentation. | documentation | `documentation/**`, arc42 | planned Slice 09 | `git diff --check`, doc review | PLANNED |
| REQ-013 | Static preflight reports missing, stale, duplicate or mismatched image contracts before live artifact mutation. | acceptance | static preflight | planned Slice 04 | failure-mode tests | PLANNED |
| REQ-014 | Selected service profile determines required image inventory. | acceptance | service-profile/Compose mapping | planned Slice 03 | default/non-default profile tests | PLANNED |
| REQ-015 | Compose image references and artifact contracts cannot silently diverge. | acceptance | Compose repository, contract alignment | planned Slice 03 | alignment tests | PLANNED |
| REQ-016 | All supported image overrides resolve to the same effective image reference in both paths. | acceptance | composition and artifact/Compose consumers | planned Slice 03 | all override tests | PLANNED |
| REQ-017 | Missing build contexts fail before `docker build` is attempted. | acceptance / safety | local storage port, build adapter | planned Slice 02/03/05 | missing-context test with publisher mock | PLANNED |
| REQ-018 | Untagged or implicit-`latest` images fail closed. | acceptance | domain contract | planned Slice 01 | invalid-tag tests | PLANNED |
| REQ-019 | Failed live artifact readiness prevents image publication and dependent deployment. | acceptance / safety | artifact/setup/deployment orchestration | planned Slice 06 | phase-stop tests; optional live evidence | PLANNED |
| REQ-020 | Successful artifact readiness produces redacted evidence identifying contracts, targets and check status. | acceptance / observability | result/evidence adapters | planned Slice 07/08 | evidence schema/redaction tests | PLANNED |
| REQ-021 | Static checks remain non-mutating; live checks are consent-gated and use bounded timeouts. | acceptance / resilience | preflight/readiness adapters | planned Slice 04/05/08 | static mocks; timeout/consent tests | PLANNED |
| REQ-022 | Native Linux and WSL2 host-preflight behavior from Issue #218 remains unchanged. | regression / architecture | host-preflight paths and tests | planned Slice 06 | native/WSL regression tests | PLANNED |
| REQ-023 | Unit, application, adapter, integration/simulation, architecture, type and full quality-gate checks pass. | quality-gate | `tests/**`, `QUALITY.md` commands | planned Slice 07/09 | exact command results | PLANNED |
| REQ-024 | Documentation and issue-level evidence are complete. | completion / evidence | `.tiny-swarm/evidence/issue-232/**`, docs | planned Slice 07/09 | required evidence-file audit | PLANNED |

## Review Gate

- Requirement Lead: Senior Requirement Engineer — required before execution
  starts and before final audit.
- System Architect Reviewer: Senior System Architect — required before
  execution starts and before final audit.
- Test / Evidence Reviewer: Senior Tester — required before final audit.
- Issue Completion Auditor: independent final decision after implementation.

No requirement may move from `PLANNED` to `VERIFIED` without implementation
evidence and a named test, check or redacted evidence artifact. Any unresolved
or unverifiable row forces `INCOMPLETE`, `BLOCKED` or `FAILED`.
