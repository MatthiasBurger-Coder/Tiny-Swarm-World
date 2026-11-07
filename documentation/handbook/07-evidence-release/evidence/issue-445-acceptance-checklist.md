# Acceptance checklist — issue #445

- [x] AC1: discovery/preview avoid runtime composition, commands and writes;
  file-content/mtime and mock assertions verify both successful and refused calls.
- [x] AC2: unsupported transitions/downgrades, uninstalled/unknown/invalid service
  selections fail explicitly; no mutation or implicit service admission.
- [x] AC3: deterministic selected batch order, exact bundle identities,
  compatibility, availability impact, migration/backup/recovery restrictions.
- [x] AC4: native baseline references remain distinct from qualified targets;
  latest is rejected by policy and zero native upgrades are fabricated.
- [x] No-op requires recorded immutable desired/observed agreement with no drift;
  missing/mismatched metadata cannot be hidden by matching image digests.
- [x] Portainer dedicated-path classification and Incus host-owner refusal.
- [x] CLI help and argument validation; preview-only route refuses live consent.
- [x] Operator documentation and requirement-to-evidence matrix exist.
- [x] Independent requirement and architecture perspectives PASS.
- [x] Full local quality PASS on the byte-matched Linux verification worktree
  with Python 3.12.14: 2747 tests, 18 opt-in skips.
- [x] Independent final completion audit PASS; requirement, architecture and
  test/evidence perspectives PASS. R445-01–08 verified; no open requirements.

Live: LIVE_NOT_APPLICABLE; external: EXTERNAL_GATE_NOT_APPLICABLE for local
completion. W09 retains actual native Linux and WSL2 qualification ownership.
