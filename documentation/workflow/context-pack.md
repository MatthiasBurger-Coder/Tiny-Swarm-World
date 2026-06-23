# Workflow Context Pack

Workflow: `sonar-s2083-path-v1.0.0`
Workflow ID: `workflow-sonar-s2083-path-20260623`
Branch: `fix/workflow-sonar-s2083-path-20260623`
Created: `2026-06-23`
Status: `IN_PROGRESS`
Evidence Root: `.codex/evidence/workflow-sonar-s2083-path-20260623/`

## Purpose

Focused workflow-execute context for SonarCloud Blocker issue
`AZ7kEe0S3UILYpQnQ6zA`.

## Process Strand

- Active command: `workflow execute`
- Execution profile: `NORMAL_PATH`

## Affected Areas

- `tests/application/services/deployment/test_secret_management.py`
- `documentation/workflow/**`
- `.codex/evidence/workflow-sonar-s2083-path-20260623/**`

## Forbidden Areas

- live infrastructure mutation
- production secret-management behavior changes
- committed secrets or raw env payloads

## Required Roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior React Frontend Developer impact check
- Senior Tester

## Quality Commands

Targeted:

- `PYTHONPATH=src python -m unittest tests.application.services.deployment.test_secret_management`

Required final:

- `python3 tools/quality_gate.py test`

## Branch Evidence

- `git show-ref --verify --quiet refs/heads/fix/workflow-sonar-s2083-path-20260623`
- `git branch --show-current`
