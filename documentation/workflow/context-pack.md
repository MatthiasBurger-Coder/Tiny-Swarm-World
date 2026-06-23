# Workflow Context Pack

Workflow: `sonar-s5527-tls-v1.0.0`
Workflow ID: `workflow-sonar-s5527-tls-20260623`
Branch: `fix/workflow-sonar-s5527-tls-20260623`
Created: `2026-06-23`
Status: `READY_FOR_EXECUTION`
Evidence Root: `.codex/evidence/workflow-sonar-s5527-tls-20260623/`

## Purpose

Focused context for remediating SonarCloud issue `AZ7kEe623UILYpQnQ6zD`
(`python:S5527`) in the host preflight HTTPS probe.

## Process Strand

- Active command shape: issue-specific `workflow create` plus
  workflow-execute-style slice execution.
- Execution profile: `NORMAL_PATH`.

## Affected Areas

- `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
- `tests/infrastructure/adapters/preflight/test_host_preflight_probe.py`
- `documentation/workflow/**`
- `.codex/evidence/workflow-sonar-s5527-tls-20260623/**`

## Forbidden Areas

- live infrastructure mutation
- LXD, Incus, LXC, Docker Swarm, compose, or service bootstrap commands
- domain model changes
- application orchestration changes
- SonarCloud issue mutation through credentials
- push, pull request creation, merge, or branch cleanup

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior Tester
- Senior Workflow Architect

## Conditional Roles

- Security reviewer for TLS verification assertions.
- Senior DevOps only if quality tooling fails for environment reasons.

## Quality Commands

Targeted:

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe`
- `python3 tools/quality_gate.py test`
- `git diff --check`

Required final when practical:

- `python3 tools/quality_gate.py quality`

## Governing Inputs

- `AGENTS.md` hash `335a60cd362e40090b09fdd9b982cfce87912aae`
- `QUALITY.md` hash `17002150bab9f168eb60be85d55b7a0c1cb441e5`
- `.agents/orchestrator/routing-rules.md` hash `0ae51d5d1a02c8a123bec92f546dfce51c1d17ef`
- `.agents/orchestrator/swarm-orchestrator.md` hash `c23db2d76231c6fa06ca608651e1315084a4c71d`
- `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`
- `tests/infrastructure/adapters/preflight/test_host_preflight_probe.py`

## Branch Evidence

- `git show-ref --verify --quiet refs/heads/fix/workflow-sonar-s5527-tls-20260623`
- `git branch --show-current`
- `git status --short --branch`

## Environment Note

WSL is available, but WSL Git cannot open this worktree because the `.git`
file points at a Windows `gitdir`. Python checks may still run from WSL where
they do not require Git metadata. Git status and diff evidence use the host
shell in the requested worktree.
