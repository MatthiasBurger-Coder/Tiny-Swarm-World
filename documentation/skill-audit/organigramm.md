# Skill And Agent Organigramm

## Status

```text
CURRENT_AFTER_SLICE_05
```

## Root

The Tiny Swarm World lead authority is the project governance defined in root
`AGENTS.md`, with root `QUALITY.md` as quality authority.

## Primary Routing

- Python automation: `senior-python-automation-developer` and Python-specific
  skills under `.agents/skills/`.
- Architecture: `senior-system-architect`, `hexagonal-architecture-expert` and
  project architecture skills.
- Workflow and process: `senior-workflow-architect`, workflow skills and S3D
  orchestration.
- Documentation and registry: `senior-documentation-engineer` and
  `skill-registry-conflict-auditor`.
- Quality: `senior-tester`, `platform-quality-gates` and `quality-gate`.
- Console/status UI: `frontend-developer`, `console-status-ui-developer` and
  `terminal-status-dashboard`.
- Service-boundary questions: Senior System Architect plus
  `service-decomposition-bounded-context`,
  `microservice-runtime-readiness-expert`,
  `microservice-migration-safety-gate` and `contract-governance-expert`.

## Boundaries

Tiny Swarm World is not a Spring Boot application, not a React frontend
project, not forensic analytics, and not Kubernetes-first. Docker Swarm remains
the current runtime target; Kubernetes guidance is future-runtime review only.
