# Issue #444 — LCM-W04 integration record

Branch: feat/issue-444-selective-setup. Baseline: 2363ade0 (completed W03 / #443).
The retained issue-355 workflow is locally complete and unrelated; it has no
active #444 slice locks. This issue request authorizes implementation, not workflow
regeneration, commit/push or live infrastructure changes.

Requirements and acceptance: #444 and parent #440 LCM-04/05. Stable matrix and
executed evidence: `.tiny-swarm/evidence/issue-444/`. Local gate authority:
QUALITY.md and the canonical verification-state policy.

Architecture: reuse SelectionPlan, native catalog, W02 instance manifest/CAS,
existing setup phases, provider reconciliation and service adapters. No new
orchestrator, service catalog, runtime backend or destructive path.

Distribution: root owns composition/CLI/state/docs integration. Isolated
feat/issue-444-routing, feat/issue-444-artifacts and feat/issue-444-tests worktrees
own disjoint routing, artifact and focused integration/state tests. Parent applies
reviewed diffs serially and owns all final checks. Workers do not commit or merge.
Independent Senior System Architect reviews requirements and integration; final
issue-completion-auditor review is separate from implementation ownership.

Applicability: unit, composition, architecture, mock/runtime-boundary tests are
APPLICABLE_LOCAL. Installation/browser preservation is APPLICABLE_LIVE with
LIVE_CONSENT_MISSING; #449/W09 owns native/WSL qualification. External gate results
are unavailable here and no external success is claimed. Missing declarations
remain unknown; fixed topology/provider budgets are disclosed separately.

Review corrections: direct localhost access when Traefik is omitted; Infisical
sync before Jenkins without dashboard; WSL selected bridge registry; effective
image/version/provenance inventory; unchanged metadata no-op; stale/CAS and
persistence-partial handling; host-mismatch/unmanaged-install refusal. No live
commands, secret values, credential rotation or resets are part of development.
