# Issue #232 Requirement Matrix

Issue: [#232 Implement complete artifact and container-image installation preflight](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/232)
Workflow: `issue-232-20260808`
Status at workflow creation: `READY_FOR_WORKFLOW`

This matrix is the implementation gate. It records issue requirements,
implementation evidence and named verification evidence. `VERIFIED_LOCAL`
means the repository behavior is locally verified; it does not claim live
installation success. `OPEN` or `IN_PROGRESS` rows block `DONE`.

| ID | Requirement from Issue #232 | Type | Files likely affected | Implementation evidence | Test/evidence verification | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Define a canonical, profile-aware artifact image inventory for all images required by the selected Compose/service profile. | functional / architecture | `domain/artifacts/**`, Compose repository, service-profile contracts | Domain inventory and profile-aware Compose repository | `tests/domain/artifacts/**`, `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | VERIFIED_LOCAL |
| REQ-002 | Every deployed image has exactly one matching image contract and every required contract is consumed by deployment. | functional / quality | domain contracts, Compose repository, composition | Profile inventory validation and default contract alignment | Compose inventory/alignment tests | VERIFIED_LOCAL |
| REQ-003 | Image references do not allow implicit `latest` and follow the approved tag or digest strategy. | security / functional | `container_image_contract.py` | Immutable tag/digest validation | Domain invalid-reference tests | VERIFIED_LOCAL |
| REQ-004 | `build` contracts resolve to an existing approved repository-local context; `pull` contracts have an immutable reference and declared upstream expectations. | functional / safety | domain contract, `PortLocalFileStorage`, adapters | Approved context resolution and directory port | Static preflight and local-storage tests | VERIFIED_LOCAL |
| REQ-005 | Reject duplicate artifact target IDs, duplicate logical build contexts and conflicting image references. | functional / quality | domain inventory and contract validation | Inventory duplicate/conflict validation | Domain artifact inventory tests | VERIFIED_LOCAL |
| REQ-006 | Apply every supported `TSW_*_IMAGE` override consistently to Compose rendering and artifact preparation. | functional | composition, Compose repository, artifact services | Shared override resolution for all supported image contexts | Composition override matrix tests | VERIFIED_LOCAL |
| REQ-007 | Add a non-mutating static artifact-contract check to installation preflight. | functional / safety | preflight service, CLI/composition | `StaticArtifactContractPreflight` wired before mutating phases | Static preflight success/failure/no-mutation tests | VERIFIED_LOCAL |
| REQ-008 | After required Nexus/registry bootstrap and before image build/pull/push, check manager Docker readiness, endpoint reachability, repository readiness, storage/build inputs and public pull prerequisites. | functional / resilience | readiness ports/adapters, artifact workflow | Seven-target port, bounded adapters, bootstrap/gate/prepare phase order | Readiness adapter tests; setup phase-order and gate tests | VERIFIED_LOCAL |
| REQ-009 | Return typed machine-readable results with safe evidence and remediation; never expose credentials, tokens, command output or secret values. | security / observability | result models, adapters, evidence | Typed readiness/preflight results, live state enum and safe evidence | Redaction/schema tests; evidence package | VERIFIED_LOCAL |
| REQ-010 | Stop setup before `artifacts prepare`, `artifacts verify` or dependent deployment when a mandatory prerequisite fails. | functional / safety | artifact/setup/deployment orchestration | Fail-closed `ArtifactReadinessGate` and setup phase stop contract | Artifact gate and setup downstream-stop tests | VERIFIED_LOCAL |
| REQ-011 | Keep domain code free of filesystem, Docker, HTTP, YAML and command-runner concerns; use ports and infrastructure adapters for live checks. | architecture | domain, application ports, adapters, composition | Port-based application orchestration and infrastructure-only probes | Import-linter, architecture tests and role review | VERIFIED_LOCAL |
| REQ-012 | Update artifact, installation, configuration and troubleshooting documentation. | documentation | `documentation/**`, arc42 | Scheduled for Slice 09 documentation synchronization | Pending documentation diff and review | OPEN |
| REQ-013 | Static preflight reports missing, stale, duplicate or mismatched image contracts before live artifact mutation. | acceptance | static preflight | Typed issue codes, remediation and mandatory static check | Static preflight failure-mode tests | VERIFIED_LOCAL |
| REQ-014 | Selected service profile determines required image inventory. | acceptance | service-profile/Compose mapping | Profile-filtered inventory generation | Default and non-default profile tests | VERIFIED_LOCAL |
| REQ-015 | Compose image references and artifact contracts cannot silently diverge. | acceptance | Compose repository, contract alignment | Effective Compose image resolution uses shared contract inventory | Compose alignment tests | VERIFIED_LOCAL |
| REQ-016 | All supported image overrides resolve to the same effective image reference in both paths. | acceptance | composition and artifact/Compose consumers | One shared override map and resolver | All supported override tests | VERIFIED_LOCAL |
| REQ-017 | Missing build contexts fail before `docker build` is attempted. | acceptance / safety | local storage port, build adapter | Static directory check precedes artifact mutation | Missing-context publisher/preflight tests | VERIFIED_LOCAL |
| REQ-018 | Untagged or implicit-`latest` images fail closed. | acceptance | domain contract | Reference validation rejects untagged and implicit latest | Invalid-tag tests | VERIFIED_LOCAL |
| REQ-019 | Failed live artifact readiness prevents image publication and dependent deployment. | acceptance / safety | artifact/setup/deployment orchestration | Readiness gate returns mandatory failed preflight and stops later phases | Unknown/failure setup gate tests | VERIFIED_LOCAL |
| REQ-020 | Successful artifact readiness produces redacted evidence identifying contracts, targets and check status. | acceptance / observability | result/evidence adapters | Per-target live evidence includes status, scope, state and remediation; consent-missing boundary is recorded in `live_acceptance.md` | Readiness evidence serialization/redaction tests; evidence package | VERIFIED_LOCAL |
| REQ-021 | Static checks remain non-mutating; live checks are consent-gated and use bounded timeouts. | acceptance / resilience | preflight/readiness adapters | Static port path and bounded readiness requests; setup outer consent guard; Slice 08 records missing consent without running probes | Static no-mutation, timeout and consent tests; `live_acceptance.md` | VERIFIED_LOCAL |
| REQ-022 | Native Linux and WSL2 host-preflight behavior from Issue #218 remains unchanged. | regression / architecture | host-preflight paths and tests | No host adapter changes in Slice 06/07; prior regression suite retained | Full quality gate and host-preflight tests | VERIFIED_LOCAL |
| REQ-023 | Unit, application, adapter, integration/simulation, architecture, type and full quality-gate checks pass. | quality-gate | `tests/**`, `QUALITY.md` commands | Full verification-policy, lint, architecture, typecheck and test gate passed after Slice 08 evidence changes | `test_results.md`; `python3 tools/quality_gate.py quality`: 1,623 tests, 28 skipped | VERIFIED_LOCAL |
| REQ-024 | Documentation and issue-level evidence are complete. | completion / evidence | `.tiny-swarm/evidence/issue-232/**`, docs | Six-file issue evidence package is being assembled | Evidence-file audit pending Slice 09/final audit | IN_PROGRESS |

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
