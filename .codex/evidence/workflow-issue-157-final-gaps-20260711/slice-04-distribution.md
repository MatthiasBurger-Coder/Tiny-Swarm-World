# Slice 04 Distribution Decision

Workflow ID: `workflow-issue-157-final-gaps-20260711`

Workflow version: `workflow-issue-157-final-gaps-v1.0.0`

Slice ID: `04`

Title: `Dynamic Browser Expectations And Deterministic Summary`

## Decision

- S3D result: `EXECUTION_PLAN`.
- Dependency `01`: satisfied by commit `578f5e57d28cc5c6536781d88e88bd6cc7b69cea`.
- Execution mode: `parallel` within G2, isolated from Slices 02 and 03.
- Selected streams: `tests`, `architecture`, `security`, `live-evidence`.
- Real subagent used: `yes`.
- Fallback role review: `no`.
- Git worktree used: `yes`.
- Stream branch: `fix/issue-157-final-gaps-20260711-slice-04-tests`.

## Expected Files And Locks

- `tests/live/browser_e2e_contract.py`
- `tests/live/test_post_install_browser_live.py`
- `tests/live/test_observability_browser_e2e.py`
- `tests/live/test_tiny_swarm_app_browser_e2e.py`
- this distribution file and `slice-04-consolidation.md`

Contracts:

- expected suite membership comes from current effective-model `service_access_links`;
- hardcoded data remains login metadata only;
- disabled/non-profile routes are not false failures;
- every expected route is passed, failed, skipped or missing;
- missing is explicit and forces failed suite status;
- ordering/result precedence is deterministic;
- live Selenium remains current-consent opt-in and static gates remain infrastructure-free.

## Conflict Risks

- No file lock overlaps Slices 02 or 03.
- Slice 01 model seam/fixture are read-only inputs.
- Stale ignored route files must not define current membership.
- No raw credentials, env files, browser, DNS, Docker or Traefik access is permitted during static execution.

## Quality Gates

```bash
PYTHONPATH=src python3 -m unittest tests.live.browser_e2e_contract
PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live.StaticPostInstallLiveSuiteTest
PYTHONPATH=src python3 -m unittest tests.live.test_observability_browser_e2e tests.live.test_tiny_swarm_app_browser_e2e
python3 tools/quality_gate.py quality
git diff --check
```

Live Selenium is not authorized by this static stream.

## Consolidation Plan

The assigned subagent performs a read-only live-evidence/test gate, implements
only the locked files, runs targeted and full static verification, and writes
`slice-04-consolidation.md`. The worker does not merge or push. Root Codex
reviews and consolidates this slice third in G2 order.
