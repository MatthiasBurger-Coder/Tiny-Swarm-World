# Implementation Plan

Status: `AUTHORED_PENDING_EXECUTION`
Workflow: `documentation/workflow/workflow.md`

## Outcome

Close only Issue #157's productive routing-evidence, optional-route,
browser-matrix and dashboard-test gaps while preserving the current central
access model and live-safety boundaries.

## Slices

1. Effective model seam and positive optional routes.
2. Productive redacted routing evidence.
3. Renderer-centric dashboard verification.
4. Dynamic browser expectations and deterministic suite summary.
5. Documentation, complete evidence, all local quality gates and independent
   completion audit.
6. Guarded branch/PR publication, required checks, SonarCloud and review
   fixing loop.

## Execution Groups

```text
G1: 01
G2: 02 || 03 || 04 (isolated worktrees only)
G3: 05
G4: 06
```

## Core Design

- One effective model port implemented by the existing compose/config adapter.
- One application evidence use case.
- One dedicated routing-evidence persistence port/adapter.
- Fixed redacted evidence projection.
- Effective-model links define browser suite membership.
- Renderer output defines dashboard tests; committed HTML has one drift test.

## Verification

Run slice-targeted `unittest` commands first, then:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
```

No live infrastructure belongs to the default plan.
