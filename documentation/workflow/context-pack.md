# Workflow Context Pack

Workflow: `config-contract-validation-issue-24-20260613`
Version: `1.0.0`
Branch: `feature/workflow-config-contracts-20260613`
Profile: `FULL_PATH`
Issue: `https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/24`

## Purpose

Navigation aid for the active Issue #24 configuration contract workflow. This
file does not replace `AGENTS.md`, `QUALITY.md`, ADRs, arc42, routing rules,
role files, skill files, or `documentation/workflow/workflow.md`.

## Process Strand

- Workflow authoring
- Configuration governance
- Python automation
- Platform preflight
- Deployment setup safety
- Documentation synchronization
- Automatic workflow execute work distribution
- Git worktree stream isolation
- Commit and push publication

## Affected Areas

- `documentation/workflow/**`
- Future `documentation/configuration/**`
- Future `src/tiny_swarm_world/domain/configuration/**`
- Future `src/tiny_swarm_world/application/services/configuration/**`
- Future `src/tiny_swarm_world/application/ports/configuration/**`
- Future `src/tiny_swarm_world/infrastructure/adapters/configuration/**`
- Future `src/tiny_swarm_world/infrastructure/composition.py`
- Future `infra/config/**`
- Future `tests/**`
- Future README, deployment, user guide, and arc42 documentation
- Future `.codex/evidence/slice-*-distribution.md`
- Future `.codex/evidence/slice-*-consolidation.md`

## Forbidden Areas

- Java, Maven, Spring Boot project structure
- React, TypeScript, Vite, TSX/JSX frontend project setup
- Kubernetes-first deployment model
- Windows-native setup examples for normal operation
- Committed secrets, passwords, tokens, local env files, generated evidence,
  logs, local IP addresses, user names, host-specific paths, or raw environment
  payloads
- Live LXD, Incus, LXC, Docker Swarm, compose deployment, or service bootstrap
  commands without explicit live consent

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer
- Senior Tester
- Senior Documentation Engineer
- Senior Security Sandbox Engineer

## Conditional Roles

- ADR Steward
- Quality Gate Orchestrator
- Documentation Sync
- Platform Quality Gates

## Quality Commands

Workflow creation:

```bash
git diff --check
```

Workflow execution targeted checks:

```bash
PYTHONPATH=src python3 -m unittest tests.domain.configuration
PYTHONPATH=src python3 -m unittest tests.application.services.configuration
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.configuration
PYTHONPATH=src python3 -m unittest tests.application.services.platform.test_preflight_service
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
PYTHONPATH=src python3 -m unittest tests.architecture.test_repository_hygiene
```

Required before merge when practical:

```bash
python3 tools/quality_gate.py quality
```

Execution closeout used the repository-local development environment because
system `python3` did not have Ruff installed:

```bash
.venv/bin/python tools/quality_gate.py quality
```

No live infrastructure command is part of this workflow by default.

## Execution Evidence

Status: `COMPLETED_WITH_EVIDENCE`

Pushed slice commits:

- `c819847` - S01 configuration surface inventory.
- `9bb2f75` - S02 typed configuration contract.
- `7ca805d` - S03 operator configuration sources.
- `57f36dd` - S04 preflight contract validation.
- `a0f8741` - S05 template and operator documentation.

Issue #24 acceptance criteria are mapped in
`documentation/workflow/workflow.md`.

## Hash Provenance

See `context-pack.json` for recorded file hashes.
