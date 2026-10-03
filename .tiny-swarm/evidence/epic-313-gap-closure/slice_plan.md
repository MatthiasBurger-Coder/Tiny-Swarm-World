# EPIC 03 gap-closure slices

Branch: fix/epic-03-orchestration-boundaries. Baseline: 7e15d539.
Existing #355 workflow is DONE on another branch and is preserved; this is a direct user-authorized EPIC remediation, not workflow execute/create. No active competing implementation locks found.

1. S313-01 CLI ownership (CLI worker): __main__.py, cli_presentation.py compatibility surface, infrastructure/adapters/cli/**, relevant CLI/host integration tests. Split parser/registry/consent/dispatcher/rendering by responsibility. Preserve all19commands/options/prompts/exits. Do not write shared architecture tests, quality tooling, docs or installer files.
2. S313-02 installer ownership (installer worker): installer.py, simple_installer.py where caller migration needs it, application/ports/installation*.py, application/services/installation*.py, infrastructure/adapters/installation/**, infrastructure/composition_installation.py, installer/simple/prepare tests. Separate sequencing from host/config/process/evidence/presentation. Keep native bootstrap dependency-light and existing guards unchanged. Do not write CLI/architecture/tools/docs.
3. S313-03 integration/governance (root): .importlinter, architecture tests, quality source targets, reviewed complexity baseline updates only for relocated responsibility owners, arc42/developer guides and this EPIC evidence. Independent read-only requirement, architecture, security and completion reviews.

Streams01/02 own disjoint files and use isolated worktrees/branches; root integrates explicit patches, never stream merges. Reviewers read-only. Root owns final consolidation, targeted and full quality, evidence and final completion. No commit/push/PR/merge is requested.

Verification: CLI/installer/bootstrap/prepare/host tests first; dependency/architecture mutation tests and lint/typecheck/complexity; python3 tools/quality_gate.py quality. Baseline current gate passed2377tests/18existing skips in prior audit.

Applicability: APPLICABLE_LOCAL. Live/browser initially NOT_APPLICABLE for strict responsibility extraction, contingent on independent command/state/safety parity review. Existing #363/#427 live runs retain actual revision attribution; any behavioral deviation needs a separate applicability/consent assessment. External gate unavailable/not executed; no new Sonar/CI/RC1 success claim.
