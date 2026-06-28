# Skill And Agent Organigramm

## Status

```text
CURRENT_WITH_ISSUE_COMPLETION_GATES
```

## Root

The Tiny Swarm World lead authority is the project governance defined in root
`AGENTS.md`, with root `QUALITY.md` as quality authority and
`documentation/process/issue-completion-discipline.md` as the authority for
issue-driven completion status.

## Primary Routing

- Python automation: `senior-python-automation-developer` and Python-specific
  skills under `.agents/skills/`.
- Architecture: `senior-system-architect`, `hexagonal-architecture-expert` and
  project architecture skills.
- Workflow and process: `senior-workflow-architect`, workflow skills and S3D
  orchestration.
- Documentation and registry: `senior-documentation-engineer` and
  `skill-registry-conflict-auditor`.
- Issue completion: `issue-completion-auditor`, Requirement Lead, System
  Architect Reviewer and Test / Evidence Reviewer.
- Quality: `senior-tester`, `platform-quality-gates` and `quality-gate`.
- Console/status UI: `frontend-developer`, `console-status-ui-developer` and
  `terminal-status-dashboard`.
- Service-boundary questions: Senior System Architect plus
  `service-decomposition-bounded-context`,
  `microservice-runtime-readiness-expert`,
  `microservice-migration-safety-gate` and `contract-governance-expert`.
- Audit and quality governance: `audit-evidence-manager`,
  `qms-light-governance-expert` and `traceability-engineer`.
- Security governance: `isms-light-security-governance-expert`,
  `owasp-asvs-local-infrastructure-expert` and
  `supply-chain-security-expert`.
- Operations, CI and release governance: `live-evidence-validation-expert`,
  `branch-ci-governance-expert` and
  `release-baseline-governance-expert`.
- Documentation audience governance: `documentation-audience-architect`.

## Boundaries

Tiny Swarm World is not a Spring Boot application, not a React frontend
project, not forensic analytics, and not Kubernetes-first. Docker Swarm remains
the current runtime target; Kubernetes guidance is future-runtime review only.
