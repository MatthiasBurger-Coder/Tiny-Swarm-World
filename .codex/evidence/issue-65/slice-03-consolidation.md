# Slice 03 Consolidation: Issue 65 Regression

Workflow id: `issue-65-backend-resource-mapping-20260614`
Slice id: `S03`
Slice title: Focused regression and architecture tests

## Stream Results

- Architecture regression stream completed.
- Full unit-test stream completed.
- Documentation drift scan completed.

## Accepted Findings

- Backend-specific resource mapping did not break composition, preflight,
  provider selection, architecture tests, or the full unittest suite.
- Documentation still contains LXD-only bridge examples in the installation
  guide and must be updated in S04.
- `_lxc_reachable_host_ip()` still probes `lxdbr0` and `incusbr0`; this is an
  auto-detection helper, not the provider resource mapping used for LXC node
  launch.

## Rejected Findings

- No S03 blocker found.

## Files Changed Per Stream

Evidence:

- `.codex/evidence/issue-65/slice-03-distribution.md`
- `.codex/evidence/issue-65/slice-03-consolidation.md`

## Tests Executed

- `python3 tools/quality_gate.py arch-tests`
  - Passed, 16 tests.
- `python3 tools/quality_gate.py test`
  - Passed, 845 tests, 17 skipped.

## Documentation Drift

Detected S04 documentation candidates:

- `documentation/user_guide/installation.adoc` still uses LXD-only `lxdbr0`
  bridge wording and commands.

## Final Integration Decision

Accept S03. Route documentation drift and full quality evidence to S04.
