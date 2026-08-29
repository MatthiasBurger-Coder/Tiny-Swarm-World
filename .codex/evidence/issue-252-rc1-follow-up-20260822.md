# Issue #252 RC1 Follow-up Evidence — 2026-08-22

Branch: `feature/classic-public-beta-rc1-stabilization`
Commit: `27ce3960da98a9ba124fd3f9ff5e003b13e89c60`

## Decision

`INCOMPLETE`

The requested open points were rechecked. Local implementation and quality
evidence are green, but the release evidence is still incomplete.

## Observed evidence

- Focused Composition/Classic/CI contract tests: PASS, 127 tests.
- Full WSL2 quality gate: PASS, 1,775 tests with 18 expected skips.
- GitHub Python Quality Gate rerun `32529513788`: PASS on the feature SHA;
  no Sonar run was emitted for that rerun.
- Authorized WSL2 Fresh Install run `20260822T095424Z`: reset exit 0,
  setup exit 1, `LIVE_FAILED_AFTER_MUTATION`.
- Failure point: `deployment:traefik-stack` and
  `traefik=connection_error`.
- `TSW_TRAEFIK_GUI_USERS_SECRET_NAME=tsw_traefik_gui_users` is present in the
  local environment and Compose contract. After the reset, the manager
  contained only the generated TLS secrets; the named
  `tsw_traefik_gui_users` Docker Swarm secret was absent.
- The contract documents this as operator-provided htpasswd material. The
  current installer carries only the external secret name through composition;
  it has no htpasswd value to recreate the secret after a managed-node reset.
  This is a lifecycle gap, not a naming mismatch.
- Native Linux: unavailable; current host is WSL2.
- SonarCloud: no observable run for this feature commit; the older green
  `main` run is not valid branch evidence. The feature branch uses the
  `workflow_run` Sonar design, while the default-branch workflow is the older
  main-only design; rerunning the quality job therefore did not create a
  current-branch Sonar result.
- Self-hosted runner inventory: zero repository runners; no eligible
  `[self-hosted, linux, tsw-classic]` execution exists. The protected
  `tiny-swarm-world-classic-live` environment and target-owner variable are
  also not present in the current repository settings.

## Architecture decision

No change to `composition.py` is required or justified by these findings.
Generating or silently injecting the Traefik htpasswd value would violate the
existing operator-owned secret contract and would invalidate the evidence.

## Final RC1 decision

`RC1_REJECTED_EVIDENCE_INCOMPLETE`

The complete requirement matrix and redacted local package are under
`.tiny-swarm/evidence/issue-252/`.
