# Context Pack: Issue #218 FR-2

- Workflow: `workflow-issue-218-fr02-filesystem-policy-20260712`
- Version: `workflow-issue-218-fr02-v1.0.0`
- Branch: `feature/workflow-issue-218-fr02-filesystem-policy-20260712`
- Baseline: `main@81ca7efab062347a87c32e5305427236b048d741`
- Process: `workflow create -> workflow execute -> PR/CI/Sonar -> merge`
- Profile: `FULL_PATH`
- Gate: `READY_FOR_WORKFLOW`, 96 percent confidence
- Slice: one serial filesystem-policy slice; no parallel write streams
- Direct requirements: FR-002, AC-002 path portion, AC-003, UT-006..009,
  CLI-002, SEQ-002, DOC-005, DOD-003, FORBID-002, GOV-006
- Architecture: pure project-filesystem domain assessment, inspector/evidence
  ports, separate evaluate/authorize services, mountinfo/XDG adapters,
  composition-root wiring
- CLI: existing global `--preflight` is CLI-002 equivalent; exact override is
  `--allow-wsl-windows-filesystem`
- Safety: WSL Windows mount blocks by default; unknown WSL mount facts fail
  closed; override affects only that blocker; no auto move/copy
- Evidence: exact project path only in the atomic owner-only local XDG
  installation decision; general output and committed evidence stay path-free
- Baseline verification: 281 relevant tests pass; merged-main full gate passes
  1,456 tests with 28 expected skips; expected FR-2 RED is documented
- Required quality: focused and `CI=1`, lint, arch-lint, arch-tests, typecheck,
  test, full quality, diff check, GitHub Python 3.12, SonarCloud, merged-main
- Live validation: `NOT_RUN`; Incus/Docker/Swarm/network/service mutation is
  forbidden for this workflow
- Evidence roots:
  `.codex/evidence/workflow-issue-218-fr02-filesystem-policy-20260712/` and
  ignored `.tiny-swarm/evidence/issue-218-fr02/`

This navigation aid does not replace `AGENTS.md`, `QUALITY.md`, the issue
discipline, accepted ADRs, routing rules, skills, the complete requirement
matrix, or the workflow. Reopen authoritative files when a recorded hash
changes.
