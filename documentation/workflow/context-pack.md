# Workflow Context Pack

## Workflow Identity

- Workflow version: `installation-integration-verification-20260523`
- Workflow branch: `docs/workflow-installation-integration-test-20260523`
- Process strand: `workflow create`
- Execution profile: `FULL_PATH`
- Created on: `2026-05-23`

## Purpose

This context pack records the governing inputs used to create the full
installation integration-verification workflow. It is a navigation aid only.
Root `AGENTS.md`, `QUALITY.md`, ADRs, arc42 and repository files remain
authoritative.

## Requirement Source

The workflow was created from the user request to define an integration test
workflow that verifies complete installation and complete functionality, with
self-remediation for blockers that are at least 90 percent solvable and Three
Amigos Q&A escalation otherwise.

Until a dedicated EPIC exists, the temporary requirement baseline is the user
request, root `AGENTS.md`, root `QUALITY.md`, `AUDIT_REPORT.md`,
`OPERATIONAL_READINESS_CHECKLIST.md`, the active workflow requirement record
and `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`.

## Verified Baseline

- The default quality gate is `python3 tools/quality_gate.py quality`.
- The default quality gate must not run live infrastructure.
- `AUDIT_REPORT.md` records missing live Multipass/Docker/Swarm evidence.
- `OPERATIONAL_READINESS_CHECKLIST.md` records open readiness checks for host,
  VM, network, Docker, Swarm, stack deployment, service reachability, smoke
  tests, observability and documentation.
- The current entrypoint exposes explicit service-level commands, not a proven
  full-installation command.
- Slice 01 defines live consent, refusal, evidence bundle, redaction,
  credential-source and resource-gating contracts for later implementation
  slices.

## Affected Areas

- `documentation/workflow`
- `OPERATIONAL_READINESS_CHECKLIST.md`
- `README.md`
- `documentation`
- `src/tiny_swarm_world`
- `infra/config`
- `infra/compose`
- `infra/prepare`
- `tools`
- `tests`

## Forbidden Areas Without Refinement

- `src/main/java/**`
- Windows-native runtime support
- default CI execution of live Multipass or Docker Swarm
- committed secrets or hardcoded credentials
- implicit destructive VM, stack or network cleanup
- live Multipass execution before explicit live-run approval
- live Docker Swarm execution before explicit live-run approval
- netplan or socat mutation before explicit live-run approval
- service bootstrap before explicit live-run approval

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer
- Senior Tester
- Senior DevOps Engineer
- Senior Security Sandbox Engineer
- Senior Documentation Engineer

## Conditional Roles

- Senior Workflow Architect when slice dependency changes are requested.
- Release and Branch Governance before commit, push or PR.
- Security Threat Modeling if secret handling or exposed service defaults
  change.

## Quality Commands

```bash
git diff --check
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

Workflow-creation checks:

```bash
git diff --check
python3 -m json.tool documentation/workflow/context-pack.json
```

Live integration commands are planned artifacts and are not current quality-gate
commands until their implementation slice adds them.

## Governing Hashes

| Path | SHA-256 |
|---|---|
| `AGENTS.md` | `6c0995195e99a2a748ad63d065706c35341977388d3c1c4402a548b388a4755e` |
| `QUALITY.md` | `d327e4060ff1729f17ffde844b1a2d6208fe203e149ae9d1af185bef0aed2155` |
| `AUDIT_REPORT.md` | `b6714f0898a5ae2eca750516e920a1f412584f43ebc6e195b5d5d61c741c0816` |
| `OPERATIONAL_READINESS_CHECKLIST.md` | `d8e54cd328674c8ce4e6237abadf86346f5f00a0e6333677e2214881e159ddd7` |
| `.agents/skills/workflow-authoring/SKILL.md` | `087658240296e3b1ec74205c60a96a9a4c67a17cf653f7867e6f316bd9afa94e` |
| `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md` | `23de7d9aac9d2694eae26fac2765d65f369c101ac348dac24d5f3bbe9e2d3ba4` |
| `.agents/skills/quality-gate-orchestrator/SKILL.md` | `3f9ef8278091f7781eacd58d000675fa6a996d81f96802a0abd37cc2a821d40f` |
| `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc` | `e93d07dc6ce9485208a40d77b6a2c52a5d5442f36845192eac0963a86dc00297` |
| `src/tiny_swarm_world/__main__.py` | `543c594c9df79faf04e83abcdc1182f05771c16494d48dd5a30cee73a05d2947` |

## Staleness Rules

This context pack is stale when:

- any recorded governing hash changes;
- `documentation/workflow/**` changes outside the active workflow branch;
- `AGENTS.md` or `QUALITY.md` changes;
- live integration commands are implemented without updating this workflow;
- mandatory service scope changes;
- secret handling or destructive cleanup policy changes;
- arc42 runtime, deployment, quality or risk sections are updated without
  checking this workflow.
