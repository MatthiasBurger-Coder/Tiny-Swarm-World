# Issue #252 — S252-07 Distribution Decision

- Workflow: `issue-252-classic-public-beta-rc1-20260818`
- Slice: `S252-07` — WSL2 failure, recovery and restart resilience
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Affected areas: runtime, tests, security, live evidence
- Execution mode: sequential
- Selected streams: runtime diagnostics, fail-closed tests, recovery evidence
- Real subagents: unavailable in this execution context
- Fallback review: explicit role-based review by Senior DevOps, Senior Tester,
  Senior Python Automation Developer, Senior System Architect and Live Evidence
  Validation Expert
- Git worktrees: not used; the WSL2/Incus/Swarm target and evidence lock are
  shared

## Planned checks

- Process-local missing-config preflight must fail before mutation.
- Existing deterministic lifecycle tests must keep partial and ambiguous state
  non-success and verify same-identity restart semantics.
- WSL2 restart must be performed once through the host lifecycle control, then
  diagnostics, platform verification, service readiness and Classic acceptance
  must be rerun from a fresh WSL process.
- Recovery must reuse the existing valid Incus/Swarm state; no reset, destroy,
  secret deletion or broad cleanup is authorized in this slice.

## Scope and locks

- Expected ignored evidence paths:
  `.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S07/`,
  `RC1-S08/` and `RC1-S09/`
- Tracked governance evidence path:
  `.codex/evidence/slice-S252-07-consolidation.md`
- File lock: `.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/`
- Contract locks: fail-closed state, recovery, restart evidence
- Architecture locks: ownership-scoped cleanup, no unsafe repair,
  live-state classification

Parallel execution is rejected because failure injection, WSL lifecycle,
recovery and readiness checks all share the same live target and must preserve
causal ordering.

## Stop conditions

Stop on failure after mutation without recovery, ambiguous state requiring
manual repair, unavailable restart path, unclear cleanup ownership, service
regression, raw sensitive output or incomplete evidence. A non-success
scenario remains explicitly non-passed.
