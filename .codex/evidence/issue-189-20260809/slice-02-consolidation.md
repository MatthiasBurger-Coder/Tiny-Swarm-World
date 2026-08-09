# Issue #189 — S189-02 Consolidation

- Workflow: `issue-189-20260809` / `issue-189-v1.0.0`
- Slice: `S189-02` — Shared resolver/utilities and consumer migration
- Branch: `feature/centralize-lxc-shared-utilities-solid`
- Real subagents: not available in the current tool surface.
- Fallback review: completed by Codex using the required role and skill
  instructions; Codex remains the final integration owner.
- Result: `S189-02_READY_FOR_S189-03`

## Implemented contract

- Added `lxc/command/backend_cli.py` as the sole production source for
  `ManagedLxcBackend -> incus/lxc` resolution, exposed as an immutable mapping
  plus a typed resolver function.
- Migrated the twelve inventory consumers, including composition and provider
  preflight, without changing the product's Incus-first composition policy.
- Centralized timeout/non-zero command failure classification and delegated the
  legacy private predicates without moving adapter policy.
- Migrated the weaker adapter log truncation helpers to the canonical
  redacting/truncating diagnostics implementation while preserving their
  400-character compatibility default.
- Centralized manager-IP behavior in `lxc/services/common.py`; the legacy
  runtime keeps its private compatibility seam and delegates to the common
  implementation.
- Removed the duplicate remote-path implementation from stack asset transfer;
  the legacy facade and image publisher continue to use compatibility exports.
- Kept JSON/YAML parsing contracts local where payload ownership differs; the
  published-port parser remains a canonical Swarm helper with a legacy
  delegation rather than an unsafe generic parser.
- Added an architecture regression guard proving that only
  `lxc/command/backend_cli.py` defines the backend mapping.

## Files changed

- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/backend_cli.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/diagnostics.py`
- `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/__init__.py`
- Declared LXC client, service, image, Swarm, preflight and composition
  consumers from the corrected S189-02 scope.
- `tests/infrastructure/adapters/clients/lxc/command/test_backend_cli.py`
- `tests/infrastructure/adapters/clients/lxc/command/test_diagnostics.py`
- `tests/architecture/test_lxc_runtime_boundaries.py`

## Checks executed

- `git diff --check` — PASS.
- Targeted command/LXC/preflight/runtime suites — PASS; `191` tests passed.
- Composition, wiring and LXC boundary suite — PASS; `101` tests passed across
  the targeted reruns.
- `python3 tools/quality_gate.py lint` — PASS.
- `python3 tools/quality_gate.py typecheck` — PASS.
- `python3 tools/quality_gate.py arch-lint` — PASS.
- `python3 tools/quality_gate.py arch-tests` — PASS.
- `python3 tools/quality_gate.py quality` in WSL — PASS; `1682` tests passed,
  `28` skipped.
- Live/browser/SonarQube checks — not run; no success claim is made.

## Requirements and handoff

REQ-189-001 through REQ-189-006 now have implementation and local regression
evidence, but remain matrix-open until S189-03 completes the after-inventory,
final acceptance checklist and independent issue-completion audit. REQ-189-007
has the required Three-Amigos and before-inventory evidence. REQ-189-008 is
represented by explicit local-only/external-unavailable policy wording and is
not a claim of live or external verification.

S189-03 may now run the duplicate-after inventory, architecture/evidence
review, Arc42 planned-status synchronization and independent completion audit.
