# Workflow Context Pack: Issue #154

This file is a navigation aid for `issue-154-20260808`. Root `AGENTS.md`,
`QUALITY.md`, process rules, ADRs, Arc42, the active workflow and source files
remain authoritative.

## Active Context

- Workflow version: `issue-154-v1.0.0`
- Workflow ID: `issue-154-20260808`
- Branch: `feature/workflow-issue-154-real-cluster-phase-20260808`
- Process strand: `workflow create` -> guarded publication -> `workflow execute`
- Execution profile: `FULL_PATH`
- Status: `READY_FOR_EXECUTION`
- Requirement matrix: `.tiny-swarm/evidence/issue-154/requirement_matrix.md`
- Issue evidence path: `.tiny-swarm/evidence/issue-154/`
- Workflow evidence path: `.codex/evidence/issue-154/`

## Affected Areas

- Installation-plan domain model and `infra/config/installation-plan.yaml`.
- LXC-native Docker installation and Swarm bootstrap services, ports, DTOs and
  managed-runtime adapters.
- Platform workflow ownership and composition wiring.
- Setup phase ordering, cluster verification and generic downstream `not_run`.
- Platform, setup, plan and regression tests.
- Installation/runtime Arc42 documentation and issue completion evidence.

The referenced `PortLocalFileStorage` was inspected for context and is not an
affected file unless execution discovers a concrete Issue #154 storage gap.

## Forbidden or Guarded Areas

- No Java, Maven, Spring Boot, browser React or new microservice.
- No Issue #218 WSL2 host-preflight redesign.
- No Issue #232 artifact/image-preflight redesign.
- No host Docker as the default cluster runtime.
- No Incus, LXC, Docker, Swarm, network or service deployment during default
  local verification.
- No unapproved live mutation, credentials, join tokens, raw command output or
  unredacted evidence.
- No broad provider or composition refactor beyond phase extraction.

## Required Roles

- Senior Requirement Engineer.
- Senior System Architect.
- Senior Python Automation Developer.
- Senior Tester.
- Senior DevOps Engineer for managed-runtime and optional live-validation
  review.
- Senior Documentation Engineer for Arc42, evidence and handoff.
- Issue Completion Auditor for the independent final decision.

Conditional roles:

- Console/status UI reviewer: `NOT_APPLICABLE` unless progress presentation
  changes.
- Browser React reviewer: `FORBIDDEN_UNLESS_SEPARATE_FRONTEND_WORKFLOW`.

## Quality Commands

Authoritative commands from `QUALITY.md`, run in WSL/Linux:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
git diff --check
```

Static plan, DTO, adapter, orchestration and regression checks are
`APPLICABLE_LOCAL`. Live LXC/Incus/Docker/Swarm validation is
`APPLICABLE_LIVE` and remains `LIVE_CONSENT_MISSING` without separate
authorization. Browser checks are `NOT_APPLICABLE`; external quality is not
inferred from local results.

## Governance Hashes

The machine-readable copy in `context-pack.json` records SHA-256 hashes of the
governing inputs used during authoring. The pack is stale if any recorded hash
changes, governance files are modified, or the task scope conflicts with the
checked baseline.
