# Workflow Context Pack: Issue #232

This file is a navigation aid for `issue-232-20260808`. Repository source files,
`AGENTS.md`, `QUALITY.md`, process rules, ADRs, arc42 and the active workflow
remain authoritative.

## Active Context

- Workflow version: `issue-232-v1.0.0`
- Workflow ID: `issue-232-20260808`
- Branch: `feature/workflow-issue-232-artifact-preflight-20260808`
- Process strand: `workflow create` -> guarded publication -> `workflow execute`
- Execution profile: `FULL_PATH`
- Status: `READY_FOR_EXECUTION`
- Requirement matrix: `.tiny-swarm/evidence/issue-232/requirement_matrix.md`
- Issue evidence path: `.tiny-swarm/evidence/issue-232/`
- Workflow evidence path: `.codex/evidence/`

## Affected Areas

- Domain artifact/image contracts and profile-aware inventory.
- Application artifact/preflight services and ports.
- `src/tiny_swarm_world/application/ports/file_management/port_local_file_storage.py`.
- Compose/service-profile repositories and `TSW_*_IMAGE` resolution.
- Docker, registry and Nexus readiness adapters.
- Composition, setup/deployment phase guards and thin CLI dispatch.
- Artifact/Compose/configuration tests, architecture checks and issue evidence.
- Artifact, installation, configuration, troubleshooting and arc42 documentation.

## Forbidden or Guarded Areas

- No Java, Maven, Spring Boot, browser React or new microservice.
- No change to the Issue #218 Platform/WSL2 host boundary.
- No Incus, Docker Swarm, Compose deployment, registry bootstrap, service
  bootstrap, network mutation or credential-backed command during static/local
  verification.
- No implicit `latest`, silent Compose/artifact divergence, raw command output,
  tokens, credentials, host-specific absolute paths or unredacted evidence.
- Live readiness is explicit-consent-gated, bounded and serialized.

## Required Roles

- Senior Requirement Engineer.
- Senior System Architect.
- Senior Python Automation Developer.
- Senior Tester.
- Senior DevOps Engineer for readiness/live adapter slices.
- Senior Documentation Engineer for synchronization and handoff.
- Issue Completion Auditor for the independent final decision.

Conditional role: Console/status UI reviewer is `NOT_APPLICABLE`; no terminal
presentation or interaction changes are in the verified scope.

## Quality Commands

Authoritative commands from `QUALITY.md`, run from Linux/WSL:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
git diff --check
```

Static checks are `APPLICABLE_LOCAL`. Docker/registry/Nexus readiness is
`APPLICABLE_LIVE` and remains `LIVE_CONSENT_MISSING` or
`LIVE_PREREQUISITE_MISSING` without explicit authorization and prerequisites.
Browser checks are `NOT_APPLICABLE`; external quality state is not inferred
from local results.

## Governance Hashes

The machine-readable copy, including SHA-256 hashes of the governing inputs,
is `context-pack.json`. The pack is stale if any recorded hash changes, if
governance files are modified, or if a scope conflict is found.
