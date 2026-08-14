# Issue #252 — S252-02 Consolidation

- Workflow: `issue-252-classic-public-beta-rc1-20260814`
- Slice: `S252-02` — Canonical test layout and tool/test separation
- Branch: `docs/workflow-issue-252-classic-public-beta-20260814`
- Result: `S252-02_READY_FOR_S252-03`
- Codex integration owner: yes

## Distribution and review

One real Senior Tester subagent was assigned as a review-only stream. It made
no changes and returned a review confirming the canonical target, warning
about stale `tests.live` imports, external Selenium assets and evidence-root
consistency. Codex incorporated those findings in the main serial stream.
The remaining role perspectives were performed as the required explicit
fallback review because no parallel write stream was safe under the shared
test-root locks.

## Accepted changes

- Created the canonical `tests/e2e/classic/` package.
- Migrated the post-install HTTP/API/evidence suite from
  `tests/live/test_post_install_browser_live.py`.
- Migrated the browser route contract and all Classic browser wrappers from
  `tests/live/` into the canonical package, updating imports and module
  references.
- Reconciled the former integration runner's installed-surface/dashboard
  contract into the canonical suite and removed the duplicate Playwright
  post-install runner. Playwright remains only in the explicitly excluded
  Vaultwarden asset, which is not part of the Classic profile.
- Moved the default browser/live evidence root to
  `.tiny-swarm-world/evidence/classic-public-beta-rc1` while retaining
  opt-in environment overrides for later host/scenario runs.
- Kept routing contracts under `tests/integration/`, fixtures under
  `tests/support/`, and utilities under `tools/`; no assertion suite was moved
  into tooling.

## Checks executed

- Canonical E2E discovery through WSL — PASS; 80 tests, 17 opt-in live tests
  skipped.
- Integration routing discovery through WSL — PASS; 35 tests.
- Focused canonical/live contract selection — PASS; 49 tests, 8 opt-in live
  tests skipped.
- `python3 tools/quality_gate.py lint` — PASS.
- `python3 tools/quality_gate.py arch-tests` — PASS; 18 tests.
- `python3 tools/quality_gate.py test` — PASS; 1,756 tests, 18 skipped.
- `python3 tools/quality_gate.py quality` — PASS; policy, lint, arch-lint,
  arch-tests, mypy and full unittest gate all passed.
- `git diff --check` — PASS.
- Live Incus/Docker/Swarm/browser/SonarQube checks — NOT RUN; no live consent.

## Residual boundaries

- `tests/integration/` intentionally retains routing contract tests; this is a
  layer boundary, not a second post-install browser runner.
- The excluded Vaultwarden Playwright asset remains outside Classic and does
  not contribute to RC1 acceptance.
- S252-03 must add deterministic lifecycle, failure/recovery, idempotence,
  update-preservation and redaction assertions.
- No RC1 release decision is implied; all host/live requirements remain open.

## Handoff

The canonical suite is discoverable, opt-in, redaction-aware and free of stale
`tests.live` imports. S252-03 may start on the clean pushed checkpoint.
