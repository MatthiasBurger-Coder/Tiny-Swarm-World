# Slice 01 Distribution

Workflow ID: `workflow-project-paths-di-20260627`
Workflow version: `workflow-project-paths-di-v1.0.0`
Slice ID: `01`
Slice title: `Baseline Audit And Path Contract Tests`

## Affected Areas

- backend: infrastructure path helpers
- tests: focused unittest coverage for path contract behavior
- architecture: confirms path ownership stays in infrastructure

## Execution Mode

Sequential.

Parallel execution is rejected because this slice establishes the test contract
that later slices depend on, and it locks `project_paths.py` plus the new
`tests/infrastructure/test_project_paths.py` file.

## Streams

- tests: Senior Tester
- backend review: Senior Python Automation Developer
- architecture review: Senior System Architect

Real subagents used: no.

Fallback role-based review used: yes. The main execution thread applies the
required role checks because callable subagents are not exposed in this
session.

Git worktrees used: no.

## Expected Touched Files

- `tests/infrastructure/test_project_paths.py`
- `.codex/evidence/workflow-project-paths-di-20260627/slice-01-distribution.md`
- `.codex/evidence/workflow-project-paths-di-20260627/slice-01-consolidation.md`

## Conflict Risks

- Low. The slice adds focused tests and evidence only.
- Later slices will touch the same test file, so execution remains serialized.

## Quality Gates

- `rg -n "project_paths|ProjectPaths|TSW_REPOSITORY_ROOT|TSW_INFRA_ROOT|config_root\\(|infra_root\\(|repository_root\\(|logs_root\\(" src tests documentation infra README.md AGENTS.md QUALITY.md`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_project_paths`

## Consolidation Plan

Run the targeted reference search and the new focused unittest, then commit and
push only Slice 01 files when the gate passes.
