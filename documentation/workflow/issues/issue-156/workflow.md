# Workflow: Issue #156 — Central Direct Docker Published Ports

Workflow ID: `issue-156-20260809`

Workflow version: `issue-156-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #156](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/156)

## Executive Summary

Make directly published Docker ports resolve from the central registry while
preserving image-specific internal targets. The workflow covers configuration,
Compose rendering, direct URLs/health checks and evidence, but does not
implement Traefik routing or provider/bootstrap changes.

## Target Picture

`infra/config/ports.yaml` is the effective source of truth for direct external
ports. Every active direct Compose port is classified as registry-backed,
ingress-owned, compatibility or deferred; rendered `published` values use the
effective mapping while `target` remains image-compatible. Direct health/URL
and evidence projections consume the same map, and RabbitMQ/unsupported legacy
messaging artifacts are absent from the active path.

## Requirement Clarification Record

- Original request: execute #156 after #163 and before #197.
- Interpreted intent: author the complete implementation workflow for the
  direct published-port correctness issue.
- Change type: deployment rendering/configuration correctness.
- Affected process strand: `workflow-create-to-workflow-execute`.
- Affected architecture areas: port registry domain, Compose repository,
  deployment/access model, service metadata, tests and arc42 deployment view.
- Requirements: [requirement matrix](requirement-matrix.md).
- Assumptions: current issue body is authoritative; absent Prometheus/Grafana
  compose assets are classified before implementation, never invented silently.
- Non-goals: Incus/LXC, Docker installation, Swarm bootstrap, install order,
  Traefik redesign, local DNS/hosts, RabbitMQ and live deployment.
- Risks: internal target/external published inversion, duplicate port ownership,
  stale URLs or evidence, and config files that describe compatibility rather
  than active direct publication.
- Open questions: none blocking; any new ownership/route decision requires a
  System Architect decision and, if durable, an ADR before implementation.
- Confidence: 94%; decision `READY_FOR_WORKFLOW`.

## Verified Baseline

- Baseline commit: `b8c64eaa50839fcbf4581ca819286ad13ee88300`.
- The repository contains `infra/config/ports.yaml`, `services.yml`, Compose
  files and `ComposeFileRepositoryYaml` with `_DIRECT_PUBLISHED_PORT_IDS` and
  resolver logic.
- Existing tests already distinguish registry-backed, compatibility and
  ingress published ports; the workflow must extend those contracts rather
  than replace them blindly.

## Scope and Non-Goals

In scope: inventory, central mapping contract, direct Compose rendering,
effective URL/health/evidence projection, negative legacy checks, tests,
documentation synchronization and completion evidence.

Out of scope: live stacks, Portainer mutation, Incus/LXC, Docker/Swarm
bootstrap, Traefik route design, local DNS, host networking and RabbitMQ.

## Python Automation and Frontend Assessment

- Python automation: `FULL_PATH`; application uses ports and infrastructure
  owns YAML/Compose details.
- Frontend/browser: `NOT_APPLICABLE`; dashboard HTML is only an evidence
  consumer and browser React review is forbidden.
- Console/status UI: only indirect evidence output; no dedicated UI slice.

## Resilience and Safety Requirements

Port resolution must fail clearly on unknown mapping or ambiguous ownership;
internal targets cannot be rewritten from external defaults. The workflow uses
mocked repositories/clients and never requires a live Docker/Swarm run.

## Ordered Slices

### Slice 01 — Inventory ports, owners and requirement matrix

Purpose: enumerate every direct published port producer, classify occurrences,
freeze the expected mapping and verify the #163 handoff.

Prerequisites: `I163-S05` is `PASS`; clean isolated worktree.

```yaml
slice_id: I156-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [infra/config/ports.yaml, infra/config/services.yml, infra/config/compose/**, src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py, documentation/workflow/issues/issue-156/requirement-matrix.md]
affected_modules: [port registry, Compose stacks, deployment access model]
affected_contracts: [direct-published-port inventory, target-vs-published classification]
dependencies: [I163-S05]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-156/**]
contract_locks: [I156-port-inventory, I156-legacy-classification]
architecture_locks: [direct-port-only-scope]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review deployment and quality sections
  adr: review existing port-ownership decisions; do not invent one
stop_conditions: ["missing #163 audit", "unclassified producer", "ambiguous owner", "live deployment required"]
```

Done criteria: every Compose/config occurrence is classified; required service
IDs and target ports are recorded; absent services and compatibility values are
explicitly distinguished from missing implementation.

Verification/evidence: port inventory, matrix and baseline evidence under
`.tiny-swarm/evidence/issue-156/`.

### Slice 02 — Stabilize the central resolution contract

Purpose: define or repair the single registry-backed mapping path used by
rendering and projections, including unknown/optional mapping behavior.

Prerequisites: I156-S01. Allowed writes: domain/ports, repository adapter,
application ports and focused tests only.

```yaml
slice_id: I156-S02
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Python Automation Developer, Senior Requirement Engineer, Senior Tester]
affected_files: [src/tiny_swarm_world/domain/network/port_forwarding_plan.py, src/tiny_swarm_world/application/ports/repositories/port_port_registry_repository.py, src/tiny_swarm_world/infrastructure/adapters/repositories/port_registry_yaml_repository.py, src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py, tests/domain/network/**, tests/infrastructure/adapters/repositories/test_port_registry_yaml_repository.py]
affected_modules: [PortRegistry, ServicePortMapping, ComposeFileRepositoryYaml]
affected_contracts: [central published-port resolution, safe mapping lookup, internal target preservation]
dependencies: [I156-S01]
parallel_group: SERIAL-CONTRACT
file_locks: [src/tiny_swarm_world/domain/network/**, src/tiny_swarm_world/application/ports/repositories/port_port_registry_repository.py, src/tiny_swarm_world/infrastructure/adapters/repositories/port_registry_yaml_repository.py, src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py, tests/domain/network/**, tests/infrastructure/adapters/repositories/test_port_registry_yaml_repository.py]
contract_locks: [I156-registry-resolution]
architecture_locks: [domain-independent-of-yaml-and-compose]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_port_registry_yaml_repository]
  required: []
documentation:
  arc42: update only if verified ownership/resolution responsibility changes
  adr: no new ADR unless ownership decision is durable
stop_conditions: [domain imports infrastructure, target/published inversion, unknown mapping silently accepted]
```

Done criteria: one explicit contract resolves external ports; internal target
ports remain independent; error/optional semantics are testable.

Verification/evidence: contract tests and architecture import checks.

### Slice 03 — Apply registry ports to core service stacks

Purpose: update direct Compose service definitions/resolution for Portainer,
Jenkins, SonarQube and Nexus, including optional Nexus Docker ports.

Prerequisites: I156-S02. This slice is parallel-eligible with I156-S04 only in
isolated worktrees because the Compose files are disjoint; the shared resolver
contract is frozen.

```yaml
slice_id: I156-S03
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester]
affected_files: [infra/config/compose/portainer/docker-compose.yml, infra/config/compose/jenkins/docker-compose.yml, infra/config/compose/sonarqube/docker-compose.yml, infra/config/compose/nexus/docker-compose.yml, tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py]
affected_modules: [core service Compose stacks]
affected_contracts: [Portainer/Jenkins/SonarQube/Nexus direct published ports]
dependencies: [I156-S02]
parallel_group: P156-COMPOSE
file_locks: [infra/config/compose/portainer/**, infra/config/compose/jenkins/**, infra/config/compose/sonarqube/**, infra/config/compose/nexus/**]
contract_locks: [I156-registry-resolution, I156-core-published-ports]
architecture_locks: [internal-target-port-preservation]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml]
  required: []
documentation:
  arc42: no change unless port ownership facts change
  adr: none
stop_conditions: [legacy external default remains active, target changed accidentally, duplicate published port]
```

Done criteria: expected central values are rendered; image targets remain
compatible; tests cover enabled/optional direct ports.

### Slice 04 — Apply registry ports to messaging, observability and gateway stacks

Purpose: update Pulsar, Traefik/gateway, Swagger and any verified
observability/service-access Compose assets; classify Prometheus/Grafana when
no active asset exists.

Prerequisites: I156-S02. Parallel-eligible with I156-S03 with isolated files.

```yaml
slice_id: I156-S04
profile: FULL_PATH
owner: Senior DevOps Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [infra/config/compose/pulsar/docker-compose.yml, infra/config/compose/traefik/docker-compose.yml, infra/config/compose/swagger/docker-compose.yml, infra/config/compose/service-access/docker-compose.yml, infra/config/compose/infisical/docker-compose.yml, infra/config/services.yml, tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py]
affected_modules: [Pulsar, gateway, Swagger, service-access, Infisical Compose configuration]
affected_contracts: [Pulsar direct ports, gateway ingress ownership, unsupported messaging exclusion]
dependencies: [I156-S02]
parallel_group: P156-COMPOSE
file_locks: [infra/config/compose/pulsar/**, infra/config/compose/traefik/**, infra/config/compose/swagger/**, infra/config/compose/service-access/**, infra/config/compose/infisical/**, infra/config/services.yml]
contract_locks: [I156-registry-resolution, I156-messaging-model, I156-ingress-ownership]
architecture_locks: [Pulsar-not-RabbitMQ, Traefik-public-ownership]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml]
  required: []
documentation:
  arc42: review deployment/quality port ownership
  adr: preserve existing ingress/service-access ADRs
stop_conditions: [RabbitMQ port generated, gateway ownership inverted, absent service silently invented]
```

Done criteria: Pulsar direct ports use the registry; gateway/Swagger values are
correct; absent Prometheus/Grafana paths are recorded as a traceability result.

### Slice 05 — Align URLs, health checks and effective evidence

Purpose: make direct generated URLs, readiness checks and published-port
evidence consume the same effective map used by Compose rendering.

Prerequisites: I156-S03 and I156-S04.

```yaml
slice_id: I156-S05
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Requirement Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py, src/tiny_swarm_world/application/services/deployment/write_effective_access_model_evidence.py, src/tiny_swarm_world/application/services/deployment/service_stack_plan.py, src/tiny_swarm_world/application/services/deployment/verify_swarm_service_readiness.py, tests/application/services/deployment/test_write_effective_access_model_evidence.py, tests/integration/test_nexus_routing.py, tests/integration/test_sonarqube_routing.py, tests/integration/test_infisical_routing.py]
affected_modules: [direct URL projection, readiness, effective access evidence]
affected_contracts: [one effective published-port map for render/URL/health/evidence]
dependencies: [I156-S03, I156-S04]
parallel_group: SERIAL-INTEGRATION
file_locks: [src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py, src/tiny_swarm_world/application/services/deployment/**, tests/application/services/deployment/**, tests/integration/**]
contract_locks: [I156-effective-port-map]
architecture_locks: [application-depends-on-ports]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_write_effective_access_model_evidence]
  required: []
documentation:
  arc42: review runtime/deployment evidence wording
  adr: none unless ownership changes
stop_conditions: [URL uses stale literal, evidence claims live state, duplicate resolver path]
```

Done criteria: render, URL/health and evidence projections agree for all
enabled direct ports and retain explicit unavailable/blocked states.

### Slice 06 — Remove or classify unsupported legacy direct-port artifacts

Purpose: clean active legacy published ports and messaging metadata without
removing valid image targets or compatibility documentation.

Prerequisites: I156-S05. Allowed writes are limited to inventory-approved
config/docs/tests.

```yaml
slice_id: I156-S06
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Requirement Engineer, Senior DevOps Engineer, Senior Tester]
affected_files: [infra/config/services.yml, infra/config/compose/**, documentation/system/network.adoc, documentation/arc42/07_deployment_view.adoc, tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py]
affected_modules: [legacy port classification, messaging metadata]
affected_contracts: [no RabbitMQ active path, no stale external defaults, compatibility classification]
dependencies: [I156-S05]
parallel_group: SERIAL-CLEANUP
file_locks: [infra/config/services.yml, infra/config/compose/**, documentation/system/network.adoc, documentation/arc42/07_deployment_view.adoc]
contract_locks: [I156-legacy-exclusion]
architecture_locks: [no-traefik-redesign, no-provider-change]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: update only verified facts
  adr: no new ADR from cleanup alone
stop_conditions: [false positive removes internal target, compatibility state unclear, source behavior expands scope]
```

Done criteria: every removed value has a requirement trace; internal targets
remain; negative checks prove unsupported paths are not generated.

### Slice 07 — Full port contract and regression verification

Purpose: cover all required service mappings, targets, optional ports,
negative RabbitMQ checks, URLs, health and evidence with deterministic tests.

Prerequisites: I156-S06.

```yaml
slice_id: I156-S07
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Python Automation Developer, Senior System Architect, Senior Requirement Engineer]
affected_files: [tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py, tests/infrastructure/adapters/repositories/test_port_registry_yaml_repository.py, tests/application/services/deployment/test_write_effective_access_model_evidence.py, tests/integration/**, .tiny-swarm/evidence/issue-156/test_results.md]
affected_modules: [port contract regression suite]
affected_contracts: [all REQ-156 mappings and negative cases]
dependencies: [I156-S06]
parallel_group: SERIAL-QUALITY
file_locks: [tests/**, .tiny-swarm/evidence/issue-156/**]
contract_locks: [I156-all-port-acceptance]
architecture_locks: [mocked-no-live-deploy]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: quality/deployment expectations checked
  adr: none
stop_conditions: [any required mapping untested, target inversion, live command required, quality failure unclassified]
```

Done criteria: all matrix rows map to passing checks or explicit blockers;
local quality state is complete and no live claim is made.

### Slice 08 — Synchronize deployment documentation and arc42

Purpose: update only verified direct-port ownership, target/published
terminology and evidence semantics in existing documentation.

Prerequisites: I156-S07. Allowed writes: documentation files named by the
inventory; no new ADR without an explicit decision.

```yaml
slice_id: I156-S08
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers: [Senior System Architect, Senior Requirement Engineer, Senior Tester]
affected_files: [documentation/system/network.adoc, documentation/user_guide/installation.adoc, documentation/arc42/07_deployment_view.adoc, documentation/arc42/10_quality_requirements.adoc]
affected_modules: [deployment documentation]
affected_contracts: [registry-backed direct ports, local-vs-live evidence wording]
dependencies: [I156-S07]
parallel_group: SERIAL-DOCUMENTATION
file_locks: [documentation/system/network.adoc, documentation/user_guide/installation.adoc, documentation/arc42/07_deployment_view.adoc, documentation/arc42/10_quality_requirements.adoc]
contract_locks: [I156-doc-port-contract]
architecture_locks: [planned-vs-implemented]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: synchronize verified deployment/quality facts
  adr: reference existing decisions only
stop_conditions: [docs claim live success, docs contradict source, new route/provider behavior appears]
```

Done criteria: docs match verified code/config and clearly separate internal
targets, external published ports and live evidence.

### Slice 09 — Evidence package and independent completion audit

Purpose: audit every requirement, changed file, test, quality gate and scope
boundary before releasing #197.

Prerequisites: I156-S08.

```yaml
slice_id: I156-S09
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Senior Documentation Engineer]
affected_files: [.tiny-swarm/evidence/issue-156/**]
affected_modules: [issue completion evidence]
affected_contracts: [issue completion discipline, direct-port acceptance]
dependencies: [I156-S08]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-156/**]
contract_locks: [I156-completion-decision]
architecture_locks: [auditor-independent-from-implementer]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed/no-change or synchronized status
  adr: final existing-reference status
stop_conditions: [open mapping, missing evidence, unverified live/external claim, failed gate not classified]
```

Done criteria: auditor decision is `PASS`, `INCOMPLETE` or `BLOCKED`; only
`PASS` permits the chain to #197.

## Dependency Graph

```text
I163-S05 -> I156-S01 -> I156-S02 -> { I156-S03, I156-S04 }
{ I156-S03, I156-S04 } -> I156-S05 -> I156-S06 -> I156-S07 -> I156-S08 -> I156-S09
```

I156-S03 and I156-S04 may run in isolated worktrees after I156-S02; all later
slices are serialized.

## Parallel Execution

- Can this workflow run in parallel? Partially: only S03/S04 after S02.
- Conflicting workflows: any direct-port, Traefik, service-access or Compose
  workflow changing the same registry/resolver/config files.
- Shared files: registry/resolver contract, Compose repository tests,
  effective-access evidence and arc42 deployment documentation.
- Shared infrastructure: none; live Docker/Swarm/Portainer is prohibited.
- Requires isolated worktree: yes for every slice; mandatory for S03/S04.
- Requires serialized live validation: not applicable by default.
- Merge-order constraints: S03/S04 converge before S05; S09 precedes #197.

## Automatic Work Distribution Policy

The executor must analyze each slice for backend, frontend, tests, runtime,
documentation, quality, architecture and security streams, use real Codex
subagents where supported or explicit role fallback, and require distribution
and consolidation evidence under `.codex/evidence/`. Codex is final
integration owner. Do not parallelize overlapping resolver/tests, unclear
ownership, generated files, contradictory requirements, live actions,
secrets ambiguity or weakened guards.

## Git Worktree Execution Rule

Every slice uses an isolated worktree. Workers verify the chain branch and
declared locks, stay within scope and never merge directly. Suggested stream
branches end in `-slice-03-compose` and `-slice-04-compose`; Codex merges only
after evidence and checks.

## Role and Ownership Map

| Responsibility | Owner |
|---|---|
| requirement matrix and inventory | Senior Requirement Engineer |
| port ownership and hexagonal boundary | Senior System Architect |
| YAML/Compose and access projection | Senior Python Automation Developer |
| config/contract tests and gates | Senior Tester |
| deployment docs/arc42 synchronization | Senior Documentation Engineer |
| final decision | Issue Completion Auditor |

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-156/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-156/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-156/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md` plus inventory/port-map evidence.
- Requirement Lead review: S01 and S09.
- System Architect Reviewer review: S02/S05/S06 and S09.
- Test / Evidence Reviewer review: S07 and S09.
- Issue Completion Auditor review: S09.
- DONE blocking rule: any open or unverified requirement forces `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use the exact `QUALITY.md` gates and `git diff --check`. Local quality is not
live Docker, Swarm, Portainer or Sonar evidence.

## Documentation Synchronization and Arc42 Check Status

Arc42 deployment, quality and risk sections plus existing port/ingress ADRs
were reviewed. S08 updates only verified drift. No automatic ADR creation is
authorized.

## Stop Conditions and Uncertainty Escalation

Stop for ambiguous port ownership, target/published inversion, unclassified
legacy messaging, live command requirements, missing external evidence,
quality ambiguity or scope expansion. Escalate ownership to the System
Architect, requirement drift to the Requirement Engineer, test failures to the
Senior Tester and documentation contradiction to the Documentation Engineer.

## Definition of Done

All fourteen matrix requirements are mapped to code/config/docs and checks;
direct ports, targets, URLs, health and evidence agree; required local gates
are recorded; no forbidden behavior changed; S09 is `PASS`.

## Handoff to workflow execute

Promote this indexed workflow explicitly only after I163-S05. Run S01/S02,
then the isolated S03/S04 pair if Three Amigos reconfirms independence, then
S05–S09 serially. Do not start #197 before I156-S09 is `PASS`.
