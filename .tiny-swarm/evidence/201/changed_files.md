# Issue #201 Changed Files

## Repository files

- `AGENTS.md` — references the canonical policy from testing and workflow governance.
- `QUALITY.md` — references the policy and defines non-success handling for optional gates.
- `documentation/process/verification-state-policy.md` — canonical policy.
- `documentation/process/issue-completion-discipline.md` — policy reference.
- `documentation/process/workflow-create.md` — policy reference and live-gate classification rule.
- `documentation/process/workflow-execute.md` — policy reference and non-success rule.
- `documentation/workflow/workflow.md` — policy reference for the active completed workflow.
- `documentation/process/skills/audit/skill-registry.json` — refreshed SHA-256 cache for changed governing files.
- `tools/check_verification_policy_consistency.py` — deterministic policy and wording checker.
- `tools/quality_gate.py` — runs the policy checker as part of `quality`.
- `tests/tools/test_check_verification_policy_consistency.py` — focused checker tests.

## Issue evidence

- `.tiny-swarm/evidence/201/requirement_matrix.md`
- `.tiny-swarm/evidence/201/implementation_summary.md`
- `.tiny-swarm/evidence/201/changed_files.md`
- `.tiny-swarm/evidence/201/test_results.md`
- `.tiny-swarm/evidence/201/remaining_risks.md`
- `.tiny-swarm/evidence/201/acceptance_checklist.md`
- `.tiny-swarm/evidence/201/issue-correction-bundle.md`
- `.tiny-swarm/evidence/201/audit-before.md`
- `.tiny-swarm/evidence/201/three-amigos.md`
- `.tiny-swarm/evidence/201/policy-reference-map.md`
- `.tiny-swarm/evidence/201/blockers.md`
- `.tiny-swarm/evidence/201/completion-report.md`

## Explicitly unchanged

- `.tiny-swarm-world/local/live-installation.env` — not read for values, not changed, and not committed.
- Product source, infrastructure configuration, and runtime deployment assets — unchanged.
