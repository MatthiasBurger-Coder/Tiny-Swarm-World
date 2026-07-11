# Routing Rules

Use these rules to select roles for a slice. Prefer the smallest set that covers the actual files and risks.

## Role Routing

## Exact Command Routing

- Exact `skills update` routes to the skills-agents strand, Skill Registry Conflict Auditor, Senior Documentation Engineer as Organigramm Maintainer, and Senior Workflow Architect as Process Governance Maintainer.
- Exact `workflow create` routes to workflow create.
- Exact `workflow execute` routes to workflow execute.
- Issue completion, DONE readiness, acceptance coverage, branch completion
  audit, or "is this issue fully done" routes to
  `skills/issue-completion-auditor/SKILL.md` after implementation evidence is
  available.

Before assigning specialist roles, route every `workflow create` and
`workflow execute` request through
`skills/execution-profile-router/SKILL.md`.

The selected execution profile decides which gates are mandatory, which role
reviews are full reviews, and which reviews may be reduced to N/A impact
checks. Profile routing must not bypass root `AGENTS.md`, `QUALITY.md`, ADRs,
active workflow STOP rules, Four-Role Three Amigos participation, S3/S3D
preflight, Typed Error Router ownership, branch rules or required quality
gates. Unclear impact defaults to `FULL_PATH`.

- Python domain, application, ports, infrastructure adapters, YAML handling, command construction, VM/network automation or repository behavior routes to `roles/senior-python-automation-developer.md`.
- Java/Maven/Spring Boot project structure is retired. Requests to reintroduce
  it must stop for scope confirmation before any role routing.
- Tiny Swarm World console/status UI work routes to `skills/frontend-developer/SKILL.md`, `skills/console-status-ui-developer/SKILL.md`, and `skills/terminal-status-dashboard/SKILL.md`. Browser React, frontend state, API client integration or UI component work stops unless a separate frontend workflow verifies a frontend module, package tooling and quality gates; only then route to `roles/senior-react-frontend.md`.
- Information architecture, accessibility, visualization UX or user-flow work routes to `roles/senior-ux-designer.md`.
- Cross-module design, package boundaries, architecture tests or module restructuring routes to `roles/senior-system-architect.md`.
- Service-boundary, bounded-context, independent-runtime, deployment-readiness or no-shared-implementation reviews route by concern: bounded context to `skills/service-decomposition-bounded-context/SKILL.md`, runtime readiness to `skills/microservice-runtime-readiness-expert/SKILL.md`, migration safety to `skills/microservice-migration-safety-gate/SKILL.md`, contract governance to `skills/contract-governance-expert/SKILL.md`, and architecture ambiguity to `roles/senior-system-architect.md`.
- Bounded-context service decomposition and "technical module is not a microservice" decisions route to `skills/service-decomposition-bounded-context/SKILL.md`.
- Cross-service REST/OpenAPI, gRPC/protobuf or event contract governance routes to `skills/contract-governance-expert/SKILL.md`.
- Production microservice migration safety, rollback, strangler strategy or multi-service risk gates route to `skills/microservice-migration-safety-gate/SKILL.md`.
- Microservice runtime independence, healthcheck, observability or container-readiness evidence routes to `skills/microservice-runtime-readiness-expert/SKILL.md`.
- Test strategy, regression coverage, Python architecture checks or quality-gate design routes to `roles/senior-tester.md`.
- Requirement matrix, acceptance verification, evidence completeness or
  no-silent-scope-reduction concerns route through
  `documentation/process/issue-completion-discipline.md`,
  `skills/three-amigos-requirement-gatekeeper/SKILL.md` and
  `skills/issue-completion-auditor/SKILL.md` by phase.
- Quality or validation failures in `workflow execute` route through the Typed Error Router before any retry:
  - `ARCH_VIOLATION` routes to Root Architect escalation, `roles/senior-system-architect.md` and `skills/architecture-hexagonal/SKILL.md`.
  - `BUILD_FAILURE` routes to the responsible Python automation or frontend owner plus `roles/senior-devops.md`; Python quality-gate failures also route to `skills/quality-gate/SKILL.md`.
  - `TEST_FAILURE` routes to `roles/senior-tester.md` and the responsible slice agent.
  - `DOC_GOVERNANCE_FAILURE` routes to `roles/senior-documentation-engineer.md` and `roles/senior-requirement-engineer/SKILL.md`.
  - `LOCK_CONFLICT` routes to `roles/senior-execution-orchestrator.md`, `skills/s3d-execution-orchestrator/SKILL.md`, Senior Swarm Orchestrator coordination and Root Architect escalation.
  - `UNKNOWN_FAILURE` routes to Root Architect escalation.
- Python tooling, Docker, Kubernetes, CI, observability or deployment work routes to `roles/senior-devops.md`.
- New workflow creation, full `documentation/workflow` regeneration, slice dependency planning or planning-risk review routes to `roles/senior-workflow-architect/SKILL.md`.
- EPIC consistency, requirement drift, requirement classification, assumption tracking or requirement-to-architecture synchronization routes to `roles/senior-requirement-engineer/SKILL.md`.
- Incoming requirement gatekeeping before workflow authoring, Three Amigos review, acceptance-criteria validation, dependency/deadlock checks or `READY_FOR_WORKFLOW` versus `REQUIRES_REFINEMENT` decisions route to `skills/three-amigos-requirement-gatekeeper/SKILL.md`.
- Multi-role coordination, conflict resolution or slice planning routes to `roles/senior-swarm-orchestrator.md`.
- S3D execution orchestration, dependency graph construction, topological sorting, parallelization grouping or file/contract/module/architecture-boundary conflict locks route to `roles/senior-execution-orchestrator.md` and `skills/s3d-execution-orchestrator/SKILL.md`.
- Automatic `workflow execute` stream distribution uses this stream map:
  backend routes to Senior Python Automation Developer or the verified backend
  owner; frontend routes to console/status UI skills unless a browser frontend
  workflow is verified; tests routes to Senior Tester; runtime routes to
  Senior DevOps; documentation routes to Senior Documentation Engineer;
  quality routes to quality-gate skills and Senior Tester; architecture routes
  to Senior System Architect; security routes to Senior Security Sandbox
  Engineer and security skills.
- Protobuf contracts, streaming RPC design, request validation or gRPC compatibility route to `roles/senior-grpc-proto-specialist.md`.
- Repository checkout, workspace lifecycle, source-root preparation or large Git repositories route to `roles/senior-git-workspace-specialist.md`.
- Plugin producer handoff, plugin-side request construction or plugin-to-server communication routes to `roles/senior-plugin-integration-developer.md`.
- Documentation, skill audit material, existing workflow updates or ADR alignment notes route to `roles/senior-documentation-engineer.md`.
- Untrusted repository handling, sandboxing, safe Git operations or secret leakage risks route to `roles/senior-security-sandbox-engineer.md`.
- Performance budgets, large repository metrics, timeouts, quotas or scalability testing route to `roles/senior-performance-engineer.md`.
- Forensic-analysis storage, Joern, Code Property Graph, semantic-analysis
  artifact or scanner requests stop as outside Tiny Swarm World scope unless a
  later explicit workflow changes the project identity in root `AGENTS.md`.
- Root Architect escalation routes through the documented Root Architect
  decision path and `roles/senior-system-architect.md` until a dedicated
  Root Architect role file exists.
- Rollback governance routes to `skills/release-branch-governance/SKILL.md`,
  `skills/git-commit-preparation/SKILL.md` and `roles/senior-devops.md`.
- Quality gate classification routes to
  `skills/quality-gate-orchestrator/SKILL.md`, `skills/quality-gate/SKILL.md`
  and `roles/senior-tester.md`.
- Flowchart integrity audit routes to
  `skills/flowchart-integrity-auditor/SKILL.md`; Senior Documentation
  Engineer owns documentation synchronization and Senior System Architect owns
  architecture-governance escalation when the auditor reports a blocker.

## Escalation

Stop and report when a required file, task, symbol, schema, command or contract cannot be verified exactly.

Use `QUALITY.md` for verification commands. Optional external checks such as Sonar require documented credentials and must be reported when skipped.
