# Issue #252 — S252-05 Distribution Decision

- Workflow: `issue-252-classic-public-beta-rc1-20260818`
- Slice: `S252-05` — WSL2 post-install acceptance and reconcile
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Affected areas: runtime, tests, security, live evidence
- Execution mode: sequential
- Selected streams: runtime, tests, live-evidence validation
- Real subagents: unavailable in this execution context
- Fallback review: explicit role-based review by Senior DevOps, Senior Tester,
  Senior Python Automation Developer, Senior System Architect and Live Evidence
  Validation Expert
- Git worktrees: not used; the live target and evidence lock are shared

## Scope and locks

- Expected ignored evidence paths:
  `.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S04/` and
  `RC1-S05/`
- Tracked governance evidence path:
  `.codex/evidence/slice-S252-05-consolidation.md`
- File lock: `.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/`
- Contract locks: service acceptance, reconcile, redaction
- Architecture locks: service-boundary ownership, observed readiness,
  no-duplicate state

## Parallelization decision

Parallel execution is rejected. The acceptance run and reconcile share the
same WSL2 Incus/Docker/Swarm target, credentials, ports and service state. The
before/after inventory must be serialized to distinguish no-op convergence from
drift, duplicate state or unintended destruction. Running another runtime or
test stream concurrently would invalidate the evidence.

## Preconditions

- S252-04 recovery evidence exists and records the current Traefik CA bundle.
- The local requirement matrix and Three-Amigos baseline are present.
- Explicit live authorization was provided by the user in this conversation.
- The operator env file is loaded only inside the WSL command process; values
  are not emitted into evidence.
- `platform verify --json` with the WSL filesystem override passed before the
  mutating reconcile.

## Checks

- Targeted: `./tsw --json ... platform verify`
- Live: `platform reconcile --live --approve-live`
- Acceptance: `PYTHONPATH=src .venv/bin/python -m unittest discover -s
  tests/e2e/classic -t .`
- Required: `python3 tools/quality_gate.py quality`
- Evidence must be redacted, include exit state and timing, and preserve the
  distinction between verified, failed-to-verify and blocked states.

## Consolidation plan

Capture redacted before/after node, stack, service, routing and secret-name
inventories; run the live reconcile; rerun the complete Classic suite with the
current CA bundle; compare object identities and readiness; then record the
result and any defect without exposing credentials.
