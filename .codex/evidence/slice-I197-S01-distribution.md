# Slice Distribution — I197-S01

Workflow: issue-197-20260809
Workflow version: issue-197-v1.0.0
Slice ID: I197-S01
Slice title: Freeze ownership matrix and tests

## Execution decision

- Serial execution after I156-S09 PASS.
- Streams reviewed: requirements, architecture, Python infrastructure, tests, quality and safety.
- No real subagent tool is visible; explicit role-based fallback review will be recorded.
- No parallel worktree: the slice freezes shared composition/exposure ownership and issue evidence.
- Expected output: inventory of every Socat helper/caller/result/test guard and execution evidence for the #197 matrix.
- No implementation refactor or live command is in scope for this baseline slice.

## Locks and gates

- File locks: `src/tiny_swarm_world/infrastructure/composition.py`, `tests/infrastructure/test_composition.py`, network adapter/application paths and `.tiny-swarm/evidence/issue-197/**`.
- Contract lock: `I197-current-socat-contract`.
- Architecture lock: no domain/application subprocess.
- Targeted gate: `git diff --check`.
- Stop conditions: unknown caller, unobservable consent semantics or missing upstream audit.

## Role review

- Senior Requirement Engineer: map all eight REQ-197 rows to current helpers/tests.
- Senior System Architect: identify the valid infrastructure adapter boundary.
- Senior Python Automation Developer: inspect process command semantics without changing them.
- Senior Tester: identify all six behavior cases and test isolation.
