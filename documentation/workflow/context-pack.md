# Workflow Context Pack

Workflow: `console-output-issue-151-v1.0.0`
Workflow ID: `workflow-console-output-issue-151-20260621`
Branch: `fix/workflow-console-output-151-20260621`
Created: `2026-06-21`
Status: `EXECUTED_WITH_EVIDENCE`
Evidence Root: `.codex/evidence/workflow-console-output-issue-151-20260621/`

## Purpose

Focused execution context for proving issue `#143`, remediating issue `#151`,
and storing console-output evidence without touching live infrastructure.

## Process Strand

- Active command: `workflow execute`
- Execution profile: `NORMAL_PATH`

## Affected Areas

- `src/tiny_swarm_world/__main__.py`
- `tests/test_package_entrypoint.py`
- `documentation/workflow/**`
- `.codex/evidence/workflow-console-output-issue-151-20260621/**`

## Forbidden Areas

- live infrastructure mutation
- domain model changes
- application orchestration changes
- committed secrets or raw env payloads

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer impact check
- Senior Tester

## Conditional Roles

- Security reviewer for secret/redaction assertions

## Quality Commands

Targeted:

- `git diff --check`
- `PYTHONPATH=src python -m unittest tests.test_package_entrypoint`
- `PYTHONPATH=src python -m unittest tests.infrastructure.adapters.ui.test_progress_trace_ui`

Required final:

- `python3 tools/quality_gate.py test`

## Governing Inputs

- `AGENTS.md`
- `QUALITY.md`
- `documentation/workflow/installer-console-reporting-policy.md`
- `documentation/user_guide/installer-console-output.md`
- `documentation/architecture/adr-installer-console-reporting-policy.adoc`
- `.tiny-swarm/evidence/secrets/secret-inventory.json`

## Branch Evidence

- `git show-ref --verify --quiet refs/heads/fix/workflow-console-output-151-20260621`
- `git branch --show-current`
