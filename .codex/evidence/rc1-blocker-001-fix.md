# RC1_BLOCKER-001 — Fix Loop Status

- Issue: #252
- Scenario owner: `RC1-01 WSL2 CLEAN FRESH INSTALL`
- Classification: `RC1_BLOCKER`
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Commit under test: `27ce3960da98a9ba124fd3f9ff5e003b13e89c60` plus the
  uncommitted blocker-fix changes in this worktree
- Real RC1 re-run: `NOT_RUN`
- Current RC1 result: `BLOCKED` — operator htpasswd material is not present in
  the local WSL2 installation environment, so no destructive reset was started
  after the fix.

## Observed

After reset, Traefik could not converge because the external Docker secret
named by `TSW_TRAEFIK_GUI_USERS_SECRET_NAME` was absent.

## Root cause

The deployment composition declared the external secret name but had no
operator-owned value source or post-reset provisioning step. Reset removed the
previous Swarm state and the subsequent Traefik stack apply therefore
referenced a non-existent external secret.

## Fix implemented

- Added required operator input `TSW_TRAEFIK_GUI_USERS_HTPASSWD`.
- Installer fails before fresh reset when that value is missing.
- Deployment apply idempotently creates the named external Docker secret from
  the operator value before any Traefik stack apply.
- Deployment apply verifies the secret exists through the Swarm runtime before
  continuing.
- Existing secret lifecycle ports and adapters are reused; no generated or
  placeholder value is accepted.
- Evidence and diagnostic paths contain only presence/state metadata, never the
  htpasswd value.

## Verification

- Focused regression tests: `PASS` — 161 tests.
- Installer and repository-hygiene tests: `PASS` — 27 tests.
- Full regression suite: `PASS` — 1,780 tests, 18 skipped.
- Full quality gate: `PASS` — verification policy, lint, architecture lint,
  architecture tests, typecheck, and full regression suite.

## Required next action

The operator must place the complete htpasswd content (not a clear-text
password) in the ignored `.tiny-swarm-world/local/live-installation.env` as
`TSW_TRAEFIK_GUI_USERS_HTPASSWD`, then the workflow must clean the WSL2 state
and rerun RC1-01 from the beginning. No subsequent RC1 scenario is released by
this local verification.
