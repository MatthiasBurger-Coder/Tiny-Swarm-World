# Issue #252 Completion Audit

- Commit audited: `a552a8fa33fd742f55895e84a8b563a9eca2ad94`
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Pull request: `#265` (open, draft, mergeable; no merge performed)
- Host used: WSL2 only

## Audit decision

`INCOMPLETE`

The implementation and verification evidence are substantial, but the issue
cannot receive a PASS because required independent host and external-gate
evidence remains open.

## Perspectives reviewed

- Requirement Lead: the issue matrix contains the lifecycle, CI, evidence and
  exact-decision requirements; open rows remain visible.
- System Architect Reviewer: the restart fix stays in the existing network
  infrastructure adapter, preserves Incus/LXC -> Docker Swarm boundaries and
  does not change `composition.py` or introduce a local bypass.
- Test / Evidence Reviewer: focused regression, full local quality, WSL2 live
  acceptance, hosted Quality/Conda checks and redaction evidence were checked;
  missing Native Linux, Sonar and self-hosted-live evidence remains explicit.

Callable subagents were unavailable, so the repository workflow's documented
role-based fallback review was used. This is not a PASS claim.

## Verified requirements and evidence

- WSL2 reconcile and update: `.codex/evidence/slice-S252-05-consolidation.md`
  and `slice-S252-06-consolidation.md`.
- WSL2 fail-closed, restart recovery and fixed bridge boot race:
  `.codex/evidence/slice-S252-07-consolidation.md`.
- Restart defect: `RC1_BLOCKER` reproduced, bounded root-cause fix committed
  in `25b9d790`, regression-tested and live-reverified.
- Local quality: `python3 tools/quality_gate.py quality` PASS, 1775 tests,
  18 expected skips.
- Hosted Quality and Conda matrix: runs `32529068741` and `32529073364` PASS
  for commit `a552a8fa`.
- Required issue evidence package: all six files exist under
  `.tiny-swarm/evidence/issue-252/` and are redaction-aware.

## Open requirements

- Fresh Install must be independently green; the historical run failed after
  mutation and later recovery is not a Fresh Install replacement.
- Native Linux Fresh Install, Acceptance, Reconcile, Acceptance, Update and
  Acceptance have not run. WSL2 is not a substitute.
- Full live failure-injection breadth for Incus, storage, network and related
  prerequisite classes is not complete.
- Sonar external status is unavailable for this feature branch.
- No verified self-hosted `tsw-classic` runner and protected target approval
  produced a real `nightly-classic-live.yml` run.
- Final evidence consolidation/audit cannot close the issue while these rows
  remain open.

## Final RC1 decision for this run

`RC1_REJECTED_EVIDENCE_INCOMPLETE`

`RC1_ACCEPTED` is prohibited. The WSL2 blocker fixed in this run is not being
waived, and missing host/external evidence is not being inferred from local or
WSL2 results.
