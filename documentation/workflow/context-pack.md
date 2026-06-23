# Workflow Context Pack

Workflow: `workflow-sonar-s2068-port-forwarding-v1.0.0`
Workflow ID: `workflow-sonar-s2068-port-forwarding-20260623`
Branch: `fix/workflow-sonar-s2068-port-forwarding-20260623`
Created: `2026-06-23`
Status: `EXECUTED_WITH_EVIDENCE`
Evidence Root: `.codex/evidence/workflow-sonar-s2068-port-forwarding-20260623/`

## Purpose

Focused execution context for remediating SonarCloud `python:S2068` issues
`AZ7kcUaJ8N9AxeIuoSBi`, `AZ7kcUaJ8N9AxeIuoSBj`, and
`AZ7kcUaJ8N9AxeIuoSBl` in `tests/domain/network/test_port_forwarding_plan.py`.

## Process Strand

- Active command: `workflow execute`
- Execution profile: `NORMAL_PATH`

## Affected Areas

- `tests/domain/network/test_port_forwarding_plan.py`
- `documentation/workflow/**`
- `.codex/evidence/workflow-sonar-s2068-port-forwarding-20260623/**`

## Forbidden Areas

- live infrastructure mutation
- product source behavior changes
- push, PR creation, merge, or branch cleanup

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior Tester
- Senior DevOps Engineer impact check

## Quality Commands

Targeted:

- `PYTHONPATH=src python -m unittest tests.domain.network.test_port_forwarding_plan`
- `git diff --check`

Required final:

- `python3 tools/quality_gate.py test`

## Governing Inputs

- `AGENTS.md`
- `QUALITY.md`
- `documentation/workflow/workflow.md`
- `tests/support/sonar_safe_literals.py`
- `src/tiny_swarm_world/domain/network/port_forwarding_plan.py`

## Branch Evidence

- `git branch --show-current`
- `git show-ref --verify refs/heads/fix/workflow-sonar-s2068-port-forwarding-20260623`
