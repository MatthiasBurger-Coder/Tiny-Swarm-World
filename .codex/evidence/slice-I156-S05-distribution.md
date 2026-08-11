# Slice Distribution — I156-S05

Workflow: issue-156-20260809
Workflow version: issue-156-v1.0.0
Slice ID: I156-S05
Slice title: Align URLs, health checks and effective evidence

## Execution decision

- Serial integration execution after I156-S03 and I156-S04.
- Streams reviewed: Python application/infrastructure, architecture, tests, requirements, quality and evidence/security.
- No real subagent tool is visible; explicit role-based fallback review will be recorded.
- No parallel streams or worktrees: the effective port-map contract crosses Compose rendering, routing and evidence projections.
- The existing design intentionally uses routed HTTPS hostnames for URL/health projections and diagnostic fallback ports for direct access; this slice must preserve that distinction.
- Expected change: integration regression coverage for Nexus, SonarQube and Infisical proving one custom registry mapping feeds published port, preserved target, routed URLs, health target and evidence fallback.
- No live deployment, Docker/Swarm command, browser check or external SonarQube claim is in scope.

## Locks and gates

- File locks: `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`, deployment projection services, and the listed routing/evidence tests.
- Contract lock: `I156-effective-port-map`.
- Architecture lock: application code depends on ports; no direct infrastructure access is added to domain code.
- Targeted gates: the effective-access evidence test and the three routing integration tests.
- Required gate: `python3 tools/quality_gate.py quality` after implementation.

## Role review

- Senior Python Automation Developer: verify the repository's effective model is the single source consumed by Compose and evidence.
- Senior System Architect: preserve routed HTTPS semantics and internal upstream targets.
- Senior Tester: cover external published values, internal targets, health/access URLs and fallback evidence.
- Senior Requirement Engineer: map REQ-156-01, REQ-156-02, REQ-156-04, REQ-156-05 and REQ-156-14.
- Security/Evidence review: ensure no credentials, live-success claims or stale localhost URLs enter the evidence contract.

## Consolidation plan

Prefer a regression-only change if the shared effective-model path is already implemented. If a defect is found, change only the declared projection boundary, add deterministic tests, rerun targeted and full gates, and record local/external/live verification states separately.
