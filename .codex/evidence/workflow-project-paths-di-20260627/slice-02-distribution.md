# Slice 02 Distribution

Workflow ID: `workflow-project-paths-di-20260627`
Workflow version: `workflow-project-paths-di-v1.0.0`
Slice ID: `02`
Slice title: `Add ProjectPaths And Compatibility Facade`

## Affected Areas

- backend: `tiny_swarm_world.infrastructure.project_paths`
- tests: focused `ProjectPaths` contract coverage
- architecture: confirms path configuration remains infrastructure-owned

## Execution Mode

Sequential.

Parallel execution is rejected because the implementation and tests touch the
same module and test file as Slice 01 and form the foundation for later
adapter migration.

## Streams

- backend: Senior Python Automation Developer
- tests: Senior Tester
- architecture: Senior System Architect

Real subagents used: no.

Fallback role-based review used: yes.

Git worktrees used: no.

## Expected Touched Files

- `src/tiny_swarm_world/infrastructure/project_paths.py`
- `tests/infrastructure/test_project_paths.py`
- `.codex/evidence/workflow-project-paths-di-20260627/slice-02-distribution.md`
- `.codex/evidence/workflow-project-paths-di-20260627/slice-02-consolidation.md`

## Conflict Risks

- Low. The change is localized to the path module and its focused tests.

## Quality Gates

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_project_paths`

## Consolidation Plan

Implement `ProjectPaths`, run the focused test, inspect the diff, then commit
and push only Slice 02 files.
